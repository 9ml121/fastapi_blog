# Toast 通知组件设计

> **功能定位**：全局非阻塞式消息通知系统
> **技术栈**：Vue 3 + Pinia + TransitionGroup

---

## 1. 设计目标

| 目标 | 说明 |
|-----|------|
| **非阻塞** | 不打断用户操作流程，自动消失 |
| **全局可用** | 任意组件都能调用，无需传递 props |
| **类型丰富** | 支持 success/error/warning/info 四种类型 |
| **动画流畅** | 进入、退出、列表重排都有过渡动画 |

---

## 2. 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│  调用方（任意组件）                                          │
│  toastStore.success('操作成功')                             │
└─────────────────────────────────────────────────────────────┘
                          ↓ 调用 addToast()
┌─────────────────────────────────────────────────────────────┐
│  toast.store.ts (Pinia Store)                               │
│  ├── toasts: Toast[]        ← 响应式数组                    │
│  ├── addToast()             ← 添加 + 自动定时删除           │
│  ├── removeToast()          ← 手动删除                      │
│  └── success/error/...      ← 便捷方法                      │
└─────────────────────────────────────────────────────────────┘
                          ↓ 响应式绑定
┌─────────────────────────────────────────────────────────────┐
│  ToastContainer.vue                                         │
│  └── <TransitionGroup>      ← 列表动画                      │
│        └── v-for Toast 卡片                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 核心技术点

### 3.1 为什么用 Pinia 而不是 Event Bus？

| 方案 | 优点 | 缺点 |
|-----|------|------|
| **Pinia Store** ✅ | 响应式、DevTools 可调试、类型安全 | 需要额外依赖 |
| Event Bus | 简单 | Vue 3 已废弃、无类型提示、难调试 |
| Provide/Inject | 官方方案 | 子组件才能访问，非全局 |

**结论**：Pinia 是 Vue 3 官方推荐的状态管理方案，最适合全局通知场景。

---

### 3.2 TransitionGroup 列表动画

```vue
<TransitionGroup name="toast">
  <div v-for="toast in toasts" :key="toast.id">...</div>
</TransitionGroup>
```

**关键点**：
- `<TransitionGroup>` 是 Vue 的内置组件，专门用于处理**列表**（即通过 `v-for` 渲染的多个元素）的动画。
- `name="toast"` 对应 CSS 类名前缀 `.toast-enter-active` 等
- 子元素必须有唯一 `key`（使用自增 ID）
- 支持三种动画：进入、离开、移动

**CSS 动画类**：

| 类名                    | 触发时机                                                    |
| --------------------- | ------------------------------------------------------- |
| `.toast-enter-active` | 当一个新的 Toast 被添加到数组中，Vue 会在它插入 DOM 的那一刻给它加上这个类。          |
| `.toast-leave-active` | 当一个 Toast 从数组中移除，Vue 不会立即把它从 DOM 删掉，而是先加上这个类，等动画播放完了再删。 |
| `.toast-move`         | 列表重排时（其他项移动）                                            |

---

### 3.3 CSS 动画详解

#### 3.3.1 Vue Transition 动画生命周期

```
进入动画 (Enter):
┌──────────┐   ┌──────────────────┐   ┌──────────┐
│ -enter   │ → │ -enter-active    │ → │ (正常)   │
│ -from    │   │ (动画进行中)      │   │          │
└──────────┘   └──────────────────┘   └──────────┘
  初始状态        应用动画/过渡          最终状态

离开动画 (Leave):
┌──────────┐   ┌──────────────────┐   ┌──────────┐
│ (正常)   │ → │ -leave-active    │ → │ -leave   │
│          │   │ (动画进行中)      │   │ -to      │
└──────────┘   └──────────────────┘   └──────────┘
  初始状态        应用动画/过渡          最终状态
```

#### 3.3.2 六个动画类的完整说明

| 类名 | 作用 | 存在时机 |
|-----|------|---------|
| `.toast-enter-from` | 进入的初始状态 | 元素插入前添加，插入后下一帧移除 |
| `.toast-enter-active` | 进入动画激活状态 | 整个进入动画期间存在 |
| `.toast-enter-to` | 进入的最终状态 | 插入后下一帧添加，动画完成后移除 |
| `.toast-leave-from` | 离开的初始状态 | 离开开始时添加，下一帧移除 |
| `.toast-leave-active` | 离开动画激活状态 | 整个离开动画期间存在 |
| `.toast-leave-to` | 离开的最终状态 | 离开开始后下一帧添加，动画完成后移除 |

#### 3.3.3 实际代码实现

**进入动画**：从右侧滑入 + 淡入

```css
/* 进入动画期间应用的样式 */
.toast-enter-active {
  animation: slideInRight 0.3s ease-out;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);  /* 起点：右侧屏幕外 */
    opacity: 0;
  }
  to {
    transform: translateX(0);     /* 终点：正常位置 */
    opacity: 1;
  }
}
```

**离开动画**：向右滑出 + 淡出

```css
/* 离开动画期间应用的样式 */
.toast-leave-active {
  animation: slideOutRight 0.3s ease-in;
}

@keyframes slideOutRight {
  from {
    transform: translateX(0);     /* 起点：正常位置 */
    opacity: 1;
  }
  to {
    transform: translateX(100%);  /* 终点：右侧屏幕外 */
    opacity: 0;
  }
}
```

**移动动画**：列表重排时的平滑过渡

```css
/* 当其他 Toast 因为一个被删除而移动位置时 */
.toast-move {
  transition: transform 0.3s ease;
}
```

- **`.toast-move`**：Vue 内部使用了一种叫 **FLIP** (First, Last, Invert, Play) 的技术。
    1. Vue 记下元素移动前的位置。
    2. Vue 记下元素移动后的位置。
    3. Vue 使用 `transform` 把元素“倒退”回原来的位置。
    4. Vue 移除“倒退”，并应用 `transition`，让元素平滑地过渡到新位置。
- **`transition: transform 0.3s ease`**：这行 CSS 告诉浏览器，“如果 `transform` 属性发生了变化，不要瞬间完成，而是用 0.3秒的时间平滑过渡”。
#### 3.3.4 动画属性对比

| 属性 | `animation` | `transition` |
|-----|-------------|--------------|
| 控制方式 | 自动播放 | 状态变化触发 |
| 关键帧 | 支持多个 `@keyframes` | 只有起点和终点 |
| 重复 | 支持循环 | 不支持 |
| 适用场景 | 复杂动画、进入/离开 | 简单过渡、移动 |

#### 3.3.5 为什么进入/离开用 animation，移动用 transition？

| 动画类型 | 选择 | 原因 |
|---------|------|------|
| 进入/离开 | `animation` | 需要从屏幕外开始，涉及多个属性变化 |
| 移动 | `transition` | 只有位置变化，Vue 会自动计算 `transform` |

#### 3.3.6 ease-out vs ease-in 的区别

```
ease-out（减速）：用于进入动画
████████████░░░░  快 → 慢（自然着陆感）

ease-in（加速）：用于离开动画
░░░░████████████  慢 → 快（逐渐消失感）

ease（默认）：
░░░░████████░░░░  慢 → 快 → 慢
```

**设计原则**：
- 进入用 `ease-out`：元素"冲进来"然后"稳稳停住"
- 离开用 `ease-in`：元素"慢慢启动"然后"飞走"

#### 3.3.7 交互细节：点击穿透 (Pointer Events)

新手容易忽略的一个细节：Toast 容器通常固定在页面上层（如右上角），即使它是透明的，默认也会挡住下面页面的点击事件。

**解决方案**：
1. 给容器设置 `pointer-events: none`，让鼠标点击"穿透"容器，直接触发下面的元素。
2. 给具体的 Toast 卡片设置 `pointer-events: auto`，恢复卡片的点击响应（以便点击关闭按钮）。

```css
.toast-container {
  pointer-events: none; /* 关键：不挡路 */
}
.toast {
  pointer-events: auto; /* 关键：自己能被点 */
}
```

#### 3.3.8 性能优化细节

在动画中，我们只改变 `transform` (位移) 和 `opacity` (透明度)。

*   **为什么不用 `right` 或 `margin-right` 做位移？**
    *   改变布局属性（如 `right`）会触发浏览器 **重排 (Reflow)**，CPU 消耗大，容易卡顿。
    *   改变 `transform` 只触发 **合成 (Composite)**，利用 GPU 硬件加速，能保证 60fps 的流畅度。

---

### 3.4 自动消失机制

```ts
function addToast(type, message, duration = 5000) {
  const id = nextId++
  toasts.value.push({ id, type, message })
  
  // 定时自动移除
  setTimeout(() => {
    removeToast(id)
  }, duration)
}
```

**设计决策**：
- 默认 5 秒自动消失
- 支持自定义时长
- 点击也可手动关闭

---

## 4. 文件结构

```
src/
├── stores/
│   └── toast.store.ts      # Pinia Store（状态管理）
├── components/
│   └── ToastContainer.vue  # 渲染组件（UI展示）
└── App.vue                 # 挂载 ToastContainer
```

---

## 5. 使用方式

```ts
import { useToastStore } from '@/stores/toast.store'

const toastStore = useToastStore()

// 四种类型
toastStore.success('操作成功')
toastStore.error('操作失败')
toastStore.warning('请注意')
toastStore.info('提示信息')

// 自定义时长（毫秒）
toastStore.addToast('error', '服务器繁忙', 8000)
```

---

## 6. 最佳实践

| 场景 | 推荐类型 | 时长建议 |
|-----|---------|---------|
| 操作成功 | `success` | 3-5 秒 |
| 操作失败 | `error` | 5-8 秒（让用户看清） |
| 警告提示 | `warning` | 5 秒 |
| 信息提示 | `info` | 3 秒 |

---

## 7. 相关文件

| 文件 | 说明 |
|-----|------|
| [toast.store.ts](file:///Users/limq/00-app/fastapi_blog/frontend/src/stores/toast.store.ts) | Pinia 状态管理 |
| [ToastContainer.vue](file:///Users/limq/00-app/fastapi_blog/frontend/src/components/ToastContainer.vue) | UI 渲染组件 |
