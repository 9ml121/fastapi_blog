<script lang="ts" setup>
/**
 * 品牌 Logo 组件
 * 用于登录页、注册页、导航栏等位置
 */

// 1.定义 Props类型并设置默认值
const props = withDefaults(
  defineProps<{
    size?: 'small' | 'medium' | 'large'
    showName?: boolean
    direction?: 'horizontal' | 'vertical'
  }>(),
  {
    size: 'medium',
    showName: true,
    direction: 'horizontal',
  },
)

// 2. Logo 尺寸映射
const logoSizeMap = {
  small: 24,
  medium: 32,
  large: 48,
}

// 3. 文字大小映射（与图标比例匹配）
const fontSizeMap = {
  small: 16,
  medium: 24,
  large: 32,
}
</script>

<template>
  <!-- Logo 容器 -->
  <div class="brand-logo" :class="props.direction">
    <!-- Logo 图标 -->
    <img
      src="@/assets/images/logo.svg"
      alt="InkFlow logo"
      :width="logoSizeMap[props.size]"
      :height="logoSizeMap[props.size]"
    />

    <!-- 品牌名称 -->
    <span
      v-if="props.showName"
      class="brand-name"
      :style="{ fontSize: fontSizeMap[props.size] + 'px' }"
      >InkFlow</span
    >
  </div>
</template>

<style scoped>
.brand-logo {
  display: flex;
  align-items: center;
  gap: 6px; /* 图标和文字间距 */
}

/* 垂直排列（默认） */
.brand-logo.vertical {
  flex-direction: column;
}

/* 水平排列 */
.brand-logo.horizontal {
  flex-direction: row;
}

.brand-name {
  font-weight: 600;
  color: #1e40af; /* 与图标颜色一致 */
}
</style>
