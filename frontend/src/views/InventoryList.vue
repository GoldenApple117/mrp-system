<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-input v-model="keyword" placeholder="搜索物料编码或名称" style="width:280px" clearable 
        @clear="fetchData" @keyup.enter="fetchData">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button type="primary" @click="fetchData"><el-icon><Search /></el-icon> 搜索</el-button>
      <el-button type="primary" @click="showTxDialog"><el-icon><Plus /></el-icon> 出入库</el-button>
      <el-tabs v-model="activeTab" style="flex:1;margin-left:16px" @tab-change="fetchData">
        <el-tab-pane label="库存总览" name="summary" />
        <el-tab-pane label="出入库流水" name="transactions" />
      </el-tabs>
    </div>

    <!-- 库存总览 -->
    <div v-if="activeTab==='summary'">
      <div v-if="selectedIds.length" class="batch-bar">
        <el-tag type="info" style="margin-right:8px">已选 {{ selectedIds.length }} 项</el-tag>
        <el-input-number v-model="batchSafetyStock" :min="0" size="small" placeholder="新安全库存" style="width:130px" />
        <el-button size="small" type="primary" @click="batchUpdateSafetyStock" :disabled="!batchSafetyStock">批量更新安全库存</el-button>
        <el-button size="small" @click="selectedIds = []">取消选择</el-button>
      </div>
      <el-table :data="summaryData" v-loading="loading" stripe border
        @selection-change="(rows) => selectedIds = rows.map(r => r.item_id)">
        <el-table-column type="selection" width="40" />
        <el-table-column prop="material_code" label="物料编码" width="130" />
        <el-table-column prop="material_name" label="物料型号" min-width="140" />
        <el-table-column prop="material_type" label="类型" width="70" />
        <el-table-column prop="unit" label="单位" width="60" />
        <el-table-column prop="on_hand" label="现有库存" width="90" />
        <el-table-column label="可用量" width="90">
          <template #default="{row}">
            <span :style="{color:row.available<0?'#f56c6c':row.available<=row.safety_stock?'#e6a23c':'#67c23a',fontWeight:'bold'}">
              {{ row.available }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="safety_stock" label="安全库存" width="90" />
        <el-table-column label="状态" width="70">
          <template #default="{row}">
            <el-tag :type="row.is_low?'danger':'success'" size="small">{{ row.is_low ? '偏低' : '正常' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最近入库" width="150">
          <template #default="{row}">
            <span v-if="row.last_received_date" style="font-size:12px;color:#67c23a">
              +{{ row.last_received_qty }} {{ row.unit }}<br/>
              <span style="color:#909399">{{ row.last_received_date?.slice(0,16) }}</span>
            </span>
            <span v-else style="color:#c0c4cc;font-size:12px">暂无入库</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{row}">
            <el-button size="small" type="success" link @click="quickIn(row)">入库</el-button>
            <el-divider direction="vertical" />
            <el-button size="small" type="danger" link @click="quickOut(row)">出库</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 出入库流水 -->
    <div v-else>
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
        <span style="font-size:13px;color:#999">📋 从采购管理到货的物料会自动入库并显示操作人；手动入库/出库的操作人由操作者填写。</span>
      </div>
      <el-table :data="txData" v-loading="loading" stripe border size="small">
        <el-table-column label="时间" width="145">
          <template #default="{row}">
            <span style="font-size:12px">{{ row.created_at?.slice(0,16)?.replace('T',' ') }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="material_code" label="物料编码" width="120" />
        <el-table-column prop="material_name" label="物料型号" min-width="100" />
        <el-table-column prop="transaction_type" label="类型" width="85">
          <template #default="{row}">
            <el-tag :type="row.transaction_type.includes('出')?'danger':row.transaction_type.includes('采购')?'warning':'success'" size="small">
              {{ row.transaction_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="数量" width="70" align="center">
          <template #default="{row}">
            <span :style="{color:row.quantity>0?'#67c23a':'#f56c6c',fontWeight:'bold',fontSize:'14px'}">
              {{ row.quantity > 0 ? '+' + row.quantity : row.quantity }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="关联单号" width="140">
          <template #default="{row}">
            <el-tag v-if="row.reference_no" type="info" size="small" style="font-size:11px">{{ row.reference_no }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="操作人" width="80" />
        <el-table-column prop="remark" label="备注" min-width="80" />
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

    <!-- 快速入库/出库弹窗 -->
    <el-dialog v-model="quickDialogVisible" :title="quickType==='in'?'快速入库':'快速出库'" width="420px">
      <el-form label-width="90px">
        <el-form-item label="物料">
          <span style="font-weight:bold;font-size:15px">{{ quickForm.material_code }} {{ quickForm.material_name }}</span>
        </el-form-item>
        <el-form-item label="当前库存">
          <el-tag :type="quickForm.on_hand>0?'success':'danger'" size="large">{{ quickForm.on_hand }} {{ quickForm.unit }}</el-tag>
        </el-form-item>
        <el-form-item :label="quickType==='in'?'入库数量':'出库数量'">
          <el-input-number v-model="quickForm.qty" :min="1" :max="quickType==='out'?quickForm.on_hand:99999" 
            size="large" style="width:180px" />
        </el-form-item>
        <el-form-item label="操作人">
          <el-input v-model="quickForm.operator" placeholder="操作人姓名" />
        </el-form-item>
        <el-form-item v-if="quickType==='out'&&quickForm.qty>0" label="出库后库存">
          <span :style="{color:quickForm.on_hand-quickForm.qty<0?'#f56c6c':'#67c23a',fontWeight:'bold',fontSize:'16px'}">
            {{ quickForm.on_hand - quickForm.qty }}
          </span>
        </el-form-item>
        <el-form-item v-if="quickType==='in'&&quickForm.qty>0" label="入库后库存">
          <span style="color:#67c23a;fontWeight:bold;fontSize:16px">
            {{ quickForm.on_hand + quickForm.qty }}
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="quickDialogVisible=false">取消</el-button>
        <el-button :type="quickType==='in'?'success':'danger'" @click="doQuickTx" :loading="quickSaving">
          {{ quickType==='in'?'确认入库':'确认出库' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const activeTab = ref('summary')
const keyword = ref('')

const summaryData = ref([])
const selectedIds = ref([])
const batchSafetyStock = ref(null)

async function batchUpdateSafetyStock() {
  if (!batchSafetyStock.value && batchSafetyStock.value !== 0) return
  await ElMessageBox.confirm(
    `确定将 ${selectedIds.value.length} 个物料的安全库存设为 ${batchSafetyStock.value}？`,
    '批量更新安全库存', { type: 'info' }
  )
  await api.put('/materials/batch/safety-stock', {
    item_ids: selectedIds.value,
    safety_stock: batchSafetyStock.value,
  })
  ElMessage.success(`已更新 ${selectedIds.value.length} 个物料`)
  selectedIds.value = []
  batchSafetyStock.value = null
  fetchData()
}

// 快速入库/出库
const quickDialogVisible = ref(false)
const quickType = ref('in')
const quickSaving = ref(false)
const quickForm = reactive({ item_id: null, material_code: '', material_name: '', unit: '', on_hand: 0, qty: 1, operator: '' })

function quickIn(row) {
  quickType.value = 'in'
  Object.assign(quickForm, {
    item_id: row.item_id, material_code: row.material_code, material_name: row.material_name,
    unit: row.unit, on_hand: row.on_hand || 0, qty: 1, operator: '',
  })
  quickDialogVisible.value = true
}

function quickOut(row) {
  quickType.value = 'out'
  Object.assign(quickForm, {
    item_id: row.item_id, material_code: row.material_code, material_name: row.material_name,
    unit: row.unit, on_hand: row.on_hand || 0, qty: 1, operator: '',
  })
  quickDialogVisible.value = true
}

async function doQuickTx() {
  if (!quickForm.qty || quickForm.qty <= 0) return
  if (quickType.value === 'out' && quickForm.qty > quickForm.on_hand) {
    ElMessage.error('出库数量不能超过现有库存')
    return
  }
  quickSaving.value = true
  try {
    const [whRes] = await Promise.all([api.get('/inventory/warehouses')])
    const whId = whRes.items[0]?.id || 1
    const qty = quickType.value === 'in' ? quickForm.qty : -quickForm.qty
    await api.post('/inventory/transaction', {
      item_id: quickForm.item_id, warehouse_id: whId,
      transaction_type: quickType.value === 'in' ? '入库' : '出库',
      quantity: qty, operator: quickForm.operator,
      remark: quickType.value === 'in' ? '手动入库' : '手动出库',
    })
    ElMessage.success(`${quickType.value==='in'?'入库':'出库'} ${quickForm.qty} ${quickForm.unit}`)
    quickDialogVisible.value = false
    fetchData()
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.message || ''))
  } finally {
    quickSaving.value = false
  }
}

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
    const params = {}
    if (keyword.value) params.keyword = keyword.value
    const res = await api.get('/inventory/summary', { params })
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
.batch-bar {
  display:flex; align-items:center; gap:8px;
  background:#f0f9eb; border:1px solid #b3e19d;
  padding:8px 14px; border-radius:6px; margin-bottom:12px;
}
</style>
