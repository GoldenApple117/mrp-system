import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useMRPScheduler } from '@/composables/useMRPScheduler'

// Mock api
vi.mock('@/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ enabled: true, hour: 8, minute: 30 }),
    put: vi.fn().mockResolvedValue({ success: true }),
  },
}))

describe('useMRPScheduler', () => {
  let scheduler
  let api

  beforeEach(async () => {
    vi.clearAllMocks()
    const mod = await import('@/api')
    api = mod.default
    scheduler = useMRPScheduler()
  })

  it('has default values before load', () => {
    expect(scheduler.timerEnabled.value).toBe(false)
    expect(scheduler.timerHour.value).toBe(6)
    expect(scheduler.timerMinute.value).toBe(0)
  })

  it('loadSchedule updates timer values', async () => {
    await scheduler.loadSchedule()
    expect(scheduler.timerEnabled.value).toBe(true)
    expect(scheduler.timerHour.value).toBe(8)
    expect(scheduler.timerMinute.value).toBe(30)
  })

  it('saveSchedule calls api.put with correct data', async () => {
    scheduler.timerEnabled.value = true
    scheduler.timerHour.value = 12
    scheduler.timerMinute.value = 45
    await scheduler.saveSchedule()
    expect(api.put).toHaveBeenCalledWith('/system/schedule', {
      enabled: true,
      hour: 12,
      minute: 45,
    })
  })
})
