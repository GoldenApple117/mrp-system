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

    <!-- ====== 导入BOM引导弹窗 ====== -->
    <el-dialog v-model="importDialogVisible" title="导入BOM" width="640px" @close="resetImport">
      <el-tabs v-model="importTab">
        <!-- Tab 1: 上传Excel -->
        <el-tab-pane label="上传Excel" name="excel">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls"
            :on-change="onFileChange"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div style="margin:8px 0">将Excel文件拖到此处，或<em>点击选择</em></div>
            <template #tip>
              <div style="color:#999;font-size:12px">支持 .xlsx / .xls 格式，表头须包含：父物料编码、子物料编码、用量</div>
            </template>
          </el-upload>
          <div v-if="importFile" style="margin:8px 0;color:#409eff">已选择: {{ importFile.name }}</div>
        </el-tab-pane>

        <!-- Tab 2: 在线链接引导 -->
        <el-tab-pane label="在线链接" name="cloud">
          <el-input
            v-model="cloudLink"
            placeholder="粘贴金山文档 / WPS / 腾讯文档等分享链接"
            clearable
            @input="identifyLink"
            style="margin-bottom:12px"
          >
            <template #prefix><el-icon><Link /></el-icon></template>
          </el-input>

          <div v-if="identified.platform" class="cloud-guide-card">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
              <span style="font-size:20px">{{ identified.icon }}</span>
              <span style="font-weight:500">已识别：{{ identified.platform }}</span>
            </div>
            <div style="background:#f0f9ff;border-radius:8px;padding:12px 16px;margin-bottom:12px;font-size:13px;line-height:1.8;">
              <div v-for="(step,si) in identified.steps" :key="si" style="display:flex;align-items:flex-start;gap:8px;margin:4px 0;">
                <span style="background:#409eff;color:#fff;border-radius:50%;width:20px;height:20px;display:inline-flex;align-items:center;justify-content:center;font-size:12px;flex-shrink:0;">{{ si+1 }}</span>
                <span>{{ step }}</span>
              </div>
            </div>
            <el-upload
              :auto-upload="false"
              :limit="1"
              accept=".xlsx,.xls"
              :on-change="onFileChange"
            >
              <el-button type="primary"><el-icon><Upload /></el-icon> 选择下载好的Excel文件</el-button>
            </el-upload>
            <div v-if="importFile" style="margin-top:8px;color:#409eff">已选择: {{ importFile.name }}</div>
          </div>
        </el-tab-pane>

        <!-- Tab 3: 粘贴数据 -->
        <el-tab-pane label="粘贴数据" name="paste">
          <div style="color:#666;font-size:13px;margin-bottom:8px;">
            请按以下格式粘贴数据（每行一条，逗号分隔）：<br>
            <code style="background:#f5f5f5;padding:2px 6px;border-radius:4px;font-size:12px;">父物料编码,子物料编码,用量,位号</code>
          </div>
          <el-input
            v-model="pasteData"
            type="textarea"
            :rows="8"
            placeholder="FG-001,SA-001,1,A1&#10;FG-001,SA-002,1,A2&#10;SA-001,RM-001,1,"
          />
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitImport" :loading="importLoading">
          {{ importTab === 'paste' ? '开始导入' : '开始导入' }}
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
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterStatus = ref('')

const treeVisible = ref(false)
const treeData = ref(null)
const treeProps = { children: 'children', label: 'material_name' }

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
    if (res.success) {
      ElMessage.success(res.message || '导入成功')
      fetchData()
    } else {
      ElMessage.error(res.message || '导入失败')
      if (res.errors && res.errors.length) {
        ElMessageBox.alert(res.errors.slice(0, 10).join('\n'), '导入错误')
      }
    }
  } catch {
    ElMessage.error('导入失败')
  }
  return false
}

// ====== 导入弹窗（云文档引导 + 粘贴数据） ======
const importDialogVisible = ref(false)
const importTab = ref('excel')
const importLoading = ref(false)
const importFile = ref(null)
const cloudLink = ref('')
const pasteData = ref('')
const identified = reactive({ platform: '', icon: '📄', steps: [] })

function showImportDialog() {
  importDialogVisible.value = true
  importTab.value = 'excel'
  resetImport()
}

function resetImport() {
  importFile.value = null
  cloudLink.value = ''
  pasteData.value = ''
  identified.platform = ''
  identified.icon = '📄'
  identified.steps = []
}

function onFileChange(uploadFile) {
  importFile.value = uploadFile.raw
  return false
}

function identifyLink() {
  const url = cloudLink.value.trim()
  if (!url) {
    identified.platform = ''
    identified.icon = '📄'
    identified.steps = []
    return
  }

  if (url.includes('kdocs.cn') || url.includes('docs.wps.cn') || url.includes('wps.cn')) {
    identified.platform = '金山文档 / WPS'
    identified.steps = [
      '在浏览器中打开该链接',
      '点击工具栏「导出 / 下载」→「下载为 Excel (.xlsx)」',
      '将下载的 .xlsx 文件拖入下方区域',
    ]
  } else if (url.includes('docs.qq.com')) {
    identified.platform = '腾讯文档'
    identified.steps = [
      '在浏览器中打开该链接',
      '点击「文件」→「导出为」→「本地 Excel 表格 (.xlsx)」',
      '将下载的 .xlsx 文件拖入下方区域',
    ]
  } else if (url.includes('shimo.im') || url.includes('石墨文档')) {
    identified.platform = '石墨文档'
    identified.steps = [
      '在浏览器中打开该链接',
      '点击右上角「···」→「导出」→「导出为 Excel」',
      '将下载的 .xlsx 文件拖入下方区域',
    ]
  } else if (url.includes('aliyundoc') || url.includes('alibabacloud')) {
    identified.platform = '阿里云文档'
    identified.steps = [
      '在浏览器中打开该链接',
      '点击「导出」→「下载为 Excel」',
      '将下载的 .xlsx 文件拖入下方区域',
    ]
  } else {
    identified.platform = '其他云文档平台'
    identified.steps = [
      '在浏览器中打开该链接',
      '查找「导出」或「下载」功能，导出为 Excel (.xlsx) 格式',
      '将下载的 .xlsx 文件拖入下方区域',
    ]
  }
}

async function submitImport() {
  if (importTab.value === 'paste') {
    const lines = pasteData.value.trim().split('\n').filter(l => l.trim())
    if (lines.length === 0) {
      ElMessage.warning('请粘贴BOM数据')
      return
    }
    importLoading.value = true
    try {
      // Parse CSV: parent_code,child_code,quantity,position
      const pairs = []
      for (let i = 0; i < lines.length; i++) {
        const parts = lines[i].split(',').map(s => s.trim())
        if (parts.length >= 2) {
          pairs.push({
            parent_code: parts[0], child_code: parts[1],
            quantity: parseFloat(parts[2]) || 1, position: parts[3] || '',
          })
        }
      }
      if (pairs.length === 0) { ElMessage.error('没有有效数据'); return }

      // Group by parent
      const groups = {}
      pairs.forEach(p => {
        if (!groups[p.parent_code]) groups[p.parent_code] = []
        groups[p.parent_code].push(p)
      })

      // Get all materials
      const matRes = await api.get('/materials/all')
      const matMap = {}
      matRes.items.forEach(m => { matMap[m.material_code] = m })

      let success = 0
      for (const [parentCode, children] of Object.entries(groups)) {
        const product = matMap[parentCode]
        if (!product) { ElMessage.warning(`物料 ${parentCode} 不存在，跳过`); continue }
        // Create BOM with lines in one call
        const linesPayload = children.map(c => ({
          parent_item_id: product.id,
          item_id: matMap[c.child_code]?.id || null,
          quantity: c.quantity,
          position: c.position,
          level: 1,
          sort_order: 0,
        })).filter(l => l.item_id)
        if (linesPayload.length === 0) continue
        const r = await api.post('/bom/headers', {
          bom_code: `BOM-${parentCode}`,
          product_id: product.id,
          version: 'A',
          status: '生效',
          lines: linesPayload,
        })
        if (r.success) success++
      }
      ElMessage.success(`成功导入 ${success} 个BOM`)
      importDialogVisible.value = false
      fetchData()
    } catch (e) {
      ElMessage.error('导入失败: ' + (e.message || e))
    } finally {
      importLoading.value = false
    }
    return
  }

  // Excel mode
  if (!importFile.value) { ElMessage.warning('请先选择Excel文件'); return }
  importLoading.value = true
  try {
    const formData = new FormData()
    formData.append('file', importFile.value)
    const res = await api.post('/bom/import/excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    if (res.success) {
      ElMessage.success(res.message || '导入成功')
      importDialogVisible.value = false
      fetchData()
    } else {
      ElMessage.error(res.message || '导入失败')
      if (res.errors?.length) {
        ElMessageBox.alert(res.errors.slice(0, 10).join('\n'), '导入错误')
      }
    }
  } catch (e) {
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
.page-container { background:#fff; padding:20px; border-radius:8px; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; }
</style>
