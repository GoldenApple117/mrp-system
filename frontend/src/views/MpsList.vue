<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-button type="primary" @click="showDialog(null)"><el-icon><Plus /></el-icon> 添加计划</el-button>
      <el-button @click="showBatchDialog"><el-icon><List /></el-icon> 批量添加</el-button>
      <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期"
        value-format="YYYY-MM-DD" style="width:280px" @change="fetchData" />
      <span style="color:#909399;font-size:13px">提示：MPS只需录入成品计划，MRP引擎会自动展开到所有物料</span>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedIds.length" class="batch-bar">
      <el-tag type="info" style="margin-right:8px">已选 {{ selectedIds.length }} 项</el-tag>
      <el-button size="small" type="danger" @click="batchDelete">批量删除</el-button>
      <el-button size="small" @click="selectedIds = []">取消选择</el-button>
    </div>

    <el-table :data="tableData" v-loading="loading" stripe border
      @selection-change="(rows) => selectedIds = rows.map(r => r.id)">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="material_code" label="成品编码" width="130" />
      <el-table-column prop="material_name" label="成品名称" min-width="160" />
      <el-table-column prop="unit" label="单位" width="70" />
      <el-table-column prop="plan_date" label="计划日期" width="120" />
      <el-table-column prop="quantity" label="计划数量" width="110" />
      <el-table-column prop="source_type" label="来源" width="100">
        <template #default="{row}">
          <el-tag size="small">{{ row.source_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="source_id" label="销售订单号" width="150" />
      <el-table-column label="状态" width="90">
        <template #default="{row}">
          <el-tag :type="row.status==='已完成'?'success':'warning'" size="small">{{ row.status||'进行中' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="冻结" width="80">
        <template #default="{row}">
          <el-tag :type="row.is_frozen?'warning':'info'" size="small">{{ row.is_frozen?'已冻结':'正常' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{row}">
          <el-button link type="primary" size="small" @click="showDialog(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="deleteItem(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total"
      layout="total,sizes,prev,pager,next" @change="fetchData" style="margin-top:16px;justify-content:flex-end" />

    <!-- 批量添加弹窗 -->
    <el-dialog v-model="batchDialogVisible" title="批量添加MPS(每周一条)" width="520px">
      <el-form label-width="100px">
        <el-form-item label="成品物料" required>
          <el-select v-model="batchForm.item_id" filterable placeholder="选择成品" style="width:100%">
            <el-option v-for="m in productOptions" :key="m.id" :label="`${m.material_code} ${m.material_name}`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="开始日期" required>
              <el-date-picker v-model="batchForm.start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期" required>
              <el-date-picker v-model="batchForm.end_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="每周数量">
          <el-input-number v-model="batchForm.weekly_qty" :min="1" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible=false">取消</el-button>
        <el-button type="primary" @click="submitBatch">生成</el-button>
      </template>
    </el-dialog>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit?'编辑计划':'添加计划'" width="450px">
      <el-alert v-if="form.source_type==='销售订单' && isEdit" type="info" :closable="false" show-icon
        title="此计划关联销售订单，修改数量/日期将自动同步到对应订单" style="margin-bottom:12px" />
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="成品物料" prop="item_id">
          <el-select v-model="form.item_id" filterable placeholder="选择成品" style="width:100%">
            <el-option v-for="m in productOptions" :key="m.id" :label="`${m.material_code} ${m.material_name}`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划日期" prop="plan_date">
          <el-date-picker v-model="form.plan_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="计划数量" prop="quantity">
          <el-input-number v-model="form.quantity" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="form.source_type">
            <el-option label="手动" value="手动" />
            <el-option label="销售订单" value="销售订单" />
            <el-option label="预测" value="预测" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源单号">
          <el-input v-model="form.source_id" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="saving">保存</el-button>
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
const dateRange = ref([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const form = reactive({
  item_id: null, plan_date: '', quantity: 0,
  source_type: '手动', source_id: '',
})
const rules = {
  item_id: [{ required: true, message: '请选择成品' }],
  plan_date: [{ required: true, message: '请选择日期' }],
  quantity: [{ required: true, message: '请输入数量' }],
}

const productOptions = ref([])
const selectedIds = ref([])
const batchDialogVisible = ref(false)
const batchForm = reactive({
  item_id: null, start_date: '', end_date: '', weekly_qty: 100,
  source_type: '手动',
})

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await api.get('/mps', { params })
    tableData.value = res.items
    total.value = res.total
  } finally { loading.value = false }
}

async function showDialog(row) {
  const res = await api.get('/materials/all', { params: { material_type: '成品' } })
  productOptions.value = res.items

  if (row) {
    isEdit.value = true
    Object.assign(form, {
      item_id: row.item_id, plan_date: row.plan_date, quantity: row.quantity,
      source_type: row.source_type, source_id: row.source_id,
    })
    form._id = row.id
  } else {
    isEdit.value = false
    Object.assign(form, { item_id: null, plan_date: '', quantity: 0, source_type: '手动', source_id: '', _id: null })
  }
  dialogVisible.value = true
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const data = { item_id: form.item_id, plan_date: form.plan_date, quantity: form.quantity, source_type: form.source_type, source_id: form.source_id }
    if (isEdit.value) {
      await api.put(`/mps/${form._id}`, data)
    } else {
      await api.post('/mps', data)
    }
    ElMessage.success(isEdit.value ? '更新成功' : '添加成功')
    dialogVisible.value = false
    fetchData()
  } finally { saving.value = false }
}

async function deleteItem(row) {
  await ElMessageBox.confirm('确定删除该计划？', '提示', { type: 'warning' })
  await api.delete(`/mps/${row.id}`)
  ElMessage.success('已删除')
  fetchData()
}

async function showBatchDialog() {
  const res = await api.get('/materials/all', { params: { material_type: '成品' } })
  productOptions.value = res.items
  Object.assign(batchForm, { item_id: null, start_date: '', end_date: '', weekly_qty: 100, source_type: '手动' })
  batchDialogVisible.value = true
}

async function submitBatch() {
  if (!batchForm.item_id || !batchForm.start_date || !batchForm.end_date) {
    return ElMessage.warning('请选择成品、开始日期和结束日期')
  }
  const entries = []
  let d = new Date(batchForm.start_date)
  const end = new Date(batchForm.end_date)
  while (d <= end) {
    entries.push({
      item_id: batchForm.item_id,
      plan_date: d.toISOString().slice(0, 10),
      quantity: batchForm.weekly_qty,
      source_type: batchForm.source_type,
    })
    d.setDate(d.getDate() + 7)
  }
  await api.post('/mps/batch', { entries })
  ElMessage.success(`已创建 ${entries.length} 条MPS计划`)
  batchDialogVisible.value = false
  fetchData()
}

async function batchDelete() {
  await ElMessageBox.confirm(`确定删除已选的 ${selectedIds.value.length} 条计划？`, '批量删除', { type: 'warning' })
  let count = 0
  for (const id of selectedIds.value) {
    try { await api.delete(`/mps/${id}`); count++ } catch {}
  }
  ElMessage.success(`已删除 ${count} 条`)
  selectedIds.value = []
  fetchData()
}

onMounted(fetchData)
</script>

<style scoped>
.page-container { background:#fff; padding:20px; border-radius:8px; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; flex-wrap:wrap; }
.batch-bar { display:flex; align-items:center; padding:8px 12px; background:#fef0f0; border-radius:6px; margin-bottom:12px; gap:8px; }
</style>
