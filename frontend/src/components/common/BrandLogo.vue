<script lang="ts" setup>
/**
 * 品牌 Logo 组件
 * 用于登录页、注册页、导航栏等位置
 */

// 1.定义 Props类型并设置默认值
const props = withDefaults(
  defineProps<{
    size?: 'small' | 'large'
    showName?: boolean
    direction?: 'horizontal' | 'vertical'
    gap?: number // logo和文字间距
  }>(),
  {
    size: 'small',
    showName: true,
    direction: 'horizontal',
    gap: 8,
  },
)

// 2. Logo 尺寸映射
const logoSizeMap = {
  small: 28,
  large: 36,
}

// 3. 文字大小映射（与图标比例匹配）
const fontSizeMap = {
  small: 18,
  large: 22,
}
</script>

<template>
  <!-- Logo 容器 -->
  <div class="brand-logo" :class="props.direction" :style="{ gap: props.gap + 'px' }">
    <!-- Logo 图标 -->
    <img
      src="@/assets/images/logo.svg"
      alt="Firefly logo"
      :width="logoSizeMap[props.size]"
      :height="logoSizeMap[props.size]"
    />

    <!-- 品牌名称 -->
    <span
      v-if="props.showName"
      class="brand-name"
      :style="{ fontSize: fontSizeMap[props.size] + 'px' }"
      >萤火</span
    >
  </div>
</template>

<style scoped>
.brand-logo {
  display: flex;
  align-items: center;
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
  font-weight: 700;
  white-space: nowrap; /* 禁止换行 */

  /* === 渐变文字 === */
  background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
  background-clip: text; /* 背景裁剪为文字形状 */
  -webkit-background-clip: text; /* 兼容 Webkit 内核浏览器 (Chrome, Safari) */
  -webkit-text-fill-color: transparent; /* 文字填充透明 */

  /* 平滑过渡 */
  letter-spacing: 1px;
  transition: opacity 0.3s ease, transform 0.3s ease;
}

/* Logo 图片保持微光效果 */
.brand-logo img {
  transition: transform 0.3s ease, filter 0.3s ease;
}

/* === 悬停效果：整体提亮，轻微上浮 === */
.brand-logo:hover .brand-name  {
  opacity: 0.8;
}

.brand-logo:hover img {
  transform: translateY(-1px) scale(1.05);
  /* 这种给图片的投影是可以的，因为图片不透明 */
  filter: drop-shadow(0 4px 6px rgba(101, 163, 13, 0.4));
}
</style>
