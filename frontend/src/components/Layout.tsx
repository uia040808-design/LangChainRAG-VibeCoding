/**
 * 全局页面布局组件
 *
 * 结构：顶部导航栏 + 侧边栏 + 主内容区
 * 顶部显示系统名称和用户信息
 * 侧边栏显示导航菜单（不同角色看到不同菜单）
 */
import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout as AntLayout, Menu, Button, Avatar, Dropdown, theme } from 'antd'
import {
  MessageOutlined,
  DatabaseOutlined,
  UserOutlined,
  DashboardOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SunOutlined,
  MoonOutlined,
} from '@ant-design/icons'
import { useAuthStore } from '../store/authStore'
import { useChatStore } from '../store/chatStore'

const { Header, Sider, Content } = AntLayout

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [darkMode, setDarkMode] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const resetChat = useChatStore(state => state.reset)

  const isAdmin = user?.is_admin

  // 普通用户菜单
  const userMenuItems = [
    { key: '/chat', icon: <MessageOutlined />, label: '知识库问答' },
    { key: '/profile', icon: <UserOutlined />, label: '个人中心' },
  ]

  // 管理员额外菜单
  const adminMenuItems = [
    { key: '/chat', icon: <MessageOutlined />, label: '知识库问答' },
    { key: '/knowledge', icon: <DatabaseOutlined />, label: '知识库管理' },
    { key: '/dashboard', icon: <DashboardOutlined />, label: '系统仪表盘' },
    { key: '/profile', icon: <UserOutlined />, label: '个人中心' },
  ]

  const menuItems = isAdmin ? adminMenuItems : userMenuItems

  const handleLogout = () => {
    logout()
    resetChat()  // 清空聊天状态，防止下一个用户看到上一个用户的消息
    navigate('/login')
  }

  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
    // 简单暗黑模式：切换body的data-theme属性
    document.body.setAttribute('data-theme', darkMode ? 'light' : 'dark')
    // 实际项目中可以用 antd 的 ConfigProvider theme 切换
  }

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      {/* ===== 左侧边栏 ===== */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={220}
        style={{
          background: darkMode ? '#141414' : '#fff',
          borderRight: '1px solid #f0f0f0',
        }}
      >
        {/* Logo区域 */}
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderBottom: '1px solid #f0f0f0',
          fontWeight: 'bold',
          fontSize: collapsed ? 16 : 18,
          color: '#1677ff',
        }}>
          {collapsed ? '📚' : '📚 知识库问答'}
        </div>

        {/* 导航菜单 */}
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 0, marginTop: 8 }}
        />
      </Sider>

      {/* ===== 右侧区域 ===== */}
      <AntLayout>
        {/* 顶部导航栏 */}
        <Header style={{
          background: darkMode ? '#141414' : '#fff',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #f0f0f0',
          height: 64,
        }}>
          {/* 左侧：折叠按钮 */}
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: 16, width: 40, height: 40 }}
          />

          {/* 右侧：暗黑模式切换 + 用户下拉菜单 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Button
              type="text"
              icon={darkMode ? <SunOutlined /> : <MoonOutlined />}
              onClick={toggleDarkMode}
            />

            <Dropdown
              menu={{
                items: [
                  { key: 'profile', icon: <UserOutlined />, label: '个人中心', onClick: () => navigate('/profile') },
                  { type: 'divider' },
                  { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: handleLogout, danger: true },
                ],
              }}
            >
              <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Avatar icon={<UserOutlined />} />
                <span>{user?.username}</span>
                {isAdmin && <span style={{ color: '#1677ff', fontSize: 12 }}>(管理员)</span>}
              </div>
            </Dropdown>
          </div>
        </Header>

        {/* 主内容区 */}
        <Content style={{
          margin: 0,
          background: darkMode ? '#000' : '#f5f5f5',
          overflow: 'auto',
        }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}
