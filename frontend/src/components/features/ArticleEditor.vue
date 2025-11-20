<template>
  <div class="flex flex-col h-full">
    <!-- Editor Header with Save/Cancel Buttons -->
    <div class="border-b border-gray-200 px-6 py-4 flex items-center justify-between gap-4 bg-gray-50">
      <div class="flex items-center gap-4 flex-1 min-w-0">
        <input
          v-model="editingArticle.title"
          type="text"
          placeholder="输入文章标题..."
          class="flex-1 text-lg font-bold text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
        />
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <button
          @click="emit('cancel')"
          class="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors text-sm font-medium"
        >
          取消
        </button>
        <button
          @click="saveArticle"
          class="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors text-sm font-medium"
        >
          保存
        </button>
      </div>
    </div>

    <!-- Editor Content Area -->
    <div class="flex-1 overflow-y-auto p-6">
      <!-- Tags Section -->
      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 mb-3">标签</label>
        <div class="flex flex-wrap gap-2 mb-3">
          <span
            v-for="tag in editingArticle.tags"
            :key="tag"
            class="inline-flex items-center gap-2 bg-blue-100 text-blue-900 px-3 py-1 rounded-full text-sm"
          >
            {{ tag }}
            <button
              @click="removeTag(tag)"
              class="hover:text-blue-600 font-bold leading-none"
            >
              ×
            </button>
          </span>
        </div>

        <!-- Tag Input -->
        <div class="flex gap-2">
          <input
            v-model="newTag"
            type="text"
            placeholder="输入标签并按回车..."
            @keydown.enter="addTag"
            class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            @click="addTag"
            class="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors text-sm font-medium"
          >
            添加
          </button>
        </div>
      </div>

      <!-- Content Section -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-3">内容</label>
        <textarea
          v-model="editingArticle.content"
          placeholder="在这里输入你的文章内容..."
          class="w-full h-96 px-4 py-3 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        ></textarea>
        <p class="text-xs text-gray-500 mt-2">
          现在支持 Markdown 格式。富文本编辑器即将推出！
        </p>
      </div>

      <!-- Meta Information -->
      <div class="mt-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p class="text-gray-500">创建时间</p>
            <p class="text-gray-900 font-medium">{{ formatDate(editingArticle.createdAt) }}</p>
          </div>
          <div>
            <p class="text-gray-500">最后修改</p>
            <p class="text-gray-900 font-medium">{{ formatDate(editingArticle.updatedAt) }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, defineProps, defineEmits, watch } from 'vue'

interface Article {
  id: string
  title: string
  content: string
  tags: string[]
  createdAt: string
  updatedAt: string
}

const props = defineProps<{
  article?: Partial<Article>
}>()

const emit = defineEmits<{
  'save': [article: Partial<Article>]
  'cancel': []
}>()

const editingArticle = reactive<Partial<Article>>({
  id: '',
  title: '',
  content: '',
  tags: [],
  createdAt: '',
  updatedAt: '',
})

const newTag = ref('')

// Sync with props when article changes
watch(
  () => props.article,
  (newArticle) => {
    if (newArticle) {
      Object.assign(editingArticle, newArticle)
    }
  },
  { immediate: true, deep: true }
)

const addTag = (): void => {
  const tag = newTag.value.trim()
  if (tag && !editingArticle.tags?.includes(tag)) {
    editingArticle.tags = [...(editingArticle.tags || []), tag]
    newTag.value = ''
  }
}

const removeTag = (tag: string): void => {
  editingArticle.tags = editingArticle.tags?.filter((t) => t !== tag) || []
}

const saveArticle = (): void => {
  // Update timestamp on save
  const now = new Date().toISOString()
  emit('save', {
    ...editingArticle,
    updatedAt: now,
  })
}

const formatDate = (dateString?: string): string => {
  if (!dateString) return '-'
  try {
    return new Date(dateString).toLocaleString('zh-CN')
  } catch {
    return dateString
  }
}
</script>

<style scoped></style>
