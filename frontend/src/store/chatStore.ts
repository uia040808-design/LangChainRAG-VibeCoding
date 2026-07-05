/**
 * 聊天状态管理
 *
 * 管理：会话列表、当前会话、消息列表、流式接收状态。
 */
import { create } from 'zustand'
import { chatAPI, Session, Message, SourceInfo } from '../services/chat'

interface ChatState {
  // 会话列表
  sessions: Session[]
  // 当前选中会话ID
  currentSessionId: string | null
  // 当前会话的消息列表
  messages: Message[]
  // 是否正在加载消息
  loadingMessages: boolean
  // 是否正在等待AI回答
  streaming: boolean
  // 流式接收中的临时内容
  streamingContent: string
  // 当前流式接收的引用来源
  streamingSources: SourceInfo[]
  // 错误信息
  errorMessage: string | null

  // 操作
  loadSessions: () => Promise<void>
  createSession: () => Promise<string>
  deleteSession: (id: string) => Promise<void>
  renameSession: (id: string, title: string) => Promise<void>
  selectSession: (id: string) => Promise<void>
  loadMessages: (sessionId: string) => Promise<void>
  sendMessage: (content: string) => Promise<void>
  addUserMessage: (content: string) => void
  appendStreamToken: (token: string) => void
  setStreamSources: (sources: SourceInfo[]) => void
  finishStreaming: (messageId: string, fullContent: string) => void
  handleStreamError: (message: string) => void
  setStreaming: (v: boolean) => void
  clearError: () => void
  /** 重置所有状态（退出登录时调用） */
  reset: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  loadingMessages: false,
  streaming: false,
  streamingContent: '',
  streamingSources: [],
  errorMessage: null,

  loadSessions: async () => {
    const data = await chatAPI.getSessions()
    set({ sessions: data.sessions || [] })
  },

  createSession: async () => {
    const session = await chatAPI.createSession()
    set(state => ({ sessions: [session, ...state.sessions] }))
    return session.id
  },

  deleteSession: async (id) => {
    await chatAPI.deleteSession(id)
    set(state => {
      const sessions = state.sessions.filter(s => s.id !== id)
      // 如果删除的是当前会话，切换到第一个
      if (state.currentSessionId === id) {
        const next = sessions[0]
        return { sessions, currentSessionId: next?.id || null, messages: [] }
      }
      return { sessions }
    })
  },

  renameSession: async (id, title) => {
    await chatAPI.renameSession(id, title)
    set(state => ({
      sessions: state.sessions.map(s =>
        s.id === id ? { ...s, title } : s
      ),
    }))
  },

  selectSession: async (id) => {
    set({ currentSessionId: id, streamingContent: '', streamingSources: [] })
    if (id) {
      await get().loadMessages(id)
    }
  },

  loadMessages: async (sessionId) => {
    set({ loadingMessages: true })
    try {
      const messages = await chatAPI.getMessages(sessionId)
      set({ messages: messages || [] })
    } finally {
      set({ loadingMessages: false })
    }
  },

  sendMessage: async (content: string) => {
    const state = get()
    let sessionId = state.currentSessionId

    // 如果没有当前会话，先创建一个
    if (!sessionId) {
      sessionId = await get().createSession()
      set({ currentSessionId: sessionId })
    }

    // 添加用户消息到界面
    get().addUserMessage(content)

    // 开始流式接收
    set({ streaming: true, streamingContent: '', streamingSources: [] })

    try {
      const response = await chatAPI.sendMessageStream(sessionId, content)

      if (!response.ok) {
        throw new Error('请求失败')
      }

      // 读取SSE流
      const reader = response.body?.getReader()
      if (!reader) throw new Error('无法读取响应流')

      const decoder = new TextDecoder()
      let buffer = ''

      let receivedDone = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let eventType = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6))
            if (eventType === 'sources') {
              get().setStreamSources(data)
            } else if (eventType === 'token') {
              get().appendStreamToken(data.content)
            } else if (eventType === 'error') {
              get().handleStreamError(data.message)
              return  // 发生错误时停止读取
            } else if (eventType === 'done') {
              receivedDone = true
              get().finishStreaming(data.message_id, data.content)
            }
          }
        }
      }

      // 如果流结束了但没有收到 done 事件，说明连接异常断开
      // 此时应该结束 streaming 状态，避免 UI 永远卡在"回答中"
      if (!receivedDone) {
        const currentContent = get().streamingContent
        if (currentContent) {
          // 有部分内容：说明连接中断前收到了一些token
          // 将已有内容作为完整回答保存，避免用户看到的内容丢失
          const partialMsg: Message = {
            id: `partial-${Date.now()}`,
            session_id: get().currentSessionId || '',
            role: 'assistant',
            content: currentContent,
            sources: get().streamingSources,
            feedback: null,
            created_at: new Date().toISOString(),
          }
          set(state => ({
            messages: [...state.messages, partialMsg],
            streaming: false,
            streamingContent: '',
            streamingSources: [],
          }))
        } else {
          // 没有任何内容：连接根本没传回数据
          get().handleStreamError('连接意外断开，请重试')
        }
      }
    } catch (err) {
      console.error('流式接收失败:', err)
      set({ streaming: false })
    }

    // 刷新会话列表（更新标题）
    await get().loadSessions()
  },

  addUserMessage: (content) => {
    const tempMsg: Message = {
      id: `temp-${Date.now()}`,
      session_id: get().currentSessionId || '',
      role: 'user',
      content,
      sources: null,
      feedback: null,
      created_at: new Date().toISOString(),
    }
    set(state => ({ messages: [...state.messages, tempMsg] }))
  },

  appendStreamToken: (token) => {
    set(state => ({ streamingContent: state.streamingContent + token }))
  },

  setStreamSources: (sources) => {
    set({ streamingSources: sources })
  },

  finishStreaming: (messageId, fullContent) => {
    const newMsg: Message = {
      id: messageId,
      session_id: get().currentSessionId || '',
      role: 'assistant',
      content: fullContent,
      sources: get().streamingSources,
      feedback: null,
      created_at: new Date().toISOString(),
    }
    set(state => ({
      messages: [...state.messages, newMsg],
      streaming: false,
      streamingContent: '',
      streamingSources: [],
    }))
  },

  handleStreamError: (message: string) => {
    set({ streaming: false, streamingContent: '', errorMessage: message })
  },

  clearError: () => set({ errorMessage: null }),

  setStreaming: (v) => set({ streaming: v }),

  /** 重置所有状态（退出登录时调用，防止不同用户之间看到对方的消息） */
  reset: () => set({
    sessions: [],
    currentSessionId: null,
    messages: [],
    loadingMessages: false,
    streaming: false,
    streamingContent: '',
    streamingSources: [],
    errorMessage: null,
  }),
}))
