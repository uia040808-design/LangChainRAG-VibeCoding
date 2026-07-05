/**
 * 知识库管理页面（仅管理员可访问）
 *
 * 功能：上传文档、查看文档列表、删除文档、查看分块预览。
 */
import { useEffect, useState, useCallback } from 'react'
import {
  Table, Button, Upload, Modal, Tag, Space, message, Popconfirm, Typography
} from 'antd'
import {
  UploadOutlined, DeleteOutlined, EyeOutlined,
  FilePdfOutlined, FileTextOutlined, FileExcelOutlined, FileWordOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { knowledgeAPI, KnowledgeDocument } from '../services/knowledge'
import dayjs from 'dayjs'

const { Title, Paragraph } = Typography

// 文件类型图标映射
const fileIcons: Record<string, React.ReactNode> = {
  pdf: <FilePdfOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />,
  txt: <FileTextOutlined style={{ color: '#1677ff', fontSize: 20 }} />,
  csv: <FileExcelOutlined style={{ color: '#52c41a', fontSize: 20 }} />,
  docx: <FileWordOutlined style={{ color: '#1677ff', fontSize: 20 }} />,
  md: <FileTextOutlined style={{ color: '#722ed1', fontSize: 20 }} />,
}

export default function KnowledgeBasePage() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [chunksModal, setChunksModal] = useState<{ open: boolean; chunks: any[]; docName: string }>({
    open: false, chunks: [], docName: '',
  })

  // 加载文档列表
  const loadDocuments = useCallback(async (p = 1) => {
    setLoading(true)
    try {
      const data = await knowledgeAPI.getDocuments(p)
      setDocuments(data.documents || [])
      setTotal(data.total || 0)
    } catch {
      message.error('加载文档列表失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDocuments(page)
  }, [page])

  // 上传文档
  const handleUpload = async (file: File) => {
    try {
      const result = await knowledgeAPI.uploadDocument(file)
      message.success(result.message || '上传成功，正在后台处理')
      loadDocuments(page)
    } catch (err: any) {
      message.error(err?.response?.data?.detail || '上传失败')
    }
    return false // 阻止默认上传行为
  }

  // 删除文档
  const handleDelete = async (id: string) => {
    try {
      await knowledgeAPI.deleteDocument(id)
      message.success('文档已删除')
      loadDocuments(page)
    } catch {
      message.error('删除失败')
    }
  }

  // 查看分块
  const handleViewChunks = async (doc: KnowledgeDocument) => {
    try {
      const data = await knowledgeAPI.getDocumentChunks(doc.id)
      setChunksModal({ open: true, chunks: data.chunks || [], docName: doc.filename })
    } catch {
      message.error('加载分块失败')
    }
  }

  const columns: ColumnsType<KnowledgeDocument> = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      render: (text, record) => (
        <Space>
          {fileIcons[record.file_type] || <FileTextOutlined />}
          <span>{text}</span>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'file_type',
      key: 'file_type',
      width: 80,
      render: (t) => <Tag>{t.toUpperCase()}</Tag>,
    },
    {
      title: '大小',
      dataIndex: 'file_size',
      key: 'file_size',
      width: 100,
      render: (size) => {
        if (size < 1024) return `${size} B`
        if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
        return `${(size / 1024 / 1024).toFixed(1)} MB`
      },
    },
    {
      title: '分块数',
      dataIndex: 'chunk_count',
      key: 'chunk_count',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status, record) => {
        const config = {
          ready: { color: 'green', text: '就绪' },
          processing: { color: 'blue', text: '处理中' },
          error: { color: 'red', text: '失败' },
        }
        const c = config[status as keyof typeof config] || { color: 'default', text: status }
        return (
          <Space direction="vertical" size={0}>
            <Tag color={c.color}>{c.text}</Tag>
            {status === 'error' && record.error_message && (
              <span style={{ fontSize: 11, color: '#ff4d4f' }}>{record.error_message}</span>
            )}
          </Space>
        )
      },
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (t) => dayjs(t).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'actions',
      width: 160,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewChunks(record)}
            disabled={record.status !== 'ready'}
          >
            分块
          </Button>
          <Popconfirm
            title="确定删除此文档？会同时删除向量数据"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>📂 知识库文档管理</Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => loadDocuments(page)}>
            刷新
          </Button>
          <Upload
            accept=".pdf,.txt,.csv,.docx,.md"
            showUploadList={false}
            beforeUpload={handleUpload}
          >
            <Button type="primary" icon={<UploadOutlined />}>
              上传文档
            </Button>
          </Upload>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={documents}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          total,
          pageSize: 20,
          onChange: setPage,
          showTotal: (t) => `共 ${t} 个文档`,
        }}
      />

      {/* 分块预览弹窗 */}
      <Modal
        title={`文档分块 - ${chunksModal.docName}`}
        open={chunksModal.open}
        onCancel={() => setChunksModal({ open: false, chunks: [], docName: '' })}
        footer={null}
        width={800}
      >
        <div style={{ maxHeight: 500, overflow: 'auto' }}>
          {chunksModal.chunks.map((chunk, i) => (
            <div
              key={chunk.chunk_id || i}
              style={{
                padding: '8px 12px',
                marginBottom: 8,
                background: '#fafafa',
                borderRadius: 6,
                border: '1px solid #f0f0f0',
              }}
            >
              <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>
                分块 #{i + 1} | ID: {chunk.chunk_id}
              </div>
              <Paragraph
                ellipsis={{ rows: 2, expandable: true, symbol: '展开' }}
                style={{ margin: 0, fontSize: 13 }}
              >
                {chunk.content}
              </Paragraph>
            </div>
          ))}
        </div>
      </Modal>
    </div>
  )
}
