<template>
  <div class="sticky top-0 z-10 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between gap-4">
    <!-- Left: Title -->
    <div class="flex items-center gap-3">
      <BookOpen :size="24" class="text-blue-600" />
      <h1 class="text-lg font-bold text-gray-900">我的文章</h1>
    </div>

    <!-- Right: Action Buttons and Search -->
    <div class="flex items-center gap-3">
      <!-- Search Input -->
      <div class="hidden sm:flex relative">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索文章..."
          @keydown.enter="handleSearch"
          class="px-3 py-2 pl-10 bg-gray-100 rounded-lg text-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
        />
        <Search :size="16" class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
      </div>

      <!-- Mobile Search Button -->
      <button
        @click="showMobileSearch = !showMobileSearch"
        class="sm:hidden p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600 hover:text-gray-900"
        title="搜索"
      >
        <Search :size="20" />
      </button>

      <!-- New Article Button -->
      <button
        @click="$emit('new-article')"
        class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
      >
        <Plus :size="18" />
        <span class="hidden sm:inline">新建</span>
      </button>

      <!-- More Actions Menu -->
      <div class="relative">
        <button
          @click="showMenu = !showMenu"
          class="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-600 hover:text-gray-900"
          title="更多操作"
        >
          <MoreVertical :size="20" />
        </button>

        <!-- Dropdown Menu -->
        <Transition
          enter-active-class="transition-all duration-150"
          leave-active-class="transition-all duration-150"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="showMenu"
            class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden"
          >
            <button
              @click="handlePublish"
              class="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors text-sm text-gray-700 border-b border-gray-100"
            >
              <Upload :size="18" class="text-gray-400" />
              <span>发布文章</span>
            </button>
            <button
              @click="handleDelete"
              class="w-full flex items-center gap-3 px-4 py-3 hover:bg-red-50 transition-colors text-sm text-red-600"
            >
              <Trash2 :size="18" />
              <span>删除文章</span>
            </button>
          </div>
        </Transition>

        <!-- Backdrop to close menu -->
        <Teleport to="body">
          <div v-if="showMenu" @click="showMenu = false" class="fixed inset-0 z-0" />
        </Teleport>
      </div>
    </div>
  </div>

  <!-- Mobile Search Bar -->
  <Transition
    enter-active-class="transition-all duration-200"
    leave-active-class="transition-all duration-200"
    enter-from-class="max-h-0 opacity-0"
    enter-to-class="max-h-20 opacity-100"
    leave-from-class="max-h-20 opacity-100"
    leave-to-class="max-h-0 opacity-0"
  >
    <div v-if="showMobileSearch" class="bg-gray-50 border-b border-gray-200 px-4 py-3">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索文章..."
        @keydown.enter="handleSearch"
        @blur="showMobileSearch = false"
        autofocus
        class="w-full px-4 py-2 bg-white rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, defineEmits } from 'vue'
import { BookOpen, Search, Plus, MoreVertical, Upload, Trash2 } from 'lucide-vue-next'

defineEmits<{
  'new-article': []
  'search': [query: string]
}>()

const searchQuery = ref('')
const showMenu = ref(false)
const showMobileSearch = ref(false)

const handleSearch = (): void => {
  if (searchQuery.value.trim()) {
    // TODO: Implement search
    console.log('Searching for:', searchQuery.value)
  }
}

const handlePublish = (): void => {
  showMenu.value = false
  // TODO: Implement publish functionality
  console.log('Publishing article...')
}

const handleDelete = (): void => {
  showMenu.value = false
  // TODO: Implement delete with confirmation
  console.log('Deleting article...')
}
</script>

<style scoped></style>
