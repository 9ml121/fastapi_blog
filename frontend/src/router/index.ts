import { createRouter, createWebHistory } from 'vue-router'

import EditorContent from '@/modules/editor/components/EditorContent.vue'
import EditorToolbar from '@/modules/editor/components/EditorToolbar.vue'
import MarkdownEditor from '@/modules/editor/components/MarkdownEditor.vue'

// todo 测试页面，后面记得删除！
import EditorDemo from '@/modules/editor/demo/EditorDemo.vue'
import HistoryTest from '@/modules/editor/demo/HistoryTest.vue'

// 路由数组：定义所有页面路由
const routes = [
  {
    path: '/', // URL 匹配路径
    name: 'home', // 路由名称（可选，用于编程式导航）
    redirect: '/markdown', // 根路径重定向
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'), // 路由懒加载 - 访问时才加载对应组件
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
    meta: { title: 'md编辑器测试', requiresAuth: true }, // 路由元信息（如权限标记）
  },
  // todo 测试页面，后面记得删除！
  {
    path: '/test-editor',
    name: 'EditorDemo',
    component: EditorDemo,
  },
  {
    path: '/test-history',
    name: 'HistoryTest',
    component: HistoryTest,
  },
]

const router = createRouter({
  // 历史模式：URL 看起来更干净（没有 # 号）
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
