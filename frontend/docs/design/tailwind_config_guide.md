# Tailwind 自定义配置指南

> **目的**：实现设计系统中定义的色彩、排版、间距等规范  
> **文件位置**：`frontend/tailwind.config.ts`  
> **优先级**：必须在开始编码前完成

---

## 📋 核心概念

Tailwind CSS 是 utility-first 框架，我们需要自定义配置来应用设计系统。

```
设计系统（设计文档） 
    ↓
Tailwind 配置（colors, typography, spacing）
    ↓
Vue 组件（应用Tailwind类）
```

---

## 🎨 完整的 Tailwind 配置

### Step 1️⃣: 更新 `tailwind.config.ts`

将以下配置复制到你的 `frontend/tailwind.config.ts`：

```typescript
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  
  theme: {
    extend: {
      // ============ 自定义色彩 ============
      colors: {
        // 基础中性色（灰色系）
        gray: {
          50: '#F9FAFB',
          100: '#F3F4F6',
          200: '#E5E7EB',
          300: '#D1D5DB',
          400: '#9CA3AF',
          500: '#6B7280',
          600: '#4B5563',
          700: '#374151',
          800: '#1F2937',
          900: '#111827',
        },
        
        // 主色彩（天蓝）
        blue: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },
        
        // 自定义主色（天蓝）
        primary: {
          DEFAULT: '#0EA5E9',
          hover: '#0284C7',
          light: '#E0F2FE',
        },
        
        // 品牌色（紫色）
        accent: {
          DEFAULT: '#8B5CF6',
          light: '#C4B5FD',
        },
        
        // 功能色
        success: '#10B981',
        warning: '#F59E0B',
        error: '#EF4444',
      },
      
      // ============ 自定义排版 ============
      fontSize: {
        // h1: 文章标题
        '4xl': ['32px', { lineHeight: '1.2', fontWeight: '700' }],
        // h2: 卡片标题
        '2xl': ['24px', { lineHeight: '1.3', fontWeight: '600' }],
        // h3: 三级标题
        'xl': ['20px', { lineHeight: '1.3', fontWeight: '600' }],
        // 正文文本
        'base': ['16px', { lineHeight: '1.6', fontWeight: '400' }],
        // 辅助文本
        'sm': ['14px', { lineHeight: '1.5', fontWeight: '400' }],
        // 小文本（标签、徽章）
        'xs': ['12px', { lineHeight: '1.5', fontWeight: '500' }],
        // 超小文本
        '2xs': ['11px', { lineHeight: '1.4', fontWeight: '400' }],
      },
      
      // ============ 自定义间距 ============
      spacing: {
        xs: '8px',
        sm: '12px',
        md: '16px',
        lg: '24px',
        xl: '32px',
        '2xl': '48px',
      },
      
      // ============ 自定义圆角 ============
      borderRadius: {
        none: '0px',
        sm: '4px',
        DEFAULT: '8px',
        md: '12px',
        lg: '16px',
        xl: '24px',
      },
      
      // ============ 自定义阴影 ============
      boxShadow: {
        none: 'none',
        sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        DEFAULT: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
        xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
      },
      
      // ============ 自定义过渡时间 ============
      transitionDuration: {
        fast: '150ms',
        DEFAULT: '300ms',
        slow: '500ms',
      },
    },
  },
  
  plugins: [],
} satisfies Config
```

---

## 🎯 使用示例

### 1. 文章标题（H1）
```vue
<h1 class="text-4xl font-bold leading-tight text-gray-900">
  深入理解 JavaScript 异步编程
</h1>
```

### 2. 卡片标题（H2）
```vue
<h2 class="text-2xl font-semibold leading-snug text-gray-900">
  为什么选择 Vue 3?
</h2>
```

### 3. 正文段落
```vue
<p class="text-base leading-relaxed text-gray-700">
  在这篇文章中，我们将深入探讨 JavaScript 的异步编程模式...
</p>
```

### 4. 辅助文本
```vue
<div class="flex items-center gap-2 text-sm text-gray-600">
  <span>张三</span>
  <span>•</span>
  <span>2025-11-15</span>
</div>
```

### 5. 标签/徽章
```vue
<!-- 普通标签 -->
<span class="inline-block px-3 py-1 rounded-md bg-blue-100 text-blue-700 text-xs font-medium">
  Vue.js
</span>

<!-- 成功标签 -->
<span class="inline-block px-3 py-1 rounded-md bg-green-100 text-green-700 text-xs font-medium">
  已发布
</span>

<!-- 警告标签 -->
<span class="inline-block px-3 py-1 rounded-md bg-amber-100 text-amber-700 text-xs font-medium">
  草稿
</span>
```

### 6. 按钮（主要）
```vue
<button class="px-6 py-2 rounded-md bg-primary text-white font-semibold hover:bg-primary-hover transition-colors duration-300">
  发布文章
</button>
```

### 7. 按钮（次要）
```vue
<button class="px-6 py-2 rounded-md bg-gray-200 text-gray-900 font-semibold hover:bg-gray-300 transition-colors duration-300">
  取消
</button>
```

### 8. 按钮（危险）
```vue
<button class="px-6 py-2 rounded-md bg-error text-white font-semibold hover:bg-red-600 transition-colors duration-300">
  删除
</button>
```

### 9. 文章卡片
```vue
<div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow duration-300">
  <!-- 作者信息 -->
  <div class="flex items-center gap-3 mb-4">
    <img :src="post.author.avatar" class="w-10 h-10 rounded-full" />
    <div>
      <p class="text-sm font-semibold text-gray-900">{{ post.author.name }}</p>
      <p class="text-xs text-gray-600">{{ formatDate(post.createdAt) }}</p>
    </div>
  </div>
  
  <!-- 标题 -->
  <h2 class="text-xl font-semibold text-gray-900 mb-3">
    {{ post.title }}
  </h2>
  
  <!-- 摘要 -->
  <p class="text-gray-700 text-base leading-relaxed mb-4 line-clamp-3">
    {{ post.excerpt }}
  </p>
  
  <!-- 标签 -->
  <div class="flex gap-2 mb-4 flex-wrap">
    <span v-for="tag in post.tags" :key="tag" class="text-sm text-gray-600">
      #{{ tag }}
    </span>
  </div>
  
  <!-- 交互按钮 -->
  <div class="flex items-center gap-4 text-gray-600 text-sm">
    <button class="flex items-center gap-1 hover:text-error transition-colors duration-200">
      ❤️ {{ post.likes }}
    </button>
    <button class="flex items-center gap-1 hover:text-primary transition-colors duration-200">
      💬 {{ post.comments }}
    </button>
    <button class="flex items-center gap-1 hover:text-success transition-colors duration-200">
      🔖 {{ post.bookmarks }}
    </button>
  </div>
</div>
```

### 10. Sidebar 导航项
```vue
<!-- 使用紫色品牌色 -->
<a
  href="/"
  class="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-700 hover:bg-gray-100 hover:text-primary transition-colors duration-200"
>
  <Icon class="w-5 h-5" />
  <span>导航项</span>
</a>

<!-- 活跃状态（使用紫色强调） -->
<a
  href="/favorites"
  class="flex items-center gap-3 px-4 py-3 rounded-lg text-accent font-semibold bg-accent-light"
>
  <Icon class="w-5 h-5" />
  <span>我的收藏</span>
</a>
```

---

## 🌈 色彩主题速查表

### 文本色

| 用途 | 类名 | 示例 |
|------|------|------|
| 主文本 | `text-gray-900` | 标题、正文 |
| 辅助文本 | `text-gray-600` | 日期、作者 |
| 禁用文本 | `text-gray-400` | 禁用按钮 |
| 链接 | `text-primary` | `text-blue-500` |
| 成功 | `text-success` | `text-green-600` |
| 警告 | `text-warning` | `text-amber-600` |
| 错误 | `text-error` | `text-red-600` |

### 背景色

| 用途 | 类名 | 示例 |
|------|------|------|
| 页面背景 | `bg-white` | 页面 |
| 卡片背景 | `bg-white` | Card |
| Hover背景 | `hover:bg-gray-50` | 交互元素 |
| 成功背景 | `bg-green-100` | 成功提示 |
| 警告背景 | `bg-amber-100` | 警告提示 |
| 错误背景 | `bg-red-100` | 错误提示 |
| 品牌背景 | `bg-accent-light` | 精选推荐 |

---

## 📝 常用 Tailwind 模式

### 1. 响应式文本大小
```vue
<!-- 手机：sm，平板：md，桌面：lg -->
<p class="text-sm md:text-base lg:text-lg">
  响应式文本
</p>
```

### 2. 响应式间距
```vue
<!-- 手机：p-4，平板：p-6，桌面：p-8 -->
<div class="p-4 md:p-6 lg:p-8">
  响应式间距
</div>
```

### 3. 响应式栅格
```vue
<!-- 手机：1列，平板：2列，桌面：3列 -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <Card v-for="post in posts" :key="post.id" :post="post" />
</div>
```

### 4. 过渡动画
```vue
<!-- 过渡时间使用自定义值 -->
<button class="hover:bg-gray-100 transition-colors duration-300">
  按钮
</button>

<!-- 多属性过渡 -->
<div class="hover:shadow-lg hover:scale-105 transition-all duration-300">
  卡片
</div>
```

### 5. 组件群组选择
```vue
<!-- 悬停卡片时，改变内部文本颜色 -->
<div class="group border border-gray-200 rounded-lg hover:border-primary transition-colors duration-300">
  <p class="text-gray-700 group-hover:text-primary transition-colors duration-300">
    鼠标悬停时变色的文本
  </p>
</div>
```

---

## ✅ 实施检查清单

在开始编码前，确认以下各项已完成：

- [ ] 更新 `tailwind.config.ts` 中的所有自定义配置
- [ ] 验证色彩定义正确（特别是 primary、accent）
- [ ] 验证排版层级完整
- [ ] 测试一个简单组件（如Button）
- [ ] 验证 Tailwind 类能正常应用
- [ ] 在 VS Code 中启用 Tailwind CSS IntelliSense 扩展

---

## 🔗 参考资源

- [Tailwind 官方文档](https://tailwindcss.com/docs)
- [Tailwind 色彩](https://tailwindcss.com/docs/customizing-colors)
- [Tailwind 排版](https://tailwindcss.com/docs/font-size)
- [VS Code Tailwind 扩展](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss)

---

**下一步**：实施完这个配置后，开始重构 Sidebar 组件 🎨
