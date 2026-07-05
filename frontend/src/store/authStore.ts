/**
 * 用户认证状态管理（Zustand）
 *
 * Zustand 是轻量级React状态管理库，比Redux简单得多。
 * 这里管理：当前用户信息、Token、登录/登出操作。
 */
import { create } from 'zustand'
import { authAPI, LoginParams, RegisterParams } from '../services/auth'

interface User {
  id: string
  username: string
  email: string
  is_admin: boolean
  created_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  loading: boolean

  /** 登录 */
  login: (params: LoginParams) => Promise<void>
  /** 注册 */
  register: (params: RegisterParams) => Promise<void>
  /** 退出登录 */
  logout: () => void
  /** 从localStorage恢复登录状态 */
  restoreSession: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  loading: false,

  login: async (params) => {
    const data = await authAPI.login(params)
    const token = data.access_token
    localStorage.setItem('token', token)
    // 拿到token后获取用户信息
    const user = await authAPI.getMe()
    localStorage.setItem('user', JSON.stringify(user))
    set({ user, token })
  },

  register: async (params) => {
    await authAPI.register(params)
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({ user: null, token: null })
  },

  restoreSession: async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      set({ user: null, token: null })
      return
    }
    try {
      const user = await authAPI.getMe()
      set({ user, token })
    } catch {
      // Token过期或无效，清除
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      set({ user: null, token: null })
    }
  },
}))
