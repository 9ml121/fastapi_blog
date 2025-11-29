import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/pages/Home.vue'
import Personal from '@/pages/Personal.vue'
import EditorContent from '@/components/editor/sub-components/EditorContent.vue'
import EditorToolbar from '@/components/editor/sub-components/EditorToolbar.vue'
import MarkdownEditor from '@/components/editor/sub-components/MarkdownEditor.vue'

// todo 测试页面，后面记得删除！
import EditorDemo from '@/components/editor/demo/EditorDemo.vue'
import HistoryTest from '@/components/editor/demo/HistoryTest.vue'

const routes = [
  {
    path: '/',
    redirect: '/markdown', // 根路径重定向
  },
  {
    path: '/home',
    name: 'Home',
    component: Home,
    meta: { title: '首页' },
  },
  {
    path: '/personal',
    name: 'Personal',
    component: Personal,
    meta: { title: '我的文章' },
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
    }
]


const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
