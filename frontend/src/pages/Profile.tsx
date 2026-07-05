/**
 * 个人中心页面
 *
 * 功能：查看个人信息、修改密码。
 */
import { useState } from 'react'
import { Card, Form, Input, Button, Descriptions, message, Divider, Typography } from 'antd'
import { UserOutlined, MailOutlined, LockOutlined, CalendarOutlined, CrownOutlined } from '@ant-design/icons'
import { useAuthStore } from '../store/authStore'
import { authAPI } from '../services/auth'
import dayjs from 'dayjs'

const { Title } = Typography

export default function ProfilePage() {
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(false)

  const handleChangePassword = async (values: { old_password: string; new_password: string }) => {
    setLoading(true)
    try {
      await authAPI.changePassword(values)
      message.success('密码修改成功！')
    } catch (err: any) {
      message.error(err?.response?.data?.detail || '修改失败')
    } finally {
      setLoading(false)
    }
  }

  if (!user) return null

  return (
    <div style={{ padding: 24, maxWidth: 700, margin: '0 auto' }}>
      <Title level={4}>👤 个人中心</Title>

      <Card style={{ marginBottom: 16 }}>
        <Descriptions title="基本信息" column={1} bordered size="small">
          <Descriptions.Item label={<><UserOutlined /> 用户名</>}>
            {user.username}
          </Descriptions.Item>
          <Descriptions.Item label={<><MailOutlined /> 邮箱</>}>
            {user.email || '未设置'}
          </Descriptions.Item>
          <Descriptions.Item label={<><CrownOutlined /> 角色</>}>
            {user.is_admin ? (
              <span style={{ color: '#1677ff', fontWeight: 'bold' }}>管理员</span>
            ) : (
              <span>普通用户</span>
            )}
          </Descriptions.Item>
          <Descriptions.Item label={<><CalendarOutlined /> 注册时间</>}>
            {dayjs(user.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="🔒 修改密码">
        <Form
          name="changePassword"
          onFinish={handleChangePassword}
          layout="vertical"
          style={{ maxWidth: 400 }}
        >
          <Form.Item
            name="old_password"
            label="旧密码"
            rules={[{ required: true, message: '请输入旧密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="输入旧密码" />
          </Form.Item>

          <Form.Item
            name="new_password"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码至少6位' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="输入新密码" />
          </Form.Item>

          <Form.Item
            name="confirm_password"
            label="确认新密码"
            dependencies={['new_password']}
            rules={[
              { required: true, message: '请确认新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="再次输入新密码" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              修改密码
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
