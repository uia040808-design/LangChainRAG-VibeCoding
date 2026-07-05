/**
 * 引用来源卡片组件
 *
 * 展示AI回答中引用的知识库片段信息：
 * - 来源文档名
 * - 相关度分数
 * - 文本片段预览
 */
import { useState } from 'react'
import { Card, Tag, Typography } from 'antd'
import { FileTextOutlined, PercentageOutlined } from '@ant-design/icons'
import { SourceInfo } from '../services/chat'

const { Text, Paragraph } = Typography

interface Props {
  source: SourceInfo
  index: number
}

export default function SourceCard({ source, index }: Props) {
  const [expanded, setExpanded] = useState(false)

  const scorePercent = Math.round(source.similarity_score * 100)

  // 根据相关度显示不同颜色
  const scoreColor = scorePercent >= 80 ? 'green' : scorePercent >= 60 ? 'orange' : 'red'

  return (
    <Card
      size="small"
      style={{
        marginBottom: 4,
        cursor: 'pointer',
        border: '1px solid #f0f0f0',
      }}
      onClick={() => setExpanded(!expanded)}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {/* 序号 */}
        <Tag color="blue">#{index + 1}</Tag>

        {/* 文档名 */}
        <FileTextOutlined />
        <Text strong style={{ flex: 1 }} ellipsis>
          {source.document_title}
        </Text>

        {/* 相关度 */}
        <Tag icon={<PercentageOutlined />} color={scoreColor}>
          相关度 {scorePercent}%
        </Tag>
      </div>

      {/* 展开查看文本片段 */}
      {expanded && (
        <Paragraph
          style={{
            marginTop: 8,
            padding: 8,
            background: '#fafafa',
            borderRadius: 4,
            fontSize: 13,
            color: '#666',
            maxHeight: 120,
            overflow: 'auto',
          }}
          ellipsis={{ rows: 4, expandable: true }}
        >
          {source.content}
        </Paragraph>
      )}
    </Card>
  )
}
