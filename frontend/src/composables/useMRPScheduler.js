import { ref } from 'vue'
import api from '@/api'

export function useMRPScheduler() {
  const timerEnabled = ref(false)
  const timerHour = ref(6)
  const timerMinute = ref(0)

  async function loadSchedule() {
    try {
      const d = await api.get('/system/schedule')
      timerEnabled.value = d.enabled
      timerHour.value = d.hour
      timerMinute.value = d.minute
    } catch (e) {
      console.error('[MRP] 加载定时器失败', e)
    }
  }

  async function saveSchedule() {
    await api.put('/system/schedule', {
      enabled: timerEnabled.value,
      hour: timerHour.value,
      minute: timerMinute.value,
    })
  }

  return { timerEnabled, timerHour, timerMinute, loadSchedule, saveSchedule }
}
