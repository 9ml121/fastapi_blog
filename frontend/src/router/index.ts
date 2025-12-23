import { createRouter, createWebHistory } from 'vue-router'

import EditorContent from '@/modules/editor/components/EditorContent.vue'
import EditorToolbar from '@/modules/editor/components/EditorToolbar.vue'
import MarkdownEditor from '@/modules/editor/components/MarkdownEditor.vue'
import { getToken } from '@/utils/token'

// 路由数组：定义所有页面路由
const routes = [
  // 1. 不需要导航栏的路由（登录页）
  {
    path: '/login', // URL 匹配路径
    name: 'Login', // 路由名称（可选，用于编程式导航）
    component: () => import('@/views/LoginView.vue'), // 路由懒加载 - 访问时才加载对应组件
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPasswordView.vue'),
  },

  // 2. 需要导航栏的路由，放在 MainLayout 的 children 下
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/BaseLayout.vue'),
    redirect: '/markdown', //重定向到 /markdown
    children: [
      {
        path: '/markdown', // 子路由路径，不需要加 /，最终路径为 /markdown
        name: 'MarkdownEditor',
        component: MarkdownEditor,
        meta: { title: 'md编辑器', requiresAuth: true }, // 路由元信息（如权限标记）
      },
    ],
  },

  // todo 临时测试的页面
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
]

const router = createRouter({
  // 历史模式：URL 看起来更干净（没有 # 号）
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 全局前置守卫：检查路由访问权限
router.beforeEach((to, from) => {
  // 检查目标路由是否需要认证
  if (to.meta.requiresAuth && !getToken()) {
    return '/login' // 未登录，重定向到登录页
  }
  // 已登录或不需要登录的页面，放行
})

export default router
