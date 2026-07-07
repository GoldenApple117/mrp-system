import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useEmailConfig } from '@/composables/useEmailConfig'

vi.mock('@/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({
      to_email: 'test@test.com',
      host: 'smtp.test.com',
      port: 465,
      username: 'user',
    }),
    put: vi.fn().mockResolvedValue({ success: true }),
    post: vi.fn().mockResolvedValue({ success: true, message: '发送成功' }),
  },
}))

describe('useEmailConfig', () => {
  let email
  let api

  beforeEach(async () => {
    vi.clearAllMocks()
    const mod = await import('@/api')
    api = mod.default
    email = useEmailConfig()
  })

  it('has default empty values', () => {
    expect(email.emailTo.value).toBe('')
    expect(email.emailHost.value).toBe('')
    expect(email.emailPort.value).toBe(587)
  })

  it('loadEmailConfig populates values from API', async () => {
    await email.loadEmailConfig()
    expect(email.emailTo.value).toBe('test@test.com')
    expect(email.emailHost.value).toBe('smtp.test.com')
    expect(email.emailPort.value).toBe(465)
  })

  it('saveEmailConfig sends correct body', async () => {
    email.emailTo.value = 'a@b.com'
    email.emailHost.value = 'smtp.qq.com'
    email.emailPort.value = 587
    email.emailUser.value = 'user@qq.com'
    email.emailPass.value = 'secret'
    await email.saveEmailConfig()
    expect(api.put).toHaveBeenCalledWith(
      '/system/email-config',
      expect.objectContaining({
        to_email: 'a@b.com',
        host: 'smtp.qq.com',
      }),
    )
  })
})
