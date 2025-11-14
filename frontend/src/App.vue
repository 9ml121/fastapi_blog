<script setup lang="ts">
import Header from './components/Header.vue'
import Footer from './components/Footer.vue'
</script>

<template>
  <div class="flex flex-col min-h-screen">
    <Header />

    <main class="grow max-w-6xl mx-auto px-4 py-8">
      <!-- 后期这里会放页面内容 -->
      <div class="text-center">
        <h1 class="text-4xl font-bold mb-4">欢迎来到博客系统</h1>
        <p class="text-gray-600">Week 1 Day 1 - 创建基础布局</p>
      </div>
    </main>

    <Footer />
  </div>
</template>

<style scoped></style>
