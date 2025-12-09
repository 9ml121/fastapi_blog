<script lang="ts" setup>
import type { TocItem } from '../composables/useTableOfContents'

// Props && Emits
defineProps<{ items: TocItem[], activeId: string | null }>()


const emit = defineEmits<{ select: [id: string] }>()

const handleClick = (id: string) => {
  emit('select', id)
}
</script>

<template>
  <div v-if="items.length > 0" class="toc-container">
    <div class="toc-title">目录</div>
    <ul class="toc-list">
      <li
        v-for="item in items"
        :key="item.id"
        :class="['toc-item', `toc-level-${item.level}`, { active: item.id === activeId }]"
        @click="handleClick(item.id)"
      >
        {{ item.text }}
      </li>
    </ul>
  </div>
</template>

<style scoped>
.toc-container {
  position: fixed; /* 固定在浏览器窗口的某个位置，滚动页面时不动 */
  right: 24px; /* 距离窗口右边 24px */
  top: 80px; /* 距离顶部 80px（避开导航栏） */
  width: 220px; /* 固定宽度 200px */
  max-height: calc(100vh - 120px); /* vh 是视口高度单位，70vh = 视口高度的 70% */
  overflow-y: auto; /* 只在需要时显示垂直滚动条 */
  font-size: 13px; /* 字体大小 */
  background: transparent; /* 透明背景 */
}

@media (max-width: 768px) {
  .toc-container {
    display: none; /* 移动端隐藏目录 */
  }
}

.toc-title {
  font-weight: 500;
  text-transform: uppercase; /* 大写字母 */
  letter-spacing: 0.1em; /* 字母间距 */
  color: #6b7280;
  margin-bottom: 16px;
  padding-left: 12px;
}

.toc-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.toc-item {
  padding: 6px 12px;
  border-left: 2px solid transparent; /* 左侧指示条占位 */
  line-height: 1.5;
  cursor: pointer;
  border-radius: 4px;
  color: #6b7280;
  transition: all 0.2s;
}

.toc-item:hover {
  color: #111827;
  background: transparent; /* 悬停不变背景 */
}

.toc-item.active {
  color: #42b983;
  border-left-color: #42b983; /* 左侧指示条 */
  font-weight: 500;
}

/* H3 缩进 */
.toc-level-3 {
  padding-left: 24px;
}

[data-line-type="h2"],
[data-line-type="h3"] {
  scroll-margin-top: 20px; /* 距离顶部的偏移量 */
}
</style>
