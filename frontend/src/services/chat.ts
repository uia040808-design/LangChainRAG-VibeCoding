/**
 * 问答/会话相关 API 调用
 */
import api from './api'

export interface SourceInfo {
  document_title: string
  chunk_id: string
  content: string
  similarity_score: number
}

export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceInfo[] | null
  feedback?: string | null
  created_at: string
}

export interface Session {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export const chatAPI = {
  /** 获取会话列表 */
  getSessions: () =>
    api.get('/sessions').then(res => res.data),

  /** 创建新会话 */
  createSession: () =>
    api.post('/sessions').then(res => res.data),

  /** 删除会话 */
  deleteSession: (id: string) =>
    api.delete(`/sessions/${id}`).then(res => res.data),

  /** 重命名会话 */
  renameSession: (id: string, title: string) =>
    api.put(`/sessions/${id}`, { title }).then(res => res.data),

  /** 获取会话的历史消息 */
  getMessages: (sessionId: string): Promise<Message[]> =>
    api.get(`/sessions/${sessionId}/messages`).then(res => res.data),

  /** 发送消息反馈 */
  sendFeedback: (messageId: string, feedback: 'like' | 'dislike') =>
    api.post(`/messages/${messageId}/feedback`, { feedback }).then(res => res.data),

  /**
   * 发送消息（SSE流式）
   * 注意：这个不用axios，因为axios不支持流式读取
   * 返回一个可以逐步读取的 ReadableStream
   */
  sendMessageStream: (sessionId: string, message: string) => {
    const token = localStorage.getItem('token')
    return fetch(`/api/chat/${sessionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ message }),
    })
  },
}
