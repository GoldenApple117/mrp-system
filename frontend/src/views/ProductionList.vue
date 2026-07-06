<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-button type="primary" @click="showDialog(null)"><el-icon><Plus /></el-icon> 新建工单</el-button>
      <el-select v-model="filterStatus" placeholder="状态筛选" style="width:140px" clearable @change="fetchData">
        <el-option label="待下达" value="待下达" />
        <el-option label="已下达" value="已下达" />
        <el-option label="进行中" value="进行中" />
        <el-option label="已完成" value="已完成" />
      </el-select>
    </div>

    <el-empty v-if="!loading &amp;&amp; tableData.length === 0" description="暂无生产工单" />

    <el-table :data="tableData" v-loading="loading" stripe border>
      <el-table-column prop="wo_number" label="工单号" width="170" show-overflow-tooltip />
      <el-table-column prop="material_code" label="物料编码" width="120" show-overflow-tooltip />
      <el-table-column prop="material_name" label="物料名称" min-width="130" show-overflow-tooltip />
      <el-table-column prop="plan_qty" label="计划量" width="70" align="center" />
      <el-table-column label="进度" width="100" align="center">
        <template #default="{row}">
          <span>{{ row.completed_qty || 0 }}/{{ row.plan_qty }}</span>
          <span v-if="row.rejected_qty" style="color:var(--el-color-danger)">(-{{ row.rejected_qty }})</span>
        </template>
      </el-table-column>
      <el-table-column prop="labor_hours" label="工时" width="65" align="center" />
      <el-table-column prop="start_date" label="开始" width="100" show-overflow-tooltip />
      <el-table-column prop="end_date" label="完成" width="100" show-overflow-tooltip />
      <el-table-column label="状态" width="90" align="center">
        <template #default="{row}">
          <el-tag :type="woStatusTag(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="work_center_name" label="工作中心" width="100" show-overflow-tooltip />
      <el-table-column label="操作" width="400">
        <template #default="{row}">
          <el-button v-if="row.status==='已下达'" link type="primary" size="small" @click="startOrder(row)">开工</el-button>
          <el-button v-if="['已下达','进行中'].includes(row.status)" link type="success" size="small" @click="openMaterials(row)">物料</el-button>
          <el-button v-if="row.status==='进行中'" link type="warning" size="small" @click="openReport(row)">报工</el-button>
          <el-button v-if="row.status==='进行中'" link type="primary" size="small" @click="openReportHistory(row)">记录</el-button>
          <el-button v-if="row.status==='进行中'" link type="success" size="small" @click="checkReadiness(row)">完工</el-button>
          <el-button v-if="!['待下达'].includes(row.status)" link type="info" size="small" @click="showCost(row)">成本</el-button>
          <el-button v-if="row.status==='待下达'" link type="danger" size="small" @click="deleteItem(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total"
      layout="total,sizes,prev,pager,next" @change="fetchData" style="margin-top:16px;justify-content:flex-end" />

    <!-- 新建工单弹窗 -->
    <el-dialog v-model="dialogVisible" title="新建生产工单" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="物料" prop="item_id">
          <el-select v-model="form.item_id" filterable placeholder="选择物料" style="width:100%">
            <el-option v-for="m in materialOptions" :key="m.id" :label="`${m.material_code} ${m.material_name}`" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="计划产量" prop="plan_qty">
          <el-input-number v-model="form.plan_qty" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="完成日期" prop="end_date">
          <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="工作中心">
          <el-select v-model="form.work_center_id" clearable placeholder="可选" style="width:100%">
            <el-option v-for="w in workCenters" :key="w.id" :label="w.center_name" :value="w.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="工艺路线">
          <el-select v-model="form.routing_id" clearable placeholder="可选" style="width:100%">
            <el-option v-for="r in routingOptions" :key="r.id" :label="`${r.routing_code} (${r.material_name})`" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 报工弹窗 -->
    <el-dialog v-model="reportVisible" title="生产报工" width="500px">
      <el-form :model="reportForm" label-width="100px">
        <el-form-item label="工单号"><b>{{ reportForm.wo_number }}</b></el-form-item>
        <el-form-item label="物料">{{ reportForm.material_name }}</el-form-item>
        <el-form-item label="计划产量">{{ reportForm.plan_qty }}</el-form-item>
        <el-form-item label="已累计完成">{{ reportForm.existing_completed }}</el-form-item>
        <el-divider />
        <el-form-item label="本次完成">
          <el-input-number v-model="reportForm.completed_qty" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="不合格数">
          <el-input-number v-model="reportForm.rejected_qty" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="工时(h)">
          <el-input-number v-model="reportForm.labor_hours" :min="0" :step="0.5" :precision="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="操作人">
          <el-input v-model="reportForm.operator" placeholder="默认：系统" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="reportForm.remark" placeholder="可选" />
        </el-form-item>
        <el-tag v-if="reportForm.totalUndone > 0" type="warning" effect="plain">
          完成进度：{{ reportForm.existing_completed + (reportForm.completed_qty||0) }}/{{ reportForm.plan_qty }}
        </el-tag>
        <el-tag v-else type="success" effect="plain">
          已完成全部计划
        </el-tag>
      </el-form>
      <template #footer>
        <el-button @click="reportVisible=false">取消</el-button>
        <el-button type="primary" @click="submitReport" :loading="saving">提交报工</el-button>
      </template>
    </el-dialog>

    <!-- 报工历史弹窗 -->
    <el-dialog v-model="reportHistoryVisible" :title="`报工历史 - ${hWoNumber}`" width="650px">
      <el-table :data="reportHistory" stripe border size="small" v-loading="hLoading">
        <el-table-column prop="report_time" label="报工时间" width="160" />
        <el-table-column prop="completed_qty" label="完成" width="60" align="center" />
        <el-table-column prop="rejected_qty" label="不合格" width="60" align="center" />
        <el-table-column prop="labor_hours" label="工时(h)" width="70" align="center" />
        <el-table-column prop="operator" label="操作人" width="80" />
        <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
      </el-table>
      <div v-if="!hLoading && !reportHistory.length" style="text-align:center;padding:20px;color:#999">暂无报工记录</div>
    </el-dialog>

    <!-- 完工就绪检查 -->
    <el-dialog v-model="readinessVisible" :title="`完工就绪检查 - ${rWoNumber}`" width="600px">
      <div v-if="rLoading" style="text-align:center;padding:30px">检查中...</div>
      <div v-else>
        <el-alert v-if="readiness.can_complete" type="success" :closable="false" show-icon title="可以完工" style="margin-bottom:16px" />
        <el-alert v-else type="warning" :closable="false" show-icon title="存在未完成项" style="margin-bottom:16px" />
        <div v-for="c in readiness.checks" :key="c.name" style="margin-bottom:12px">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <el-tag :type="c.status==='OK'?'success':c.status==='WARNING'?'warning':'info'" size="small" round>{{ c.status }}</el-tag>
            <span style="font-weight:500">{{ c.name }}</span>
            <span style="color:#999;font-size:12px">{{ c.detail }}</span>
          </div>
          <div v-if="c.items" style="margin-left:70px">
            <div v-for="it in c.items" :key="it.code" style="font-size:12px;color:#666;line-height:1.8">
              {{ it.code }} {{ it.name }}: 需 {{ it.required }}，已领 {{ it.issued }}
            </div>
          </div>
        </div>
        <el-divider />
        <div style="display:flex;justify-content:space-around;text-align:center">
          <div><span style="color:#999">计划</span><br><span style="font-size:20px;font-weight:bold">{{ readiness.summary?.plan_qty }}</span></div>
          <div><span style="color:#67c23a">完成</span><br><span style="font-size:20px;font-weight:bold;color:#67c23a">{{ readiness.summary?.completed_qty }}</span></div>
          <div><span style="color:#f56c6c">不合格</span><br><span style="font-size:20px;font-weight:bold;color:#f56c6c">{{ readiness.summary?.rejected_qty }}</span></div>
          <div><span style="color:#409eff">工时(h)</span><br><span style="font-size:20px;font-weight:bold;color:#409eff">{{ readiness.summary?.labor_hours }}</span></div>
          <div><span style="color:#999">报工次数</span><br><span style="font-size:20px;font-weight:bold">{{ readiness.summary?.total_reports }}</span></div>
        </div>
      </div>
      <template #footer>
        <el-button @click="readinessVisible=false">关闭</el-button>
        <el-button v-if="!rLoading && readiness.can_complete" type="success" @click="doComplete">确认完工入库</el-button>
        <el-button v-if="!rLoading && !readiness.can_complete" type="warning" @click="forceComplete">强制完工</el-button>
      </template>
    </el-dialog>

    <!-- 物料管理弹窗 -->
    <el-dialog v-model="materialVisible" :title="`物料清单 - ${materialWoNumber}`" width="700px">
      <div v-if="matLoading" style="text-align:center;padding:30px">加载中...</div>
      <div v-else-if="!materials.length" style="text-align:center;color:#999;padding:30px">
        暂无物料需求，请先「开工」生成物料清单
      </div>
      <el-table v-else :data="materials" stripe border size="small">
        <el-table-column prop="material_code" label="编码" width="100" />
        <el-table-column prop="material_name" label="名称" min-width="120" show-overflow-tooltip />
        <el-table-column prop="required_qty" label="需求" width="60" align="center" />
        <el-table-column label="已发" width="80" align="center">
          <template #default="{row}">
            <span :style="{color: row.issued_qty >= row.required_qty ? '#67c23a' : '#e6a23c', fontWeight:'bold'}">{{ row.issued_qty || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="未发" width="70" align="center">
          <template #default="{row}">
            <span style="color:#f56c6c">{{ Math.max(0, row.required_qty - (row.issued_qty||0)) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{row}">
            <el-button link type="success" size="small"
              @click="openIssueDialog(row)"
              :disabled="(row.issued_qty||0) >= row.required_qty">领料</el-button>
            <el-button link type="warning" size="small"
              @click="openReturnDialog(row)"
              :disabled="!(row.issued_qty > 0)">退料</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 领料弹窗 -->
    <el-dialog v-model="issueVisible" title="领料" width="400px">
      <el-form label-width="90px">
        <el-form-item label="物料"><b>{{ issueForm.material_name }}</b></el-form-item>
        <el-form-item label="已领">{{ issueForm.issued_qty }}</el-form-item>
        <el-form-item label="需求">{{ issueForm.required_qty }}</el-form-item>
        <el-form-item label="可领数">{{ issueForm.available }}</el-form-item>
        <el-form-item label="本次领料">
          <el-input-number v-model="issueForm.issue_qty" :min="1" :max="issueForm.available" style="width:150px" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="issueVisible=false">取消</el-button>
        <el-button type="success" @click="confirmIssue" :loading="matSaving" :disabled="!issueForm.issue_qty">确认领料</el-button>
      </template>
    </el-dialog>

    <!-- 退料弹窗 -->
    <el-dialog v-model="returnVisible" title="退料" width="400px">
      <el-form label-width="90px">
        <el-form-item label="物料"><b>{{ returnForm.material_name }}</b></el-form-item>
        <el-form-item label="已领">{{ returnForm.issued_qty }}</el-form-item>
        <el-form-item label="本次退回">
          <el-input-number v-model="returnForm.return_qty" :min="1" :max="returnForm.issued_qty" style="width:150px" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="returnVisible=false">取消</el-button>
        <el-button type="warning" @click="confirmReturn" :loading="matSaving" :disabled="!returnForm.return_qty">确认退料</el-button>
      </template>
    </el-dialog>

    <!-- 成本弹窗 -->
    <el-dialog v-model="costVisible" :title="`成本核算 - ${cost.wo_number}`" width="650px">
      <div v-if="costLoading" style="text-align:center;padding:30px">计算中...</div>
      <div v-else>
        <!-- 汇总卡片 -->
        <div style="display:flex;gap:16px;margin-bottom:16px">
          <div style="flex:1;background:#f0f9eb;border-radius:8px;padding:12px;text-align:center">
            <div style="font-size:12px;color:#666">实际总成本</div>
            <div style="font-size:22px;font-weight:bold;color:#67c23a">¥{{ cost.summary?.actual_total?.toFixed(2) }}</div>
          </div>
          <div style="flex:1;background:#e6f1fb;border-radius:8px;padding:12px;text-align:center">
            <div style="font-size:12px;color:#666">标准成本</div>
            <div style="font-size:22px;font-weight:bold;color:#409eff">¥{{ cost.summary?.standard_total?.toFixed(2) }}</div>
          </div>
          <div style="flex:1;background:#fcebeb;border-radius:8px;padding:12px;text-align:center">
            <div style="font-size:12px;color:#666">差异</div>
            <div :style="{fontSize:'22px',fontWeight:'bold',color: (cost.summary?.variance||0) > 0 ? '#f56c6c' : '#67c23a'}">
              {{ cost.summary?.variance > 0 ? '+' : '' }}{{ cost.summary?.variance?.toFixed(2) }}
            </div>
          </div>
          <div style="flex:1;background:#faeeda;border-radius:8px;padding:12px;text-align:center">
            <div style="font-size:12px;color:#666">单位成本</div>
            <div style="font-size:22px;font-weight:bold;color:#e6a23c">¥{{ cost.summary?.unit_actual_cost?.toFixed(2) }}</div>
          </div>
        </div>
        <!-- 材料明细 -->
        <el-table :data="cost.material_costs?.items||[]" size="small" stripe border>
          <el-table-column prop="material_code" label="编码" width="90" />
          <el-table-column prop="material_name" label="名称" min-width="110" show-overflow-tooltip />
          <el-table-column label="单价" width="70" align="right"><template #default="{row}">¥{{ row.unit_price }}</template></el-table-column>
          <el-table-column label="用量" width="70" align="center"><template #default="{row}">{{ row.issued_qty }}/{{ row.required_qty }}</template></el-table-column>
          <el-table-column label="实际成本" width="90" align="right"><template #default="{row}" style="font-weight:bold">¥{{ row.actual_cost?.toFixed(2) }}</template></el-table-column>
        </el-table>
        <div style="margin-top:12px;font-size:13px">
          <span>人工成本: ¥{{ cost.labor_cost?.toFixed(2) }} (工时 {{ cost.labor_hours }}h × 费率 ¥{{ cost.cost_rates?.labor_rate_per_hour }}/h)</span>
        </div>
      </div>
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
const filterStatus = ref('')

const materialOptions = ref([])
const workCenters = ref([])
const routingOptions = ref([])

const dialogVisible = ref(false)
const formRef = ref(null)
const form = reactive({
  item_id: null, plan_qty: 1, start_date: '', end_date: '',
  work_center_id: null, routing_id: null, remark: '',
})
const rules = {
  item_id: [{ required: true }],
  plan_qty: [{ required: true }],
  start_date: [{ required: true }],
  end_date: [{ required: true }],
}

// ====== 报工弹窗 ======
const reportVisible = ref(false)
const reportForm = reactive({
  id: null, wo_number: '', material_name: '', plan_qty: 0,
  existing_completed: 0, completed_qty: 0, rejected_qty: 0, labor_hours: 0,
})

function woStatusTag(s) {
  const map = { '待下达': 'info', '已下达': 'warning', '进行中': '', '已完成': 'success', '已关闭': 'danger' }
  return map[s] || ''
}

async function fetchData() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterStatus.value) params.status = filterStatus.value
    const res = await api.get('/production/orders', { params })
    tableData.value = res.items
    total.value = res.total
  } finally { loading.value = false }
}

async function showDialog(row) {
  const [matRes, wcRes, routingRes] = await Promise.all([
    api.get('/materials/all'),
    api.get('/production/work-centers'),
    api.get('/production/routings'),
  ])
  materialOptions.value = matRes.items
  workCenters.value = wcRes.items
  routingOptions.value = routingRes.items || []
  Object.assign(form, {
    item_id: null, plan_qty: 1, start_date: '', end_date: '',
    work_center_id: null, routing_id: null, remark: '',
  })
  dialogVisible.value = true
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const data = { ...form }
    data.status = '已下达'
    if (!data.routing_id) delete data.routing_id
    await api.post('/production/orders', data)
    ElMessage.success('工单已创建')
    dialogVisible.value = false
    fetchData()
  } finally { saving.value = false }
}

// ====== 开工 ======
async function startOrder(row) {
  await ElMessageBox.confirm(`确认开工"${row.wo_number}"？将自动根据BOM扣减原料库存。`, '开工确认', { type: 'info' })
  try {
    const res = await api.post(`/production/orders/${row.id}/start`)
    ElMessage.success(res.message)
    fetchData()
  } catch { ElMessage.error('开工失败') }
}

// ====== 报工 ======
function openReport(row) {
  Object.assign(reportForm, {
    id: row.id,
    wo_number: row.wo_number,
    material_name: row.material_name,
    plan_qty: row.plan_qty,
    existing_completed: row.completed_qty || 0,
    totalUndone: row.plan_qty - (row.completed_qty || 0),
    completed_qty: 0, rejected_qty: 0, labor_hours: 0,
    operator: '', remark: '',
  })
  reportVisible.value = true
}

async function submitReport() {
  const q = reportForm.completed_qty || 0
  const r = reportForm.rejected_qty || 0
  const h = reportForm.labor_hours || 0
  if (q <= 0 && r <= 0 && h <= 0) return ElMessage.warning('请至少填报一项')
  saving.value = true
  try {
    const res = await api.post(`/production/orders/${reportForm.id}/report`, {
      completed_qty: q, rejected_qty: r, labor_hours: h,
      operator: reportForm.operator, remark: reportForm.remark,
    })
    ElMessage.success(res.message)
    reportVisible.value = false
    fetchData()
  } catch (e) { ElMessage.error(e.message || '报工失败') } finally { saving.value = false }
}

// ====== 报工历史 ======
const reportHistoryVisible = ref(false)
const hWoNumber = ref('')
const reportHistory = ref([])
const hLoading = ref(false)
async function openReportHistory(row) {
  hWoNumber.value = row.wo_number
  reportHistoryVisible.value = true
  hLoading.value = true
  try {
    const res = await api.get(`/production/orders/${row.id}/reports`)
    reportHistory.value = res.items || []
  } finally { hLoading.value = false }
}

// ====== 完工就绪检查 ======
const readinessVisible = ref(false)
const rWoNumber = ref('')
const rWoId = ref(null)
const readiness = ref({ checks: [], can_complete: false, summary: {} })
const rLoading = ref(false)
async function checkReadiness(row) {
  rWoNumber.value = row.wo_number
  rWoId.value = row.id
  readinessVisible.value = true
  rLoading.value = true
  try {
    const res = await api.get(`/production/orders/${row.id}/readiness`)
    readiness.value = res
  } finally { rLoading.value = false }
}

async function doComplete() {
  try {
    const res = await api.post(`/production/orders/${rWoId.value}/complete`, {})
    ElMessage.success(res.message)
    readinessVisible.value = false
    fetchData()
  } catch (e) { ElMessage.error(e.message || '完工失败') }
}

async function forceComplete() {
  await ElMessageBox.confirm('物料未领完，确认强制完工？', '提示', { type: 'warning' })
  try {
    const res = await api.post(`/production/orders/${rWoId.value}/complete`, { force: true })
    ElMessage.success(res.message)
    readinessVisible.value = false
    fetchData()
  } catch (e) { ElMessage.error(e.message || '完工失败') }
}

// ====== 删除 ======
async function deleteItem(row) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await api.delete(`/production/orders/${row.id}`)
  fetchData()
}

// ====== 物料管理 ======
const materialVisible = ref(false)
const materialWoNumber = ref('')
const materialWoId = ref(null)
const materials = ref([])
const matLoading = ref(false)

async function openMaterials(row) {
  materialWoId.value = row.id
  materialWoNumber.value = row.wo_number
  materialVisible.value = true
  matLoading.value = true
  try {
    const res = await api.get(`/production/orders/${row.id}/materials`)
    materials.value = res.items || []
  } finally { matLoading.value = false }
}

// 领料
const issueVisible = ref(false)
const matSaving = ref(false)
const issueForm = reactive({
  id: null, material_code: '', material_name: '', required_qty: 0, issued_qty: 0, available: 0, issue_qty: 1,
})

function openIssueDialog(row) {
  const issued = row.issued_qty || 0
  Object.assign(issueForm, {
    id: row.id, material_code: row.material_code, material_name: row.material_name,
    required_qty: row.required_qty, issued_qty: issued,
    available: Math.max(0, row.required_qty - issued),
    issue_qty: Math.min(1, row.required_qty - issued),
  })
  issueVisible.value = true
}

async function confirmIssue() {
  if (!issueForm.issue_qty || issueForm.issue_qty <= 0) return ElMessage.warning('请输入领料数量')
  matSaving.value = true
  try {
    const res = await api.post(`/production/orders/${materialWoId.value}/issue-material`, {
      item_id: materials.value.find(m => m.id === issueForm.id)?.material_code || issueForm.material_code,
      issue_qty: issueForm.issue_qty,
    })
    ElMessage.success(res.message)
    issueVisible.value = false
    // 刷新物料列表
    await openMaterials({ id: materialWoId.value, wo_number: materialWoNumber.value })
  } catch (e) { ElMessage.error(e.message || '领料失败') } finally { matSaving.value = false }
}

// 退料
const returnVisible = ref(false)
const returnForm = reactive({
  id: null, material_code: '', material_name: '', issued_qty: 0, return_qty: 1,
})

function openReturnDialog(row) {
  Object.assign(returnForm, {
    id: row.id, material_code: row.material_code, material_name: row.material_name,
    issued_qty: row.issued_qty || 0, return_qty: Math.min(1, row.issued_qty || 0),
  })
  returnVisible.value = true
}

async function confirmReturn() {
  if (!returnForm.return_qty || returnForm.return_qty <= 0) return ElMessage.warning('请输入退料数量')
  matSaving.value = true
  try {
    const res = await api.post(`/production/orders/${materialWoId.value}/return-material`, {
      item_id: materials.value.find(m => m.id === returnForm.id)?.material_code || returnForm.material_code,
      return_qty: returnForm.return_qty,
    })
    ElMessage.success(res.message)
    returnVisible.value = false
    await openMaterials({ id: materialWoId.value, wo_number: materialWoNumber.value })
  } catch (e) { ElMessage.error(e.message || '退料失败') } finally { matSaving.value = false }
}

// ====== 成本核算 ======
const costVisible = ref(false)
const costLoading = ref(false)
const cost = ref({ wo_number: '', material_costs: { items: [] }, labor_cost: 0, summary: {} })
async function showCost(row) {
  costVisible.value = true
  costLoading.value = true
  try {
    const res = await api.get(`/production/orders/${row.id}/cost`)
    cost.value = res
  } finally { costLoading.value = false }
}

onMounted(fetchData)
</script>

<style scoped>
.page-container { padding: 0; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; }
/* 允许表格在列宽总和小于容器时自然滚动，避免固定列与相邻列重叠 */
:deep(.el-table__body-wrapper) { overflow-x: auto; }
</style>
