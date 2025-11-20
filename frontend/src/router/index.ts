import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/pages/Home.vue'
import Personal from '@/pages/Personal.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { title: '首页 - 博客' }
  },
  {
    path: '/personal',
    name: 'Personal',
    component: Personal,
    meta: { title: '我的文章 - 博客' }
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
