/**
 * 知识库问答主页面
 *
 * 布局：[左侧会话列表 | 右侧聊天区]
 * 聊天区包含：消息列表 + 输入框
 * 支持流式输出（打字机效果）
 */
import { useEffect, useRef, useState } from 'react'
import { Input, Button, Spin, Empty, Typography, Alert } from 'antd'
import { SendOutlined, StopOutlined } from '@ant-design/icons'
import { useChatStore } from '../store/chatStore'
import ChatBubble from '../components/ChatBubble'
import SessionList from '../components/SessionList'

const { Text } = Typography

export default function ChatPage() {
  const {
    currentSessionId, messages, streaming, streamingContent,
    loadingMessages, errorMessage,
    loadSessions, sendMessage, clearError,
  } = useChatStore()

  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<any>(null)

  // 初始化：加载会话列表
  useEffect(() => {
    loadSessions()
  }, [])

  // 新消息到来时自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const handleSend = async () => {
    const content = inputValue.trim()
    if (!content || streaming) return
    setInputValue('')
    await sendMessage(content)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // 组合消息列表：历史消息 + 正在流式输出的AI回答
  const allMessages = [...messages]
  if (streaming && streamingContent) {
    allMessages.push({
      id: 'streaming',
      session_id: currentSessionId || '',
      role: 'assistant',
      content: streamingContent,
      sources: null,
      feedback: null,
      created_at: new Date().toISOString(),
    })
  }

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 64px)' }}>
      {/* ===== 左侧会话列表 ===== */}
      <div style={{
        width: 280,
        borderRight: '1px solid #f0f0f0',
        background: '#fafafa',
        overflow: 'auto',
      }}>
        <SessionList />
      </div>

      {/* ===== 右侧聊天区 ===== */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        background: '#f5f5f5',
      }}>
        {/* 消息列表 */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          padding: '20px 32px',
        }}>
          {/* 错误提示 */}
          {errorMessage && (
            <Alert
              type="error"
              message="请求失败"
              description={errorMessage}
              showIcon
              closable
              onClose={clearError}
              style={{ marginBottom: 16 }}
            />
          )}
          {loadingMessages ? (
            <div style={{ textAlign: 'center', padding: 48 }}>
              <Spin tip="加载消息中..." />
            </div>
          ) : allMessages.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 80 }}>
              <Empty description={
                <div>
                  <div style={{ fontSize: 16, marginBottom: 8 }}>开始知识库问答</div>
                  <Text type="secondary">
                    在下方输入你的问题，AI将基于知识库内容回答
                  </Text>
                </div>
              } />
            </div>
          ) : (
            allMessages.map((msg, i) => (
              <ChatBubble key={msg.id || i} msg={msg} />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div style={{
          padding: '16px 32px',
          borderTop: '1px solid #f0f0f0',
          background: '#fff',
        }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
            <Input.TextArea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={streaming ? 'AI正在回答中...' : '输入你的问题，按Enter发送（Shift+Enter换行）'}
              autoSize={{ minRows: 1, maxRows: 5 }}
              disabled={streaming}
              style={{ flex: 1 }}
            />
            <Button
              type="primary"
              icon={streaming ? <StopOutlined /> : <SendOutlined />}
              onClick={handleSend}
              disabled={!inputValue.trim() && !streaming}
              size="large"
            >
              {streaming ? '回答中' : '发送'}
            </Button>
          </div>

          {currentSessionId && (
            <div style={{ marginTop: 4, fontSize: 11, color: '#999', textAlign: 'right' }}>
              提示：AI回答基于知识库内容，回答会标注引用来源
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
