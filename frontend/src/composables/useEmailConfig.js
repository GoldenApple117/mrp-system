import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

export function useEmailConfig() {
  const emailTo = ref('')
  const emailHost = ref('')
  const emailPort = ref(587)
  const emailUser = ref('')
  const emailPass = ref('')

  async function loadEmailConfig() {
    try {
      const d = await api.get('/system/email-config')
      emailTo.value = d.to_email || ''
      emailHost.value = d.host || ''
      emailPort.value = d.port || 587
      emailUser.value = d.username || ''
    } catch (e) {
      console.error('[MRP] 加载邮件配置失败', e)
    }
  }

  async function saveEmailConfig() {
    try {
      const body = {
        to_email: emailTo.value,
        host: emailHost.value,
        port: emailPort.value,
        username: emailUser.value,
        password: emailPass.value,
        from_addr: emailUser.value,
      }
      const d = await api.put('/system/email-config', body)
      if (d.success) {
        ElMessage.success('邮件配置已保存')
        emailPass.value = ''
      }
    } catch {
      ElMessage.error('保存失败')
    }
  }

  async function sendTestEmail() {
    if (!emailTo.value) {
      ElMessage.warning('请先填写接收邮箱')
      return
    }
    try {
      const d = await api.post('/system/email-test', { to_email: emailTo.value })
      ElMessage[d.success ? 'success' : 'error'](d.message)
    } catch {
      ElMessage.error('发送失败')
    }
  }

  return {
    emailTo,
    emailHost,
    emailPort,
    emailUser,
    emailPass,
    loadEmailConfig,
    saveEmailConfig,
    sendTestEmail,
  }
}
