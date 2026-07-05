/**
 * 根组件 - 路由配置
 *
 * 路由说明：
 *   /login       - 登录页（无需认证）
 *   /register    - 注册页（无需认证）
 *   /chat        - 知识库问答主页（需登录）
 *   /knowledge   - 知识库管理（仅管理员）
 *   /dashboard   - 系统仪表盘（仅管理员）
 *   /profile     - 个人中心（需登录）
 *   /            - 重定向到 /chat
 */
import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Spin } from 'antd'
import { useAuthStore } from './store/authStore'
import AppLayout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/Login'
import RegisterPage from './pages/Register'
import ChatPage from './pages/Chat'
import KnowledgeBasePage from './pages/KnowledgeBase'
import DashboardPage from './pages/Dashboard'
import ProfilePage from './pages/Profile'

export default function App() {
  const { token, restoreSession } = useAuthStore()

  // 应用启动时尝试恢复登录状态
  useEffect(() => {
    if (token) {
      restoreSession()
    }
  }, [])

  return (
    <Routes>
      {/* 公开路由（无需登录） */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* 需要登录的路由（使用Layout布局） */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/profile" element={<ProfilePage />} />

        {/* 管理员专属路由 */}
        <Route
          path="/knowledge"
          element={
            <ProtectedRoute adminOnly>
              <KnowledgeBasePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute adminOnly>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* 默认重定向 */}
      <Route path="/" element={<Navigate to="/chat" replace />} />
      <Route path="*" element={<Navigate to="/chat" replace />} />
    </Routes>
  )
}
