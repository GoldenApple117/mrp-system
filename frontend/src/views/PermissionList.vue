<template>
  <div class="perm-page">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="审批申请" name="requests">
        <el-table v-loading="loading" :data="requests" size="small" empty-text="暂无申请记录">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="username" label="申请人" width="120" />
          <el-table-column prop="created_at" label="申请时间" width="180">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="reviewed_at" label="审批时间" width="180">
            <template #default="{ row }">{{ row.reviewed_at ? formatTime(row.reviewed_at) : '-' }}</template>
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
      </el-tab-pane>

      <el-tab-pane label="用户与权限" name="modules">
        <div class="flex justify-between items-center mb-3">
          <span class="text-sm text-[var(--color-text-tertiary)]">共 {{ users.length }} 个用户</span>
          <el-button type="primary" size="small" @click="showAddDialog = true">+ 新增用户</el-button>
        </div>
        <div v-if="modLoading" class="text-center py-8 text-sm text-[var(--color-text-tertiary)]">加载中...</div>
        <el-table v-else :data="users" size="small" empty-text="暂无用户">
          <el-table-column prop="id" label="ID" width="50" />
          <el-table-column prop="username" label="用户名" width="110" />
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.role === 'admin'" type="danger" size="small">管理员</el-tag>
              <el-tag v-else :type="row.is_approved ? 'success' : 'warning'" size="small">
                {{ row.is_approved ? '已授权' : '待审批' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="可访问模块">
            <template #default="{ row }">
              <template v-if="row.role === 'admin'"><span class="text-xs text-[var(--color-text-tertiary)]">全部</span></template>
              <el-checkbox-group v-else v-model="row.editPerms" class="module-check-group">
                <el-checkbox v-for="m in allModules" :key="m.key" :label="m.key" :value="m.key" size="small">{{ m.label }}</el-checkbox>
              </el-checkbox-group>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="editUser(row)">编辑</el-button>
              <el-button v-if="row.role !== 'admin'" type="primary" size="small"
                :loading="savingUserId === row.id" :disabled="row.editPerms === row.savedPerms"
                @click="savePerms(row)">保存</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新增用户弹窗 -->
    <el-dialog v-model="showAddDialog" title="新增用户" width="400px" :close-on-click-modal="false">
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="80px" size="small">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="addForm.username" placeholder="登录用账号" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="addForm.password" type="password" placeholder="至少4位" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="addForm.role">
            <el-option label="普通用户" value="normal" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" size="small" :loading="addingUser" @click="createUser">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户弹窗 -->
    <el-dialog v-model="showEditDialog" title="编辑用户" width="400px" :close-on-click-modal="false">
      <el-form ref="editFormRef" :model="editForm" label-width="80px" size="small">
        <el-form-item label="用户名">
          <span class="text-sm">{{ editForm.username }}</span>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role">
            <el-option label="普通用户" value="normal" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="editForm.password" type="password" placeholder="留空则不修改密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button size="small" @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" size="small" :loading="editingUser" @click="updateUser">保存</el-button>
      </template>
    </el-dialog>
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
  try { const res = await api.put(`/permissions/approve/${id}`); ElMessage.success(res.message); fetchList() }
  catch (e) { console.error('[MRP] 审批失败', e) }
  finally { approvingId.value = null }
}

async function reject(id) {
  rejectingId.value = id
  try {
    await ElMessageBox.confirm('确定拒绝该申请？', '确认', { type: 'warning' })
    const res = await api.put(`/permissions/reject/${id}`); ElMessage.success(res.message); fetchList()
  } catch (e) { console.error('[MRP] 拒绝失败', e) }
  finally { rejectingId.value = null }
}

// === 用户与权限 ===
const allModules = ref([])
const users = ref([])
const modLoading = ref(false)
const savingUserId = ref(null)

async function fetchModules() {
  try { const res = await api.get('/permissions/modules'); allModules.value = res.modules || [] }
  catch (e) { console.error('[MRP] 获取模块列表失败', e) }
}

async function fetchUsers() {
  modLoading.value = true
  try {
    const userList = await api.get('/permissions/users')
    const rows = []
    for (const u of userList) {
      let perms = []
      if (u.role !== 'admin') {
        const permRes = await api.get(`/permissions/users/${u.id}/modules`)
        perms = permRes.module_permissions || []
      }
      rows.push({ ...u, editPerms: [...perms], savedPerms: [...perms] })
    }
    users.value = rows
  } catch (e) { console.error('[MRP] 获取用户列表失败', e) }
  finally { modLoading.value = false }
}

async function savePerms(row) {
  savingUserId.value = row.id
  try {
    const res = await api.put(`/permissions/users/${row.id}/modules`, { modules: row.editPerms })
    row.savedPerms = [...row.editPerms]
    ElMessage.success(res.message || '已保存')
  } catch (e) { console.error('[MRP] 保存模块权限失败', e) }
  finally { savingUserId.value = null }
}

// === 新增用户 ===
const showAddDialog = ref(false)
const addingUser = ref(false)
const addFormRef = ref(null)
const addForm = ref({ username: '', password: '', role: 'normal' })
const addRules = { username: [{ required: true, message: '请输入用户名' }], password: [{ required: true, message: '请输入密码' }] }

async function createUser() {
  const valid = await addFormRef.value?.validate().catch(() => false)
  if (!valid) return
  addingUser.value = true
  try {
    const res = await api.post('/permissions/users', { ...addForm.value })
    ElMessage.success(res.message)
    showAddDialog.value = false
    addForm.value = { username: '', password: '', role: 'normal' }
    fetchUsers()
  } catch (e) { console.error('[MRP] 创建用户失败', e) }
  finally { addingUser.value = false }
}

// === 编辑用户 ===
const showEditDialog = ref(false)
const editingUser = ref(false)
const editFormRef = ref(null)
const editForm = ref({ id: null, username: '', role: 'normal', password: '' })

function editUser(row) {
  editForm.value = { id: row.id, username: row.username, role: row.role, password: '' }
  showEditDialog.value = true
}

async function updateUser() {
  editingUser.value = true
  try {
    const body = { role: editForm.value.role }
    if (editForm.value.password) body.password = editForm.value.password
    const res = await api.put(`/permissions/users/${editForm.value.id}`, body)
    ElMessage.success(res.message)
    showEditDialog.value = false
    fetchUsers()
  } catch (e) { console.error('[MRP] 更新用户失败', e) }
  finally { editingUser.value = false }
}

watch(activeTab, (val) => { if (val === 'modules' && users.value.length === 0) fetchUsers() })

function statusType(s) { return { pending: 'warning', approved: 'success', rejected: 'danger' }[s] || 'info' }
function statusLabel(s) { return { pending: '审批中', approved: '已授权', rejected: '已拒绝' }[s] || s }
function formatTime(t) { return t ? new Date(t).toLocaleString('zh-CN') : '' }
</script>

<style scoped>
.perm-page { padding: 0; }
.module-check-group { display: flex; flex-wrap: wrap; gap: 4px 12px; }
.module-check-group :deep(.el-checkbox) { margin-right: 0; height: 28px; }
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
.mb-3 { margin-bottom: 12px; }
</style>