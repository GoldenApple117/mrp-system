<template>
  <div class="perm-page">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="审批申请" name="requests">
        <el-table
          v-loading="loading"
          :data="requests"
          class="w-full"
          size="small"
          empty-text="暂无申请记录"
        >
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
                <el-button
                  type="success"
                  size="small"
                  :loading="approvingId === row.id"
                  @click="approve(row.id)"
                  >同意</el-button
                >
                <el-button
                  type="danger"
                  size="small"
                  :loading="rejectingId === row.id"
                  @click="reject(row.id)"
                  >拒绝</el-button
                >
              </template>
              <span v-else class="text-xs text-[var(--color-text-tertiary)]">-</span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="模块权限" name="modules">
        <div v-if="modLoading" class="text-center py-8 text-sm text-[var(--color-text-tertiary)]">加载中...</div>
        <el-table
          v-else
          :data="users"
          size="small"
          empty-text="暂无用户"
          style="width: 100%"
        >
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="username" label="用户名" width="120" />
          <el-table-column label="角色" width="80">
            <template #default="{ row }">
              <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
                {{ row.role === 'admin' ? '管理员' : '普通' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="可访问模块">
            <template #default="{ row }">
              <template v-if="row.role === 'admin'">
                <span class="text-xs text-[var(--color-text-tertiary)]">全部</span>
              </template>
              <el-checkbox-group v-else v-model="row.editPerms" class="module-check-group">
                <el-checkbox
                  v-for="m in allModules"
                  :key="m.key"
                  :label="m.key"
                  :value="m.key"
                  size="small"
                  >{{ m.label }}</el-checkbox
                >
              </el-checkbox-group>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.role !== 'admin'"
                type="primary"
                size="small"
                :loading="savingUserId === row.id"
                :disabled="row.editPerms === row.savedPerms"
                @click="savePerms(row)"
                >保存</el-button
              >
              <span v-else class="text-xs text-[var(--color-text-tertiary)]">-</span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const activeTab = ref('requests')

// === 审批申请 ===
const requests = ref([])
const loading = ref(false)
const approvingId = ref(null)
const rejectingId = ref(null)

onMounted(() => { fetchList(); fetchModules() })

async function fetchList() {
  loading.value = true
  try { requests.value = await api.get('/permissions/list') }
  catch (e) { console.error('[MRP] 获取审批列表失败', e) }
  finally { loading.value = false }
}

async function approve(id) {
  approvingId.value = id
  try {
    const res = await api.put(`/permissions/approve/${id}`)
    ElMessage.success(res.message)
    fetchList()
  } catch (e) { console.error('[MRP] 审批失败', e) }
  finally { approvingId.value = null }
}

async function reject(id) {
  rejectingId.value = id
  try {
    await ElMessageBox.confirm('确定拒绝该申请？', '确认', { type: 'warning' })
    const res = await api.put(`/permissions/reject/${id}`)
    ElMessage.success(res.message)
    fetchList()
  } catch (e) { console.error('[MRP] 拒绝失败', e) }
  finally { rejectingId.value = null }
}

// === 模块权限 ===
const allModules = ref([])
const users = ref([])
const modLoading = ref(false)
const savingUserId = ref(null)

async function fetchModules() {
  try {
    const res = await api.get('/permissions/modules')
    allModules.value = res.modules || []
  } catch (e) { console.error('[MRP] 获取模块列表失败', e) }
}

async function fetchUsers() {
  modLoading.value = true
  try {
    const userList = await api.get('/permissions/users')
    // 为每个用户加载当前模块权限
    const rows = []
    for (const u of userList) {
      let perms = []
      if (u.role !== 'admin') {
        const permRes = await api.get(`/permissions/users/${u.id}/modules`)
        perms = permRes.module_permissions || []
      }
      rows.push({
        ...u,
        editPerms: [...perms],
        savedPerms: [...perms],
      })
    }
    users.value = rows
  } catch (e) { console.error('[MRP] 获取用户列表失败', e) }
  finally { modLoading.value = false }
}

async function savePerms(row) {
  savingUserId.value = row.id
  try {
    const res = await api.put(`/permissions/users/${row.id}/modules`, {
      modules: row.editPerms,
    })
    row.savedPerms = [...row.editPerms]
    ElMessage.success(res.message || '已保存')
  } catch (e) { console.error('[MRP] 保存模块权限失败', e) }
  finally { savingUserId.value = null }
}

// 切换标签时按需加载
const prevTab = ref('')
function handleTabClick(tab) {
  if (tab.props.name === 'modules' && prevTab.value !== 'modules') {
    fetchUsers()
  }
  prevTab.value = tab.props.name
}

watch(activeTab, (val) => {
  if (val === 'modules' && users.value.length === 0) {
    fetchUsers()
  }
})

function statusType(s) { return { pending: 'warning', approved: 'success', rejected: 'danger' }[s] || 'info' }
function statusLabel(s) { return { pending: '审批中', approved: '已授权', rejected: '已拒绝' }[s] || s }
function formatTime(t) { return t ? new Date(t).toLocaleString('zh-CN') : '' }
</script>

<style scoped>
.perm-page { padding: 0; }
.module-check-group {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 12px;
}
.module-check-group :deep(.el-checkbox) {
  margin-right: 0;
  height: 28px;
}
</style>