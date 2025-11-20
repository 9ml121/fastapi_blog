<template>
  <div class="flex flex-col h-screen bg-gray-50">
    <!-- Top Toolbar -->
    <PersonalToolbar @new-article="handleNewArticle" @search="handleSearch" />

    <!-- Main Content Area -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Left Panel: Article Tag Tree Navigation -->
      <div
        class="hidden lg:flex lg:w-64 bg-white border-r border-gray-200 flex-col overflow-y-auto"
      >
        <ArticleTagTree :tags="tags" :selected-article="selectedArticle" @select-article="selectArticle" />
      </div>

      <!-- Middle Panel: Article Editor -->
      <div class="flex-1 flex flex-col overflow-hidden bg-white">
        <ArticleEditor 
          v-if="selectedArticle || isCreatingNew"
          :article="editingArticle" 
          @save="saveArticle"
          @cancel="cancelEdit"
        />
        <div v-else class="flex items-center justify-center h-full text-gray-500">
          <div class="text-center">
            <BookOpen :size="48" class="mx-auto mb-4 text-gray-300" />
            <p class="text-lg">选择一篇文章进行编辑</p>
            <p class="text-sm text-gray-400">或点击"新建"按钮创建新文章</p>
          </div>
        </div>
      </div>

      <!-- Right Panel: Article Outline (Desktop Only) -->
      <div
        class="hidden xl:flex xl:w-72 bg-white border-l border-gray-200 flex-col overflow-y-auto"
      >
        <ArticleOutline v-if="selectedArticle" :article="editingArticle" />
        <div v-else class="flex items-center justify-center h-full text-gray-500">
          <p class="text-sm">大纲将显示在此处</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { BookOpen } from 'lucide-vue-next'
import PersonalToolbar from '@/components/features/PersonalToolbar.vue'
import ArticleTagTree from '@/components/features/ArticleTagTree.vue'
import ArticleEditor from '@/components/features/ArticleEditor.vue'
import ArticleOutline from '@/components/features/ArticleOutline.vue'

// Mock data types
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

// State management
const tags = ref<TagNode[]>([
  {
    id: '1',
    name: '技术',
    articles: [
      { id: 'a1', title: 'Vue 3 最佳实践', content: '', tags: ['技术'], createdAt: '', updatedAt: '' },
      { id: 'a2', title: 'FastAPI 异步编程', content: '', tags: ['技术'], createdAt: '', updatedAt: '' },
    ],
    children: [
      {
        id: '1-1',
        name: 'Frontend',
        articles: [],
        children: [
          {
            id: '1-1-1',
            name: 'Vue',
            articles: [{ id: 'a3', title: 'Vue Router 深度解析', content: '', tags: ['技术', 'Frontend', 'Vue'], createdAt: '', updatedAt: '' }],
          },
        ],
      },
      {
        id: '1-2',
        name: 'Backend',
        articles: [],
      },
    ],
  },
  {
    id: '2',
    name: '生活',
    articles: [
      { id: 'a4', title: '2024年总结', content: '', tags: ['生活'], createdAt: '', updatedAt: '' },
    ],
  },
])

const selectedArticle = ref<Article | null>(null)
const isCreatingNew = ref(false)
const editingArticle = reactive<Partial<Article>>({
  id: '',
  title: '',
  content: '',
  tags: [],
  createdAt: '',
  updatedAt: '',
})

// Methods
const selectArticle = (article: Article): void => {
  selectedArticle.value = article
  isCreatingNew.value = false
  Object.assign(editingArticle, article)
}

const handleNewArticle = (): void => {
  isCreatingNew.value = true
  selectedArticle.value = null
  Object.assign(editingArticle, {
    id: '',
    title: '',
    content: '',
    tags: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  })
}

const saveArticle = (article: Partial<Article>): void => {
  if (isCreatingNew.value) {
    // TODO: Save new article to backend
    console.log('Creating new article:', article)
  } else {
    // TODO: Update existing article on backend
    console.log('Updating article:', article)
  }
  isCreatingNew.value = false
  selectedArticle.value = null
}

const cancelEdit = (): void => {
  isCreatingNew.value = false
  selectedArticle.value = null
}

const handleSearch = (query: string): void => {
  // TODO: Implement search functionality
  console.log('Searching for:', query)
}
</script>

<style scoped></style>
