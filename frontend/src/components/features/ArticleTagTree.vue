<template>
  <div class="p-4">
    <h2 class="text-sm font-bold text-gray-900 mb-4 px-2">文章分类</h2>
    <div class="space-y-1">
      <TreeNode
        v-for="tag in tags"
        :key="tag.id"
        :node="tag"
        :selected-article="selectedArticle"
        @select-article="$emit('select-article', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import TreeNode from '@/components/features/TreeNode.vue'

interface Article {
  id: string
  title: string
  content: string
  tags: string[]
  createdAt: string
  updatedAt: string
}

interface TagNode {
  id: string
  name: string
  articles: Article[]
  children?: TagNode[]
}

defineProps<{
  tags: TagNode[]
  selectedArticle: Article | null
}>()

defineEmits<{
  'select-article': [article: Article]
}>()
</script>

<style scoped></style>
