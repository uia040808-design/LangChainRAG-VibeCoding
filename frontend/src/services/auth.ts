/**
 * 认证相关 API 调用
 */
import api from './api'

export interface LoginParams {
  username: string
  password: string
}

export interface RegisterParams {
  username: string
  password: string
  email?: string
}

export interface ChangePasswordParams {
  old_password: string
  new_password: string
}

export const authAPI = {
  /** 登录 */
  login: (params: LoginParams) =>
    api.post('/auth/login', params).then(res => res.data),

  /** 注册 */
  register: (params: RegisterParams) =>
    api.post('/auth/register', params).then(res => res.data),

  /** 修改密码 */
  changePassword: (params: ChangePasswordParams) =>
    api.post('/auth/change-password', params).then(res => res.data),

  /** 获取当前用户信息 */
  getMe: () =>
    api.get('/auth/me').then(res => res.data),
}
