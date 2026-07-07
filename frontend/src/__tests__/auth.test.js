import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

// Mock localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => {
      store[key] = value
    }),
    removeItem: vi.fn((key) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
  }
})()

Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorageMock.clear()
  })

  it('initializes with user from localStorage', () => {
    localStorageMock.setItem('user', JSON.stringify({ username: 'admin', role: 'admin' }))
    localStorageMock.setItem('token', 'test-token')
    const store = useAuthStore()
    expect(store.user.username).toBe('admin')
    expect(store.token).toBe('test-token')
    expect(store.isLoggedIn).toBe(true)
  })

  it('isLoggedIn is false when no token', () => {
    const store = useAuthStore()
    expect(store.isLoggedIn).toBe(false)
  })

  it('logout clears user and token', () => {
    localStorageMock.setItem('token', 'test-token')
    const store = useAuthStore()
    store.logout()
    expect(store.token).toBe('')
    expect(store.user).toBeNull()
    expect(store.isLoggedIn).toBe(false)
  })
})
