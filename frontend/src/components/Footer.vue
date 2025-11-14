<template>
  <footer class="bg-gray-900 text-white">
    <div class="max-w-6xl mx-auto px-4 py-8">
      <!-- 三列布局（用 flex 或自己想的方式） -->
      <div class="flex justify-between items-center">
        <!-- 左列：版权 -->
        <div>© 2025 FastAPI 博客</div>

        <!-- 中列：链接（遍历数组） -->
         <div class="flex gap-6">
    <a
      v-for="link in footerLinks"
      :key="link.name"
      :href="link.href"
      class="hover:text-gray-400 transition-colors"
    >
      {{ link.name }}
    </a>
  </div>

        <!-- 右列：邮箱 -->
        <div>contact@blog.com</div>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// 定义链接数组
const footerLinks = ref([
  { name: '关于', href: '/about' },
  { name: '隐私政策', href: '/privacy' },
  { name: '服务条款', href: '/terms' },
])
</script>
