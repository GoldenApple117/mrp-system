<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-button type="primary" @click="runMrp"><el-icon><Cpu /></el-icon> 运行MRP</el-button>
      <el-button @click="clearAll"><el-icon><Delete /></el-icon> 清空记录</el-button>
      <span style="flex:1"></span>
      <el-select v-model="filterSeverity" placeholder="严重程度" style="width:120px" clearable @change="fetchData">
        <el-option label="错误" value="ERROR" /><el-option label="警告" value="WARNING" /><el-option label="信息" value="INFO" />
      </el-select>
      <el-select v-model="filterType" placeholder="类型" style="width:130px" clearable @change="fetchData">
        <el-option label="缺料" value="SHORTAGE" /><el-option label="逾期订单" value="OVERDUE_ORDER" />
        <el-option label="安全库存" value="SAFETY_STOCK_ALERT" /><el-option label="替代料" value="SUBSTITUTE" />
      </el-select>
      <el-checkbox v-model="filterResolved" @change="fetchData" style="margin-left:8px">含已处理</el-checkbox>
    </div>

    <!-- 汇总卡片 -->
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="4"><div class="stat-card" style="border-left:3px solid #909399"><div class="sl">未处理</div><div class="sv">{{ summary.unresolved }}</div></div></el-col>
      <el-col :span="4"><div class="stat-card" style="border-left:3px solid #f56c6c"><div class="sl">错误</div><div class="sv" style="color:#f56c6c">{{ summary.errors }}</div></div></el-col>
      <el-col :span="4"><div class="stat-card" style="border-left:3px solid #e6a23c"><div class="sl">警告</div><div class="sv" style="color:#e6a23c">{{ summary.warnings }}</div></div></el-col>
      <el-col :span="4" v-for="t in summary.by_type" :key="t.type">
        <div class="stat-card" :style="{borderLeft:'3px solid '+typeColor(t.type)}">
          <div class="sl">{{ summary.type_labels?.[t.type] || t.type }}</div>
          <div class="sv">{{ t.count }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 批量栏 -->
    <div v-if="selectedIds.length" class="batch-bar">
      <el-tag type="info">已选 {{ selectedIds.length }} 项</el-tag>
      <el-button size="small" type="success" @click="batchResolve">批量标记已处理</el-button>
      <el-button size="small" @click="selectedIds=[]">取消</el-button>
    </div>

    <el-table :data="tableData" v-loading="loading" stripe border
      @selection-change="(rows)=>selectedIds=rows.map(r=>r.id)">
      <el-table-column type="selection" width="40" :selectable="row=>!row.is_resolved" />
      <el-table-column label="等级" width="70">
        <template #default="{row}">
          <el-tag :type="row.severity==='ERROR'?'danger':row.severity==='WARNING'?'warning':'info'" size="small">{{ row.severity }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="exception_type" label="类型" width="90">
        <template #default="{row}">{{ summary.type_labels?.[row.exception_type] || row.exception_type }}</template>
      </el-table-column>
      <el-table-column prop="item_code" label="物料编码" width="110" />
      <el-table-column prop="material_name" label="物料型号" min-width="120" show-overflow-tooltip />
      <el-table-column prop="message" label="详情" min-width="200" show-overflow-tooltip />
      <el-table-column label="状态" width="80">
        <template #default="{row}">
          <el-tag :type="row.is_resolved?'success':'danger'" size="small">{{ row.is_resolved?'已处理':'待处理' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="时间" width="145">
        <template #default="{row}"><span style="font-size:12px">{{ row.created_at?.slice(0,16)?.replace('T',' ') }}</span></template>
      </el-table-column>
      <el-table-column label="操作" width="80">
        <template #default="{row}">
          <el-button v-if="!row.is_resolved" link type="success" size="small" @click="resolveOne(row)">处理</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total"
      layout="total,prev,pager,next" @change="fetchData" style="margin-top:12px;justify-content:flex-end" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false); const tableData = ref([])
const total = ref(0); const page = ref(1); const pageSize = ref(30)
const filterSeverity = ref(''); const filterType = ref(''); const filterResolved = ref(false)
const selectedIds = ref([])

const summary = reactive({
  unresolved: 0, errors: 0, warnings: 0,
  by_type: [], type_labels: {},
})

function typeColor(t) {
  return {SHORTAGE:'#f56c6c',OVERDUE_ORDER:'#e6a23c',SAFETY_STOCK_ALERT:'#409eff',SUBSTITUTE:'#67c23a'}[t]||'#909399'
}

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterSeverity.value) params.severity = filterSeverity.value
    if (filterType.value) params.exception_type = filterType.value
    if (!filterResolved.value) params.resolved = false
    const [d, s] = await Promise.all([
      api.get('/exceptions', { params }),
      api.get('/exceptions/summary'),
    ])
    tableData.value = d.items; total.value = d.total
    Object.assign(summary, s)
  } finally { loading.value = false }
}

async function runMrp() {
  await ElMessageBox.confirm('运行MRP将生成计划订单并记录例外信息，确定继续？', '运行MRP', { type: 'info' })
  loading.value = true
  try {
    const res = await api.post('/mrp/run', { horizon_days: 90 })
    ElMessage.success(res.message || 'MRP完成')
    fetchData()
  } catch (e) {
    ElMessage.error('MRP运行失败: '+ (e.message||''))
  } finally { loading.value = false }
}

async function resolveOne(row) {
  await api.post(`/exceptions/resolve/${row.id}`)
  ElMessage.success('已标记处理'); fetchData()
}

async function batchResolve() {
  await api.post('/exceptions/resolve/batch', { ids: selectedIds.value })
  ElMessage.success(`已处理 ${selectedIds.value.length} 条`)
  selectedIds.value = []; fetchData()
}

async function clearAll() {
  await ElMessageBox.confirm('确定清空所有例外记录？', '警告', { type: 'warning' })
  await api.delete('/exceptions/clear')
  ElMessage.success('已清空'); fetchData()
}

onMounted(fetchData)
</script>

<style scoped>
.page-container { padding: 0; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; flex-wrap:wrap }
.stat-card { background:var(--color-bg-overlay); border-radius:8px; padding:12px 16px; border:1px solid #ebeef5 }
.sl { font-size:13px; color:#909399; margin-bottom:4px }
.sv { font-size:22px; font-weight:bold; color:#303133 }
.batch-bar { display:flex; align-items:center; gap:8px; background:#f0f9eb; border:1px solid #b3e19d; padding:8px 14px; border-radius:6px; margin-bottom:12px }
</style>
