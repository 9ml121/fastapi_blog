/**
 * Editor 模块入口
 * 对外暴露编辑器相关组件和 API
 */

// 主组件
export { default as MarkdownEditor } from './components/MarkdownEditor.vue'
export { default as EditorContent } from './components/EditorContent.vue'
export { default as EditorToolbar } from './components/EditorToolbar.vue'
export { default as TableOfContents } from './components/TableOfContents.vue'

// Composables
export { useMarkdownEditor } from './composables/useMarkdownEditor'
export { useTableOfContents } from './composables/useTableOfContents'

// Types
export type * from './composables/editor.types'
