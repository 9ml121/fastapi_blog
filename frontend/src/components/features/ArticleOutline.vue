<template>
  <div class="p-4 flex flex-col h-full">
    <h3 class="text-sm font-bold text-gray-900 mb-4 px-2">文章大纲</h3>

    <div v-if="headings.length > 0" class="flex-1 overflow-y-auto space-y-1">
      <button
        v-for="heading in headings"
        :key="heading.id"
        @click="scrollToHeading(heading.id)"
        :class="[
          'w-full text-left px-2 py-1.5 rounded hover:bg-blue-50 transition-colors text-xs',
          `pl-${heading.level * 3 + 2}`,
          activeHeadingId === heading.id ? 'bg-blue-100 text-blue-900 font-medium' : 'text-gray-600 hover:text-gray-900',
        ]"
      >
        {{ heading.title }}
      </button>
    </div>

    <div v-else class="flex items-center justify-center h-full text-gray-500">
      <p class="text-sm">暂无标题</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, watch } from 'vue'

interface Article {
  id: string
  title: string
  content: string
  tags: string[]
  createdAt: string
  updatedAt: string
}

interface Heading {
  id: string
  level: number
  title: string
}

const props = defineProps<{
  article?: Partial<Article>
}>()

const activeHeadingId = ref<string>('')

const headings = computed((): Heading[] => {
  if (!props.article?.content) return []

  const lines = props.article.content.split('\n')
  const headingList: Heading[] = []
  let headingCount = 0

  lines.forEach((line) => {
    // Match markdown headings: # H1, ## H2, ### H3, etc.
    const match = line.match(/^(#{1,6})\s+(.+)$/)
    if (match && match[1] && match[2]) {
      const level = match[1].length
      const title = match[2].trim()
      const id = `heading-${headingCount++}`

      headingList.push({ id, level, title })
    }
  })

  return headingList
})

// Extract headings and update active heading as content changes
watch(
  () => props.article?.content,
  () => {
    // Reset active heading when content changes
    if (headings.value && headings.value.length > 0 && headings.value[0]) {
      activeHeadingId.value = headings.value[0].id
    }
  },
  { immediate: true }
)

const scrollToHeading = (headingId: string): void => {
  activeHeadingId.value = headingId

  // In a real implementation with rendered markdown,
  // you would scroll to the actual heading element
  // TODO: Implement actual scroll-to-heading functionality
  console.log('Scrolling to heading:', headingId)
}
</script>

<style scoped>
/* Dynamic padding utility classes for outline indentation */
.pl-2 {
  padding-left: 0.5rem;
}

.pl-5 {
  padding-left: 1.25rem;
}

.pl-8 {
  padding-left: 2rem;
}

.pl-11 {
  padding-left: 2.75rem;
}

.pl-14 {
  padding-left: 3.5rem;
}

.pl-17 {
  padding-left: 4.25rem;
}

.pl-20 {
  padding-left: 5rem;
}
</style>
