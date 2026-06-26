<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-button type="primary" @click="showDialog(null)"><el-icon><Plus /></el-icon> 新建工单</el-button>
      <el-select v-model="filterStatus" placeholder="状态筛选" style="width:140px" clearable @change="fetchData">
        <el-option label="待下达" value="待下达" />
        <el-option label="已下达" value="已下达" />
        <el-option label="进行中" value="进行中" />
        <el-option label="已完成" value="已完成" />
      </el-select>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedIds.length" class="batch-bar">
      <el-tag type="info" style="margin-right:8px">已选 {{ selectedIds.length }} 项</el-tag>
      <el-button size="small" type="warning" @click="batchUpdateStatus('已下达')">批量下达</el-button>
      <el-button size="small" type="primary" @click="batchUpdateStatus('进行中')">批量开工</el-button>
      <el-button size="small" type="success" @click="batchUpdateStatus('已完成')">批量完工</el-button>
      <el-button size="small" type="danger" @click="batchDelete">批量删除</el-button>
      <el-button size="small" @click="selectedIds = []">取消选择</el-button>
    </div>

    <el-table :data="tableData" v-loading="loading" stripe border
      @selection-change="(rows) => selectedIds = rows.map(r => r.id)">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="wo_number" label="工单号" width="180" />
      <el-table-column prop="material_code" label="物料编码" width="130" />
      <el-table-column prop="material_name" label="物料名称" min-width="150" />
      <el-table-column prop="plan_qty" label="计划产量" width="100" />
      <el-table-column prop="completed_qty" label="完成数量" width="100" />
      <el-table-column prop="start_date" label="开始日期" width="120" />
      <el-table-column prop="end_date" label="完成日期" width="120" />
      <el-table-column label="状态" width="100">
        <template #default="{row}">
          <el-tag :type="woStatusTag(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="work_center_name" label="工作中心" width="120" />
      <el-table-column prop="source_type" label="来源" width="90" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{row}">
          <el-button link type="primary" size="small" @click="updateStatus(row)">更新状态</el-button>
          <el-button link type="danger" size="small" @click="deleteItem(row)">删除</el-button>
        </template>
      </el-table-column>          <el-button link type="danger" size="small" @click="deleteItem(row)" v-if="row.status==='待下达'">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total"
      layout="total,sizes,prev,pager,next" @change="fetchData" style="margin-top:16px;justify-content:flex-end" />

    <!-- 工单弹窗 -->
    <el-dialog v-model="dialogVisible" title="新建生产工单" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="物料" prop="item_id">
          <el-select v-model="form.item_id" filterable placeholder="选择物料" style="width:100%">
            <el-option v-for="m in materialOptions" :key="m.id" :label="`${m.material_code} ${m.material_name}`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划产量" prop="plan_qty">
          <el-input-number v-model="form.plan_qty" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="完成日期" prop="end_date">
          <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="工作中心">
          <el-select v-model="form.work_center_id" clearable placeholder="可选" style="width:100%">
            <el-option v-for="w in workCenters" :key="w.id" :label="w.center_name" :value="w.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="工艺路线">
          <el-select v-model="form.routing_id" clearable placeholder="可选" style="width:100%">
            <el-option v-for="r in routingOptions" :key="r.id" :label="`${r.routing_code} (${r.material_name})`" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 状态更新弹窗 -->
    <el-dialog v-model="statusDialogVisible" title="更新工单状态" width="400px">
      <el-form label-width="90px">
        <el-form-item label="当前状态"><el-tag>{{ statusForm.oldStatus }}</el-tag></el-form-item>
        <el-form-item label="新状态">
          <el-select v-model="statusForm.newStatus">
            <el-option label="待下达" value="待下达" />
            <el-option label="已下达" value="已下达" />
            <el-option label="进行中" value="进行中" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已关闭" value="已关闭" />
          </el-select>
        </el-form-item>
        <el-form-item label="完成数量" v-if="['已完成','进行中'].includes(statusForm.newStatus)">
          <el-input-number v-model="statusForm.completed_qty" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusDialogVisible=false">取消</el-button>
        <el-button type="primary" @click="confirmStatus">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterStatus = ref('')

const materialOptions = ref([])
const workCenters = ref([])
const routingOptions = ref([])

const dialogVisible = ref(false)
const formRef = ref(null)
const form = reactive({
  item_id: null, plan_qty: 1, start_date: '', end_date: '',
  work_center_id: null, routing_id: null, remark: '',
})
const rules = {
  item_id: [{ required: true }],
  plan_qty: [{ required: true }],
  start_date: [{ required: true }],
  end_date: [{ required: true }],
}

const statusDialogVisible = ref(false)
const statusForm = reactive({ id: null, oldStatus: '', newStatus: '', completed_qty: null })

const selectedIds = ref([])

function woStatusTag(s) {
  const map = { '待下达': 'info', '已下达': 'warning', '进行中': '', '已完成': 'success', '已关闭': 'danger' }
  return map[s] || ''
}

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterStatus.value) params.status = filterStatus.value
    const res = await api.get('/production/orders', { params })
    tableData.value = res.items
    total.value = res.total
  } finally { loading.value = false }
}

async function showDialog(row) {
  const [matRes, wcRes, routingRes] = await Promise.all([
    api.get('/materials/all'),
    api.get('/production/work-centers'),
    api.get('/production/routings'),
  ])
  materialOptions.value = matRes.items
  workCenters.value = wcRes.items
  routingOptions.value = routingRes.items || []
  Object.assign(form, {
    item_id: null, plan_qty: 1, start_date: '', end_date: '',
    work_center_id: null, routing_id: null, remark: '',
  })
  dialogVisible.value = true
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const data = { ...form }
    if (!data.routing_id) delete data.routing_id
    await api.post('/production/orders', data)
    ElMessage.success('工单已创建')
    dialogVisible.value = false
    fetchData()
  } finally { saving.value = false }
}

function updateStatus(row) {
  Object.assign(statusForm, { id: row.id, oldStatus: row.status, newStatus: '', completed_qty: row.completed_qty })
  statusDialogVisible.value = true
}

async function confirmStatus() {
  await api.put(`/production/orders/${statusForm.id}/status`, {
    status: statusForm.newStatus,
    completed_qty: statusForm.completed_qty,
  })
  ElMessage.success('状态已更新')
  statusDialogVisible.value = false
  fetchData()
}

async function deleteItem(row) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await api.delete(`/production/orders/${row.id}`)
  fetchData()
}

async function batchUpdateStatus(newStatus) {
  await ElMessageBox.confirm(`确定将 ${selectedIds.value.length} 个工单状态更新为"${newStatus}"？`, '批量操作', { type: 'info' })
  let count = 0
  for (const id of selectedIds.value) {
    try { await api.put(`/production/orders/${id}/status`, { status: newStatus }); count++ } catch {}
  }
  ElMessage.success(`已更新 ${count} 个工单`)
  selectedIds.value = []
  fetchData()
}

async function batchDelete() {
  await ElMessageBox.confirm(`确定删除 ${selectedIds.value.length} 个工单？(仅删除"待下达"状态)`, '批量删除', { type: 'warning' })
  let count = 0
  for (const id of selectedIds.value) {
    try { await api.delete(`/production/orders/${id}`); count++ } catch {}
  }
  ElMessage.success(`已删除 ${count} 个工单`)
  selectedIds.value = []
  fetchData()
}

onMounted(fetchData)
</script>

<style scoped>
.page-container { background:#fff; padding:20px; border-radius:8px; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; }
.batch-bar { display:flex; align-items:center; padding:8px 12px; background:#fef0f0; border-radius:6px; margin-bottom:12px; gap:8px; }
</style>
