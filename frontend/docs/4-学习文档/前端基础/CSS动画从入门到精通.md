# CSS 动画从入门到精通

> **目标读者**：CSS 动画新手
> **学习目标**：掌握 CSS 动画核心概念，能独立实现常见 UI 动效

---

## 1. 动画基础：两种实现方式

CSS 动画有两种实现方式，理解它们的区别是学习的第一步：

| 方式 | 触发条件 | 适用场景 | 控制粒度 |
|-----|---------|---------|---------|
| `transition` | 状态变化（hover、class 切换等） | 简单的 A → B 过渡 | 起点 + 终点 |
| `animation` | 自动播放 / 手动触发 | 复杂动画、循环、多关键帧 | 任意多个关键帧 |

### 1.1 Transition（过渡）

**核心思想**：告诉浏览器"当某个属性变化时，不要瞬间完成，而是平滑过渡"

```css
.button {
  background: blue;
  transition: background 0.3s ease;
  /*          ↑属性       ↑时长  ↑缓动函数 */
}

.button:hover {
  background: red;  /* hover 时，背景色会平滑变化 */
}
```

**完整语法**：
```css
transition: property duration timing-function delay;
/*          属性      时长     缓动函数        延迟 */

/* 示例 */
transition: all 0.3s ease 0s;
transition: transform 0.5s ease-out;
transition: opacity 0.2s linear, transform 0.3s ease;  /* 多属性 */
```

---

### 1.2 Animation（动画）

**核心思想**：定义一系列关键帧，浏览器自动补间

```css
/* 1. 定义关键帧 */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* 2. 应用动画 */
.element {
  animation: fadeIn 0.5s ease-out;
  /*         ↑名称  ↑时长 ↑缓动函数 */
}
```

**完整语法**：
```css
animation: name duration timing-function delay iteration-count direction fill-mode;
/*         名称 时长     缓动函数        延迟  播放次数        方向      填充模式 */

/* 示例 */
animation: fadeIn 0.5s ease-out 0s 1 normal forwards;
animation: spin 1s linear infinite;  /* 无限循环 */
```

---

## 2. 关键帧详解

### 2.1 基础语法

```css
@keyframes 动画名称 {
  from { /* 起始状态 */ }
  to { /* 结束状态 */ }
}

/* 或使用百分比（更精细控制） */
@keyframes bounce {
  0% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
  100% { transform: translateY(0); }
}
```

### 2.2 多属性动画

```css
@keyframes slideInFade {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
```

---

## 3. 缓动函数（Easing）

缓动函数决定动画的**速度曲线**，是动画"有灵魂"的关键！

### 3.1 内置缓动函数

| 名称 | 效果 | 适用场景 |
|-----|------|---------|
| `linear` | 匀速 | 加载动画、进度条 |
| `ease` | 慢-快-慢 | 默认值，通用 |
| `ease-in` | 慢-快（加速） | 离开动画 |
| `ease-out` | 快-慢（减速） | 进入动画 |
| `ease-in-out` | 慢-快-慢（对称） | 循环动画 |

### 3.2 速度曲线可视化

```
linear（匀速）：
████████████████ 恒定速度

ease-out（减速）：
████████████░░░░ 快 → 慢（自然着陆）

ease-in（加速）：
░░░░████████████ 慢 → 快（起飞感）

ease-in-out（加减速）：
░░░░████████░░░░ 慢 → 快 → 慢
```

### 3.3 自定义贝塞尔曲线

```css
/* cubic-bezier(x1, y1, x2, y2) */
transition: transform 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

**推荐工具**：
- [cubic-bezier.com](https://cubic-bezier.com/) - 可视化调试贝塞尔曲线
- [easings.net](https://easings.net/) - 常用缓动函数参考

---

## 4. Transform（变换）

`transform` 是动画中最常用的属性，因为它**不触发重排**，性能最好！

### 4.1 基础变换

| 函数 | 作用 | 示例 |
|-----|------|------|
| `translateX/Y/Z` | 平移 | `translateX(100px)` |
| `scale` | 缩放 | `scale(1.5)` 放大 1.5 倍 |
| `rotate` | 旋转 | `rotate(45deg)` |
| `skew` | 倾斜 | `skewX(10deg)` |

### 4.2 组合使用

```css
/* 注意：顺序会影响结果！ */
transform: translateX(100px) rotate(45deg);

/* 常见组合 */
transform: translate(-50%, -50%);  /* 居中技巧 */
transform: scale(1.1) translateY(-5px);  /* hover 放大 + 上浮 */
```

### 4.3 3D 变换

```css
/* 开启 3D 透视 */
.container {
  perspective: 1000px;
}

.card {
  transform: rotateY(180deg);  /* 翻转卡片 */
}
```

---

## 5. 性能优化

### 5.1 黄金法则：只动画这两个属性

| 属性 | 渲染层级 | 性能 |
|-----|---------|------|
| `transform` | Composite | ⚡ 最佳（GPU 加速） |
| `opacity` | Composite | ⚡ 最佳（GPU 加速） |
| `width/height` | Layout | 🐌 差（触发重排） |
| `margin/padding` | Layout | 🐌 差（触发重排） |
| `color/background` | Paint | 😐 中等（触发重绘） |

### 5.2 开启硬件加速

```css
.animated-element {
  /* 告诉浏览器：这个元素会变化，请做好准备 */
  will-change: transform, opacity;
  
  /* 或者用一个"无副作用"的 3D 变换触发 GPU 层 */
  transform: translateZ(0);
}
```

### 5.3 调试工具

Chrome DevTools → Performance 面板：
- 绿色条 = 合成层渲染（好）
- 紫色条 = 布局重排（需优化）
- 绿色条 = 绘制（一般）

---

## 6. 常见动画实战

### 6.1 淡入淡出

```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}
```

### 6.2 滑入滑出

```css
/* 从右侧滑入 */
@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 向右滑出 */
@keyframes slideOutRight {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}
```

### 6.3 弹跳效果

```css
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}

.element {
  animation: bounce 0.5s ease infinite;
}
```

### 6.4 旋转加载

```css
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loader {
  animation: spin 1s linear infinite;
}
```

### 6.5 心跳效果

```css
@keyframes heartbeat {
  0% { transform: scale(1); }
  25% { transform: scale(1.1); }
  50% { transform: scale(1); }
  75% { transform: scale(1.1); }
  100% { transform: scale(1); }
}
```

### 6.6 按钮 Hover 效果

```css
.button {
  transition: all 0.3s ease;
}

.button:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.button:active {
  transform: translateY(-1px);
  box-shadow: 0 5px 10px rgba(0, 0, 0, 0.2);
}
```

---

## 7. Vue 中的动画

### 7.1 Transition 组件

```vue
<template>
  <Transition name="fade">
    <div v-if="show">内容</div>
  </Transition>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
```

### 7.2 TransitionGroup 列表动画

```vue
<template>
  <TransitionGroup name="list" tag="ul">
    <li v-for="item in items" :key="item.id">{{ item.text }}</li>
  </TransitionGroup>
</template>

<style>
.list-enter-active,
.list-leave-active {
  transition: all 0.5s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.list-move {
  transition: transform 0.5s ease;
}
</style>
```

---

## 8. 学习资源

### 8.1 在线工具

| 工具 | 用途 | 链接 |
|-----|------|------|
| cubic-bezier | 贝塞尔曲线调试 | [cubic-bezier.com](https://cubic-bezier.com/) |
| easings.net | 缓动函数参考 | [easings.net](https://easings.net/) |
| Animista | 动画生成器 | [animista.net](https://animista.net/) |
| Keyframes.app | 可视化关键帧编辑 | [keyframes.app](https://keyframes.app/) |

### 8.2 学习路径

```
入门阶段（1-2 周）：
├── 理解 transition vs animation 区别
├── 掌握 transform 基础变换
├── 熟悉常用缓动函数
└── 实现 hover 效果、淡入淡出

进阶阶段（2-4 周）：
├── 学习贝塞尔曲线自定义
├── 掌握 @keyframes 复杂动画
├── 理解 will-change 和硬件加速
└── 在 Vue 中使用 Transition/TransitionGroup

精通阶段（持续）：
├── 研究知名网站的动画实现
├── 学习 FLIP 动画技术
├── 探索 CSS Houdini
└── 结合 JS 实现复杂交互动画
```

### 8.3 推荐阅读

- [MDN: Using CSS animations](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Animations/Using_CSS_animations)
- [MDN: Using CSS transitions](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Transitions/Using_CSS_transitions)
- [Vue: Transition](https://cn.vuejs.org/guide/built-ins/transition.html)
- [High Performance Animations](https://www.html5rocks.com/en/tutorials/speed/high-performance-animations/)

---

## 9. 练习建议

| 练习项目 | 涉及技能 | 难度 |
|---------|---------|------|
| 按钮 hover 效果 | transition, transform | ⭐ |
| 加载旋转动画 | @keyframes, infinite | ⭐ |
| 下拉菜单动画 | height transition, opacity | ⭐⭐ |
| Toast 通知动画 | slideIn/Out, TransitionGroup | ⭐⭐ |
| 卡片翻转效果 | 3D transform, perspective | ⭐⭐⭐ |
| 页面切换过渡 | Vue router transition | ⭐⭐⭐ |

---

> 💡 **学习心得**：CSS 动画的精髓在于**细节调优**——同样的动画，调整一下缓动函数、时长、延迟，效果可能天差地别。多观察优秀网站的动画实现，用 DevTools 分析它们的 CSS，是快速进步的捷径！
