<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-input v-model="keyword" placeholder="搜索物料" style="width:240px" clearable @clear="fetchData">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button type="primary" @click="showTxDialog"><el-icon><Plus /></el-icon> 出入库</el-button>
      <el-tabs v-model="activeTab" style="flex:1;margin-left:16px" @tab-change="fetchData">
        <el-tab-pane label="库存总览" name="summary" />
        <el-tab-pane label="出入库流水" name="transactions" />
      </el-tabs>
    </div>

    <!-- 库存总览 -->
    <div v-if="activeTab==='summary'">
      <el-table :data="summaryData" v-loading="loading" stripe border>
        <el-table-column prop="material_code" label="物料编码" width="130" />
        <el-table-column prop="material_name" label="物料名称" min-width="160" />
        <el-table-column prop="unit" label="单位" width="70" />
        <el-table-column prop="on_hand" label="现有库存" width="110" />
        <el-table-column prop="allocated" label="已分配" width="90" />
        <el-table-column prop="on_order" label="在途" width="90" />
        <el-table-column label="可用量" width="100">
          <template #default="{row}">
            <span :style="{color:row.available<0?'#f56c6c':''}">{{ row.available }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="safety_stock" label="安全库存" width="90" />
        <el-table-column label="状态" width="80">
          <template #default="{row}">
            <el-tag :type="row.is_low?'danger':'success'" size="small">{{ row.is_low ? '偏低' : '正常' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 出入库流水 -->
    <div v-else>
      <el-table :data="txData" v-loading="loading" stripe border>
        <el-table-column prop="material_code" label="物料编码" width="130" />
        <el-table-column prop="material_name" label="物料名称" min-width="140" />
        <el-table-column prop="transaction_type" label="类型" width="100">
          <template #default="{row}">
            <el-tag :type="row.transaction_type.includes('出')?'danger':'success'" size="small">{{ row.transaction_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="90" />
        <el-table-column prop="reference_no" label="关联单号" width="140" />
        <el-table-column prop="operator" label="操作人" width="100" />
        <el-table-column prop="remark" label="备注" min-width="120" />
        <el-table-column prop="created_at" label="时间" width="170" />
      </el-table>
      <el-pagination v-model:current-page="txPage" v-model:page-size="txPageSize" :total="txTotal"
        layout="total,prev,pager,next" @change="fetchTransactions" style="margin-top:16px;justify-content:flex-end" />
    </div>

    <!-- 出入库弹窗 -->
    <el-dialog v-model="txDialogVisible" title="出入库操作" width="500px">
      <el-form ref="txFormRef" :model="txForm" :rules="txRules" label-width="90px">
        <el-form-item label="物料" prop="item_id">
          <el-select v-model="txForm.item_id" filterable placeholder="选择物料" style="width:100%">
            <el-option v-for="m in materialOptions" :key="m.id" :label="`${m.material_code} ${m.material_name}`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="仓库" prop="warehouse_id">
          <el-select v-model="txForm.warehouse_id" placeholder="选择仓库" style="width:100%">
            <el-option v-for="w in warehouseOptions" :key="w.id" :label="w.warehouse_name" :value="w.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作类型" prop="transaction_type">
          <el-radio-group v-model="txForm.transaction_type">
            <el-radio-button value="入库">入库</el-radio-button>
            <el-radio-button value="出库">出库</el-radio-button>
            <el-radio-button value="盘点调整">盘点调整</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="txForm.quantity" :min="0.01" style="width:100%" />
        </el-form-item>
        <el-form-item label="关联单号">
          <el-input v-model="txForm.reference_no" placeholder="采购单号/工单号" />
        </el-form-item>
        <el-form-item label="操作人">
          <el-input v-model="txForm.operator" placeholder="操作工人姓名" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="txForm.remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="txDialogVisible=false">取消</el-button>
        <el-button type="primary" @click="submitTx" :loading="txSaving">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const activeTab = ref('summary')
const keyword = ref('')

const summaryData = ref([])

const txData = ref([])
const txTotal = ref(0)
const txPage = ref(1)
const txPageSize = ref(20)

const materialOptions = ref([])
const warehouseOptions = ref([])

const txDialogVisible = ref(false)
const txSaving = ref(false)
const txFormRef = ref(null)
const txForm = reactive({
  item_id: null, warehouse_id: 1, transaction_type: '入库',
  quantity: 1, reference_no: '', operator: '', remark: '',
})
const txRules = {
  item_id: [{ required: true, message: '请选择物料' }],
  warehouse_id: [{ required: true, message: '请选择仓库' }],
  transaction_type: [{ required: true }],
  quantity: [{ required: true, message: '请输入数量' }],
}

async function fetchData() {
  loading.value = true
  try {
    const res = await api.get('/inventory/summary')
    summaryData.value = res.items
  } finally {
    loading.value = false
  }
}

async function fetchTransactions() {
  const res = await api.get('/inventory/transactions', {
    params: { page: txPage.value, page_size: txPageSize.value },
  })
  txData.value = res.items
  txTotal.value = res.total
}

async function showTxDialog() {
  const [matRes, whRes] = await Promise.all([
    api.get('/materials/all'),
    api.get('/inventory/warehouses'),
  ])
  materialOptions.value = matRes.items
  warehouseOptions.value = whRes.items
  if (warehouseOptions.value.length === 0) {
    await api.post('/inventory/warehouses', { warehouse_code: 'WH01', warehouse_name: '主仓库' })
    const whRes2 = await api.get('/inventory/warehouses')
    warehouseOptions.value = whRes2.items
  }
  txForm.warehouse_id = warehouseOptions.value[0]?.id || 1
  txDialogVisible.value = true
}

async function submitTx() {
  const valid = await txFormRef.value.validate().catch(() => false)
  if (!valid) return
  txSaving.value = true
  try {
    const qty = txForm.transaction_type === '出库' ? -Math.abs(txForm.quantity) : txForm.quantity
    await api.post('/inventory/transaction', { ...txForm, quantity: qty })
    ElMessage.success(`${txForm.transaction_type}成功`)
    txDialogVisible.value = false
    fetchData()
  } finally {
    txSaving.value = false
  }
}

onMounted(() => { fetchData(); fetchTransactions() })
</script>

<style scoped>
.page-container { background:#fff; padding:20px; border-radius:8px; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; flex-wrap:wrap; }
</style>
