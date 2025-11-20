<template>
  <!-- 文章卡片：展示单篇文章的信息 -->
  <article class="group border-b border-gray-200 py-8 hover:bg-gray-50 transition-colors cursor-pointer px-2 -mx-2 rounded">
    
    <!-- 文章上半部分：作者 + 标题 + 摘要 + 标签 -->
    <div class="flex gap-4">
      <!-- 左侧：主要内容 -->
      <div class="flex-1 min-w-0">
        <!-- 作者信息 -->
        <div class="flex items-center gap-2 mb-3">
          <img 
            :src="post.author.avatar" 
            :alt="post.author.name"
            class="w-8 h-8 rounded-full object-cover" 
          />
          <div class="text-sm">
            <p class="font-semibold text-gray-900">{{ post.author.name }}</p>
            <p class="text-xs text-gray-500">{{ formatDate(post.createdAt) }}</p>
          </div>
        </div>

        <!-- 标题 -->
        <h2 class="text-lg md:text-xl font-bold text-gray-900 mb-3 line-clamp-2 group-hover:text-blue-500 transition-colors cursor-pointer">
          {{ post.title }}
        </h2>

        <!-- 摘要 -->
        <p class="text-gray-700 text-base leading-relaxed line-clamp-3 mb-4">
          {{ post.excerpt }}
        </p>

        <!-- 底部元数据：标签 + 阅读时间 -->
        <div class="flex items-center justify-between text-sm">
          <div class="flex gap-2 flex-wrap">
            <span 
              v-for="tag in post.tags" 
              :key="tag"
              class="text-xs font-medium px-2 py-1 rounded bg-gray-100 text-gray-700 hover:bg-blue-100 hover:text-blue-700 transition-colors cursor-pointer"
            >
              {{ tag }}
            </span>
          </div>
          <span class="text-gray-500 whitespace-nowrap">
            {{ post.readingTime }} 分钟阅读
          </span>
        </div>
      </div>

      <!-- 右侧：文章封面图（仅在 sm 屏幕及以上显示） -->
      <div v-if="post.coverImage" class="hidden sm:block flex-shrink-0 w-28 h-28">
        <img 
          :src="post.coverImage" 
          :alt="post.title"
          class="w-full h-full object-cover rounded-lg group-hover:shadow-md transition-shadow" 
        />
      </div>
    </div>

    <!-- 交互按钮：点赞、评论、收藏 -->
    <div class="flex items-center gap-4 mt-4 text-gray-600 text-sm">
      <button 
        class="flex items-center gap-2 hover:text-red-600 transition-colors group/btn"
        @click="handleLike"
        :title="`点赞 (${post.likes})`"
      >
        <Heart :size="18" class="group-hover/btn:fill-red-600" />
        <span class="text-gray-600 group-hover/btn:text-red-600">{{ post.likes }}</span>
      </button>
      <button 
        class="flex items-center gap-2 hover:text-blue-600 transition-colors group/btn"
        @click="handleComment"
        :title="`评论 (${post.comments})`"
      >
        <MessageCircle :size="18" />
        <span class="text-gray-600 group-hover/btn:text-blue-600">{{ post.comments }}</span>
      </button>
      <button 
        class="flex items-center gap-2 hover:text-purple-600 transition-colors group/btn"
        @click="handleBookmark"
        :title="`收藏 (${post.bookmarks})`"
      >
        <Bookmark :size="18" />
        <span class="text-gray-600 group-hover/btn:text-purple-600">{{ post.bookmarks }}</span>
      </button>
    </div>
  </article>
</template>

<script setup lang="ts">
import { Heart, MessageCircle, Bookmark } from 'lucide-vue-next'

/**
 * PostCard 组件
 * 
 * Props:
 *   - post: 文章对象，包含 id, title, excerpt, author, tags, createdAt, readingTime, likes, comments, bookmarks, coverImage
 * 
 * Emits:
 *   - post-clicked: 点击卡片时触发
 *   - post-liked: 点赞时触发
 *   - post-commented: 评论时触发
 *   - post-bookmarked: 收藏时触发
 */

interface Author {
  id: number
  name: string
  avatar: string
}

interface Post {
  id: number
  title: string
  excerpt: string
  author: Author
  tags: string[]
  createdAt: Date
  readingTime: number
  likes: number
  comments: number
  bookmarks: number
  coverImage?: string
}

// Props 定义
const props = withDefaults(
  defineProps<{
    post: Post
  }>(),
  {}
)

// Emits 定义
const emit = defineEmits<{
  'post-clicked': [postId: number]
  'post-liked': [postId: number]
  'post-commented': [postId: number]
  'post-bookmarked': [postId: number]
}>()

/**
 * 格式化日期为相对时间
 * @param date - 日期对象
 * @returns 相对时间字符串（如"2 天前"）
 */
const formatDate = (date: Date): string => {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) return `${diffDays} 天前`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} 周前`
  return `${Math.floor(diffDays / 30)} 个月前`
}

// 事件处理函数
const handleLike = () => {
  emit('post-liked', props.post.id)
}

const handleComment = () => {
  emit('post-commented', props.post.id)
}

const handleBookmark = () => {
  emit('post-bookmarked', props.post.id)
}
</script>

<style scoped>
/* 文章卡片悬停效果 */
article {
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
}

article:hover {
  background-color: rgba(0, 0, 0, 0.01);
}
</style>
