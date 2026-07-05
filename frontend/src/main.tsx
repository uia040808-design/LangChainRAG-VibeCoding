/**
 * 前端入口文件
 * React 应用从这里启动
 */
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider, theme, App as AntApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'

// 全局样式
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {/* BrowserRouter：React路由，管理页面导航 */}
    <BrowserRouter>
      {/* ConfigProvider：Ant Design全局配置，中文化 */}
      <ConfigProvider
        locale={zhCN}
        theme={{
          // 默认使用浅色主题，暗黑模式通过算法切换
          algorithm: theme.defaultAlgorithm,
          token: {
            colorPrimary: '#1677ff',
            borderRadius: 8,
          },
        }}
      >
        {/* AntApp：Ant Design 5.x 的消息/通知/弹窗上下文 */}
        <AntApp>
          <App />
        </AntApp>
      </ConfigProvider>
    </BrowserRouter>
  </React.StrictMode>
)
