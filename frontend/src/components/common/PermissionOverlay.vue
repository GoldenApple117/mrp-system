<template>
  <div v-if="show" class="perm-overlay">
    <div class="perm-overlay-card">
      <el-icon :size="48" class="text-[var(--color-text-disabled)] mb-3"><Lock /></el-icon>
      <p class="text-sm text-[var(--color-text-primary)] font-medium mb-1">暂无操作权限</p>
      <p class="text-xs text-[var(--color-text-tertiary)] mb-4">
        请联系管理员申请权限后查看和编辑数据
      </p>
      <el-button
        v-if="status !== 'pending'"
        type="primary"
        size="small"
        :loading="loading"
        @click="apply"
      >
        {{ status === 'none' ? '申请权限' : '重新申请' }}
      </el-button>
      <el-tag v-else type="warning" size="small">审批中...</el-tag>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import api from '@/api'

const auth = useAuthStore()
const loading = ref(false)
const status = ref('none')

const show = computed(() => {
  if (!auth.isLoggedIn) return false
  if (auth.user?.role === 'admin') return false
  if (auth.user?.is_approved) return false
  return true
})

onMounted(async () => {
  try {
    const res = await api.get('/permissions/my-status')
    status.value = res.status
  } catch (e) { console.error('[MRP] 获取权限状态失败', e) }
})

async function apply() {
  loading.value = true
  try {
    const res = await api.post('/permissions/request')
    ElMessage.success(res.message)
    status.value = 'pending'
  } catch {
    ElMessage.error('申请失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.perm-overlay {
  position: absolute;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(4px);
}
.perm-overlay-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 40px;
  background: var(--color-bg-raised);
  border: 1px solid var(--color-border-light);
  border-radius: 12px;
  text-align: center;
}
</style>
