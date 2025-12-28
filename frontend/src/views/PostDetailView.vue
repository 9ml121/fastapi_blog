<script lang="ts" setup>
import MainLayout from '@/components/layout/MainLayout.vue'
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/preview.css'
import { onMounted, ref } from 'vue'

// 1. 定义测试用的 Markdown 内容
const markdownText = ref(`
# 欢迎使用萤火博客

这是一篇测试文章，展示 **Markdown** 渲染效果。

## 代码高亮演示
\`\`\`python
def hello_firefly():
    print("Hello, Firefly Blog!")
\`\`\`

> 这是一个引用块，用来展示 UI 细节。
`)

// 2. 主题处理
const theme = ref<'light' | 'dark'>('light')
onMounted(() => {
  // 从 HTML 标签或 localStorage 获取当前主题
  theme.value = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light'
})
</script>

<template>
  <MainLayout>
    <div class="post-detail-container">
      <!-- 文章头部：标题、元数据 -->
      <header class="post-header">
        <h1 class="post-title">如何使用 FastAPI 与 Vue3 构建全栈博客</h1>
        <div class="post-meta">
          <span>📅 2023-10-27</span>
          <span>👤 Sensei</span>
          <span>🏷️ 技术, 全栈</span>
        </div>
      </header>

      <!-- 文章正文 -->
      <div class="post-content">
        <MdPreview :modelValue="markdownText" :theme="theme" />
      </div>
    </div>
  </MainLayout>
</template>

<style scoped>
.post-detail-container {
  max-width: 900px; /* 限制最大宽度，提升阅读舒适度 */
  margin: 40px auto; /* 居中 */
  padding: 0 24px;
}

.post-header {
  margin-bottom: 32px;
  text-align: center;
}

.post-title {
  font-size: 2.5rem;
  color: var(--color-text-primary);
  margin-bottom: 16px;
}

.post-meta {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  display: flex;
  justify-content: center;
  gap: 16px;
}

.post-content {
  background: var(--color-bg-card);
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--shadow-sm);
}
</style>
