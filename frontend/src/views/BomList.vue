<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-button type="primary" @click="showBomDialog(null)"><el-icon><Plus /></el-icon> 新建BOM</el-button>
      <el-button type="success" @click="showImportDialog"><el-icon><UploadFilled /></el-icon> 导入BOM</el-button>
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

    <!-- BOM树形弹窗（可编辑 — 三级折叠视图） -->
    <el-dialog v-model="treeVisible" :title="treeData ? `${treeData.product_code} ${treeData.product_name} BOM编辑` : 'BOM 树形结构'" width="900px" @close="editingId=null">
      <div v-if="treeData">
        <div style="display:flex;align-items:center;margin-bottom:12px">
          <el-alert :title="`${treeData.product_code} ${treeData.product_name} [${treeData.version}]`" type="info" :closable="false" style="flex:1" />
          <el-button type="primary" size="small" style="margin-left:12px" @click="showAddPart"><el-icon><Plus /></el-icon> 添加零件</el-button>
        </div>

        <!-- 产品根节点 -->
        <div class="bom-proj-card">
          <div class="bom-proj-header" @click="rootOpen=!rootOpen">
            <span style="font-weight:600;font-size:15px">{{ treeData.product_code }} {{ treeData.product_name }}</span>
            <el-tag size="small" type="danger" style="margin:0 8px">{{ bomModules.length }}个模块</el-tag>
            <el-tag size="small" type="info" style="margin:0 8px">{{ bomModules.reduce((s,m)=>s+(m.parts?.length||0),0) }}个零件</el-tag>
            <span style="margin-left:auto;color:#999">{{ rootOpen?'▲':'▼' }}</span>
          </div>

          <!-- 模块层 -->
          <div v-show="rootOpen" style="padding:0 12px 8px">
            <div v-for="m in bomModules" :key="m.module_code" class="bom-mod-card">
              <div class="bom-mod-header" @click="toggleModule(m.module_code)">
                <span style="font-weight:500">{{ m.module_name }}</span>
                <el-tag size="small" style="margin:0 6px">{{ m.parts?.length || 0 }}项</el-tag>
                <span style="margin-left:auto;color:#999;font-size:12px">{{ m._open?'▲':'▼' }}</span>
              </div>
              <div v-show="m._open">
                <el-table :data="m.parts||[]" size="small" stripe border>
                  <el-table-column prop="material_code" label="编码" width="120" />
                  <el-table-column prop="material_name" label="型号" min-width="120" show-overflow-tooltip />
                  <el-table-column label="用量" width="90" align="center">
                    <template #default="{row}">
                      <span v-if="editingId!==row.line_id" @click="startEditQty(row)" style="cursor:pointer;text-decoration:underline dashed #409eff">{{ row.quantity }}</span>
                      <span v-else style="display:flex;gap:4px;justify-content:center">
                        <el-input-number v-model="editQty" :min="0.001" size="small" style="width:65px" controls-position="right" />
                        <el-button size="small" type="primary" @click="saveQty(row)">✓</el-button>
                        <el-button size="small" @click="editingId=null">✕</el-button>
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column label="位号" width="85">
                    <template #default="{row}">
                      <span v-if="editingPosId!==row.line_id" @click="startEditPos(row)" style="cursor:pointer;text-decoration:underline dashed #409eff">{{ row.position || '—' }}</span>
                      <span v-else style="display:flex;gap:4px">
                        <el-input v-model="editPos" size="small" style="width:60px" />
                        <el-button size="small" type="primary" @click="savePos(row)">✓</el-button>
                        <el-button size="small" @click="editingPosId=null">✕</el-button>
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="80" fixed="right">
                    <template #default="{row}">
                      <el-button link type="danger" size="small" @click="deleteLine(row)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无BOM数据" />
    </el-dialog>

    <!-- 添加零件弹窗 -->
    <el-dialog v-model="addPartVisible" title="选择零件加入BOM" width="500px" append-to-body>
      <el-input v-model="searchPart" placeholder="搜索物料编码或型号" clearable style="margin-bottom:12px" @keyup.enter="searchParts">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button type="primary" size="small" @click="searchParts" style="margin-bottom:8px">搜索</el-button>
      <el-table :data="filteredParts.slice(0,15)" stripe border size="small" max-height="300" @row-click="confirmAddPart" style="cursor:pointer">
        <el-table-column prop="material_code" label="编码" width="120" />
        <el-table-column prop="material_name" label="型号" min-width="120" />
        <el-table-column prop="level_type" label="类型" width="60" />
      </el-table>
      <el-empty v-if="!filteredParts.length" description="输入关键词搜索物料" />
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

    <!-- ====== 导入BOM弹窗 ====== -->
    <el-dialog v-model="importDialogVisible" title="导入BOM" width="640px" @close="resetImport">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:16px;font-size:13px;">
        支持 Multi-Sheet Excel 文件（.xlsx / .xls）—— 每个 Sheet 自动作为一个模块，一键创建产品→模块→零件三层 BOM 结构。
        <a href="javascript:void(0)" @click="showCloudGuide = !showCloudGuide" style="color:#409eff;margin-left:4px;">从云端文档导入？</a>
      </el-alert>

      <!-- 云端文档导入指引（可折叠） -->
      <div v-if="showCloudGuide" style="background:#f0f9ff;border-radius:8px;padding:12px 16px;margin-bottom:16px;font-size:13px;line-height:1.8;">
        <el-input v-model="cloudLink" placeholder="粘贴金山文档 / WPS / 腾讯文档等分享链接" clearable @input="identifyLink" style="margin-bottom:8px">
          <template #prefix><el-icon><Link /></el-icon></template>
        </el-input>
        <div v-if="identified.platform" style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
          <span style="font-size:20px">{{ identified.icon }}</span>
          <span style="font-weight:500">{{ identified.platform }}</span>
        </div>
        <div v-for="(step,si) in identified.steps" :key="si" style="display:flex;align-items:flex-start;gap:8px;margin:4px 0;">
          <span style="background:#409eff;color:#fff;border-radius:50%;width:20px;height:20px;display:inline-flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0;">{{ si+1 }}</span>
          <span>{{ step }}</span>
        </div>
      </div>

      <!-- 产品编码/名称（可选） -->
      <el-form :model="importOpts" label-width="90px" style="margin-bottom:12px;">
        <el-form-item label="产品编码">
          <el-input v-model="importOpts.product_code" placeholder="留空自动生成" />
        </el-form-item>
        <el-form-item label="产品名称">
          <el-input v-model="importOpts.product_name" placeholder="留空使用文件名" />
        </el-form-item>
      </el-form>

      <!-- Excel 上传 -->
      <el-upload ref="uploadRef" :auto-upload="false" :limit="1" accept=".xlsx,.xls" :on-change="onFileChange" drag>
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div style="margin:8px 0">将 Excel 文件拖到此处，或<em>点击选择</em></div>
        <template #tip>
          <div style="color:#999;font-size:12px;line-height:1.6;">
            每个 Sheet &rarr; 一个模块，自动识别列名（编码/名称/规格/数量）。
            <br>支持单 Sheet 扁平 BOM、多 Sheet 模块化 BOM。
          </div>
        </template>
      </el-upload>
      <div v-if="importFile" style="margin-top:8px;padding:8px 12px;background:#f0f9ff;border-radius:6px;color:#409eff;display:flex;align-items:center;gap:8px;">
        <el-icon><Document /></el-icon> {{ importFile.name }}
      </div>

      <!-- 导入结果 -->
      <div v-if="importResult" :style="{marginTop:'12px',padding:'12px 16px',borderRadius:'8px',fontSize:'13px',lineHeight:'1.6',background:importResult.success?'#f0f9eb':'#fef0f0',color:importResult.success?'#67c23a':'#f56c6c'}">
        <div style="font-weight:500;">{{ importResult.success ? '✅ 导入成功' : '❌ 导入失败' }}</div>
        <div style="margin-top:4px;white-space:pre-wrap;">{{ importResult.message }}</div>
      </div>

      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitImport" :loading="importLoading">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
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

// ====== BOM树形编辑（三级折叠视图） ======
const editingId = ref(null); const editQty = ref(1)
const editingPosId = ref(null); const editPos = ref('')
const addPartVisible = ref(false); const searchPart = ref('')
const allPartOptions = ref([]); const filteredParts = ref([])
const rootOpen = ref(true)
const openModules = ref(new Set())  // 追踪哪些模块展开了

async function showBomTree(row) {
  try {
    const res = await api.get(`/bom/tree/${row.product_id}`)
    treeData.value = res.tree
    rootOpen.value = true
    // 默认展开所有模块
    const nodes = res.tree?.nodes || []
    nodes.filter(n => n.depth === 1).forEach(m => openModules.value.add(m.material_code))
    treeVisible.value = true
  } catch {
    ElMessage.error('获取BOM树失败')
  }
}

// 将树节点重组为模块→零件二级折叠结构
const bomModules = computed(() => {
  if (!treeData.value?.nodes) return []
  const nodes = treeData.value.nodes
  const depth1 = nodes.filter(n => n.depth === 1)
  const depth2 = nodes.filter(n => n.depth === 2)
  return depth1.map(m => ({
    module_code: m.material_code,
    module_name: m.material_name,
    _open: openModules.value.has(m.material_code),
    parts: depth2.filter(p => p.parent_item_id === m.item_id).map(p => ({
      ...p, line_id: p.id,
    }))
  }))
})

function toggleModule(code) {
  if (openModules.value.has(code)) openModules.value.delete(code)
  else openModules.value.add(code)
  openModules.value = new Set(openModules.value)  // 触发响应式更新
}

function startEditQty(row) { editingId.value = row.line_id; editQty.value = row.quantity }
async function saveQty(row) {
  await api.put(`/bom/lines/${row.line_id}`, { quantity: editQty.value })
  row.quantity = editQty.value; editingId.value = null; ElMessage.success('用量已更新')
}
function startEditPos(row) { editingPosId.value = row.line_id; editPos.value = row.position || '' }
async function savePos(row) {
  await api.put(`/bom/lines/${row.line_id}`, { position: editPos.value })
  row.position = editPos.value; editingPosId.value = null; ElMessage.success('位号已更新')
}
async function deleteLine(row) {
  await ElMessageBox.confirm(`确定删除 ${row.material_code}？`, '提示', { type: 'warning' })
  await api.delete(`/bom/lines/${row.line_id}`)
  ElMessage.success('已删除')
  const productId = treeData.value.nodes[0]?.item_id
  if (productId) { const res = await api.get(`/bom/tree/${productId}`); treeData.value = res.tree }
}

async function showAddPart() {
  if (!allPartOptions.value.length) {
    const res = await api.get('/materials/all')
    allPartOptions.value = res.items || []
  }
  searchPart.value = ''; filteredParts.value = allPartOptions.value
  addPartVisible.value = true
}

function searchParts() {
  const kw = searchPart.value.toLowerCase()
  filteredParts.value = allPartOptions.value.filter(m =>
    (m.material_code || '').toLowerCase().includes(kw) ||
    (m.material_name || '').toLowerCase().includes(kw)
  )
}

async function confirmAddPart(part) {
  if (!treeData.value) return
  const nodes = treeData.value.nodes
  const root = nodes[0]
  // Find the BOM header from root's parent
  const headerId = treeData.value.header_id
  const parentItemId = root.item_id
  await api.post('/bom/lines', {
    bom_header_id: headerId,
    parent_item_id: parentItemId,
    item_id: part.id,
    quantity: 1,
    position: '',
    level: 1,
  })
  ElMessage.success(`已添加 ${part.material_code}`)
  addPartVisible.value = false
  // Reload tree
  const res = await api.get(`/bom/tree/${parentItemId}`)
  treeData.value = res.tree
}

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

// ====== 导入BOM弹窗 ======
const importDialogVisible = ref(false)
const importLoading = ref(false)
const importFile = ref(null)
const cloudLink = ref('')
const identified = reactive({ platform: '', icon: '📄', steps: [] })

function showImportDialog() {
  importDialogVisible.value = true
  resetImport()
}

function resetImport() {
  importFile.value = null
  importResult.value = null
  importOpts.product_code = ''
  importOpts.product_name = ''
  cloudLink.value = ''
  showCloudGuide.value = false
  identified.platform = ''
  identified.icon = '📄'
  identified.steps = []
}

function onFileChange(uploadFile) {
  importFile.value = uploadFile.raw
  importResult.value = null
  if (!importOpts.product_name) {
    importOpts.product_name = uploadFile.name.replace(/\.(xlsx|xls)$/i, '')
  }
  return false
}

function identifyLink() {
  const url = cloudLink.value.trim()
  if (!url) { identified.platform = ''; identified.steps = []; return }
  const guides = {
    'kdocs.cn': ['金山文档 / WPS', ['在浏览器中打开该链接', '点击「文件」→「导出」→「下载为 Excel (.xlsx)」', '将下载的 .xlsx 文件拖入上方区域']],
    'docs.wps.cn': ['金山文档 / WPS', ['在浏览器中打开该链接', '点击工具栏「导出」→「下载为 Excel」', '将下载的 .xlsx 文件拖入上方区域']],
    'docs.qq.com': ['腾讯文档', ['在浏览器中打开该链接', '点击「文件」→「导出为」→「本地 Excel (.xlsx)」', '将下载的 .xlsx 文件拖入上方区域']],
    'shimo.im': ['石墨文档', ['在浏览器中打开该链接', '点击「···」→「导出」→「导出为 Excel」', '将下载的 .xlsx 文件拖入上方区域']],
  }
  for (const [domain, [p, steps]] of Object.entries(guides)) {
    if (url.includes(domain)) { identified.platform = p; identified.steps = steps; return }
  }
  identified.platform = '其他云文档平台'
  identified.steps = ['在浏览器中打开该链接', '查找「导出」功能，导出为 Excel (.xlsx)', '将下载的 .xlsx 文件拖入上方区域']
}

// ====== BOM 导入状态 ======
const importResult = ref(null)
const showCloudGuide = ref(false)
const importOpts = reactive({ product_code: '', product_name: '' })

async function submitImport() {
  if (!importFile.value) { ElMessage.warning('请先选择Excel文件'); return }
  importLoading.value = true
  importResult.value = null
  try {
    const formData = new FormData()
    formData.append('file', importFile.value)
    const params = {}
    if (importOpts.product_code) params.product_code = importOpts.product_code
    if (importOpts.product_name) params.product_name = importOpts.product_name
    const res = await api.post('/bom/import/excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params,
    })
    importResult.value = res
    if (res.success) {
      ElMessage.success(res.message || '导入成功')
      fetchData()
    } else {
      ElMessage.error(res.message || '导入失败')
    }
  } catch (e) {
    importResult.value = { success: false, message: e.message || '导入失败' }
    ElMessage.error('导入失败: ' + (e.message || e))
  } finally {
    importLoading.value = false
  }
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
.page-container { padding: 0; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; }

/* BOM三级折叠卡片样式 */
.bom-proj-card { border:1px solid var(--color-border-light); border-radius:var(--radius-md); margin-bottom:12px; overflow:hidden }
.bom-proj-header { display:flex; align-items:center; padding:12px 16px; background:var(--color-bg-overlay); cursor:pointer; user-select:none; border-bottom:1px solid var(--color-border-subtle) }
.bom-proj-header:hover { background:var(--color-bg-hover) }
.bom-mod-card { border:1px solid var(--color-border-light); border-radius:var(--radius-sm); margin:8px 0; overflow:hidden }
.bom-mod-header { display:flex; align-items:center; padding:8px 12px; background:var(--color-bg-raised); cursor:pointer; user-select:none }
.bom-mod-header:hover { background:var(--color-bg-hover) }

/* 导入对话框适配 */
:deep(.cloud-guide-card) {
  background: var(--color-bg-overlay) !important;
  border-radius: var(--radius-md) !important;
}
</style>
