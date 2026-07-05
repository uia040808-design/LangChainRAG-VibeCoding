/**
 * 会话列表组件
 *
 * 显示在聊天页面的左侧，列出用户的所有会话。
 * 支持：切换会话、新建、重命名、删除。
 */
import { useState } from 'react'
import { List, Button, Input, Popconfirm, message } from 'antd'
import { PlusOutlined, MessageOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { useChatStore } from '../store/chatStore'

export default function SessionList() {
  const {
    sessions, currentSessionId,
    loadSessions, createSession, deleteSession, renameSession, selectSession,
  } = useChatStore()

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')

  const handleCreate = async () => {
    const id = await createSession()
    selectSession(id)
  }

  const handleDelete = async (id: string) => {
    await deleteSession(id)
    message.success('会话已删除')
  }

  const handleStartRename = (id: string, currentTitle: string) => {
    setEditingId(id)
    setEditTitle(currentTitle)
  }

  const handleFinishRename = async (id: string) => {
    if (editTitle.trim()) {
      await renameSession(id, editTitle.trim())
    }
    setEditingId(null)
  }

  const formatTime = (timeStr: string) => {
    const d = dayjs(timeStr)
    const now = dayjs()
    if (d.isSame(now, 'day')) return d.format('HH:mm')
    if (d.isSame(now, 'week')) return d.format('ddd HH:mm')
    return d.format('MM-DD')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* 新建会话按钮 */}
      <div style={{ padding: '12px' }}>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          block
          onClick={handleCreate}
        >
          新建会话
        </Button>
      </div>

      {/* 会话列表 */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        <List
          dataSource={sessions}
          locale={{ emptyText: '暂无会话，点击上方按钮创建' }}
          renderItem={(session) => (
            <List.Item
              key={session.id}
              onClick={() => selectSession(session.id)}
              style={{
                cursor: 'pointer',
                padding: '10px 16px',
                background: currentSessionId === session.id ? '#e6f4ff' : undefined,
                borderLeft: currentSessionId === session.id ? '3px solid #1677ff' : '3px solid transparent',
              }}
              actions={[
                <EditOutlined
                  key="edit"
                  onClick={(e) => { e.stopPropagation(); handleStartRename(session.id, session.title) }}
                  style={{ fontSize: 12 }}
                />,
                <Popconfirm
                  key="delete"
                  title="确定删除此会话？"
                  onConfirm={(e) => { e?.stopPropagation(); handleDelete(session.id) }}
                  onCancel={(e) => e?.stopPropagation()}
                >
                  <DeleteOutlined
                    onClick={(e) => e.stopPropagation()}
                    style={{ fontSize: 12, color: '#ff4d4f' }}
                  />
                </Popconfirm>,
              ]}
            >
              <List.Item.Meta
                avatar={<MessageOutlined style={{ fontSize: 16, color: '#1677ff' }} />}
                title={
                  editingId === session.id ? (
                    <Input
                      size="small"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onBlur={() => handleFinishRename(session.id)}
                      onPressEnter={() => handleFinishRename(session.id)}
                      onClick={(e) => e.stopPropagation()}
                      autoFocus
                    />
                  ) : (
                    <span style={{ fontSize: 13, fontWeight: currentSessionId === session.id ? 600 : 400 }}>
                      {session.title}
                    </span>
                  )
                }
                description={
                  <span style={{ fontSize: 11, color: '#999' }}>
                    {formatTime(session.updated_at)}
                  </span>
                }
              />
            </List.Item>
          )}
        />
      </div>
    </div>
  )
}
