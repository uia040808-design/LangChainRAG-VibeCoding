/**
 * 路由守卫组件
 *
 * 作用：包装需要登录才能访问的页面。
 * 如果用户未登录，自动跳转到登录页。
 * 如果页面仅管理员可访问且用户不是管理员，显示403。
 */
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Result, Button } from 'antd'

interface Props {
  children: React.ReactNode
  /** 是否仅管理员可访问 */
  adminOnly?: boolean
}

export default function ProtectedRoute({ children, adminOnly = false }: Props) {
  const { token, user } = useAuthStore()

  // 未登录 → 跳转登录页
  if (!token) {
    return <Navigate to="/login" replace />
  }

  // 需要管理员权限但用户不是管理员 → 提示403
  if (adminOnly && user && !user.is_admin) {
    return (
      <Result
        status="403"
        title="403"
        subTitle="抱歉，你没有权限访问此页面，仅管理员可访问"
        extra={
          <Button type="primary" onClick={() => window.location.href = '/'}>
            返回首页
          </Button>
        }
      />
    )
  }

  return <>{children}</>
}
