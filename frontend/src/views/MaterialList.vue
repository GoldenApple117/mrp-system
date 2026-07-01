<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-input v-model="keyword" placeholder="搜索物料编码/名称" style="width:260px" clearable @clear="fetchData" @keyup.enter="fetchData">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="filterType" placeholder="物料类型" style="width:140px" clearable @change="fetchData">
        <el-option label="成品" value="成品" />
        <el-option label="半成品" value="半成品" />
        <el-option label="零件" value="零件" />
        <el-option label="原材料" value="原材料" />
      </el-select>
      <el-select v-model="filterLevelType" placeholder="层级类型" style="width:120px" clearable @change="fetchData">
        <el-option label="产品" value="产品" />
        <el-option label="模块" value="模块" />
        <el-option label="零件" value="零件" />
      </el-select>
      <el-button type="primary" @click="showDialog(null)"><el-icon><Plus /></el-icon> 新增物料</el-button>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedIds.length" class="batch-bar">
      <el-tag type="info" style="margin-right:8px">已选 {{ selectedIds.length }} 项</el-tag>
      <el-button size="small" type="danger" @click="batchDelete">批量停用</el-button>
      <el-button size="small" @click="selectedIds = []">取消选择</el-button>
    </div>

    <el-table :data="tableData" v-loading="loading" stripe border style="width:100%"
      @selection-change="(rows) => selectedIds = rows.map(r => r.id)">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="material_code" label="物料编码" width="170" />
      <el-table-column prop="classification_code" label="分类码" width="120" />
      <el-table-column prop="material_name" label="物料型号" min-width="160" />
      <el-table-column prop="specification" label="规格型号" width="160" />
      <el-table-column prop="unit" label="单位" width="70" />
      <el-table-column prop="material_type" label="类型" width="90">
        <template #default="{row}">
          <el-tag :type="typeTag(row.material_type)" size="small">{{ row.material_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="lead_time" label="提前期(天)" width="100" />
      <el-table-column prop="safety_stock" label="安全库存" width="100" />
      <el-table-column prop="lot_size_rule" label="批量规则" width="90" />
      <el-table-column label="外购/自制" width="90">
        <template #default="{row}">{{ row.is_purchased ? '外购' : '自制' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{row}">
          <el-button link type="primary" size="small" @click="showDialog(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="deleteItem(row)">停用</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10,20,50,100]"
      layout="total,sizes,prev,pager,next"
      @change="fetchData"
      style="margin-top:16px;justify-content:flex-end"
    />

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑物料' : '新增物料'" width="600px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="物料编码" prop="material_code">
              <el-input v-model="form.material_code" :disabled="isEdit" placeholder="留空自动生成" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="物料型号" prop="material_name">
              <el-input v-model="form.material_name" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="分类码">
              <el-input v-model="form.classification_code" placeholder="手动填写分类编码" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="层级类型">
              <el-select v-model="form.level_type">
                <el-option label="产品" value="产品" />
                <el-option label="模块" value="模块" />
                <el-option label="零件" value="零件" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="单位">
              <el-input v-model="form.unit" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="提前期(天)">
              <el-input-number v-model="form.lead_time" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="安全库存">
              <el-input-number v-model="form.safety_stock" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="损耗率(%)">
              <el-input-number v-model="form.scrap_rate" :min="0" :max="100" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="批量规则">
              <el-select v-model="form.lot_size_rule">
                <el-option label="LFL 按需" value="LFL" />
                <el-option label="FOQ 固定批量" value="FOQ" />
                <el-option label="EOQ 经济批量" value="EOQ" />
                <el-option label="MULT 倍数" value="MULT" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="批量数量">
              <el-input-number v-model="form.lot_size_qty" :min="1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="外购/自制">
              <el-switch v-model="form.is_purchased" active-text="外购" inactive-text="自制" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
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
const keyword = ref('')
const filterType = ref('')
const filterLevelType = ref('')

const selectedIds = ref([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const form = reactive({
  material_code: '', classification_code: '', material_name: '', specification: '', unit: '个',
  material_type: '原材料', level_type: '零件', lead_time: 0, safety_stock: 0, scrap_rate: 0,
  lot_size_rule: 'LFL', lot_size_qty: 1, min_order_qty: 0, max_order_qty: 0,
  is_purchased: true, remark: '',
})

const rules = {
  material_name: [{ required: true, message: '请输入物料型号', trigger: 'blur' }],
}

const typeTag = (type) => {
  const map = { '成品': 'danger', '半成品': 'warning', '零件': 'info', '原材料': '' }
  return map[type] || ''
}

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (keyword.value) params.keyword = keyword.value
    if (filterType.value) params.material_type = filterType.value
    if (filterLevelType.value) params.level_type = filterLevelType.value
    const res = await api.get('/materials', { params })
    tableData.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function showDialog(row) {
  if (row) {
    isEdit.value = true
    Object.assign(form, {
      material_code: row.material_code, classification_code: row.classification_code || '',
      material_name: row.material_name,
      specification: row.specification, unit: row.unit, material_type: row.material_type,
      level_type: row.level_type || '零件',
      lead_time: row.lead_time, safety_stock: row.safety_stock, scrap_rate: row.scrap_rate,
      lot_size_rule: row.lot_size_rule, lot_size_qty: row.lot_size_qty,
      min_order_qty: row.min_order_qty, max_order_qty: row.max_order_qty,
      is_purchased: row.is_purchased, remark: row.remark || '',
    })
    form._id = row.id
  } else {
    isEdit.value = false
    resetForm()
  }
  dialogVisible.value = true
}

function resetForm() {
  Object.assign(form, {
    material_code: '', material_name: '', specification: '', unit: '个',
    material_type: '原材料', lead_time: 0, safety_stock: 0, scrap_rate: 0,
    lot_size_rule: 'LFL', lot_size_qty: 1, min_order_qty: 0, max_order_qty: 0,
    is_purchased: true, remark: '', _id: null,
  })
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const data = { ...form }
    delete data._id
    if (isEdit.value) {
      await api.put(`/materials/${form._id}`, data)
      ElMessage.success('更新成功')
    } else {
      await api.post('/materials', data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } finally {
    saving.value = false
  }
}

async function deleteItem(row) {
  await ElMessageBox.confirm(`确定停用物料「${row.material_name}」？`, '提示', { type: 'warning' })
  await api.delete(`/materials/${row.id}`)
  ElMessage.success('已停用')
  fetchData()
}

async function batchDelete() {
  await ElMessageBox.confirm(`确定停用已选的 ${selectedIds.value.length} 个物料？`, '批量停用', { type: 'warning' })
  let count = 0
  for (const id of selectedIds.value) {
    try { await api.delete(`/materials/${id}`); count++ } catch {}
  }
  ElMessage.success(`已停用 ${count} 个物料`)
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
