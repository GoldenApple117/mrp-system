<template>
  <div class="page-container">
    <el-tabs v-model="tab" @tab-change="fetchData">
      <el-tab-pane label="到货检验" name="inspection">
        <div class="page-toolbar">
          <el-button type="primary" @click="showInspectionDialog"><el-icon><Plus /></el-icon> 创建检验</el-button>
          <el-select v-model="filterResult" placeholder="结果筛选" style="width:120px" clearable @change="fetchData">
            <el-option label="待检" value="待检" />
            <el-option label="合格" value="合格" />
            <el-option label="部分合格" value="部分合格" />
            <el-option label="不合格" value="不合格" />
          </el-select>
        </div>
        <el-table :data="inspections" v-loading="loading" stripe border>
          <el-table-column prop="inspection_no" label="检验单号" width="180" />
          <el-table-column prop="po_number" label="采购单号" width="150" />
          <el-table-column prop="material_code" label="物料编码" width="120" />
          <el-table-column prop="material_name" label="物料型号" min-width="140" />
          <el-table-column prop="inspect_qty" label="检验数量" width="100" />
          <el-table-column prop="pass_qty" label="合格" width="80" />
          <el-table-column prop="reject_qty" label="不合格" width="80" />
          <el-table-column label="结果" width="100">
            <template #default="{row}"><el-tag :type="resultTag(row.result)" size="small">{{ row.result }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="inspector" label="检验员" width="100" />
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{row}">
              <el-button link type="primary" size="small" @click="showResultDialog(row)" v-if="row.result==='待检'">录入结果</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" layout="total,prev,pager,next" @change="fetchData" style="margin-top:12px;justify-content:flex-end" />
      </el-tab-pane>

      <el-tab-pane label="盘点管理" name="stock">
        <div class="page-toolbar">
          <el-button type="primary" @click="showStockDialog"><el-icon><Plus /></el-icon> 创建盘点</el-button>
        </div>
        <el-table :data="stockCounts" v-loading="loading2" stripe border>
          <el-table-column prop="count_no" label="盘点单号" width="180" />
          <el-table-column prop="material_code" label="物料编码" width="120" />
          <el-table-column prop="material_name" label="物料型号" min-width="140" />
          <el-table-column prop="warehouse_name" label="仓库" width="100" />
          <el-table-column prop="system_qty" label="系统库存" width="100" />
          <el-table-column prop="actual_qty" label="实盘数量" width="100" />
          <el-table-column prop="difference" label="差异" width="90">
            <template #default="{row}"><span :style="{color:row.difference<0?'#f56c6c':'#67c23a'}">{{ row.difference>0?'+':'' }}{{ row.difference }}</span></template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{row}"><el-tag :type="row.status==='已调整'?'success':'warning'" size="small">{{ row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="counter" label="盘点人" width="100" />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{row}">
              <el-button v-if="row.status==='待盘点'" link type="primary" size="small" @click="showStockResult(row)">录入结果</el-button>
              <el-button v-if="row.status==='已盘点'" link type="success" size="small" @click="adjustStock(row)">确认调整</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination v-model:current-page="spage" v-model:page-size="spageSize" :total="stotal" layout="total,prev,pager,next" @change="fetchStock" style="margin-top:12px;justify-content:flex-end" />
      </el-tab-pane>
    </el-tabs>

    <!-- 创建检验弹窗 -->
    <el-dialog v-model="inspDialogVisible" title="创建到货检验" width="500px">
      <el-form ref="inspFormRef" :model="inspForm" label-width="100px">
        <el-form-item label="采购单" required>
          <el-select v-model="inspForm.purchase_order_id" filterable placeholder="选择采购单" style="width:100%">
            <el-option v-for="po in poOptions" :key="po.id" :label="`${po.po_number} - ${po.material_name} x${po.order_qty}`" :value="po.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="检验数量" required>
          <el-input-number v-model="inspForm.inspect_qty" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="检验员">
          <el-input v-model="inspForm.inspector" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="inspForm.remark" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="inspDialogVisible=false">取消</el-button>
        <el-button type="primary" @click="createInspection" :loading="saving">创建</el-button>
      </template>
    </el-dialog>

    <!-- 检验结果弹窗 -->
    <el-dialog v-model="resultDialogVisible" title="录入检验结果" width="450px">
      <el-form label-width="100px">
        <el-form-item label="检验数量"><span>{{ resultForm.inspect_qty }}</span></el-form-item>
        <el-form-item label="合格数量" required>
          <el-input-number v-model="resultForm.pass_qty" :min="0" :max="resultForm.inspect_qty" style="width:100%" />
        </el-form-item>
        <el-form-item label="不合格数量" required>
          <el-input-number v-model="resultForm.reject_qty" :min="0" :max="resultForm.inspect_qty" style="width:100%" />
        </el-form-item>
        <el-form-item label="入库仓库">
          <el-select v-model="resultForm.warehouse_id" style="width:100%">
            <el-option v-for="w in warehouses" :key="w.id" :label="w.warehouse_name" :value="w.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resultDialogVisible=false">取消</el-button>
        <el-button type="primary" @click="submitResult">提交</el-button>
      </template>
    </el-dialog>

    <!-- 盘点创建弹窗 -->
    <el-dialog v-model="stockDialogVisible" title="创建盘点计划" width="450px">
      <el-form ref="stockFormRef" :model="stockForm" label-width="100px">
        <el-form-item label="物料" required>
          <el-select v-model="stockForm.item_id" filterable placeholder="选择物料" style="width:100%">
            <el-option v-for="m in materialOptions" :key="m.id" :label="`${m.material_code} ${m.material_name}`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="仓库">
          <el-select v-model="stockForm.warehouse_id" style="width:100%">
            <el-option v-for="w in warehouses" :key="w.id" :label="w.warehouse_name" :value="w.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="盘点人">
          <el-input v-model="stockForm.counter" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stockDialogVisible=false">取消</el-button>
        <el-button type="primary" @click="createStockCount" :loading="saving">创建</el-button>
      </template>
    </el-dialog>

    <!-- 盘点结果弹窗 -->
    <el-dialog v-model="stockResultVisible" title="录入盘点结果" width="400px">
      <el-form label-width="100px">
        <el-form-item label="系统库存"><span>{{ stockResultForm.system_qty }}</span></el-form-item>
        <el-form-item label="实盘数量" required>
          <el-input-number v-model="stockResultForm.actual_qty" :min="0" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stockResultVisible=false">取消</el-button>
        <el-button type="primary" @click="submitStockResult">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const tab = ref('inspection')
const loading = ref(false)
const loading2 = ref(false)
const saving = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const spage = ref(1)
const spageSize = ref(20)
const stotal = ref(0)
const filterResult = ref('')

const inspections = ref([])
const stockCounts = ref([])
const poOptions = ref([])
const materialOptions = ref([])
const warehouses = ref([{id:1, warehouse_name:'主仓库'}])

const inspDialogVisible = ref(false)
const resultDialogVisible = ref(false)
const stockDialogVisible = ref(false)
const stockResultVisible = ref(false)

const inspFormRef = ref(null)
const stockFormRef = ref(null)

const inspForm = reactive({ purchase_order_id: null, item_id: null, inspect_qty: 1, inspector: '', remark: '' })
const resultForm = reactive({ id: null, inspect_qty: 0, pass_qty: 0, reject_qty: 0, warehouse_id: 1 })
const stockForm = reactive({ item_id: null, warehouse_id: 1, counter: '' })
const stockResultForm = reactive({ id: null, system_qty: 0, actual_qty: 0 })

function resultTag(r) {
  const map = { '待检': '', '合格': 'success', '部分合格': 'warning', '不合格': 'danger' }
  return map[r] || ''
}

async function fetchData() {
  if (tab.value === 'inspection') {
    loading.value = true
    try {
      const params = { page: page.value, page_size: pageSize.value }
      if (filterResult.value) params.result = filterResult.value
      const res = await api.get('/inspection', { params })
      inspections.value = res.items; total.value = res.total
    } finally { loading.value = false }
  } else {
    fetchStock()
  }
}

async function fetchStock() {
  loading2.value = true
  try {
    const res = await api.get('/inspection/stock-counts', { params: { page: spage.value, page_size: spageSize.value } })
    stockCounts.value = res.items; stotal.value = res.total
  } finally { loading2.value = false }
}

async function showInspectionDialog() {
  const [poRes] = await Promise.all([
    api.get('/purchase/orders', { params: { status: '已下单', page_size: 10000 } }),
  ])
  poOptions.value = poRes.items || []
  Object.assign(inspForm, { purchase_order_id: null, item_id: null, inspect_qty: 1, inspector: '', remark: '' })
  inspDialogVisible.value = true
}

async function createInspection() {
  if (!inspForm.purchase_order_id) return ElMessage.warning('请选择采购单')
  saving.value = true
  try {
    const po = poOptions.value.find(p => p.id === inspForm.purchase_order_id)
    await api.post('/inspection', {
      purchase_order_id: inspForm.purchase_order_id,
      item_id: po.item_id,
      inspect_qty: inspForm.inspect_qty,
      inspector: inspForm.inspector,
      remark: inspForm.remark,
    })
    ElMessage.success('检验单已创建')
    inspDialogVisible.value = false
    fetchData()
  } finally { saving.value = false }
}

function showResultDialog(row) {
  Object.assign(resultForm, { id: row.id, inspect_qty: row.inspect_qty, pass_qty: 0, reject_qty: 0, warehouse_id: 1 })
  resultDialogVisible.value = true
}

async function submitResult() {
  await api.put(`/inspection/${resultForm.id}/result`, {
    pass_qty: resultForm.pass_qty, reject_qty: resultForm.reject_qty,
    result: resultForm.reject_qty === 0 ? '合格' : resultForm.pass_qty > 0 ? '部分合格' : '不合格',
    warehouse_id: resultForm.warehouse_id, inspector: '',
  })
  ElMessage.success('检验结果已提交，合格自动入库')
  resultDialogVisible.value = false
  fetchData()
}

async function showStockDialog() {
  const [matRes] = await Promise.all([api.get('/materials/all')])
  materialOptions.value = matRes.items
  Object.assign(stockForm, { item_id: null, warehouse_id: 1, counter: '' })
  stockDialogVisible.value = true
}

async function createStockCount() {
  saving.value = true
  try {
    await api.post('/inspection/stock-counts', { ...stockForm })
    ElMessage.success('盘点计划已创建')
    stockDialogVisible.value = false
    fetchStock()
  } finally { saving.value = false }
}

function showStockResult(row) {
  Object.assign(stockResultForm, { id: row.id, system_qty: row.system_qty, actual_qty: row.system_qty })
  stockResultVisible.value = true
}

async function submitStockResult() {
  await api.put(`/inspection/stock-counts/${stockResultForm.id}/result`, { actual_qty: stockResultForm.actual_qty, counter: '' })
  ElMessage.success('盘点结果已提交')
  stockResultVisible.value = false
  fetchStock()
}

async function adjustStock(row) {
  await ElMessageBox.confirm(`确认调整库存？差异 ${row.difference} 件`, '提示')
  await api.post(`/inspection/stock-counts/${row.id}/adjust`, { operator: '系统' })
  ElMessage.success('库存已调整')
  fetchStock()
}

onMounted(fetchData)
</script>

<style scoped>
.page-container { background:#fff; padding:20px; border-radius:8px; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; }
</style>
