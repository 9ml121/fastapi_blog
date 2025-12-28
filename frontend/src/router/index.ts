import { createRouter, createWebHistory } from 'vue-router'

import { getToken } from '@/utils/token'

// 路由数组：定义所有页面路由
const routes = [
  // 1. 认证页面（无导航栏）
  { path: '/login', name: 'Login', component: () => import('@/views/LoginView.vue') },
  { path: '/register', name: 'Register', component: () => import('@/views/RegisterView.vue') },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPasswordView.vue'),
  },

  // 2. 主菜单栏页面（有导航栏）
  // 首页·
  { path: '/', name: 'Home', component: () => import('@/views/HomeView.vue') },
  // 博文
  { path: '/posts', name: 'Posts', component: () => import('@/views/PostsView.vue') },
  {
    path: '/posts/:id',
    name: 'PostDetail',
    component: () => import('@/views/PostDetailView.vue'),
  },
  // 项目
  { path: '/projects', name: 'Projects', component: () => import('@/views/ProjectsView.vue') },
  // 好物
  { path: '/picks', name: 'Picks', component: () => import('@/views/PicksView.vue') },

  // 3. 个人中心（需要认证）
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/profile/ProfileLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/profile/info',
    children: [
      {
        path: 'info',
        name: 'ProfileInfo',
        component: () => import('@/views/profile/ProfileInfoView.vue'),
      },
      {
        path: 'posts',
        name: 'ProfilePosts',
        component: () => import('@/views/profile/ProfilePostsView.vue'),
      },
    ],
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
