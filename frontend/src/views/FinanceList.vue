<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-button type="primary" @click="showDialog(null)"><el-icon><Plus /></el-icon> 新建收款记录</el-button>
      <el-select v-model="filterStatus" placeholder="状态" style="width:130px" clearable @change="fetchData">
        <el-option label="未到账" value="未到账" /><el-option label="已到账" value="已到账" /><el-option label="部分到账" value="部分到账" />
      </el-select>
      <el-input v-model="keyword" placeholder="搜索收款单号" style="width:200px" clearable @clear="fetchData" @keyup.enter="fetchData">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
    </div>

    <!-- 汇总卡片 -->
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="6"><div class="stat-card"><div class="stat-label">总应收</div><div class="stat-val">¥{{ formatMoney(summary.total_amount) }}</div></div></el-col>
      <el-col :span="6"><div class="stat-card" style="border-left:3px solid #67c23a"><div class="stat-label">已到账</div><div class="stat-val" style="color:#67c23a">¥{{ formatMoney(summary.total_paid) }}</div></div></el-col>
      <el-col :span="6"><div class="stat-card" style="border-left:3px solid #f56c6c"><div class="stat-label">未到账</div><div class="stat-val" style="color:#f56c6c">¥{{ formatMoney(summary.total_pending) }}</div></div></el-col>
      <el-col :span="6"><div class="stat-card"><div class="stat-label">记录数</div><div class="stat-val">{{ total }}</div></div></el-col>
    </el-row>

    <el-table :data="tableData" v-loading="loading" stripe border>
      <el-table-column prop="payment_number" label="收款单号" width="170" />
      <el-table-column prop="order_number" label="销售订单号" width="170" />
      <el-table-column prop="customer_name" label="客户" width="120" />
      <el-table-column prop="product_name" label="产品" min-width="120" show-overflow-tooltip />
      <el-table-column label="订单 出货/总量" width="100" align="center">
        <template #default="{row}"><span style="color:#67c23a">{{ row.shipped_qty }}</span><span style="color:#999">/</span>{{ row.order_qty }}</template>
      </el-table-column>
      <el-table-column label="收款金额" width="120" align="right">
        <template #default="{row}"><span style="font-weight:bold;color:#409eff">¥{{ formatMoney(row.amount) }}</span></template>
      </el-table-column>
      <el-table-column label="收款日期" width="120" align="center">
        <template #default="{row}">{{ row.payment_date || '—' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{row}">
          <el-tag :type="row.status==='已到账'?'success':row.status==='部分到账'?'warning':'danger'" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="payment_method" label="付款方式" width="100" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{row}">
          <el-button link type="primary" size="small" @click="showDialog(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="deleteItem(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" layout="total,prev,pager,next" @change="fetchData" style="margin-top:16px;justify-content:flex-end" />

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editId?'编辑收款':'新建收款'" width="500px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="销售订单" required>
          <el-select v-model="form.sales_order_id" filterable placeholder="选择订单" style="width:100%" :disabled="!!editId">
            <el-option v-for="o in orderOptions" :key="o.id" :label="`${o.order_number} - ${o.customer_name} ${o.product_name||''}`" :value="o.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="客户" required>
          <el-input :model-value="form._customer_name" disabled />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="金额" required><el-input-number v-model="form.amount" :min="0" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="状态"><el-select v-model="form.status"><el-option label="未到账" value="未到账" /><el-option label="已到账" value="已到账" /><el-option label="部分到账" value="部分到账" /></el-select></el-form-item></el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="收款日期"><el-date-picker v-model="form.payment_date" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="付款方式"><el-select v-model="form.payment_method"><el-option label="银行转账" value="银行转账" /><el-option label="现金" value="现金" /><el-option label="微信" value="微信" /><el-option label="支付宝" value="支付宝" /></el-select></el-form-item></el-col>
        </el-row>
        <el-form-item label="备注"><el-input v-model="form.remark" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" :loading="saving" @click="submitForm">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false); const saving = ref(false); const keyword = ref(''); const filterStatus = ref('')
const tableData = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(20)
const summary = reactive({ total_amount: 0, total_paid: 0, total_pending: 0 })
const orderOptions = ref([])

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterStatus.value) params.status = filterStatus.value
    if (keyword.value) params.keyword = keyword.value
    const [payRes, sumRes] = await Promise.all([
      api.get('/finance/payments', { params }),
      api.get('/finance/summary'),
    ])
    tableData.value = payRes.items; total.value = payRes.total
    Object.assign(summary, sumRes)
  } finally { loading.value = false }
}

function formatMoney(v) { return Number(v||0).toLocaleString('zh-CN',{maximumFractionDigits:0}) }

const dialogVisible = ref(false); const editId = ref(null)
const form = reactive({ sales_order_id: null, customer_id: null, _customer_name: '', amount: 0, status: '未到账', payment_date: '', payment_method: '', remark: '' })

async function showDialog(row) {
  if (!orderOptions.value.length) {
    const r = await api.get('/sales/orders', { params: { page_size: 200 } })
    orderOptions.value = r.items || []
  }
  if (row) {
    editId.value = row.id
    const ord = orderOptions.value.find(o => o.id === row.sales_order_id)
    Object.assign(form, {
      sales_order_id: row.sales_order_id, customer_id: row.customer_id,
      _customer_name: row.customer_name,
      amount: row.amount, status: row.status, payment_date: row.payment_date||'',
      payment_method: row.payment_method, remark: row.remark||'',
    })
  } else {
    editId.value = null
    Object.assign(form, { sales_order_id: null, customer_id: null, _customer_name: '', amount: 0, status: '未到账', payment_date: '', payment_method: '', remark: '' })
  }
  dialogVisible.value = true
}

watch(() => form.sales_order_id, (val) => {
  if (!val) { form.customer_id = null; form._customer_name = ''; return }
  const ord = orderOptions.value.find(o => o.id === val)
  if (ord) { form.customer_id = ord.customer_id; form._customer_name = ord.customer_name || '' }
})

async function submitForm() {
  if (!form.sales_order_id) return ElMessage.warning('请选择销售订单')
  saving.value = true
  try {
    const payload = { sales_order_id: form.sales_order_id, customer_id: form.customer_id, amount: form.amount, status: form.status, payment_date: form.payment_date||null, payment_method: form.payment_method, remark: form.remark }
    if (editId.value) { await api.put(`/finance/payments/${editId.value}`, payload) }
    else { await api.post('/finance/payments', payload) }
    ElMessage.success(editId.value?'已更新':'已创建'); dialogVisible.value = false; fetchData()
  } finally { saving.value = false }
}

async function deleteItem(row) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await api.delete(`/finance/payments/${row.id}`)
  fetchData()
}

onMounted(fetchData)
</script>

<style scoped>
.page-container { background:#fff; padding:20px; border-radius:8px }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; flex-wrap:wrap }
.stat-card { background:#fafbfc; border-radius:8px; padding:14px 18px; border:1px solid #ebeef5 }
.stat-label { font-size:13px; color:#909399; margin-bottom:6px }
.stat-val { font-size:22px; font-weight:bold; color:#303133 }
</style>
