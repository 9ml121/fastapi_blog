<script lang="ts" setup>
import AppNavbar from '@/components/layout/AppNavbar.vue'
</script>

<template>
  <div class="main-layout">
    <!-- 顶部导航栏 -->
    <AppNavbar />

    <!-- 主内容区 -->
    <main class="main-content">
      <div class="container">
        <slot />
        <!-- 页面内容插槽 -->
      </div>
    </main>
  </div>
</template>

<style scoped>
.main-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding-top: 24px;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}
</style>
