# 前端样式规范（Tailwind CSS）

基于 Tailwind CSS v4 和现代 Web 开发最佳实践

---

## 📚 目录

1. [核心概念](#核心概念)
2. [样式组织模式](#样式组织模式)
3. [常见 UI 模式](#常见-ui-模式)
4. [响应式设计](#响应式设计)
5. [暗色模式](#暗色模式)
6. [性能优化](#性能优化)
7. [最佳实践](#最佳实践)
8. [检查清单](#检查清单)

---

## 核心概念

### 什么是 Utility-First CSS？

Tailwind CSS 采用 **utility-first** 哲学，这意味着：

- ✅ **不写自定义 CSS**，而是组合预定义的实用类
- ✅ **样式和 HTML 紧密结合**，便于查看和修改
- ✅ **通过类名描述样式**，而不是通过语义类名

**对比示例**：

```html
<!-- ❌ 传统方式（Bootstrap + 自定义 CSS） -->
<div class="card card-highlight">
  <h3 class="card-title">标题</h3>
  <p class="card-text">内容</p>
</div>

<style>
  .card { background: white; border-radius: 8px; ... }
  .card-highlight { border: 2px solid blue; }
  .card-title { font-size: 18px; font-weight: bold; }
  .card-text { color: #666; }
</style>

<!-- ✅ Tailwind 方式（组合实用类） -->
<div class="bg-white rounded-lg border-2 border-blue-500 p-4">
  <h3 class="text-lg font-bold text-gray-900">标题</h3>
  <p class="text-gray-600">内容</p>
</div>
```

**为什么选择 Tailwind？**

| 维度 | Tailwind | 自定义 CSS |
|------|----------|-----------|
| 学习难度 | 低（学习 CSS 属性） | 中高（需要学习设计模式） |
| 开发速度 | 快（不用切换文件） | 慢（频繁切换 HTML 和 CSS） |
| 代码可维护性 | 高（样式定义在 HTML 旁边） | 低（CSS 和 HTML 分离） |
| 包体积 | 小（tree-shaking） | 取决于代码质量 |
| 自定义程度 | 灵活（扩展配置） | 完全自由 |

---

## 样式组织模式

### 三层样式架构

在 Vue 3 + Tailwind 项目中，样式分为三个层次：

```
┌─────────────────────────────────────────────────────────┐
│ 第 1 层：全局样式主题（style.css - @apply 指令）        │
│ ├─ 跨项目通用的组件类（卡片、按钮、表单等）            │
│ ├─ 全局颜色主题和变量                                   │
│ └─ 应该在 style.css 中定义                              │
├─────────────────────────────────────────────────────────┤
│ 第 2 层：组件内样式（Vue 组件脚本）                     │
│ ├─ 特定组件的样式常量和动态样式                        │
│ ├─ 使用 computed() 计算样式组合                         │
│ └─ 应该在组件的 <script setup> 中定义                   │
├─────────────────────────────────────────────────────────┤
│ 第 3 层：原子类（HTML 模板）                            │
│ ├─ 微小的样式调整（不超过 3-4 个类）                   │
│ ├─ 响应式前缀（sm:, md:, lg: 等）                       │
│ └─ 应该在模板中使用                                     │
└─────────────────────────────────────────────────────────┘
```

### Layer 1：全局主题（@apply 指令）

**目的**：定义整个项目通用的样式组件

**位置**：`src/style.css`

**示例**：

```css
/* src/style.css */

@import "tailwindcss";

/* ============ 通用组件样式 ============ */
@layer components {
  /* -------- 卡片组件 -------- */
  .card {
    @apply bg-white rounded-lg shadow-md transition-shadow;
  }

  .card-hover {
    @apply hover:shadow-lg cursor-pointer;
  }

  .card-highlight {
    @apply border-2 border-blue-500;
  }

  /* -------- 按钮组件 -------- */
  .btn {
    @apply inline-flex items-center justify-center px-4 py-2 rounded-lg transition-colors font-medium;
  }

  .btn-primary {
    @apply btn bg-blue-500 text-white hover:bg-blue-600 active:bg-blue-700;
  }

  .btn-secondary {
    @apply btn bg-gray-200 text-gray-700 hover:bg-gray-300 active:bg-gray-400;
  }

  .btn-danger {
    @apply btn bg-red-500 text-white hover:bg-red-600 active:bg-red-700;
  }

  /* -------- 表单元素 -------- */
  .input {
    @apply w-full px-4 py-2 border border-gray-300 rounded-lg transition-colors;
    @apply focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200;
  }

  .input-error {
    @apply border-red-500 focus:border-red-500 focus:ring-red-200;
  }

  .textarea {
    @apply input resize-vertical min-h-[120px];
  }

  /* -------- 文本样式 -------- */
  .text-primary {
    @apply text-lg font-bold text-gray-900;
  }

  .text-secondary {
    @apply text-sm text-gray-600;
  }

  .text-caption {
    @apply text-xs text-gray-500;
  }

  /* -------- 布局工具 -------- */
  .container-main {
    @apply max-w-6xl mx-auto px-4 py-8;
  }

  .flex-center {
    @apply flex items-center justify-center;
  }

  /* -------- 状态指示器 -------- */
  .badge {
    @apply inline-block px-3 py-1 rounded-full text-sm font-medium;
  }

  .badge-success {
    @apply bg-green-100 text-green-800;
  }

  .badge-warning {
    @apply bg-yellow-100 text-yellow-800;
  }

  .badge-error {
    @apply bg-red-100 text-red-800;
  }
}

/* ============ 全局样式 ============ */
html {
  scroll-behavior: smooth;
}

body {
  @apply bg-gray-50 text-gray-900;
}

/* 禁用平滑滚动（某些情况） */
@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto;
  }
}
```

**使用这些类的好处**：
- 避免在模板中重复长串的类名
- 集中管理项目的设计语言
- 修改样式只需改一个地方

### Layer 2：组件内样式（脚本部分）

**目的**：特定组件的样式定义和动态样式

**位置**：`<script setup lang="ts">` 中

**示例**：

```vue
<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  title: string
  isActive?: boolean
  variant?: 'default' | 'highlight' | 'danger'
}

const props = withDefaults(defineProps<Props>(), {
  isActive: false,
  variant: 'default'
})

// -------- 样式常量 --------
const baseClasses = 'bg-white rounded-lg p-4'

// -------- 动态样式 --------
const cardClasses = computed(() => {
  const variantStyles = {
    default: 'shadow-md hover:shadow-lg',
    highlight: 'border-2 border-blue-500 shadow-lg',
    danger: 'border-2 border-red-500 bg-red-50'
  }

  const activeClass = props.isActive ? 'ring-2 ring-blue-300' : ''

  return `${baseClasses} ${variantStyles[props.variant]} ${activeClass}`
})

// -------- 其他组件状态 --------
const isHovered = ref(false)
</script>

<template>
  <div :class="cardClasses" @mouseenter="isHovered = true" @mouseleave="isHovered = false">
    <h3 class="text-lg font-bold mb-2">{{ title }}</h3>
    <slot />
  </div>
</template>
```

**组件内样式的原则**：
- ✅ 使用常量存储不变的类组合
- ✅ 使用 `computed()` 实现动态样式
- ✅ 保持组件高度可复用
- ❌ 不要在模板中写超过 3-4 个类

### Layer 3：原子类（模板部分）

**目的**：在模板中使用 Tailwind 原子类进行微调

**规则**：
- ✅ 用于响应式前缀（`sm:`, `md:`, `lg:` 等）
- ✅ 用于交互状态（`hover:`, `focus:`, `active:` 等）
- ✅ 用于单独的微调修饰
- ❌ 不要在模板中写超过 4 个类

**示例**：

```vue
<template>
  <!-- ✅ 好：使用组件类 + 响应式前缀 -->
  <div class="card md:shadow-lg sm:rounded-md">
    <h3 class="text-primary sm:text-sm md:text-lg">标题</h3>
    <button class="btn-primary sm:w-full md:w-auto">提交</button>
  </div>

  <!-- ❌ 差：模板中类名过多 -->
  <div class="bg-white rounded-lg shadow-md hover:shadow-lg p-4 mb-4 border border-gray-200">
    <h3 class="text-lg font-bold text-gray-900 mb-2">标题</h3>
  </div>
</template>
```

---

## 常见 UI 模式

### 1. 卡片模式

**应用场景**：文章列表、用户卡片、功能展示

```vue
<!-- PostCard.vue -->
<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  title: string
  summary: string
  author: string
  createdAt: string
  featured?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  featured: false
})

const emit = defineEmits<{
  'post-clicked': [title: string]
}>()

// 样式定义
const cardClasses = computed(() => {
  const baseClasses = 'card card-hover p-6 mb-4'
  const featuredClass = props.featured ? 'card-highlight' : ''
  return `${baseClasses} ${featuredClass}`
})

const titleClasses = 'text-primary mb-2'
const summaryClasses = 'text-secondary mb-4 line-clamp-3'
const footerClasses = 'flex justify-between items-center text-caption'

const handleClick = () => {
  emit('post-clicked', props.title)
}
</script>

<template>
  <article :class="cardClasses" @click="handleClick">
    <h3 :class="titleClasses">{{ title }}</h3>
    <p :class="summaryClasses">{{ summary }}</p>
    <div :class="footerClasses">
      <span class="font-medium">{{ author }}</span>
      <span>{{ createdAt }}</span>
    </div>
  </article>
</template>
```

**卡片常用类**：
- `rounded-lg` - 圆角
- `shadow-md hover:shadow-lg` - 阴影和交互
- `p-4` - 内边距
- `border border-gray-200` - 边框

### 2. 按钮模式

**应用场景**：表单提交、操作触发、链接导航

```vue
<!-- Button.vue -->
<script setup lang="ts">
import { computed } from 'vue'

type ButtonVariant = 'primary' | 'secondary' | 'danger'
type ButtonSize = 'sm' | 'md' | 'lg'

interface Props {
  variant?: ButtonVariant
  size?: ButtonSize
  disabled?: boolean
  loading?: boolean
  fullWidth?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  disabled: false,
  loading: false,
  fullWidth: false
})

// 尺寸映射
const sizeClasses = {
  sm: 'px-3 py-1 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg'
}

// 样式计算
const buttonClasses = computed(() => {
  const variant = `btn-${props.variant}`
  const size = sizeClasses[props.size]
  const widthClass = props.fullWidth ? 'w-full' : ''
  const disabledClass = props.disabled ? 'opacity-50 cursor-not-allowed' : ''
  const loadingClass = props.loading ? 'pointer-events-none' : ''

  return `${variant} ${size} ${widthClass} ${disabledClass} ${loadingClass}`
})
</script>

<template>
  <button :class="buttonClasses" :disabled="disabled || loading">
    <span v-if="loading" class="inline-block mr-2 animate-spin">⏳</span>
    <slot />
  </button>
</template>
```

**按钮常用类**：
- `px-4 py-2` - 内边距（水平/垂直）
- `rounded-lg` - 圆角
- `font-bold` - 粗体
- `transition-colors` - 平滑过渡
- `hover:` `active:` `disabled:` - 交互状态

### 3. 表单模式

**应用场景**：用户输入、数据收集

```vue
<!-- LoginForm.vue -->
<script setup lang="ts">
import { ref, reactive } from 'vue'

const formData = reactive({
  email: '',
  password: ''
})

const errors = reactive({
  email: '',
  password: ''
})

const isLoading = ref(false)

const handleSubmit = async () => {
  isLoading.value = true
  // API 调用
  isLoading.value = false
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="max-w-md mx-auto">
    <!-- 邮箱字段 -->
    <div class="mb-4">
      <label class="block text-primary mb-2">邮箱</label>
      <input
        v-model="formData.email"
        type="email"
        placeholder="user@example.com"
        :class="['input', errors.email && 'input-error']"
      />
      <p v-if="errors.email" class="text-red-500 text-sm mt-1">{{ errors.email }}</p>
    </div>

    <!-- 密码字段 -->
    <div class="mb-6">
      <label class="block text-primary mb-2">密码</label>
      <input
        v-model="formData.password"
        type="password"
        placeholder="输入密码"
        :class="['input', errors.password && 'input-error']"
      />
      <p v-if="errors.password" class="text-red-500 text-sm mt-1">{{ errors.password }}</p>
    </div>

    <!-- 提交按钮 -->
    <button type="submit" class="btn-primary w-full" :disabled="isLoading">
      {{ isLoading ? '登录中...' : '登录' }}
    </button>
  </form>
</template>
```

**表单常用类**：
- `input` - 输入框样式
- `focus:ring-2 focus:ring-blue-200` - 焦点环
- `border-red-500` - 错误状态
- `mb-4` - 字段间距

### 4. 栅格布局

**应用场景**：多列布局、响应式网格

```vue
<!-- ArticleGrid.vue -->
<script setup lang="ts">
import { ref } from 'vue'

const articles = ref([
  { id: 1, title: '文章1', summary: '...' },
  { id: 2, title: '文章2', summary: '...' },
  { id: 3, title: '文章3', summary: '...' }
])
</script>

<template>
  <!-- 栅格布局：1 列（移动）→ 2 列（平板）→ 3 列（桌面） -->
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <article v-for="article in articles" :key="article.id" class="card">
      <h3 class="text-primary">{{ article.title }}</h3>
      <p class="text-secondary">{{ article.summary }}</p>
    </article>
  </div>
</template>
```

**栅格常用类**：
- `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3` - 响应式栅格
- `gap-4` - 元素间距
- `flex-col md:flex-row` - 响应式 Flex 方向

### 5. 导航栏模式

**应用场景**：网站顶部导航、侧边栏

```vue
<!-- Header.vue -->
<template>
  <header class="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg sticky top-0 z-50">
    <div class="container-main flex items-center justify-between">
      <!-- Logo -->
      <div class="flex items-center gap-3">
        <span class="text-3xl">📚</span>
        <h1 class="text-xl font-bold">FastAPI 博客</h1>
      </div>

      <!-- 导航链接 -->
      <nav class="hidden md:flex gap-6">
        <a href="/" class="hover:text-blue-200 transition-colors">首页</a>
        <a href="/posts" class="hover:text-blue-200 transition-colors">文章</a>
        <a href="/tags" class="hover:text-blue-200 transition-colors">标签</a>
      </nav>

      <!-- 用户菜单 -->
      <div class="flex items-center gap-3">
        <button class="btn btn-secondary md:inline-block hidden">登录</button>
        <!-- 移动端菜单按钮 -->
        <button class="md:hidden">≡</button>
      </div>
    </div>
  </header>
</template>
```

**导航栏常用类**：
- `sticky top-0 z-50` - 粘性导航
- `bg-gradient-to-r from-blue-600 to-blue-800` - 渐变背景
- `hidden md:flex` - 响应式显示/隐藏

---

## 响应式设计

### 响应式前缀

Tailwind 提供 **移动优先** 的响应式设计：

```vue
<template>
  <!-- 
    基础：移动端（< 640px）
    sm:  平板竖屏（≥ 640px）
    md:  平板横屏（≥ 768px）
    lg:  小屏电脑（≥ 1024px）
    xl:  电脑屏幕（≥ 1280px）
    2xl: 超大屏幕（≥ 1536px）
  -->

  <!-- 栅格示例 -->
  <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
    <article class="card">文章</article>
  </div>

  <!-- 文字大小 -->
  <h1 class="text-2xl sm:text-3xl md:text-4xl">响应式标题</h1>

  <!-- 内边距 -->
  <div class="p-2 sm:p-4 md:p-6 lg:p-8">内容</div>

  <!-- 显示/隐藏 -->
  <button class="md:hidden">移动端菜单</button>
  <nav class="hidden md:flex">桌面导航</nav>
</template>
```

**移动优先原则**：
- ✅ 先为移动设备设计（没有前缀）
- ✅ 然后逐步增强到更大屏幕（sm:, md: 等）
- ❌ 不要从 `lg:` 开始，然后回到基础样式

### 容器查询（可选高级特性）

```css
/* tailwind.config.js */
module.exports = {
  plugins: [
    require('@tailwindcss/container-queries'),
  ],
}
```

```vue
<template>
  <!-- 根据容器宽度，而不是视口宽度 -->
  <div class="@container">
    <div class="@md:grid @md:grid-cols-2">
      <article class="card">根据容器宽度响应</article>
    </div>
  </div>
</template>
```

---

## 暗色模式

### 启用暗色模式支持

```javascript
// tailwind.config.js
export default {
  darkMode: 'class', // 使用 class 策略（推荐）
  // darkMode: 'media', // 或使用系统偏好
}
```

### 使用暗色模式类

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'

const isDark = ref(false)

const handleToggleDark = () => {
  isDark.value = !isDark.value
  // 更新 HTML class
  if (isDark.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}
</script>

<template>
  <div>
    <!-- 使用 dark: 前缀定义暗色样式 -->
    <div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
      <h1 class="text-primary dark:text-blue-300">标题</h1>
      <button
        @click="handleToggleDark"
        class="btn-secondary dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
      >
        {{ isDark ? '🌙 暗色' : '☀️ 亮色' }}
      </button>
    </div>
  </div>
</template>
```

**暗色模式常用类**：
- `dark:bg-gray-900` - 暗色背景
- `dark:text-white` - 暗色文本
- `dark:border-gray-700` - 暗色边框
- `dark:hover:bg-gray-800` - 暗色交互态

### 全局暗色模式配置

```css
/* src/style.css */
@layer base {
  :root {
    color-scheme: light;
  }

  .dark {
    color-scheme: dark;
  }
}
```

---

## 性能优化

### 1. 避免动态类名

**❌ 问题代码**：
```vue
<script>
const bgColor = `bg-${condition ? 'blue' : 'red'}-500` // ❌ 动态生成类名
</script>

<template>
  <div :class="bgColor">内容</div>
</template>
```

Tailwind 无法识别这样的动态类名，最终类不会被包含在构建文件中。

**✅ 解决方案**：
```vue
<script setup lang="ts">
import { computed } from 'vue'

const bgColor = computed(() => {
  return condition ? 'bg-blue-500' : 'bg-red-500'
})
</script>

<template>
  <div :class="bgColor">内容</div>
</template>
```

或者使用 `clsx` / `classnames` 库：
```typescript
import clsx from 'clsx'

const buttonClasses = clsx(
  'btn px-4 py-2 rounded',
  {
    'bg-blue-500': isActive,
    'bg-gray-200': !isActive
  }
)
```

### 2. Tree-shaking 优化

Tailwind 会自动移除未使用的样式。要最大化效果：

```javascript
// tailwind.config.js
export default {
  content: [
    './src/**/*.{vue,js,ts,jsx,tsx}', // 扫描这些文件
  ],
}
```

### 3. 减少 CSS 包体积

```css
/* ❌ 避免：为所有元素添加样式 */
body {
  @apply text-gray-900 bg-white;
}

/* ✅ 推荐：只在需要时添加 */
@layer base {
  body {
    @apply text-gray-900 bg-white;
  }
}
```

### 4. 使用 PostCSS 压缩

项目自动配置的 Vite 会在生产环境压缩 CSS，无需额外配置。

---

## 最佳实践

### 1. 样式常量命名规范

```vue
<script setup lang="ts">
// ✅ 清晰的命名
const cardClasses = 'bg-white rounded-lg shadow-md'
const cardHoverClasses = 'hover:shadow-lg'
const titleClasses = 'text-lg font-bold text-gray-900'

// ❌ 模糊的命名
const s1 = 'bg-white'
const c = 'rounded-lg'
</script>
```

### 2. 使用 TypeScript 增强类型安全

```vue
<script setup lang="ts">
import { computed, type ComputedRef } from 'vue'

interface ButtonProps {
  variant: 'primary' | 'secondary' | 'danger'
  size: 'sm' | 'md' | 'lg'
  disabled?: boolean
}

const props = defineProps<ButtonProps>()

// ✅ 类型检查：不会出现打字错误
const variantMap: Record<ButtonProps['variant'], string> = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  danger: 'btn-danger'
}

const buttonClasses: ComputedRef<string> = computed(() => {
  return variantMap[props.variant]
})
</script>
```

### 3. 避免样式重复

**❌ 重复**：
```vue
<template>
  <div class="bg-white rounded-lg shadow-md p-4 mb-4">卡片 1</div>
  <div class="bg-white rounded-lg shadow-md p-4 mb-4">卡片 2</div>
  <div class="bg-white rounded-lg shadow-md p-4 mb-4">卡片 3</div>
</template>
```

**✅ 使用组件**：
```vue
<script setup lang="ts">
import Card from './Card.vue'
</script>

<template>
  <Card>卡片 1</Card>
  <Card>卡片 2</Card>
  <Card>卡片 3</Card>
</template>
```

**✅ 或使用样式常量**：
```vue
<script setup lang="ts">
const cardClasses = 'bg-white rounded-lg shadow-md p-4 mb-4'
</script>

<template>
  <div :class="cardClasses">卡片 1</div>
  <div :class="cardClasses">卡片 2</div>
  <div :class="cardClasses">卡片 3</div>
</template>
```

### 4. 颜色系统的一致性

```vue
<!-- 遵循项目的颜色主题 -->
<template>
  <!-- 主要操作 -->
  <button class="bg-blue-500 hover:bg-blue-600">保存</button>

  <!-- 危险操作 -->
  <button class="bg-red-500 hover:bg-red-600">删除</button>

  <!-- 次要操作 -->
  <button class="bg-gray-500 hover:bg-gray-600">取消</button>

  <!-- 成功状态 -->
  <span class="bg-green-100 text-green-800">✓ 已完成</span>

  <!-- 警告状态 -->
  <span class="bg-yellow-100 text-yellow-800">⚠ 注意</span>
</template>
```

### 5. 可访问性（Accessibility）

```vue
<template>
  <!-- ✅ 充分的颜色对比度 -->
  <button class="bg-blue-600 text-white">提交</button>

  <!-- ❌ 对比度不足 -->
  <button class="bg-blue-200 text-blue-300">提交</button>

  <!-- ✅ 焦点可见 -->
  <input class="focus:outline-none focus:ring-2 focus:ring-blue-500" />

  <!-- ✅ 响应式文字大小 -->
  <h1 class="text-xl md:text-3xl">标题</h1>

  <!-- ✅ 充分的点击区域（最少 44x44px） -->
  <button class="px-4 py-3">点击按钮</button>
</template>
```

---

## 项目中的实际应用

### Tailwind 4.0 配置（CSS-First 方式）

本项目使用 **Tailwind CSS 4.0** 的零配置方式。不需要 `tailwind.config.js`！

```javascript
// vite.config.ts - 已配置
export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(), // ✅ Tailwind 4.0 Vite 插件
  ],
})
```

```css
/* src/style.css - 所有配置都在这里 */
@import "tailwindcss";

/* 自定义颜色主题（使用 @theme 指令）*/
@theme {
  --color-primary: #3b82f6;
  --color-secondary: #6b7280;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
}
```

### 暗色模式配置（CSS 变量）

```css
/* src/style.css */
@layer base {
  .dark {
    --color-primary: #60a5fa;
    --color-secondary: #d1d5db;
    --color-success: #6ee7b7;
    --color-warning: #fcd34d;
    --color-error: #fca5a5;
  }
}
```

### 何时才需要 `tailwind.config.js`？

**通常不需要**。仅当你需要以下功能时：

```javascript
// tailwind.config.js - 仅在需要时创建
export default {
  content: ['./src/**/*.{vue,js}'], // 扫描额外的文件
  darkMode: 'class', // 或 'media'
  plugins: [require('@tailwindcss/forms')], // 第三方插件
}
```

---

## 检查清单

在提交样式代码前，确保：

### 样式组织
- [ ] 全局样式定义在 `style.css` 中（使用 @apply）
- [ ] 组件样式定义在 Vue 脚本中（使用 computed）
- [ ] 模板中的类不超过 4 个
- [ ] 没有重复的样式代码

### 代码质量
- [ ] 没有动态生成的类名（使用 computed 而非字符串拼接）
- [ ] 所有响应式设计都从移动端开始
- [ ] 使用了合适的颜色对比度
- [ ] 交互元素有明确的焦点状态

### 性能
- [ ] 使用了全局主题类避免重复
- [ ] 考虑了暗色模式支持
- [ ] 没有不必要的组件嵌套

### 可维护性
- [ ] 样式常量有清晰的名称
- [ ] TypeScript 类型正确
- [ ] 组件高度可复用
- [ ] 代码有必要的注释

---

## 🔗 参考资源

### 官方文档
- [Tailwind CSS 官方文档](https://tailwindcss.com)
- [Tailwind CSS 配置](https://tailwindcss.com/docs/configuration)
- [Tailwind CSS 扩展指南](https://tailwindcss.com/docs/customizing-your-theme)

### 设计系统参考
- [Tailwind UI Components](https://tailwindui.com)
- [Headless UI - 无头组件库](https://headlessui.dev)
- [Material Design 色彩系统](https://material.io/design/color)

### 学习资源
- [Tailwind CSS Cheat Sheet](https://tailwindcss.com/docs/width)
- [Web Accessibility Guidelines (WCAG)](https://www.w3.org/WAI/WCAG21/quickref/)

---

## 常见问题

### Q: 为什么类名看起来很长？
A: 这是 utility-first 的特点。长的类名是可读的、可维护的。使用组件类和样式常量可以大幅简化。

### Q: 如何调试样式问题？
A: 使用 Vue DevTools 和浏览器开发者工具的元素检查器，查看实际应用的 CSS。

### Q: 性能会不会很差？
A: 不会。Tailwind 使用 tree-shaking 移除未使用的样式，生产包体积通常很小（50-100KB）。

### Q: 可以和 SCSS / LESS 混合使用吗？
A: 可以，但不推荐。Tailwind 足以应对大多数场景。

---

**💡 记住**：好的样式是可维护的、可重用的、性能优良的。使用这份规范，你会写出更好的前端代码！
