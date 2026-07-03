<template>
  <div class="page-container space-y-4">
    <!-- 工具栏 -->
    <div class="page-toolbar">
      <el-input v-model="keyword" placeholder="搜索物料编码/名称" style="width:240px" clearable @clear="fetchData" @keyup.enter="fetchData">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-tag v-if="keyword" size="small" type="info" effect="plain" closable @close="keyword='';fetchData()" class="ml-1">
        "{{ keyword }}"
      </el-tag>
      <span class="flex-1"></span>
      <el-button type="primary" @click="showDialog()"><el-icon><Plus /></el-icon> 新增物料</el-button>
    </div>

    <!-- 批量操作 -->
    <div v-if="selIds.length" class="batch-bar">
      <el-tag type="info" effect="dark" size="small">已选 {{ selIds.length }} 项</el-tag>
      <div class="flex items-center gap-1.5 text-xs text-[var(--color-text-tertiary)]">
        <span>单价</span>
        <el-input-number v-model="batchPrice" :min="0" size="small" style="width:100px" placeholder="新单价"/>
      </div>
      <el-button size="small" type="primary" @click="batchUpdate('reference_unit_price',batchPrice,'单价')" :disabled="!batchPrice && batchPrice !== 0">更新单价</el-button>
      <div class="w-px h-4 bg-[var(--color-border-light)]"></div>
      <div class="flex items-center gap-1.5 text-xs text-[var(--color-text-tertiary)]">
        <span>提交人</span>
        <el-input v-model="batchSubmitter" size="small" style="width:80px" placeholder="提交人"/>
      </div>
      <el-button size="small" type="primary" @click="batchUpdate('reference_submitter',batchSubmitter,'提交人')" :disabled="!batchSubmitter">更新提交人</el-button>
      <span class="flex-1"></span>
      <el-button size="small" text @click="selIds=[];batchPrice=null;batchSubmitter=''">取消选择</el-button>
    </div>

    <!-- 主体：三级折叠视图 -->
    <div v-loading="loading">
      <div v-if="projects.length" class="space-y-3">
        <div v-for="p in projects" :key="p.product_code" class="proj-card">
          <!-- L1: 产品 -->
          <div class="proj-header" @click="p._open = !p._open">
            <div class="flex items-center gap-2.5 flex-1 min-w-0">
              <span class="font-semibold text-[15px] text-[var(--color-text-primary)]">{{ p.product_name }}</span>
              <span class="text-xs text-[var(--color-text-tertiary)]">{{ p.product_code }}</span>
            </div>
            <div class="flex items-center gap-3">
              <span class="flex items-center gap-1 text-xs text-[var(--color-text-tertiary)]">
                <span class="w-1.5 h-1.5 rounded-sm bg-[var(--color-danger)]"></span>
                {{ p.module_count }} 模块
              </span>
              <span class="flex items-center gap-1 text-xs text-[var(--color-text-tertiary)]">
                <span class="w-1.5 h-1.5 rounded-sm bg-[var(--color-accent)]"></span>
                {{ p.total_parts }} 零件
              </span>
              <el-icon :size="12" color="var(--color-text-tertiary)" class="transition-transform duration-200" :style="{ transform: p._open ? 'rotate(180deg)' : '' }">
                <ArrowDown />
              </el-icon>
            </div>
          </div>

          <!-- L2: 模块列表 -->
          <div v-show="p._open" class="px-3 pb-3 space-y-2">
            <div v-for="m in p.modules" :key="m.module_code" class="mod-card">
              <div class="mod-header" @click="m._open = !m._open">
                <div class="flex items-center gap-2 flex-1 min-w-0">
                  <span class="font-medium text-[var(--color-text-primary)]">{{ m.module_name }}</span>
                  <span class="text-xs text-[var(--color-text-tertiary)]">{{ m.module_code }}</span>
                </div>
                <div class="flex items-center gap-3">
                  <span class="text-xs text-[var(--color-text-tertiary)]">{{ filterParts(m.parts).length }} 项零件</span>
                  <el-icon :size="11" color="var(--color-text-tertiary)" class="transition-transform duration-200" :style="{ transform: m._open ? 'rotate(180deg)' : '' }">
                    <ArrowDown />
                  </el-icon>
                </div>
              </div>

              <!-- L3: 零件表格 -->
              <div v-show="m._open">
                <el-table
                  :data="filterParts(m.parts)"
                  size="small"
                  stripe
                  @selection-change="onSel"
                  max-height="400"
                >
                  <el-table-column type="selection" width="38" />
                  <el-table-column prop="material_code" label="物料编码" width="120" />
                  <el-table-column prop="material_name" label="物料型号" min-width="120" show-overflow-tooltip />
                  <el-table-column prop="specification" label="品牌" width="80" show-overflow-tooltip />
                  <el-table-column prop="unit" label="单位" width="50" align="center" />
                  <el-table-column label="参考单价" width="90" align="right">
                    <template #default="{ row }">
                      <span v-if="row.reference_unit_price > 0" class="tabular-nums">¥{{ row.reference_unit_price.toFixed(2) }}</span>
                      <span v-else class="text-[var(--color-text-disabled)]">—</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="提交人" width="65" align="center">
                    <template #default="{ row }">
                      <span v-if="row.reference_submitter">{{ row.reference_submitter }}</span>
                      <span v-else class="text-[var(--color-text-disabled)]">—</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="安全库存" width="70" align="center" prop="safety_stock" />
                  <el-table-column label="采购件" width="65" align="center">
                    <template #default="{ row }">
                      <el-tag :type="row.is_purchased ? 'success' : 'info'" size="small" effect="dark">
                        {{ row.is_purchased ? '是' : '否' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="提前期" width="65" align="center" prop="lead_time" />
                </el-table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <el-empty v-if="!loading && !projects.length" description="暂无物料数据">
        <el-button type="primary" @click="showDialog()">新增第一个物料</el-button>
      </el-empty>
    </div>

    <!-- ═══ 新增物料对话框 ═══ -->
    <el-dialog v-model="dialogVisible" title="新增物料" width="520px">
      <el-form :model="form" :rules="rules" label-width="80px" label-position="top">
        <el-row :gutter="14">
          <el-col :span="12">
            <el-form-item label="编码" required><el-input v-model="form.material_code" /></el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="名称" required><el-input v-model="form.material_name" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="14">
          <el-col :span="8">
            <el-form-item label="类型">
              <el-select v-model="form.material_type">
                <el-option v-for="t in ['成品', '半成品', '零件', '原材料', '模块']" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="层级">
              <el-select v-model="form.level_type">
                <el-option v-for="t in ['产品', '模块', '零件']" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="单位"><el-input v-model="form.unit" /></el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="14">
          <el-col :span="8">
            <el-form-item label="提前期"><el-input-number v-model="form.lead_time" :min="0" style="width:100%" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="安全库存"><el-input-number v-model="form.safety_stock" :min="0" style="width:100%" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="采购件"><el-switch v-model="form.is_purchased" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="规格"><el-input v-model="form.specification" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const saving = ref(false)
const keyword = ref('')
const projects = ref([])
const selIds = ref([])
const batchPrice = ref(null)
const batchSubmitter = ref('')

function onSel(rows) { selIds.value = rows.map(r => r.id) }

function filterParts(parts) {
  if (!keyword.value) return parts
  const kw = keyword.value.toLowerCase()
  return parts.filter(p =>
    (p.material_code || '').toLowerCase().includes(kw) ||
    (p.material_name || '').toLowerCase().includes(kw)
  )
}

async function batchUpdate(field, value, label) {
  if (!value && value !== 0) return
  try {
    await api.put('/materials/batch/update', { item_ids: selIds.value, fields: { [field]: value } })
    ElMessage.success(`已更新 ${selIds.value.length} 项${label}`)
    selIds.value = []
    batchPrice.value = null
    batchSubmitter.value = ''
    fetchData()
  } catch {}
}

async function fetchData() {
  loading.value = true
  try {
    const res = await api.get('/materials/tree')
    projects.value = (res.projects || []).map(p => ({
      ...p,
      _open: true,
      modules: (p.modules || []).map(m => ({ ...m, _open: false })),
    }))
  } catch {
    projects.value = []
  } finally {
    loading.value = false
  }
}

const dialogVisible = ref(false)
const form = reactive({
  material_code: '', material_name: '', material_type: '原材料',
  level_type: '零件', unit: '个', lead_time: 5, safety_stock: 0,
  is_purchased: true, specification: '',
})
const rules = {
  material_code: [{ required: true, message: '请输入物料编码', trigger: 'blur' }],
  material_name: [{ required: true, message: '请输入物料名称', trigger: 'blur' }],
}

function showDialog() {
  Object.assign(form, {
    material_code: '', material_name: '', material_type: '原材料',
    level_type: '零件', unit: '个', lead_time: 5, safety_stock: 0,
    is_purchased: true, specification: '',
  })
  dialogVisible.value = true
}

async function submitForm() {
  if (!form.material_code || !form.material_name) return ElMessage.warning('请填写编码和名称')
  saving.value = true
  try {
    await api.post('/materials', { ...form })
    ElMessage.success('物料创建成功')
    dialogVisible.value = false
    fetchData()
  } finally {
    saving.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
/* 覆盖旧硬编码颜色为设计 Token */
.page-container { padding: 0; }
</style>
