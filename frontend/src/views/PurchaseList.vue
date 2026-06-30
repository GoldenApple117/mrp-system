<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-button type="primary" @click="showDialog(null)"><el-icon><Plus /></el-icon> 新建采购单</el-button>
      <el-button @click="handleImport"><el-icon><Upload /></el-icon> 导入Excel</el-button>
      <el-button @click="downloadTemplate"><el-icon><Download /></el-icon> 下载模板</el-button>
      <el-select v-model="filterStatus" placeholder="状态筛选" style="width:140px" clearable @change="fetchData">
        <el-option label="申请" value="申请" />
        <el-option label="已审批" value="已审批" />
        <el-option label="已下单" value="已下单" />
        <el-option label="部分收货" value="部分收货" />
        <el-option label="已完成" value="已完成" />
      </el-select>
      <span style="flex:1"></span>
      <el-button @click="tab='suppliers'" :type="tab==='suppliers'?'':'default'">供应商管理</el-button>
    </div>

    <el-tabs v-model="tab" @tab-change="onTabChange">
      <el-tab-pane label="采购订单" name="orders" />
      <el-tab-pane label="供应商" name="suppliers" />
    </el-tabs>

    <!-- 采购订单 -->
    <div v-if="tab==='orders'">
      <div v-if="selectedIds.length" class="batch-bar">
        <el-tag type="info" style="margin-right:8px">已选 {{ selectedIds.length }} 项</el-tag>
        <el-button size="small" type="warning" @click="batchUpdateStatus('已下单')">批量下单</el-button>
        <el-button size="small" type="success" @click="batchComplete">批量完成</el-button>
        <el-button size="small" type="danger" @click="batchDelete">批量删除</el-button>
        <el-button size="small" @click="selectedIds = []">取消选择</el-button>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe border
        @selection-change="(rows) => selectedIds = rows.map(r => r.id)">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="po_number" label="采购单号" width="180" />
        <el-table-column prop="material_code" label="物料编码" width="130" />
        <el-table-column prop="material_name" label="物料名称" min-width="150" />
        <el-table-column prop="supplier_name" label="供应商" width="140" />
        <el-table-column prop="order_qty" label="订购数量" width="100" />
        <el-table-column prop="received_qty" label="已收数量" width="100" />
        <el-table-column prop="due_date" label="预计到货" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{row}">
            <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source_type" label="来源" width="90" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{row}">
            <el-button link type="primary" size="small" @click="updateStatus(row)">更新状态</el-button>
            <el-button link type="danger" size="small" @click="deleteItem(row)" v-if="row.status==='申请'">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total"
        layout="total,sizes,prev,pager,next" @change="fetchData" style="margin-top:16px;justify-content:flex-end" />
    </div>

    <!-- 供应商 -->
    <div v-else>
      <div style="margin-bottom:12px">
        <el-button type="primary" size="small" @click="showSupplierDialog"><el-icon><Plus /></el-icon> 新增供应商</el-button>
      </div>
      <el-table :data="suppliers" stripe border>
        <el-table-column prop="supplier_code" label="编码" width="120" />
        <el-table-column prop="supplier_name" label="名称" min-width="160" />
        <el-table-column prop="contact_person" label="联系人" width="100" />
        <el-table-column prop="contact_phone" label="电话" width="140" />
        <el-table-column prop="lead_time_days" label="交期(天)" width="90" />
      </el-table>
    </div>

    <!-- 采购单弹窗 -->
    <el-dialog v-model="dialogVisible" title="新建采购单" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="物料" prop="item_id">
          <el-select v-model="form.item_id" filterable placeholder="选择物料" style="width:100%">
            <el-option v-for="m in materialOptions" :key="m.id" :label="`${m.material_code} ${m.material_name}`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="供应商" prop="supplier_id">
          <el-select v-model="form.supplier_id" filterable placeholder="选择供应商" style="width:100%">
            <el-option v-for="s in suppliers" :key="s.id" :label="s.supplier_name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="订购数量" prop="order_qty">
          <el-input-number v-model="form.order_qty" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="预计到货" prop="due_date">
          <el-date-picker v-model="form.due_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
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

    <!-- 更新状态弹窗 -->
    <el-dialog v-model="statusDialogVisible" title="更新采购单状态" width="400px">
      <el-form label-width="90px">
        <el-form-item label="当前状态">
          <el-tag>{{ statusForm.oldStatus }}</el-tag>
        </el-form-item>
        <el-form-item label="新状态">
          <el-select v-model="statusForm.newStatus">
            <el-option label="申请" value="申请" />
            <el-option label="已审批" value="已审批" />
            <el-option label="已下单" value="已下单" />
            <el-option label="部分收货" value="部分收货" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已取消" value="已取消" />
          </el-select>
        </el-form-item>
        <el-form-item label="收货数量" v-if="['部分收货','已完成'].includes(statusForm.newStatus)">
          <el-input-number v-model="statusForm.received_qty" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusDialogVisible=false">取消</el-button>
        <el-button type="primary" @click="confirmStatus">确认</el-button>
      </template>
    </el-dialog>

    <!-- 供应商弹窗 -->
    <el-dialog v-model="supplierDialogVisible" title="新增供应商" width="450px">
      <el-form ref="supplierFormRef" :model="supplierForm" label-width="90px">
        <el-form-item label="编码" required><el-input v-model="supplierForm.supplier_code" /></el-form-item>
        <el-form-item label="名称" required><el-input v-model="supplierForm.supplier_name" /></el-form-item>
        <el-form-item label="联系人"><el-input v-model="supplierForm.contact_person" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="supplierForm.contact_phone" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="supplierForm.address" /></el-form-item>
        <el-form-item label="交期(天)"><el-input-number v-model="supplierForm.lead_time_days" :min="0" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="supplierDialogVisible=false">取消</el-button>
        <el-button type="primary" @click="submitSupplier">保存</el-button>
      </template>
    </el-dialog>
  </div>

  <!-- 导入弹窗 -->
  <el-dialog v-model="importDialogVisible" title="导入采购订单" width="500px">
    <el-upload
      ref="uploadRef"
      :auto-upload="false"
      :limit="1"
      accept=".xlsx,.xls"
      @change="onFileChange"
    >
      <el-button type="primary"><el-icon><Upload /></el-icon> 选择Excel文件</el-button>
      <template #tip>
        <div style="color:#999;font-size:12px;margin-top:8px">
          支持 .xlsx 格式，表头须包含：物料编码、数量、供应商编码、交货日期
          <el-link type="primary" @click="downloadTemplate" style="margin-left:8px">下载模板</el-link>
        </div>
      </template>
    </el-upload>
    <div v-if="importResult" style="margin-top:12px;white-space:pre-wrap;font-size:13px;">{{ importResult }}</div>
    <template #footer>
      <el-button @click="importDialogVisible = false">关闭</el-button>
      <el-button type="primary" @click="submitImport" :loading="importLoading">开始导入</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const saving = ref(false)
const tab = ref('orders')
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterStatus = ref('')

const materialOptions = ref([])
const suppliers = ref([])

const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const importLoading = ref(false)
const importResult = ref('')
const formRef = ref(null)
const form = reactive({
  item_id: null, supplier_id: null, order_qty: 1,
  due_date: '', remark: '',
})
const rules = {
  item_id: [{ required: true }],
  supplier_id: [{ required: true }],
  order_qty: [{ required: true }],
  due_date: [{ required: true }],
}

const statusDialogVisible = ref(false)
const statusForm = reactive({ id: null, oldStatus: '', newStatus: '', received_qty: null })

const selectedIds = ref([])
const uploadRef = ref(null)
let importFile = null

function onFileChange(uploadFile) {
  importFile = uploadFile.raw
}

async function handleImport() {
  importResult.value = ''
  importFile = null
  importDialogVisible.value = true
}

async function downloadTemplate() {
  window.open('/api/purchase/orders/import/template', '_blank')
}

async function submitImport() {
  if (!importFile) {
    ElMessage.warning('请先选择文件')
    return
  }
  importLoading.value = true
  importResult.value = ''
  try {
    const formData = new FormData()
    formData.append('file', importFile)
    const res = await api.post('/purchase/orders/import/excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    importResult.value = res.message || '导入完成'
    if (res.errors && res.errors.length) {
      importResult.value += '\n⚠️ 错误:\n' + res.errors.slice(0, 5).join('\n')
      if (res.total_errors > 5) importResult.value += `\n...还有${res.total_errors - 5}个错误`
    }
    fetchData()
  } catch (e) {
    importResult.value = '导入失败: ' + (e.message || e)
  } finally {
    importLoading.value = false
  }
}

const supplierDialogVisible = ref(false)
const supplierFormRef = ref(null)
const supplierForm = reactive({
  supplier_code: '', supplier_name: '', contact_person: '',
  contact_phone: '', address: '', lead_time_days: 0,
})

function statusTag(s) {
  const map = { '申请': '', '已审批': 'info', '已下单': 'warning', '部分收货': '', '已完成': 'success', '已取消': 'danger' }
  return map[s] || ''
}

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterStatus.value) params.status = filterStatus.value
    const res = await api.get('/purchase/orders', { params })
    tableData.value = res.items
    total.value = res.total
  } finally { loading.value = false }
}

async function fetchSuppliers() {
  const res = await api.get('/purchase/suppliers')
  suppliers.value = res.items
}

async function showDialog(row) {
  const [matRes] = await Promise.all([
    api.get('/materials/all', { params: { is_purchased: true } }),
    fetchSuppliers(),
  ])
  materialOptions.value = matRes.items
  Object.assign(form, { item_id: null, supplier_id: suppliers.value[0]?.id || null, order_qty: 1, due_date: '', remark: '' })
  dialogVisible.value = true
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await api.post('/purchase/orders', { ...form })
    ElMessage.success('采购单已创建')
    dialogVisible.value = false
    fetchData()
  } finally { saving.value = false }
}

function updateStatus(row) {
  Object.assign(statusForm, { id: row.id, oldStatus: row.status, newStatus: '', received_qty: row.received_qty })
  statusDialogVisible.value = true
}

async function confirmStatus() {
  await api.put(`/purchase/orders/${statusForm.id}/status`, {
    status: statusForm.newStatus,
    received_qty: statusForm.received_qty,
  })
  ElMessage.success('状态已更新')
  statusDialogVisible.value = false
  fetchData()
}

async function deleteItem(row) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await api.delete(`/purchase/orders/${row.id}`)
  fetchData()
}

function showSupplierDialog() {
  Object.assign(supplierForm, { supplier_code: '', supplier_name: '', contact_person: '', contact_phone: '', address: '', lead_time_days: 0 })
  supplierDialogVisible.value = true
}

async function submitSupplier() {
  await api.post('/purchase/suppliers', { ...supplierForm })
  ElMessage.success('供应商已添加')
  supplierDialogVisible.value = false
  fetchSuppliers()
}

async function batchUpdateStatus(newStatus) {
  await ElMessageBox.confirm(`确定将 ${selectedIds.value.length} 个采购单状态更新为"${newStatus}"？`, '批量操作', { type: 'info' })
  let count = 0
  for (const id of selectedIds.value) {
    try { await api.put(`/purchase/orders/${id}/status`, { status: newStatus }); count++ } catch {}
  }
  ElMessage.success(`已更新 ${count} 个采购单`)
  selectedIds.value = []
  fetchData()
}

async function batchComplete() {
  await ElMessageBox.confirm(`确定将 ${selectedIds.value.length} 个采购单标记为已完成？`, '批量完成', { type: 'warning' })
  let count = 0
  for (const id of selectedIds.value) {
    try { await api.put(`/purchase/orders/${id}/status`, { status: '已完成', received_qty: null }); count++ } catch {}
  }
  ElMessage.success(`已完成 ${count} 个采购单`)
  selectedIds.value = []
  fetchData()
}

function onTabChange(val) {
  if (val === 'suppliers') fetchSuppliers()
  else fetchData()
}

async function batchDelete() {
  await ElMessageBox.confirm(`确定删除 ${selectedIds.value.length} 个采购单？(仅删除"申请"状态)`, '批量删除', { type: 'warning' })
  let count = 0
  for (const id of selectedIds.value) {
    try { await api.delete(`/purchase/orders/${id}`); count++ } catch (e) { /* 非"申请"状态无法删除 */ }
  }
  ElMessage.success(`已删除 ${count} 个采购单`)
  selectedIds.value = []
  fetchData()
}

onMounted(() => { fetchData(); fetchSuppliers() })
</script>

<style scoped>
.page-container { background:#fff; padding:20px; border-radius:8px; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; }
</style>
