import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const modulePermissions = ref(
    JSON.parse(localStorage.getItem('module_permissions') || '[]')
  )

  const isLoggedIn = computed(() => !!token.value)

  function setAuth(t, u, perms = []) {
    token.value = t
    user.value = u
    modulePermissions.value = perms
    localStorage.setItem('token', t)
    localStorage.setItem('user', JSON.stringify(u))
    localStorage.setItem('module_permissions', JSON.stringify(perms))
  }

  function hasModule(name) {
    if (user.value?.role === 'admin') return true
    return modulePermissions.value.includes(name)
  }

  function logout() {
    token.value = ''
    user.value = null
    modulePermissions.value = []
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('module_permissions')
  }

  return { token, user, modulePermissions, isLoggedIn, setAuth, hasModule, logout }
})
