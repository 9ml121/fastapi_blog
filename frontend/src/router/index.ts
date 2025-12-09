import { createRouter, createWebHistory } from 'vue-router'

import EditorContent from '@/modules/editor/components/EditorContent.vue'
import EditorToolbar from '@/modules/editor/components/EditorToolbar.vue'
import MarkdownEditor from '@/modules/editor/components/MarkdownEditor.vue'

// todo 测试页面，后面记得删除！
import EditorDemo from '@/modules/editor/demo/EditorDemo.vue'
import HistoryTest from '@/modules/editor/demo/HistoryTest.vue'

const routes = [
  {
    path: '/',
    redirect: '/markdown', // 根路径重定向
  },
  {
    path: '/editor',
    name: 'EditorContent',
    component: EditorContent,
  },
  {
    path: '/toolbar',
    name: 'EditorToolbar',
    component: EditorToolbar,
  },
  {
    path: '/markdown',
    name: 'MarkdownEditor',
    component: MarkdownEditor,
  },
  // todo 测试页面，后面记得删除！
  {
    path: '/test-editor',
    name: 'EditorDemo',
    component: EditorDemo,
    meta: { title: 'useSelection 测试' },
  },
  {
    path: '/test-history',
    name: 'HistoryTest',
    component: HistoryTest,
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
