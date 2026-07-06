<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-button type="primary" @click="showOrderDialog(null)"><el-icon><Plus /></el-icon> 新建订单</el-button>
      <el-select v-model="filterStatus" placeholder="状态筛选" style="width:120px" clearable @change="fetchData">
        <el-option label="待审核" value="待审核" />
        <el-option label="已审核" value="已审核" />
        <el-option label="待出货" value="待出货" />
        <el-option label="部分出货" value="部分出货" />
        <el-option label="全部出货" value="全部出货" />
        <el-option label="已取消" value="已取消" />
      </el-select>
      <span style="flex:1"></span>
      <el-button @click="tab='customers'" :type="tab==='customers'?'':'default'">客户管理</el-button>
    </div>

    <el-tabs v-model="tab" @tab-change="onTabChange">
      <el-tab-pane label="销售订单" name="orders" />
      <el-tab-pane label="客户" name="customers" />
    </el-tabs>

    <!-- 订单列表 -->
    <div v-if="tab==='orders'">
      <div v-if="selectedIds.length" class="batch-bar">
        <el-tag type="info" style="margin-right:8px">已选 {{ selectedIds.length }} 项</el-tag>
        <el-button size="small" type="primary" @click="batchToMps">生成MPS计划</el-button>
        <el-button size="small" type="danger" @click="batchDeleteSO">批量删除</el-button>
        <el-button size="small" @click="selectedIds = []">取消选择</el-button>
      </div>
      <el-table :data="orderData" v-loading="loading" stripe border
        :row-class-name="soRowClass"
        @selection-change="(rows) => selectedIds = rows.map(r => r.id)">
        <el-table-column type="selection" width="40" />
        <el-table-column prop="order_number" label="订单号" width="170" />
        <el-table-column prop="customer_name" label="客户" width="120" />
        <el-table-column prop="material_code" label="产品编码" width="120" />
        <el-table-column prop="material_name" label="产品型号" min-width="120" show-overflow-tooltip />
        <el-table-column label="单价" width="80" align="right">
          <template #default="{row}">¥{{ formatMoney(row.unit_price) }}</template>
        </el-table-column>
        <el-table-column label="数量" width="85" align="center">
          <template #default="{row}">
            <span @click="showEdit(row)" style="cursor:pointer;text-decoration:underline dashed var(--color-accent, #409eff)">{{ row.order_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column label="出货状态" width="130" align="center">
          <template #default="{row}">
            <span style="color:var(--color-success, #67c23a)">{{ row.shipped_qty || 0 }}</span>/{{ row.order_qty }}
            <el-tag :type="row.ship_status==='全部出货'?'success':row.ship_status==='部分出货'?'warning':'danger'" size="small" style="margin-left:4px">{{ row.ship_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="收款状态" width="130" align="center">
          <template #default="{row}">
            <span style="color:var(--color-accent, #409eff)">¥{{ formatMoney(row.paid_amount) }}</span>/¥{{ formatMoney(row.total_amount) }}
            <el-tag :type="row.pay_status==='全部收款'?'success':row.pay_status==='部分收款'?'warning':'danger'" size="small" style="margin-left:4px">{{ row.pay_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="订单状态" width="90">
          <template #default="{row}">
            <el-tag :type="row.status==='已完成'?'success':row.status==='待审核'?'warning':row.status==='已审核'?'primary':row.status==='已取消'?'danger':'info'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="交期" width="100" prop="delivery_date" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{row}">
            <el-button link type="primary" size="small" @click="showEdit(row)">编辑</el-button>
            <el-button link type="success" size="small" @click="approveSO(row)" v-if="row.status==='待审核'">审核</el-button>
            <el-button link type="success" size="small" @click="toMps(row)" v-if="row.status==='已审核' && row.ship_status==='待出货'">→MPS</el-button>
            <el-button link type="danger" size="small" @click="cancelSO(row)" v-if="row.status!=='已完成' && row.status!=='已取消'">作废</el-button>
            <el-button link type="danger" size="small" @click="deleteSO(row)" v-if="row.ship_status==='待出货'">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total"
        layout="total,prev,pager,next" @change="fetchData" style="margin-top:16px;justify-content:flex-end" />
    </div>

    <!-- 客户列表 -->
    <div v-else>
      <div style="margin-bottom:12px">
        <el-button type="primary" size="small" @click="showCustomerDialog(null)"><el-icon><Plus /></el-icon> 新增客户</el-button>
      </div>
      <el-table :data="customerData" stripe border>
        <el-table-column prop="customer_code" label="编码" width="120" />
        <el-table-column prop="customer_name" label="名称" min-width="160" />
        <el-table-column prop="contact_person" label="联系人" width="90" />
        <el-table-column prop="contact_phone" label="电话" width="130" />
        <el-table-column prop="address" label="地址" min-width="150" />
      </el-table>
    </div>

    <!-- 新建/编辑订单弹窗 -->
    <el-dialog v-model="dialogVisible" title="新建销售订单" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="客户" prop="customer_id">
          <el-select v-model="form.customer_id" filterable placeholder="选择客户" style="width:100%">
            <el-option v-for="c in customerData" :key="c.id" :label="c.customer_name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="产品" prop="item_id">
          <el-select v-model="form.item_id" filterable placeholder="选择产品" style="width:100%">
            <el-option v-for="m in productOptions" :key="m.id" :label="`${m.material_code} ${m.material_name}`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" prop="order_qty">
          <el-input-number v-model="form.order_qty" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="单价 ¥">
          <el-input-number v-model="form.unit_price" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="交期" prop="delivery_date">
          <el-date-picker v-model="form.delivery_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
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

    <!-- 编辑订单弹窗 -->
    <el-dialog v-model="editVisible" title="编辑订单" width="420px">
      <el-form label-width="90px">
        <el-form-item label="订单号"><strong>{{ editForm.order_number }}</strong></el-form-item>
        <el-form-item label="数量"><el-input-number v-model="editForm.order_qty" :min="1" style="width:100%" /></el-form-item>
        <el-form-item label="单价 ¥"><el-input-number v-model="editForm.unit_price" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="交期"><el-date-picker v-model="editForm.delivery_date" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="editVisible=false">取消</el-button><el-button type="primary" :loading="saving" @click="submitEdit">保存</el-button></template>
    </el-dialog>

    <!-- 状态更新弹窗 -->
    <el-dialog v-model="statusVisible" title="更新订单状态" width="350px">
      <el-form label-width="90px">
        <el-form-item label="当前状态"><el-tag>{{ statusForm.oldStatus }}</el-tag></el-form-item>
        <el-form-item label="新状态">
          <el-select v-model="statusForm.newStatus">
            <el-option label="待处理" value="待处理" />
            <el-option label="生产中" value="生产中" />
            <el-option label="已发货" value="已发货" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已取消" value="已取消" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusVisible=false">取消</el-button>
        <el-button type="primary" @click="confirmStatus">确认</el-button>
      </template>
    </el-dialog>

    <!-- 客户弹窗 -->
    <el-dialog v-model="customerVisible" title="新增客户" width="450px">
      <el-form ref="custFormRef" :model="custForm" label-width="90px">
        <el-form-item label="编码" required><el-input v-model="custForm.customer_code" /></el-form-item>
        <el-form-item label="名称" required><el-input v-model="custForm.customer_name" /></el-form-item>
        <el-form-item label="联系人"><el-input v-model="custForm.contact_person" /></el-form-item>
        <el-form-item label="电话"><el-input v-model="custForm.contact_phone" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="custForm.address" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="customerVisible=false">取消</el-button>
        <el-button type="primary" @click="submitCustomer">保存</el-button>
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
const tab = ref('orders')
const filterStatus = ref('')

const orderData = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const selectedIds = ref([])

const customerData = ref([])
const productOptions = ref([])

const dialogVisible = ref(false)
const editVisible = ref(false)
const editForm = reactive({ id: null, order_number: '', order_qty: 1, unit_price: 0, delivery_date: '' })
const formRef = ref(null)
const form = reactive({
  customer_id: null, item_id: null, order_qty: 1, unit_price: 0, delivery_date: '', remark: '',
})
const rules = {
  customer_id: [{ required: true }], item_id: [{ required: true }],
  order_qty: [{ required: true }], delivery_date: [{ required: true }],
}

const statusVisible = ref(false)
const statusForm = reactive({ id: null, oldStatus: '', newStatus: '' })

const customerVisible = ref(false)
const custFormRef = ref(null)
const custForm = reactive({
  customer_code: '', customer_name: '', contact_person: '', contact_phone: '', address: '',
})

function soStatusTag(s) {
  const map = { '进行中':'info','已完成':'success','已取消':'danger' }
  return map[s] || ''
}

function formatMoney(v) { return Number(v||0).toLocaleString('zh-CN',{maximumFractionDigits:0}) }

function showEdit(row) {
  Object.assign(editForm, { id: row.id, order_number: row.order_number, order_qty: row.order_qty, unit_price: row.unit_price, delivery_date: row.delivery_date })
  editVisible.value = true
}

async function submitEdit() {
  saving.value = true
  try {
    await api.put(`/sales/orders/${editForm.id}`, { order_qty: editForm.order_qty, unit_price: editForm.unit_price, total_amount: editForm.order_qty * editForm.unit_price, delivery_date: editForm.delivery_date })
    ElMessage.success('已更新'); editVisible.value = false; fetchData()
  } finally { saving.value = false }
}

function soRowClass({ row }) {
  const map = { '待处理':'row-pending','生产中':'row-making','已发货':'row-shipped','已完成':'row-done','已取消':'row-cancel' }
  return map[row.status] || ''
}

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterStatus.value) params.status = filterStatus.value
    const res = await api.get('/sales/orders', { params })
    orderData.value = res.items; total.value = res.total
  } finally { loading.value = false }
}

async function fetchCustomers() {
  const res = await api.get('/sales/customers')
  customerData.value = res.items
}

async function showOrderDialog() {
  await fetchCustomers()
  const matRes = await api.get('/materials/all', { params: { material_type: '成品' } })
  if (!matRes.items?.length) {
    const all = await api.get('/materials/all')
    productOptions.value = all.items.filter(m => m.level_type === '产品' || m.material_type === '成品')
  } else {
    productOptions.value = matRes.items
  }
  Object.assign(form, { customer_id: null, item_id: null, order_qty: 1, delivery_date: '', remark: '' })
  dialogVisible.value = true
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    await api.post('/sales/orders', { ...form })
    ElMessage.success('销售订单已创建')
    dialogVisible.value = false
    fetchData()
  } finally { saving.value = false }
}

function updateStatus(row) {
  Object.assign(statusForm, { id: row.id, oldStatus: row.status, newStatus: '' })
  statusVisible.value = true
}

async function confirmStatus() {
  await api.put(`/sales/orders/${statusForm.id}/status`, { status: statusForm.newStatus })
  ElMessage.success('状态已更新')
  statusVisible.value = false
  fetchData()
}

async function toMps(row) {
  try {
    const res = await api.post(`/sales/orders/${row.id}/to-mps`)
    ElMessage.success(res.message)
    fetchData()
  } catch (e) { ElMessage.error(e.message || '操作失败') }
}

async function approveSO(row) {
  try {
    const res = await api.post(`/sales/orders/${row.id}/approve`)
    ElMessage.success(res.message)
    fetchData()
  } catch (e) { ElMessage.error(e.message || '审核失败') }
}

async function cancelSO(row) {
  await ElMessageBox.confirm(`确定作废订单 ${row.order_number}？关联的MPS计划将同时清除。`, '作废确认', { type: 'warning' })
  try {
    const res = await api.post(`/sales/orders/${row.id}/cancel`)
    ElMessage.success(res.message)
    fetchData()
  } catch (e) { ElMessage.error(e.message || '作废失败') }
}

async function deleteSO(row) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await api.delete(`/sales/orders/${row.id}`)
  fetchData()
}

async function batchToMps() {
  await ElMessageBox.confirm(`将 ${selectedIds.value.length} 个订单转为MPS计划？`, '批量生成MPS', { type: 'info' })
  let count = 0
  for (const id of selectedIds.value) {
    try { await api.post(`/sales/orders/${id}/to-mps`); count++ } catch (e) { console.error('[MRP] 转MPS失败', e) }
  }
  ElMessage.success(`已生成 ${count} 个MPS计划`)
  selectedIds.value = []
  fetchData()
}

async function batchDeleteSO() {
  await ElMessageBox.confirm(`确定删除 ${selectedIds.value.length} 个订单？`, '批量删除', { type: 'warning' })
  let count = 0
  for (const id of selectedIds.value) {
    try { await api.delete(`/sales/orders/${id}`); count++ } catch (e) { console.error('[MRP] 删除订单失败', e) }
  }
  ElMessage.success(`已删除 ${count} 个订单`)
  selectedIds.value = []
  fetchData()
}

function showCustomerDialog() {
  Object.assign(custForm, { customer_code: '', customer_name: '', contact_person: '', contact_phone: '', address: '' })
  customerVisible.value = true
}

async function submitCustomer() {
  await api.post('/sales/customers', { ...custForm })
  ElMessage.success('客户已添加')
  customerVisible.value = false
  fetchCustomers()
}

function onTabChange(val) {
  if (val === 'customers') fetchCustomers()
  else fetchData()
}

onMounted(() => { fetchData(); fetchCustomers() })
</script>

<style scoped>
.page-container { padding: 0;; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; }
.batch-bar {
  display:flex; align-items:center; gap:8px;
  background:var(--color-accent-muted, rgba(59,130,246,0.06)); border:1px solid var(--color-accent, #a0cfff); padding:8px 14px; border-radius:6px; margin-bottom:12px;
}
:deep(.row-pending) { background-color:var(--color-warning-muted, rgba(234,179,8,0.08)) !important; }
:deep(.row-making) { background-color:var(--color-accent-muted, rgba(59,130,246,0.06)) !important; }
:deep(.row-shipped) { background-color:var(--color-success-muted, rgba(34,197,94,0.06)) !important; }
:deep(.row-done) { background-color:var(--color-bg-overlay, rgba(255,255,255,0.03)) !important; }
:deep(.row-cancel) { background-color:var(--color-danger-muted, rgba(239,68,68,0.06)) !important; text-decoration:line-through; }
</style>
