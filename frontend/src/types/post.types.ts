import type { PaginatedParams } from './common.types'
import type { User } from './user.types'

// 文章状态类型
export type PostStatus = 'draft' | 'published' | 'archived'

// 标签实体
export interface Tag {
  id: string
  name: string
  slug: string
}

/**
 * 基础文章类型 (对应后端的 PostListResponse)
 *
 * 用于：列表展示、搜索结果(不包含 content)
 */
export interface Post {
  id: string
  title: string
  slug: string
  summary: string | null
  status: PostStatus
  is_featured: boolean
  published_at: string | null

  // 关联信息
  author: User
  tags: Tag[]

  // 社交计数
  view_count: number
  like_count: number
  favorite_count: number
}

/**
 * 文章详情类型 (对应后端的 PostDetailResponse)
 * 用于：文章详情页、编辑页
 */
export interface PostDetailResponse extends Post {
  content: string // 核心：增加正文内容
  created_at: string // 增加时间戳
  updated_at: string
}

/**
 * 创建文章请求体 (对应后端的 PostCreate)
 */
export interface PostCreateParams {
  title: string
  content: string
  summary?: string | null
  slug?: string | null
  tags?: string[] // 传字符串数组
}

/**
 * 更新文章请求体 (对应后端的 PostUpdate)
 */
export interface PostUpdateParams {
  title?: string
  content?: string
  summary?: string | null
  slug?: string | null
  tags?: string[]
}

/**
 * 文章列表查询参数 (与后端 PostFilters 和 PostPaginationParams 对应)
 */
export interface PostQueryParams extends PaginatedParams {
  prioritize_featured?: boolean // 是否优先显示置顶文章
  author_id?: string
  tag_name?: string
  title_contains?: string
  published_at_from?: string
  published_at_to?: string
}
