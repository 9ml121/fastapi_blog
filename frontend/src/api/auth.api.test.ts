import { describe, it, expect } from 'vitest'
import { loginApi } from './auth.api'

describe('Auth API', () => {
  it('should login successfully', async () => {
    console.log('Current CWD:', process.cwd())
    console.log('API URL:', import.meta.env.VITE_API_BASE_URL)

    // 准备真实的测试账号 (确保后端数据库里有这个用户)
    const params = {
      username: 'test_auto@example.com', // 刚才注册的那个
      password: 'test123456',
    }

    try {
      const res = await loginApi(params)
      console.log('Login Result:', res) // 在控制台看结果

      expect(res).toHaveProperty('access_token')
      expect(res.user.email).toBe(params.username)
    } catch (error) {
      console.error('Login Failed:', error)
      throw error // 让测试失败
    }
  })
})
