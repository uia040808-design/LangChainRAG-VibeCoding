/**
 * 知识库管理相关 API 调用（仅管理员可用）
 */
import api from './api'

export interface KnowledgeDocument {
  id: string
  filename: string
  title: string
  file_type: string
  file_size: number
  chunk_count: number
  status: 'processing' | 'ready' | 'error'
  error_message: string
  created_at: string
}

export const knowledgeAPI = {
  /** 获取文档列表 */
  getDocuments: (page = 1, pageSize = 20) =>
    api.get('/knowledge/documents', { params: { page, page_size: pageSize } })
      .then(res => res.data),

  /** 获取文档详情 */
  getDocument: (id: string) =>
    api.get(`/knowledge/documents/${id}`).then(res => res.data),

  /** 上传文档 */
  uploadDocument: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(res => res.data)
  },

  /** 删除文档 */
  deleteDocument: (id: string) =>
    api.delete(`/knowledge/documents/${id}`).then(res => res.data),

  /** 获取文档分块 */
  getDocumentChunks: (id: string) =>
    api.get(`/knowledge/documents/${id}/chunks`).then(res => res.data),

  /** 获取系统统计 */
  getStats: () =>
    api.get('/knowledge/stats').then(res => res.data),
}
