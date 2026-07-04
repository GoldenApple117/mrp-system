<template>
  <div class="perm-page">
    <h2 class="text-lg font-semibold text-[var(--color-text-primary)] mb-4">权限管理</h2>

    <el-table :data="requests" style="width:100%" size="small" v-loading="loading" empty-text="暂无申请记录">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="申请人" width="120" />
      <el-table-column prop="created_at" label="申请时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="reviewed_at" label="审批时间" width="180">
        <template #default="{ row }">
          {{ row.reviewed_at ? formatTime(row.reviewed_at) : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button type="success" size="small" :loading="approvingId === row.id" @click="approve(row.id)">同意</el-button>
            <el-button type="danger" size="small" :loading="rejectingId === row.id" @click="reject(row.id)">拒绝</el-button>
          </template>
          <span v-else class="text-xs text-[var(--color-text-tertiary)]">-</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const requests = ref([])
const loading = ref(false)
const approvingId = ref(null)
const rejectingId = ref(null)

onMounted(fetchList)

async function fetchList() {
  loading.value = true
  try {
    const res = await api.get('/permissions/list')
    requests.value = res
  } catch {} finally {
    loading.value = false
  }
}

async function approve(id) {
  approvingId.value = id
  try {
    const res = await api.put(`/permissions/approve/${id}`)
    ElMessage.success(res.message)
    fetchList()
  } catch {} finally {
    approvingId.value = null
  }
}

async function reject(id) {
  rejectingId.value = id
  try {
    await ElMessageBox.confirm('确定拒绝该申请？', '确认', { type: 'warning' })
    const res = await api.put(`/permissions/reject/${id}`)
    ElMessage.success(res.message)
    fetchList()
  } catch {} finally {
    rejectingId.value = null
  }
}

function statusType(s) { return { pending: 'warning', approved: 'success', rejected: 'danger' }[s] || 'info' }
function statusLabel(s) { return { pending: '审批中', approved: '已授权', rejected: '已拒绝' }[s] || s }
function formatTime(t) { return t ? new Date(t).toLocaleString('zh-CN') : '' }
</script>

<style scoped>
.perm-page {
  padding: 0;
}
</style>
