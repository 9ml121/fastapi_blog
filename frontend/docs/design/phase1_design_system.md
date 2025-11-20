# 前端设计系统 - Phase 1.1

> **文档目的**：定义本项目的视觉设计系统、色彩体系、排版规范和交互模式  
> **维护人**：项目团队  
> **更新日期**：2025-11-15  
> **版本**：v1.0

---

## 📋 项目定位与设计理念

### 项目双模式架构

本项目致力于打造一个**个人博客 + 文章社交** 的二合一平台：

#### 模式1️⃣: **个人博客模式**
- **用户**：博主、内容创作者
- **核心功能**：发布文章、管理博客、个人品牌建设
- **设计强调**：沉浸式阅读体验、内容优先、专业感
- **典型场景**：浏览个人博客首页、阅读完整文章、查看创作者资料

#### 模式2️⃣: **文章社交模式**
- **用户**：读者、社区成员、发现者
- **核心功能**：发现优质文章、互动评论、关注创作者
- **设计强调**：内容发现、社交互动、社区感
- **典型场景**：浏览文章流、点赞评论、关注创作者

### 设计理念：**极简专业 + 创新个性**

我们的设计既遵循**极简专业风格**（参考Claude.ai、Medium），又融入**个人创新**，使项目独具特色：

| 维度 | 设计原则 |
|------|---------|
| **内容优先** | 界面是内容的舞台，不是主角 |
| **留白艺术** | 充分的留白让信息呼吸，减少认知负担 |
| **层级清晰** | 通过色彩、大小、权重明确指导用户注意力 |
| **一致性** | 所有交互元素遵循统一的视觉语言 |
| **个性创新** | 在保持专业的基础上，加入独特的品牌元素 |
| **可访问性** | WCAG AA标准，确保所有用户都能使用 |

---

## 🎨 色彩系统

### 核心色彩体系

```
┌─────────────────────────────────────────────────────┐
│              主题色彩定义（极简专业+创新）          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  基础色彩（中性灰）                                 │
│  ───────────────────────────────────────           │
│  Black:        #1F2937  (深灰-文本、主要元素)      │
│  Gray-900:     #111827  (极深灰-标题)              │
│  Gray-600:     #4B5563  (中灰-辅助文本)            │
│  Gray-400:     #9CA3AF  (浅灰-禁用、边框)          │
│  Gray-200:     #E5E7EB  (极浅灰-背景分割)          │
│  White:        #FFFFFF  (纯白-背景)                │
│                                                     │
│  强调色（创新个性）                                 │
│  ───────────────────────────────────────           │
│  Primary:      #0EA5E9  (天蓝-主要交互、链接)     │
│  Primary-Hover: #0284C7 (深天蓝-悬停状态)         │
│  Success:      #10B981  (翠绿-成功、已发布)       │
│  Warning:      #F59E0B  (琥珀-警告、草稿)         │
│  Error:        #EF4444  (红色-删除、错误)         │
│                                                     │
│  品牌色（个人创新）                                 │
│  ───────────────────────────────────────           │
│  Accent:       #8B5CF6  (紫色-创新、突出)         │
│  Light-Accent: #C4B5FD  (浅紫-背景点缀)           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 色彩使用规范

#### **文本色彩**
```
主文本（标题、正文）：#1F2937 (灰-900)
辅助文本（日期、分类）：#4B5563 (灰-600)
禁用文本：#9CA3AF (灰-400)
链接：#0EA5E9 (Primary)
链接悬停：#0284C7 (Primary-Hover)
```

#### **背景色彩**
```
页面背景：#FFFFFF (纯白)
卡片背景：#FFFFFF (纯白)
次级背景（分割区）：#F9FAFB (极浅灰)
Hover背景：#F3F4F6 (浅灰)
Active背景：#EFF6FF (天蓝浅)
```

#### **边框与分割线**
```
主边框：#E5E7EB (灰-200)
弱边框：#F3F4F6 (灰-100)
强边框：#D1D5DB (灰-300)
```

#### **特殊用途**
```
成功状态：#10B981 + #ECFDF5 (背景)
警告状态：#F59E0B + #FFFBEB (背景)
错误状态：#EF4444 + #FEF2F2 (背景)
品牌点缀：#8B5CF6（侧边栏、精选推荐）
```

### 创新要素：紫色品牌色

我们加入**紫色（#8B5CF6）** 作为品牌色，用于：
- ✅ Sidebar折叠箭头的动画渐变
- ✅ 精选文章、精选创作者的标记
- ✅ 用户等级徽章（高级创作者）
- ✅ 特殊功能的强调（如AI生成的摘要）

这让设计既保持专业，又有独特的品牌辨识度。

---

## 📝 排版系统

### 字体选择

```
英文字体：System Font Stack
  -apple-system
  BlinkMacSystemFont
  "Segoe UI"
  Roboto
  sans-serif

中文字体：系统默认（Tailwind默认配置）
  -apple-system 内置字体

等宽字体（代码）：Fira Code / Monaco
```

### 排版层级

| 用途 | 大小 | 粗细 | 行高 | 使用场景 |
|------|------|------|------|---------|
| **H1 标题** | 32px | bold | 1.2 | 文章标题、页面标题 |
| **H2 副标题** | 24px | semibold | 1.3 | 文章小节、卡片标题 |
| **H3 三级标题** | 20px | semibold | 1.3 | 评论者名字、菜单组 |
| **正文文本** | 16px | normal | 1.6 | 文章内容、段落 |
| **辅助文本** | 14px | normal | 1.5 | 日期、作者、简介 |
| **小文本** | 12px | medium | 1.5 | 标签、徽章、按钮 |
| **超小文本** | 11px | normal | 1.4 | 图表标签、时间戳 |

### Tailwind 类映射

```vue
<!-- H1: 文章标题 -->
<h1 class="text-4xl font-bold leading-tight text-gray-900">
  文章标题
</h1>

<!-- H2: 卡片标题 -->
<h2 class="text-2xl font-semibold leading-snug text-gray-900">
  卡片标题
</h2>

<!-- 正文段落 -->
<p class="text-base leading-relaxed text-gray-700">
  这是一个段落...
</p>

<!-- 辅助文本 -->
<span class="text-sm text-gray-600">
  2025年11月15日
</span>

<!-- 标签 -->
<span class="text-xs font-medium text-gray-700">
  Vue.js
</span>
```

---

## 🎬 间距与布局系统

### 间距规范（Tailwind默认）

```
基础单位：4px（Tailwind rem = 16px）

常用间距：
- xs: 8px    (p-2)
- sm: 12px   (p-3)
- md: 16px   (p-4)
- lg: 24px   (p-6)
- xl: 32px   (p-8)
- 2xl: 48px  (p-12)

应用场景：
- 文字之间：8-12px (xs/sm)
- 组件内部：16px (md)
- 卡片间距：24px (lg)
- 区块间距：32px (xl)
- 大区块间距：48px (2xl)
```

### 响应式断点

```
sm:  640px   平板横向
md:  768px   小屏幕
lg:  1024px  桌面
xl:  1280px  大桌面
2xl: 1536px  超大屏幕

设计策略：
✅ 移动优先：从 320px 开始设计
✅ 逐步扩展：sm → md → lg → xl
✅ 优雅降级：确保所有断点都优雅
```

---

## 🎨 组件样式指南

### Button（按钮）

```vue
<!-- 主要按钮（蓝色） -->
<button class="px-6 py-2 rounded-lg bg-blue-500 text-white font-semibold hover:bg-blue-600 transition-colors duration-200">
  发布文章
</button>

<!-- 次要按钮（灰色） -->
<button class="px-6 py-2 rounded-lg bg-gray-200 text-gray-900 font-semibold hover:bg-gray-300 transition-colors duration-200">
  取消
</button>

<!-- 幽灵按钮（边框） -->
<button class="px-6 py-2 rounded-lg border-2 border-gray-300 text-gray-900 font-semibold hover:bg-gray-50 transition-colors duration-200">
  更多
</button>

<!-- 危险按钮（红色） -->
<button class="px-6 py-2 rounded-lg bg-red-500 text-white font-semibold hover:bg-red-600 transition-colors duration-200">
  删除
</button>
```

### Card（卡片）

```vue
<!-- 文章卡片 -->
<div class="rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow duration-200">
  <h2 class="text-xl font-semibold text-gray-900 mb-3">
    文章标题
  </h2>
  <p class="text-gray-700 text-base leading-relaxed mb-4 line-clamp-3">
    文章摘要...
  </p>
  <div class="flex items-center justify-between text-sm text-gray-600">
    <span>张三</span>
    <span>2025-11-15</span>
  </div>
</div>
```

### Input（输入框）

```vue
<input 
  type="text" 
  class="w-full px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-900 placeholder-gray-500 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none transition-all duration-200"
  placeholder="输入你的想法..."
/>
```

### Badge（徽章）

```vue
<!-- 标签 -->
<span class="inline-block px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold">
  Vue.js
</span>

<!-- 成功状态 -->
<span class="inline-block px-3 py-1 rounded-full bg-green-100 text-green-700 text-xs font-semibold">
  已发布
</span>

<!-- 警告状态 -->
<span class="inline-block px-3 py-1 rounded-full bg-amber-100 text-amber-700 text-xs font-semibold">
  草稿
</span>
```

---

## 🎬 动画与过渡

### 过渡时间规范

```
快速反应（UI反馈）：150ms
标准过渡（页面切换）：300ms
缓慢动画（强调）：500ms
```

### 常用动画模式

#### 1. Fade（淡入淡出）
```vue
<Transition name="fade">
  <div v-if="isVisible">内容</div>
</Transition>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 300ms ease-out;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
```

#### 2. Slide（滑动）
```vue
<Transition name="slide">
  <Sidebar v-if="isSidebarOpen" />
</Transition>

<style scoped>
.slide-enter-active, .slide-leave-active {
  transition: transform 300ms ease-out;
}
.slide-enter-from, .slide-leave-to {
  transform: translateX(-100%);
}
</style>
```

#### 3. Hover（悬停效果）
```vue
<button class="hover:shadow-md transition-shadow duration-200">
  按钮
</button>

<!-- 或使用Tailwind群组选择器 -->
<div class="group rounded-lg border border-gray-200 hover:border-blue-300 transition-colors duration-200">
  <p class="text-gray-700 group-hover:text-blue-600 transition-colors duration-200">
    文本
  </p>
</div>
```

---

## 🌍 两种模式的布局差异

### 模式1: 个人博客模式
**布局特点：**
- 左侧：Sidebar 导航
- 中央：文章内容（宽度受限，最优阅读宽度）
- 右侧：文章目录 / 精选推荐

**色彩特点：**
- 极度简洁，白色 + 灰色
- 蓝色仅用于链接和CTA
- 内容独占舞台

**示例页面：**
```
个人博客首页
├─ 侧边栏（导航、个人资料）
├─ 中央区域
│  ├─ 个人简介卡片
│  ├─ 文章列表（按时间）
│  └─ 分页
└─ 右侧栏（可选，文章分类）
```

### 模式2: 文章社交模式
**布局特点：**
- 左侧：Sidebar 导航
- 中央：文章流（信息流式设计）
- 右侧：热门话题、推荐创作者

**色彩特点：**
- 加入品牌色（紫色）做点缀
- 卡片更明显的视觉分割
- 交互元素更突出

**示例页面：**
```
文章发现页
├─ 侧边栏（导航、关注列表）
├─ 中央区域
│  ├─ 文章流
│  │  ├─ PostCard 1
│  │  ├─ PostCard 2
│  │  └─ PostCard 3
│  └─ 无限滚动
└─ 右侧栏（热门话题、推荐作者）
```

---

## 📐 设计实施路线

### Phase 1: 基础样式系统（当前）
- [ ] 定义 Tailwind 自定义配置（色彩、间距、排版）
- [ ] 创建全局样式文件（reset、通用类）
- [ ] 实现基础组件（Button、Card、Input、Badge）

### Phase 2: 高保真组件
- [ ] Sidebar 完善（Lucide icon、颜色、交互）
- [ ] PostCard 组件（两种模式适配）
- [ ] 评论组件（嵌套、交互）

### Phase 3: 整合与优化
- [ ] 响应式测试（所有断点）
- [ ] 辅助功能检查（WCAG AA）
- [ ] 性能优化（CSS打包、动画优化）

---

## 🔗 相关文档

- [plan_frontend.md](../project/plan_frontend.md) - 技术栈和学习计划
- [process.md](../project/process.md) - 当前开发进度
- Tailwind 官方：https://tailwindcss.com/

---

## ✅ 下一步

1. ✅ **确认设计系统** - 此文档定义
2. 📝 **创建 Tailwind 配置** - 实施色彩、排版
3. 🎨 **编写全局样式** - reset + 通用类
4. 🧩 **实现基础组件** - Button / Card / Input
5. 🎯 **重构 Sidebar** - 应用新设计系统

---

**设计文档版本管理**

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-11-15 | 初始设计系统 |
