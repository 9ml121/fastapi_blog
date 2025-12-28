import api from '@/api'
import type { PaginatedResponse } from '@/types/common.types'
import type { Post, PostQueryParams} from '@/types/post.types'

/**
 * 获取文章列表 (支持分页和筛选)
 */
export async function getPostsApi(
  params: PostQueryParams,
): Promise<PaginatedResponse<Post>> {
  const response = await api.get<PaginatedResponse<Post>>('/posts', { params })

  return response.data
}

/**
 * 获取文章详情
 */
export async function getPostDetailApi(id: string): Promise<Post> {
  const response = await api.get<Post>(`/posts/${id}`)

  return response.data
}
