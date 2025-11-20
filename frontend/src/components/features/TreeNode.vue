<template>
  <div class="select-none">
    <!-- Tag/Folder Node -->
    <button
      @click="toggleExpanded"
      :class="[
        'w-full flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-100 transition-colors',
        'text-gray-700 hover:text-gray-900 text-sm font-medium',
      ]"
    >
      <!-- Expand/Collapse Icon -->
      <ChevronRight
        :size="16"
        :class="[
          'flex-shrink-0 transition-transform',
          isExpanded ? 'rotate-90' : '',
          hasChildren ? '' : 'invisible',
        ]"
      />
      <!-- Folder Icon -->
      <Folder :size="16" class="flex-shrink-0 text-blue-500" />
      <!-- Tag Name -->
      <span class="flex-1 text-left truncate">{{ node.name }}</span>
      <!-- Article Count Badge -->
      <span v-if="totalArticles > 0" class="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full flex-shrink-0">
        {{ totalArticles }}
      </span>
    </button>

    <!-- Expandable Content -->
    <Transition
      enter-active-class="transition-all duration-200"
      leave-active-class="transition-all duration-200"
      enter-from-class="max-h-0 opacity-0"
      enter-to-class="max-h-screen opacity-100"
      leave-from-class="max-h-screen opacity-100"
      leave-to-class="max-h-0 opacity-0"
    >
      <div v-if="isExpanded" class="overflow-hidden">
        <!-- Articles in this tag -->
        <div v-if="node.articles.length > 0" class="ml-4 space-y-0.5">
          <button
            v-for="article in node.articles"
            :key="article.id"
            @click="$emit('select-article', article)"
            :class="[
              'w-full flex items-center gap-2 px-2 py-1 rounded hover:bg-blue-50 transition-colors',
              'text-gray-600 hover:text-gray-900 text-xs',
              selectedArticle?.id === article.id ? 'bg-blue-100 text-blue-900' : '',
            ]"
            title="article.title"
          >
            <FileText :size="14" class="flex-shrink-0" />
            <span class="flex-1 text-left truncate">{{ article.title }}</span>
          </button>
        </div>

        <!-- Child nodes (nested tags) -->
        <div v-if="hasChildren" class="ml-4 space-y-1">
          <TreeNode
            v-for="child in node.children"
            :key="child.id"
            :node="child"
            :selected-article="selectedArticle"
            @select-article="$emit('select-article', $event)"
          />
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from 'vue'
import { ChevronRight, Folder, FileText } from 'lucide-vue-next'

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

const props = defineProps<{
  node: TagNode
  selectedArticle: Article | null
}>()

const emit = defineEmits<{
  'select-article': [article: Article]
}>()

const isExpanded = ref(false)

const hasChildren = computed(() => (props.node.children?.length ?? 0) > 0)

const totalArticles = computed(() => {
  let count = props.node.articles.length
  if (props.node.children) {
    props.node.children.forEach((child) => {
      count += countArticlesRecursive(child)
    })
  }
  return count
})

const countArticlesRecursive = (node: TagNode): number => {
  let count = node.articles.length
  if (node.children) {
    node.children.forEach((child) => {
      count += countArticlesRecursive(child)
    })
  }
  return count
}

const toggleExpanded = (): void => {
  isExpanded.value = !isExpanded.value
}
</script>

<style scoped></style>
