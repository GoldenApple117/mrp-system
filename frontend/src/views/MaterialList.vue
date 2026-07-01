<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-input v-model="keyword" placeholder="搜索物料编码/名称" style="width:240px" clearable @clear="onSearch" @keyup.enter="onSearch">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button type="primary" @click="showDialog(null)"><el-icon><Plus /></el-icon> 新增物料</el-button>
    </div>

    <div v-loading="loading">
      <div v-for="p in projects" :key="p.product_code" class="proj-card">
        <div class="proj-header" @click="p._open=!p._open">
          <span style="font-weight:600;font-size:15px">{{ p.product_name }}</span>
          <el-tag size="small" type="danger" style="margin:0 8px">{{ p.module_count }}模块</el-tag>
          <span style="font-size:12px;color:#999">{{ p.total_parts }}零件</span>
          <span style="margin-left:auto;color:#999">{{ p._open?'▲':'▼' }}</span>
        </div>
        <div v-show="p._open" style="padding:0 12px 8px">
          <div v-for="m in p.modules" :key="m.module_code" class="mod-card">
            <div class="mod-header" @click="m._open=!m._open">
              <span style="font-weight:500">{{ m.module_name }}</span>
              <el-tag size="small" style="margin:0 6px">{{ filterParts(m.parts).length }}项</el-tag>
              <span style="margin-left:auto;color:#999;font-size:12px">{{ m._open?'▲':'▼' }}</span>
            </div>
            <div v-show="m._open">
              <el-table :data="filterParts(m.parts)" size="small" stripe border>
                <el-table-column prop="material_code" label="物料编码" width="120" />
                <el-table-column prop="material_name" label="物料型号" min-width="130" show-overflow-tooltip />
                <el-table-column prop="specification" label="品牌/规格" width="100" show-overflow-tooltip />
                <el-table-column prop="unit" label="单位" width="60" />
                <el-table-column label="参考单价" width="90" align="right">
                  <template #default="{row}"><span v-if="row.reference_unit_price>0">¥{{ row.reference_unit_price }}</span><span v-else style="color:#c0c4cc">—</span></template>
                </el-table-column>
                <el-table-column label="安全库存" width="80" align="center" prop="safety_stock" />
                <el-table-column label="采购件" width="65" align="center">
                  <template #default="{row}"><el-tag :type="row.is_purchased?'success':'info'" size="small">{{ row.is_purchased?'是':'否' }}</el-tag></template>
                </el-table-column>
                <el-table-column label="提前期" width="65" align="center" prop="lead_time" />
              </el-table>
            </div>
          </div>
        </div>
      </div>
      <el-empty v-if="!loading && !projects.length" description="暂无物料数据" />
    </div>

    <el-dialog v-model="dialogVisible" title="新增物料" width="520px">
      <el-form :model="form" :rules="rules" label-width="90px">
        <el-row :gutter="16"><el-col :span="12"><el-form-item label="编码" required><el-input v-model="form.material_code" /></el-form-item></el-col><el-col :span="12"><el-form-item label="名称" required><el-input v-model="form.material_name" /></el-form-item></el-col></el-row>
        <el-row :gutter="16"><el-col :span="8"><el-form-item label="类型"><el-select v-model="form.material_type"><el-option v-for="t in ['成品','半成品','零件','原材料','模块']" :key="t" :label="t" :value="t" /></el-select></el-form-item></el-col><el-col :span="8"><el-form-item label="层级"><el-select v-model="form.level_type"><el-option v-for="t in ['产品','模块','零件']" :key="t" :label="t" :value="t" /></el-select></el-form-item></el-col><el-col :span="8"><el-form-item label="单位"><el-input v-model="form.unit" /></el-form-item></el-col></el-row>
        <el-row :gutter="16"><el-col :span="8"><el-form-item label="提前期"><el-input-number v-model="form.lead_time" :min="0" style="width:100%" /></el-form-item></el-col><el-col :span="8"><el-form-item label="安全库存"><el-input-number v-model="form.safety_stock" :min="0" style="width:100%" /></el-form-item></el-col><el-col :span="8"><el-form-item label="采购件"><el-switch v-model="form.is_purchased" /></el-form-item></el-col></el-row>
        <el-form-item label="规格"><el-input v-model="form.specification" /></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" :loading="saving" @click="submitForm">保存</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const loading = ref(false); const saving = ref(false); const keyword = ref('')
const projects = ref([])

async function loadData() {
  loading.value = true
  try {
    const res = await api.get('/materials/tree')
    projects.value = (res.projects || []).map(p => ({
      ...p, _open: true,
      modules: p.modules.map(m => ({ ...m, _open: false }))
    }))
  } finally { loading.value = false }
}

function filterParts(parts) {
  if (!keyword.value) return parts
  const kw = keyword.value.toLowerCase()
  return parts.filter(p => (p.material_code||'').toLowerCase().includes(kw) || (p.material_name||'').toLowerCase().includes(kw))
}
function onSearch() { loadData() }

const dialogVisible = ref(false)
const form = reactive({ material_code:'', material_name:'', material_type:'原材料', level_type:'零件', unit:'个', lead_time:5, safety_stock:0, is_purchased:true, specification:'' })
const rules = { material_code:[{required:true}], material_name:[{required:true}] }
function showDialog() { dialogVisible.value = true }
async function submitForm() {
  if (!form.material_code||!form.material_name) return ElMessage.warning('请填写编码和名称')
  saving.value = true
  try { await api.post('/materials', {...form}); ElMessage.success('创建成功'); dialogVisible.value = false; loadData() }
  finally { saving.value = false }
}

onMounted(loadData)
</script>

<style scoped>
.page-container { background:#fff; padding:20px; border-radius:8px }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center }
.proj-card { border:1px solid #e4e7ed; border-radius:8px; margin-bottom:12px; overflow:hidden }
.proj-header { display:flex; align-items:center; padding:12px 16px; background:#fafbfc; cursor:pointer; user-select:none; border-bottom:1px solid #ebeef5 }
.proj-header:hover { background:#f0f5ff }
.mod-card { border:1px solid #f0f0f0; border-radius:6px; margin:8px 0; overflow:hidden }
.mod-header { display:flex; align-items:center; padding:8px 12px; background:#fafbfc; cursor:pointer; user-select:none }
.mod-header:hover { background:#f5f7fa }
</style>
