<script setup lang="ts">
import ToastContainer from '@/components/common/ToastContainer.vue'
</script>

<template>
  <!-- 全局 Toast 通知 -->
  <ToastContainer />

  <!-- 路由出口 -->
  <router-view />
</template>
