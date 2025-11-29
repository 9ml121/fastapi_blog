<script lang="ts" setup>
import {
  Bold,
  Italic,
  Link,
  Code,
  Heading1,
  Heading2,
  Heading3,
  Quote,
  FileCode,
  Image,
  Table,
  Divide,
} from 'lucide-vue-next'
import type { InlineFormatType, ParagraphFormatType, BlockInsertType } from '../types/editor'

// ==================== Emits ====================
interface Emits {
  (e: 'inline-format', action: InlineFormatType): void
  (e: 'paragraph-format', action: ParagraphFormatType): void
  (e: 'insert-block', action: BlockInsertType): void
}

const emit = defineEmits<Emits>()

// ==================== 方法 ====================
const handleFormat = (action: string) => {
  // 行内格式
  const inlineFormats: InlineFormatType[] = ['bold', 'italic', 'code', 'highlight', 'link']
  if (inlineFormats.includes(action as InlineFormatType)) {
    emit('inline-format', action as InlineFormatType)
    return
  }

  // 段落格式
  const paragraphFormats: ParagraphFormatType[] = ['heading1', 'heading2', 'heading3', 'quote']
  if (paragraphFormats.includes(action as ParagraphFormatType)) {
    emit('paragraph-format', action as ParagraphFormatType)
    return
  }
}

const handleInsert = (action: BlockInsertType) => {
  emit('insert-block', action)
}
</script>

<template>
  <div class="toolbar">
    <!-- 行内格式 -->
    <div class="toolbar-group">
      <button @click="handleFormat('bold')" title="加粗 (Ctrl+B)" class="toolbar-btn">
        <Bold :size="18" />
      </button>
      <button @click="handleFormat('italic')" title="斜体 (Ctrl+I)" class="toolbar-btn">
        <Italic :size="18" />
      </button>
      <button @click="handleFormat('code')" title="行内代码" class="toolbar-btn">
        <Code :size="18" />
      </button>
      <button @click="handleFormat('link')" title="插入链接 (Ctrl+K)" class="toolbar-btn">
        <Link :size="18" />
      </button>
    </div>

    <!-- 分割线 -->
    <div class="toolbar-divider"></div>

    <!-- 段落格式 -->
    <div class="toolbar-group">
      <button @click="handleFormat('heading1')" title="一级标题" class="toolbar-btn">
        <Heading1 :size="18" />
      </button>
      <button @click="handleFormat('heading2')" title="二级标题" class="toolbar-btn">
        <Heading2 :size="18" />
      </button>
      <button @click="handleFormat('heading3')" title="三级标题" class="toolbar-btn">
        <Heading3 :size="18" />
      </button>
      <button @click="handleFormat('quote')" title="引用块" class="toolbar-btn">
        <Quote :size="18" />
      </button>
    </div>

    <!-- 分割线 -->
    <div class="toolbar-divider"></div>

    <!-- 插入块 -->
    <div class="toolbar-group">
      <button @click="handleInsert('divider')" title="分割线" class="toolbar-btn">
        <Divide :size="18" />
      </button>
      <button @click="handleInsert('codeBlock')" title="代码块" class="toolbar-btn">
        <FileCode :size="18" />
      </button>
      <button @click="handleInsert('image')" title="插入图片" class="toolbar-btn">
        <Image :size="18" />
      </button>
      <button @click="handleInsert('table')" title="插入表格" class="toolbar-btn">
        <Table :size="18" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.toolbar-group {
  display: flex;
  gap: 2px;
}

.toolbar-divider {
  width: 1px;
  background: #d1d5db;
  margin: 0 6px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s;
}

.toolbar-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.toolbar-btn:active {
  background: #d1d5db;
}

/* 响应式 */
@media (max-width: 768px) {
  .toolbar {
    overflow-x: auto;
  }
}
</style>
