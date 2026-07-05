/**
 * 聊天气泡组件
 *
 * 区分用户消息和AI消息的展示样式。
 * AI消息带有来源引用卡片和反馈按钮。
 */
import { useState } from 'react'
import { Avatar, Button, Space, message } from 'antd'
import { UserOutlined, RobotOutlined, LikeOutlined, DislikeOutlined, CopyOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import SourceCard from './SourceCard'
import { chatAPI, SourceInfo, Message } from '../services/chat'

interface Props {
  msg: Message
}

export default function ChatBubble({ msg }: Props) {
  const isUser = msg.role === 'user'
  const [feedback, setFeedback] = useState<string | null>(msg.feedback || null)

  const handleFeedback = async (type: 'like' | 'dislike') => {
    if (!msg.id || msg.id.startsWith('temp-')) return
    try {
      await chatAPI.sendFeedback(msg.id, type)
      setFeedback(type)
      message.success(type === 'like' ? '感谢你的认可！' : '感谢你的反馈，我们会继续改进')
    } catch {
      message.error('反馈提交失败')
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.content)
    message.success('已复制到剪贴板')
  }

  return (
    <div style={{
      display: 'flex',
      gap: 12,
      padding: '16px 0',
      flexDirection: isUser ? 'row-reverse' : 'row',
    }}>
      {/* 头像 */}
      <Avatar
        icon={isUser ? <UserOutlined /> : <RobotOutlined />}
        style={{
          backgroundColor: isUser ? '#1677ff' : '#52c41a',
          flexShrink: 0,
        }}
      />

      {/* 消息内容 */}
      <div style={{
        maxWidth: '75%',
        minWidth: 100,
      }}>
        {/* 气泡 */}
        <div style={{
          background: isUser ? '#1677ff' : '#ffffff',
          color: isUser ? '#fff' : 'inherit',
          padding: '12px 16px',
          borderRadius: 12,
          borderTopRightRadius: isUser ? 4 : 12,
          borderTopLeftRadius: isUser ? 12 : 4,
          boxShadow: isUser ? 'none' : '0 1px 3px rgba(0,0,0,0.08)',
          lineHeight: 1.8,
        }}>
          {isUser ? (
            <span>{msg.content}</span>
          ) : (
            <div className="chat-markdown">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* 非用户消息：显示来源引用 + 操作按钮 */}
        {!isUser && (
          <div style={{ marginTop: 8 }}>
            {/* 引用来源 */}
            {msg.sources && msg.sources.length > 0 && (
              <div style={{ marginBottom: 8 }}>
                <div style={{ fontSize: 12, color: '#888', marginBottom: 4 }}>
                  📖 引用来源（{msg.sources.length} 条）：
                </div>
                {msg.sources.map((source, i) => (
                  <SourceCard key={i} source={source} index={i} />
                ))}
              </div>
            )}

            {/* 操作按钮 */}
            <Space size="small">
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={handleCopy}
              >
                复制
              </Button>
              <Button
                type="text"
                size="small"
                icon={<LikeOutlined style={{ color: feedback === 'like' ? '#1677ff' : undefined }} />}
                onClick={() => handleFeedback('like')}
                disabled={!!feedback}
              />
              <Button
                type="text"
                size="small"
                icon={<DislikeOutlined style={{ color: feedback === 'dislike' ? '#ff4d4f' : undefined }} />}
                onClick={() => handleFeedback('dislike')}
                disabled={!!feedback}
              />
            </Space>
          </div>
        )}
      </div>
    </div>
  )
}
