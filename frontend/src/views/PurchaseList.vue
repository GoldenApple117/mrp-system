<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-button type="primary" @click="showDialog(null)"><el-icon><Plus /></el-icon> 新建采购单</el-button>
      <el-button type="success" @click="syncFromBom" :loading="syncing"><el-icon><Refresh /></el-icon> 从BOM同步</el-button>
      <el-button @click="handleImport"><el-icon><Upload /></el-icon> 导入Excel</el-button>
      <el-button @click="downloadTemplate"><el-icon><Download /></el-icon> 下载模板</el-button>
      <el-select v-model="filterStatus" placeholder="状态筛选" style="width:140px" clearable @change="fetchData">
        <el-option label="已下单" value="已下单" />
        <el-option label="部分到货" value="部分到货" />
        <el-option label="全部到货" value="全部到货" />
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
        <el-button size="small" type="success" @click="batchAllReceived">批量全部到货</el-button>
        <el-button size="small" type="danger" @click="batchDelete">批量删除</el-button>
        <el-button size="small" @click="selectedIds = []">取消选择</el-button>
      </div>
      <el-table :data="tableData" v-loading="loading" stripe border
        :row-class-name="rowClassName"
        @selection-change="(rows) => selectedIds = rows.map(r => r.id)">
        <el-table-column type="selection" width="50" />
        <el-table-column prop="po_number" label="采购单号" width="180" />
        <el-table-column prop="material_code" label="物料编码" width="130" />
        <el-table-column prop="material_name" label="物料型号" min-width="140" />
        <el-table-column prop="supplier_name" label="供应商" width="120" />
        <el-table-column prop="order_qty" label="订购数量" width="90" align="center" />
        <el-table-column label="到货数量" width="110" align="center">
          <template #default="{row}">
            <span :style="{color: row.received_qty > 0 ? '#67c23a' : '#c0c4cc', fontWeight: row.received_qty > 0 ? 'bold' : 'normal'}">
              {{ row.received_qty || 0 }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="未到数量" width="110" align="center">
          <template #default="{row}">
            <span :style="{color: (row.order_qty - (row.received_qty||0)) > 0 ? '#f56c6c' : '#67c23a', fontWeight: 'bold'}">
              {{ (row.order_qty - (row.received_qty || 0)).toFixed(0) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{row}">
            <div class="status-cell">
              <span class="status-dot" :class="statusDotClass(row)"></span>
              <el-tag :type="statusTag(row.status)" size="small">{{ row.status }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="source_type" label="来源" width="90" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{row}">
            <el-button link type="primary" size="small" @click="updateStatus(row)">更新到货</el-button>
            <el-button link type="danger" size="small" @click="deleteItem(row)" v-if="row.status==='已下单'">删除</el-button>
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

    <!-- 更新到货弹窗 -->
    <el-dialog v-model="statusDialogVisible" title="更新到货数量" width="480px">
      <el-form label-width="90px">
        <el-form-item label="物料型号">
          <span style="font-weight:bold">{{ statusForm.material_name }}</span>
        </el-form-item>
        <el-form-item label="订购总数">
          <el-tag type="info" size="large">{{ statusForm.order_qty }}</el-tag>
        </el-form-item>
        <el-form-item label="当前状态">
          <el-tag :type="statusTag(statusForm.oldStatus)">{{ statusForm.oldStatus }}</el-tag>
        </el-form-item>
        <el-form-item label="本次到货">
          <el-input-number v-model="statusForm.received_delta" :min="0" :max="statusForm.remain_qty" 
            size="large" style="width:180px" @change="calcRemain" />
          <span style="margin-left:12px;color:#999">(累计已到: {{ statusForm.existing_received }})</span>
        </el-form-item>
        <el-divider />
        <el-form-item label="到货后状态">
          <el-tag :type="statusTag(statusForm.calcNewStatus)" size="large" style="font-size:14px">
            {{ statusForm.calcNewStatus || '—' }}
          </el-tag>
        </el-form-item>
        <el-form-item label="累计到货">
          <span style="font-size:18px;color:#67c23a;font-weight:bold">{{ statusForm.total_after }}</span>
        </el-form-item>
        <el-form-item label="剩余未到">
          <span style="font-size:18px;color:#f56c6c;font-weight:bold">{{ statusForm.remain_after }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusDialogVisible=false">取消</el-button>
        <el-button type="primary" @click="confirmStatus" :disabled="!statusForm.received_delta">确认到货</el-button>
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

    <!-- BOM同步弹窗 -->
    <el-dialog v-model="bomSyncVisible" title="选择BOM同步生成采购单" width="500px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:16px">
        系统将自动提取BOM中所有采购件，生成采购申请并匹配供应商。
      </el-alert>
      <el-form label-width="100px">
        <el-form-item label="选择BOM">
          <el-select v-model="bomSyncBomId" placeholder="选择要同步的BOM" style="width:100%">
            <el-option v-for="b in bomOptions" :key="b.id" 
              :label="`${b.bom_code} - ${b.product_name}`" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="自动审批">
          <el-switch v-model="bomSyncAutoApprove" />
          <span style="margin-left:8px;color:#999;font-size:12px">开启后直接生成"已审批"状态的采购单</span>
        </el-form-item>
      </el-form>
      <div v-if="syncResult" style="margin-top:12px;white-space:pre-wrap;font-size:14px;color:#67c23a;background:#f0f9eb;padding:12px;border-radius:6px;">
        {{ syncResult }}
      </div>
      <template #footer>
        <el-button @click="bomSyncVisible=false">取消</el-button>
        <el-button type="primary" @click="doBomSync" :loading="syncing">开始同步</el-button>
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
const syncing = ref(false)
const tab = ref('orders')
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterStatus = ref('')

const materialOptions = ref([])
const suppliers = ref([])
const bomOptions = ref([])

const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const importLoading = ref(false)
const importResult = ref('')
const bomSyncVisible = ref(false)
const bomSyncBomId = ref(null)
const bomSyncAutoApprove = ref(false)
const syncResult = ref('')
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
const statusForm = reactive({ 
  id: null, material_name: '', order_qty: 0, oldStatus: '', 
  existing_received: 0, received_delta: 0,
  remain_qty: 0, calcNewStatus: '', total_after: 0, remain_after: 0,
})

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
  const map = { '已下单': 'danger', '部分到货': 'warning', '全部到货': 'success' }
  return map[s] || ''
}

function statusDotClass(row) {
  const map = { '已下单': 'dot-ordered', '部分到货': 'dot-partial', '全部到货': 'dot-done' }
  return map[row.status] || ''
}

function rowClassName({ row }) {
  const map = { '已下单': 'row-ordered', '部分到货': 'row-partial', '全部到货': 'row-done' }
  return map[row.status] || ''
}

function calcRemain() {
  const delta = statusForm.received_delta || 0
  statusForm.total_after = statusForm.existing_received + delta
  statusForm.remain_after = statusForm.order_qty - statusForm.total_after
  if (statusForm.remain_after <= 0) {
    statusForm.calcNewStatus = '全部到货'
    statusForm.remain_after = 0
  } else {
    statusForm.calcNewStatus = '部分到货'
  }
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
  const existRec = row.received_qty || 0
  const remain = row.order_qty - existRec
  Object.assign(statusForm, { 
    id: row.id, material_name: row.material_name,
    order_qty: row.order_qty, oldStatus: row.status,
    existing_received: existRec, received_delta: 0,
    remain_qty: remain, calcNewStatus: '', total_after: existRec, remain_after: remain,
  })
  statusDialogVisible.value = true
}

async function confirmStatus() {
  const delta = statusForm.received_delta || 0
  if (delta <= 0) { ElMessage.warning('请输入到货数量'); return }
  
  const total = statusForm.existing_received + delta
  const newStatus = total >= statusForm.order_qty ? '全部到货' : '部分到货'
  
  await api.put(`/purchase/orders/${statusForm.id}/status`, {
    status: newStatus,
    received_qty: total,
  })
  ElMessage.success(`收货 ${delta} 件, 累计 ${total}/${statusForm.order_qty}, 状态: ${newStatus}`)
  statusDialogVisible.value = false
  fetchData()
}

async function deleteItem(row) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await api.delete(`/purchase/orders/${row.id}`)
  fetchData()
}

async function batchAllReceived() {
  await ElMessageBox.confirm(
    `确定将 ${selectedIds.value.length} 个采购单标记为"全部到货"？\n(到货数量将自动设为订购数量)`,
    '批量全部到货', { type: 'info' }
  )
  let count = 0
  for (const id of selectedIds.value) {
    try { 
      const item = tableData.value.find(r => r.id === id)
      await api.put(`/purchase/orders/${id}/status`, { 
        status: '全部到货', 
        received_qty: item?.order_qty || 0
      })
      count++
    } catch {}
  }
  ElMessage.success(`已更新 ${count} 个采购单为全部到货`)
  selectedIds.value = []
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

async function batchDelete() {
  await ElMessageBox.confirm(`确定删除 ${selectedIds.value.length} 个采购单？`, '批量删除', { type: 'warning' })
  let count = 0
  for (const id of selectedIds.value) {
    try { await api.delete(`/purchase/orders/${id}`); count++ } catch (e) {}
  }
  ElMessage.success(`已删除 ${count} 个采购单`)
  selectedIds.value = []
  fetchData()
}

function onTabChange(val) {
  if (val === 'suppliers') fetchSuppliers()
  else fetchData()
}

// BOM同步功能
async function syncFromBom() {
  syncResult.value = ''
  bomSyncBomId.value = null
  bomSyncAutoApprove.value = false
  const res = await api.get('/bom/headers')
  bomOptions.value = res.items || []
  bomSyncVisible.value = true
}

async function doBomSync() {
  if (!bomSyncBomId.value) {
    ElMessage.warning('请选择BOM')
    return
  }
  syncing.value = true
  syncResult.value = ''
  try {
    const res = await api.post('/purchase/sync-from-bom', {
      bom_header_id: bomSyncBomId.value,
      auto_approve: bomSyncAutoApprove.value,
    })
    syncResult.value = res.message
    fetchData()
    fetchSuppliers()
  } catch (e) {
    syncResult.value = '同步失败: ' + (e.message || e)
  } finally {
    syncing.value = false
  }
}

onMounted(() => { fetchData(); fetchSuppliers() })
</script>

<style scoped>
.page-container { background:#fff; padding:20px; border-radius:8px; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; }

/* 采购状态彩色标注 */
.status-cell { display:flex; align-items:center; gap:6px; }
.status-dot {
  width: 8px; height: 8px; border-radius: 50%; display:inline-block;
  box-shadow: 0 0 6px currentColor;
}
.dot-ordered  { background:#f56c6c; box-shadow:0 0 8px #f56c6c; }   /* 已下单 - 红色 */
.dot-partial  { background:#e6a23c; box-shadow:0 0 8px #e6a23c; }   /* 部分到货 - 黄色 */
.dot-done     { background:#67c23a; box-shadow:0 0 8px #67c23a; }   /* 全部到货 - 绿色 */

/* 行级高亮 */
:deep(.row-ordered)  { background-color:#fef0f0 !important; }
:deep(.row-partial)  { background-color:#fdf6ec !important; }
:deep(.row-done)     { background-color:#f0f9eb !important; }

:deep(.row-ordered:hover)  { background-color:#fde2e2 !important; }
:deep(.row-partial:hover)  { background-color:#faecd8 !important; }
:deep(.row-done:hover)     { background-color:#e1f3d8 !important; }
</style>
