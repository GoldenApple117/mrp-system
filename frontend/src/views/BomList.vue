<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-button type="primary" @click="showBomDialog(null)"><el-icon><Plus /></el-icon> 新建BOM</el-button>
      <el-upload
        :show-file-list="false"
        :before-upload="handleExcelUpload"
        accept=".xlsx,.xls"
        action="#"
      >
        <el-button type="success"><el-icon><Upload /></el-icon> 导入Excel BOM</el-button>
      </el-upload>
      <el-button @click="downloadTemplate"><el-icon><Download /></el-icon> 下载模板</el-button>
      <span style="flex:1"></span>
      <el-select v-model="filterStatus" placeholder="状态筛选" style="width:120px" clearable @change="fetchData">
        <el-option label="草稿" value="草稿" />
        <el-option label="生效" value="生效" />
        <el-option label="失效" value="失效" />
      </el-select>
    </div>

    <el-table :data="tableData" v-loading="loading" stripe border @row-click="showBomTree" style="cursor:pointer">
      <el-table-column prop="bom_code" label="BOM编号" width="150" />
      <el-table-column prop="product_code" label="成品编码" width="130" />
      <el-table-column prop="product_name" label="成品名称" min-width="160" />
      <el-table-column prop="version" label="版本" width="80" />
      <el-table-column label="状态" width="90">
        <template #default="{row}">
          <el-tag :type="row.status==='生效'?'success':row.status==='草稿'?'':'danger'" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="effective_date" label="生效日期" width="120" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{row}">
          <el-button link type="primary" size="small" @click.stop="showBomTree(row)">查看</el-button>
          <el-button link type="success" size="small" @click.stop="activateBom(row)" v-if="row.status!=='生效'">生效</el-button>
          <el-button link type="danger" size="small" @click.stop="deleteBom(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total"
      :page-sizes="[10,20,50]" layout="total,sizes,prev,pager,next" @change="fetchData" style="margin-top:16px;justify-content:flex-end" />

    <!-- BOM树形弹窗 -->
    <el-dialog v-model="treeVisible" title="BOM 树形结构" width="800px">
      <div v-if="treeData">
        <el-alert :title="`${treeData.product_code} ${treeData.product_name} [${treeData.version}]`" type="info" :closable="false" style="margin-bottom:12px" />
        <el-tree :data="buildTree(treeData.nodes)" :props="treeProps" node-key="id" default-expand-all highlight-current>
          <template #default="{node,data}">
            <span style="display:flex;align-items:center;gap:8px;font-size:14px">
              <el-tag size="small" :type="node.level===0?'danger':node.level===1?'warning':'info'">L{{ node.level }}</el-tag>
              <strong>{{ data.material_code }}</strong>
              <span>{{ data.material_name }}</span>
              <el-tag size="small" type="success" effect="plain">x{{ data.quantity }}</el-tag>
              <span v-if="data.position" style="color:#999">位号:{{ data.position }}</span>
              <el-tag v-if="data.is_substitute" size="small" type="danger" effect="plain">替代料</el-tag>
            </span>
          </template>
        </el-tree>
      </div>
      <el-empty v-else description="暂无BOM数据" />
    </el-dialog>

    <!-- Excel导入结果 -->
    <el-dialog v-model="importResultVisible" title="导入结果" width="500px">
      <el-result :icon="importSuccess ? 'success' : 'error'" :title="importMessage">
        <template #extra v-if="importErrors.length">
          <div style="max-height:200px;overflow-y:auto;text-align:left">
            <p v-for="(e,i) in importErrors" :key="i" style="color:#e6a23c;font-size:13px">{{ e }}</p>
          </div>
        </template>
      </el-result>
    </el-dialog>

    <!-- 新建BOM弹窗 -->
    <el-dialog v-model="bomDialogVisible" title="新建BOM" width="650px">
      <el-form ref="bomFormRef" :model="bomForm" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="BOM编号" required>
              <el-input v-model="bomForm.bom_code" placeholder="如: BOM-FG-001" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="成品物料" required>
              <el-select v-model="bomForm.product_id" filterable placeholder="选择成品" style="width:100%">
                <el-option v-for="m in productOptions" :key="m.id" :label="`${m.material_code} ${m.material_name}`" :value="m.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="版本">
              <el-input v-model="bomForm.version" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="状态">
              <el-select v-model="bomForm.status">
                <el-option label="草稿" value="草稿" />
                <el-option label="生效" value="生效" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="生效日期">
              <el-date-picker v-model="bomForm.effective_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="BOM明细">
          <el-table :data="bomForm.lines" stripe border size="small" style="width:100%">
            <el-table-column label="父物料" width="160">
              <template #default="{row,$index}">
                <el-select v-model="row.parent_item_id" filterable clearable placeholder="(空=顶层)" style="width:140px">
                  <el-option v-for="m in productOptions" :key="m.id" :label="m.material_code" :value="m.id" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="子物料" width="160">
              <template #default="{row,$index}">
                <el-select v-model="row.item_id" filterable placeholder="必选" style="width:140px">
                  <el-option v-for="m in allMatOptions" :key="m.id" :label="m.material_code" :value="m.id" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="用量" width="80">
              <template #default="{row}"><el-input-number v-model="row.quantity" :min="1" size="small" /></template>
            </el-table-column>
            <el-table-column label="位号" width="70">
              <template #default="{row}"><el-input v-model="row.position" size="small" /></template>
            </el-table-column>
            <el-table-column label="操作" width="60">
              <template #default="{row,$index}">
                <el-button link type="danger" size="small" @click="bomForm.lines.splice($index,1)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-button size="small" style="margin-top:8px" @click="bomForm.lines.push({parent_item_id:null,item_id:null,quantity:1,position:''})">
            添加行
          </el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bomDialogVisible=false">取消</el-button>
        <el-button type="primary" @click="submitBom" :loading="savingBom">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterStatus = ref('')

const treeVisible = ref(false)
const treeData = ref(null)
const treeProps = { children: 'children', label: 'material_name' }

const importResultVisible = ref(false)
const importSuccess = ref(false)
const importMessage = ref('')
const importErrors = ref([])

const bomDialogVisible = ref(false)
const savingBom = ref(false)
const bomFormRef = ref(null)
const productOptions = ref([])
const allMatOptions = ref([])
const bomForm = ref({
  bom_code: '', product_id: null, version: 'A', status: '草稿',
  effective_date: '', lines: [{ parent_item_id: null, item_id: null, quantity: 1, position: '' }],
})

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterStatus.value) params.status = filterStatus.value
    const res = await api.get('/bom/headers', { params })
    tableData.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function showBomTree(row) {
  try {
    const res = await api.get(`/bom/tree/${row.product_id}`)
    treeData.value = res.tree
    treeVisible.value = true
  } catch {
    ElMessage.error('获取BOM树失败')
  }
}

function buildTree(nodes) {
  if (!nodes) return []
  const map = {}
  const roots = []
  nodes.forEach(n => { map[n.item_id] = { ...n, children: [] } })
  nodes.forEach(n => {
    if (n.parent_item_id && map[n.parent_item_id]) {
      map[n.parent_item_id].children.push(map[n.item_id])
    } else if (!n.parent_item_id) {
      roots.push(map[n.item_id])
    }
  })
  return roots
}

async function handleExcelUpload(file) {
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await api.post('/bom/import/excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    importSuccess.value = res.success
    importMessage.value = res.message
    importErrors.value = res.errors || []
    importResultVisible.value = true
    if (res.success) fetchData()
  } catch {
    ElMessage.error('导入失败')
  }
  return false
}

async function downloadTemplate() {
  ElMessage.info('模板已生成在后端 uploads 目录: BOM导入模板.xlsx')
  window.open('/uploads/BOM导入模板.xlsx')
}

async function activateBom(row) {
  await api.put(`/bom/headers/${row.id}`, { status: '生效' })
  ElMessage.success('BOM已生效')
  fetchData()
}

async function deleteBom(row) {
  await ElMessageBox.confirm('确定删除该BOM？', '提示', { type: 'warning' })
  await api.delete(`/bom/headers/${row.id}`)
  ElMessage.success('已删除')
  fetchData()
}

async function showBomDialog(row) {
  const [proRes, allRes] = await Promise.all([
    api.get('/materials/all', { params: { material_type: '成品' } }),
    api.get('/materials/all'),
  ])
  productOptions.value = proRes.items || []
  allMatOptions.value = allRes.items || []
  bomForm.value = {
    bom_code: `BOM-${Date.now()}`.slice(0, 18),
    product_id: null, version: 'A', status: '草稿',
    effective_date: new Date().toISOString().slice(0, 10),
    lines: [{ parent_item_id: null, item_id: null, quantity: 1, position: '' }],
  }
  bomDialogVisible.value = true
}

async function submitBom() {
  if (!bomForm.value.product_id || !bomForm.value.bom_code) {
    return ElMessage.warning('请填写BOM编号和成品物料')
  }
  savingBom.value = true
  try {
    const lines = bomForm.value.lines.filter(l => l.item_id)
    if (!lines.length) return ElMessage.warning('请添加至少一行BOM明细')
    await api.post('/bom/headers', { ...bomForm.value, lines })
    ElMessage.success('BOM创建成功')
    bomDialogVisible.value = false
    fetchData()
  } finally { savingBom.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.page-container { background:#fff; padding:20px; border-radius:8px; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; }
</style>
