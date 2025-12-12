<script lang="ts" setup>
/**
 * 通用卡片容器布局
 * 1. 提供卡片外观样式，内容通过 slot 插入
 */
const props = withDefaults(
  defineProps<{
    maxWidth?: string
  }>(),
  {
    maxWidth: '420px',
  },
)
</script>

<template>
  <div class="base-card">
    <!-- 默认插槽：父组件传入的内容会显示在这里 -->
    <slot></slot>
  </div>
</template>

<style scoped>
/* 通用卡片容器 - 白色圆角卡片 */
.base-card {
  width: 100%;
  max-width: v-bind('props.maxWidth'); /* 最大宽度由 props 控制 */
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  padding: 40px;
  background: #ffffff; /* 简写属性，可设置颜色、图片、渐变等多种属性 */
  border-radius: 24px;
  border: 1px solid rgba(53, 92, 194, 0.1);
  backdrop-filter: blur(10px); /*让元素背后的内容变模糊（毛玻璃效果）*/
  display: flex;
  flex-direction: column;
  gap: 20px; /* 子元素间距 20px */
}
</style>
