<template>
  <div class="bg-white">
    <!-- 主要内容区域 -->
    <main class="max-w-7xl mx-auto px-4 py-12">
      <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-8">

        <!-- 左侧边栏：推荐作者 -->
        <aside class="hidden md:block md:col-span-1">
          <div class="sticky top-24 bg-linear-to-b from-gray-50 to-white p-6 rounded-lg border border-gray-100">
            <h3 class="font-bold text-lg mb-6 text-gray-900">🌟 推荐作者</h3>

            <div v-for="author in recommendedAuthors" :key="author.id"
                 class="flex items-start gap-3 mb-6 pb-6 border-b border-gray-100 last:border-b-0 last:mb-0 last:pb-0">
              <img :src="author.avatar" :alt="author.name"
                   class="w-10 h-10 rounded-full object-cover flex-shrink-0" />
              <div class="flex-1 min-w-0">
                <p class="font-semibold text-sm text-gray-900">{{ author.name }}</p>
                <p class="text-xs text-gray-500 line-clamp-2">{{ author.bio }}</p>
                <button class="mt-2 text-xs font-semibold text-blue-600 hover:text-blue-700">
                  关注
                </button>
              </div>
            </div>
          </div>
        </aside>

        <!-- 中间：文章列表（主内容） -->
        <div class="md:col-span-2 lg:col-span-2">
          <!-- 筛选选项卡 -->
          <div class="flex gap-4 mb-8 border-b border-gray-200 pb-4">
            <button v-for="filter in filters" :key="filter"
                    :class="[
                      'text-sm font-semibold pb-2 border-b-2 transition-colors',
                      activeFilter === filter
                        ? 'text-black border-b-black'
                        : 'text-gray-600 border-b-transparent hover:text-gray-900'
                    ]"
                    @click="activeFilter = filter">
              {{ filter }}
            </button>
          </div>

          <!-- 文章卡片列表 -->
          <div>
            <PostCard
              v-for="post in filteredPosts"
              :key="post.id"
              :post="post"
              @post-liked="handlePostLiked"
              @post-commented="handlePostCommented"
              @post-bookmarked="handlePostBookmarked"
            />
          </div>

          <!-- 加载更多 -->
          <div class="text-center py-8">
            <button class="px-8 py-3 text-gray-900 border border-gray-300 rounded-full font-semibold hover:bg-gray-50 transition-colors">
              加载更多文章
            </button>
          </div>
        </div>

        <!-- 右侧边栏：热门话题 -->
        <aside class="hidden lg:block lg:col-span-1">
          <div class="sticky top-24 bg-gradient-to-b from-gray-50 to-white p-6 rounded-lg border border-gray-100">
            <h3 class="font-bold text-lg mb-6 text-gray-900">🔥 热门话题</h3>

            <div v-for="topic in hotTopics" :key="topic.id"
                 class="mb-6 pb-6 border-b border-gray-100 last:border-b-0 last:mb-0 last:pb-0 hover:bg-gray-100 p-3 rounded transition-colors cursor-pointer">
              <p class="font-semibold text-sm text-blue-600 mb-1">#{{ topic.name }}</p>
              <p class="text-xs text-gray-500">{{ topic.count }} 篇文章</p>
            </div>
          </div>
        </aside>

      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import PostCard from '@/components/PostCard.vue'

// ============ 状态管理 ============
const activeFilter = ref('最新')
const filters = ref(['最新', '热门', '关注的'])

// ============ 示例数据 ============

// 推荐作者
const recommendedAuthors = ref([
  {
    id: 1,
    name: 'Alice Chen',
    avatar: 'https://i.pravatar.cc/40?img=1',
    bio: 'Full Stack Engineer，热爱分享 Web 开发最佳实践'
  },
  {
    id: 2,
    name: 'Bob Johnson',
    avatar: 'https://i.pravatar.cc/40?img=2',
    bio: 'Python 爱好者，专注于后端架构设计'
  },
  {
    id: 3,
    name: 'Carol Davis',
    avatar: 'https://i.pravatar.cc/40?img=3',
    bio: 'UI/UX 设计师，分享设计思考'
  },
])

// 热门话题
const hotTopics = ref([
  { id: 1, name: 'JavaScript', count: 1240 },
  { id: 2, name: 'React', count: 856 },
  { id: 3, name: 'Python', count: 920 },
  { id: 4, name: 'Web Design', count: 567 },
  { id: 5, name: 'DevOps', count: 432 },
])

// 文章列表
const posts = ref([
  {
    id: 1,
    title: '深入理解 JavaScript 异步编程：从 Callback 到 Async/Await',
    excerpt: '在这篇文章中，我们将深入探讨 JavaScript 的异步编程模式。从最基础的 Callback，到 Promise，再到现代的 Async/Await，我们会逐一讲解它们的工作原理、优缺点，以及最佳实践。',
    author: {
      id: 1,
      name: 'Alice Chen',
      avatar: 'https://i.pravatar.cc/40?img=1'
    },
    tags: ['JavaScript', '异步编程', 'Web开发'],
    createdAt: new Date('2025-11-12'),
    readingTime: 12,
    likes: 342,
    comments: 28,
    bookmarks: 145,
    coverImage: 'https://images.unsplash.com/photo-1633356122544-f134324ef6db?w=200&h=200&fit=crop'
  },
  {
    id: 2,
    title: 'React Hooks 完全指南：如何正确使用和避免常见陷阱',
    excerpt: 'React Hooks 已经成为现代 React 开发的标准。但许多开发者在使用 Hooks 时仍然会遇到各种问题。本文将详细讲解 useState、useEffect 等常用 Hooks 的用法，以及如何避免性能问题。',
    author: {
      id: 2,
      name: 'Bob Johnson',
      avatar: 'https://i.pravatar.cc/40?img=2'
    },
    tags: ['React', 'Hooks', 'JavaScript'],
    createdAt: new Date('2025-11-11'),
    readingTime: 15,
    likes: 521,
    comments: 42,
    bookmarks: 267,
    coverImage: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=200&h=200&fit=crop'
  },
  {
    id: 3,
    title: 'FastAPI 快速入门：构建高性能 Python Web API',
    excerpt: 'FastAPI 是一个现代的、快速的 Python Web 框架，用于构建 API。与传统的 Flask 和 Django 相比，FastAPI 提供了更好的性能和开发体验。让我们从零开始学习 FastAPI。',
    author: {
      id: 3,
      name: 'Carol Davis',
      avatar: 'https://i.pravatar.cc/40?img=3'
    },
    tags: ['FastAPI', 'Python', '后端'],
    createdAt: new Date('2025-11-10'),
    readingTime: 18,
    likes: 287,
    comments: 35,
    bookmarks: 156,
    coverImage: 'https://images.unsplash.com/photo-1536817617318-7f91d3c3443b?w=200&h=200&fit=crop'
  },
  {
    id: 4,
    title: '现代 CSS 布局完全掌握：Flexbox 和 Grid',
    excerpt: '告别浮动和定位！Flexbox 和 CSS Grid 已经彻底改变了我们设计网页布局的方式。这篇文章将从基础开始，逐步讲解这两个强大的布局工具如何使用。',
    author: {
      id: 1,
      name: 'Alice Chen',
      avatar: 'https://i.pravatar.cc/40?img=1'
    },
    tags: ['CSS', '布局', '前端'],
    createdAt: new Date('2025-11-09'),
    readingTime: 14,
    likes: 456,
    comments: 38,
    bookmarks: 201,
    coverImage: 'https://images.unsplash.com/photo-1517694712571-f3ece2daaf51?w=200&h=200&fit=crop'
  },
  {
    id: 5,
    title: '数据库设计最佳实践：从范式到性能优化',
    excerpt: '好的数据库设计是构建高性能应用的基础。但许多开发者在数据库设计上投入不足。本文将讲解数据库设计的重要原则，以及如何进行性能优化。',
    author: {
      id: 2,
      name: 'Bob Johnson',
      avatar: 'https://i.pravatar.cc/40?img=2'
    },
    tags: ['数据库', 'SQL', '性能优化'],
    createdAt: new Date('2025-11-08'),
    readingTime: 20,
    likes: 398,
    comments: 45,
    bookmarks: 198,
    coverImage: 'https://images.unsplash.com/photo-1533050487297-20b450cf0d1d?w=200&h=200&fit=crop'
  },
])

// ============ 辅助函数 ============

/**
 * 格式化日期（相对时间）
 * @param date - 日期对象
 * @returns 相对时间字符串
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

// ============ 计算属性 ============

/**
 * 根据 activeFilter 过滤文章
 * 实际项目中，这应该来自 API
 */
const filteredPosts = computed(() => {
  // 这里只是示例，实际应该根据 activeFilter 调用 API
  return posts.value
})

// ============ 事件处理函数 ============

/**
 * 处理文章点赞事件
 * @param postId - 文章 ID
 */
const handlePostLiked = (postId: number): void => {
  console.log(`文章 ${postId} 被点赞`)
  // 后期调用 API 更新点赞状态
  const post = posts.value.find(p => p.id === postId)
  if (post) {
    post.likes += 1
  }
}

/**
 * 处理文章评论事件
 * @param postId - 文章 ID
 */
const handlePostCommented = (postId: number): void => {
  console.log(`文章 ${postId} 被评论`)
  // 后期跳转到文章详情页面或打开评论区
}

/**
 * 处理文章收藏事件
 * @param postId - 文章 ID
 */
const handlePostBookmarked = (postId: number): void => {
  console.log(`文章 ${postId} 被收藏`)
  // 后期调用 API 更新收藏状态
  const post = posts.value.find(p => p.id === postId)
  if (post) {
    post.bookmarks += 1
  }
}
</script>

<style scoped>
/* 自定义平滑滚动行为 */
@supports (scroll-behavior: smooth) {
  html {
    scroll-behavior: smooth;
  }
}

/* 文章卡片悬停效果的细微阴影 */
article {
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
}

article:hover {
  background-color: rgba(0, 0, 0, 0.01);
}
</style>
