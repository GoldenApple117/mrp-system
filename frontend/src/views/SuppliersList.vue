<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-input v-model="keyword" placeholder="搜索供应商" style="width:240px" clearable 
        @clear="fetchData" @keyup.enter="fetchData">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button type="primary" @click="search"><el-icon><Search /></el-icon> 搜索</el-button>
      <span style="flex:1"></span>
      <el-button type="primary" @click="showDialog(null)"><el-icon><Plus /></el-icon> 新增供应商</el-button>
    </div>

    <el-table :data="tableData" v-loading="loading" stripe border>
      <el-table-column prop="supplier_code" label="编码" width="140" />
      <el-table-column prop="supplier_name" label="供应商名称" min-width="140" />
      <el-table-column label="购买链接" min-width="200">
        <template #default="{row}">
          <a v-if="row.purchase_link" :href="row.purchase_link" target="_blank" 
            style="color:#409eff;font-size:12px;word-break:break-all">{{ row.purchase_link }}</a>
          <span v-else style="color:#c0c4cc;font-size:12px">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="contact_person" label="联系人" width="100" />
      <el-table-column prop="contact_phone" label="联系电话" width="140" />
      <el-table-column prop="address" label="地址" min-width="180" />
      <el-table-column prop="lead_time_days" label="交期(天)" width="90" align="center" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{row}">
          <el-button link type="primary" size="small" @click="showDialog(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="deleteSupplier(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total"
      layout="total,prev,pager,next" @change="fetchData" style="margin-top:16px;justify-content:flex-end" />

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editId?'编辑供应商':'新增供应商'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="编码" prop="supplier_code">
              <el-input v-model="form.supplier_code" :disabled="!!editId" placeholder="如: SUP-三菱" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="名称" prop="supplier_name">
              <el-input v-model="form.supplier_name" placeholder="如: 三菱电机" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="联系人">
              <el-input v-model="form.contact_person" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话">
              <el-input v-model="form.contact_phone" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="地址">
          <el-input v-model="form.address" />
        </el-form-item>
        <el-form-item label="购买链接">
          <el-input v-model="form.purchase_link" placeholder="如: https://item.taobao.com/item..." />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="交期(天)">
              <el-input-number v-model="form.lead_time_days" :min="0" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="备注">
              <el-input v-model="form.remark" />
            </el-form-item>
          </el-col>
        </el-row>
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
const keyword = ref('')

const dialogVisible = ref(false)
const editId = ref(null)
const formRef = ref(null)
const form = reactive({
  supplier_code: '', supplier_name: '', contact_person: '',
  contact_phone: '', address: '', lead_time_days: 0, remark: '',
  purchase_link: '',
})
const rules = {
  supplier_code: [{ required: true, message: '请输入编码' }],
  supplier_name: [{ required: true, message: '请输入名称' }],
}

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (keyword.value) params.keyword = keyword.value
    const res = await api.get('/purchase/suppliers', { params })
    tableData.value = res.items; total.value = res.total
  } finally { loading.value = false }
}

function search() { page.value = 1; fetchData() }

function showDialog(row) {
  if (row) {
    editId.value = row.id
    Object.assign(form, {
      supplier_code: row.supplier_code, supplier_name: row.supplier_name,
      contact_person: row.contact_person || '', contact_phone: row.contact_phone || '',
      address: row.address || '', lead_time_days: row.lead_time_days || 0, remark: row.remark || '',
    })
  } else {
    editId.value = null
    Object.assign(form, {
      supplier_code: '', supplier_name: '', contact_person: '',
      contact_phone: '', address: '', lead_time_days: 0, remark: '',
    })
  }
  dialogVisible.value = true
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editId.value) {
      await api.put(`/purchase/suppliers/${editId.value}`, { ...form })
      ElMessage.success('已更新')
    } else {
      await api.post('/purchase/suppliers', { ...form })
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    fetchData()
  } finally { saving.value = false }
}

async function deleteSupplier(row) {
  await ElMessageBox.confirm(`确定删除供应商「${row.supplier_name}」？`, '提示', { type: 'warning' })
  await api.delete(`/purchase/suppliers/${row.id}`)
  ElMessage.success('已删除')
  fetchData()
}

onMounted(fetchData)
</script>

<style scoped>
.page-container { padding: 0;; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; }
</style>
