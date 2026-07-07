<template>
  <div class="page-container">
    <el-tabs v-model="tab" @tab-change="onTabChange">
      <!-- Tab 1: 检验记录 -->
      <el-tab-pane label="检验记录" name="inspection">
        <div class="page-toolbar">
          <el-button type="primary" @click="showInspectionDialog"
            ><el-icon><Plus /></el-icon> 创建检验</el-button
          >
          <el-select
            v-model="filterType"
            placeholder="类型"
            class="w-[100px]"
            clearable
            @change="fetchInspections"
          >
            <el-option label="IQC" value="IQC" /><el-option label="PQC" value="PQC" /><el-option
              label="OQC"
              value="OQC"
            />
          </el-select>
          <el-select
            v-model="filterResult"
            placeholder="结果"
            class="w-[100px]"
            clearable
            @change="fetchInspections"
          >
            <el-option label="待检" value="待检" /><el-option label="合格" value="合格" />
            <el-option label="部分合格" value="部分合格" /><el-option
              label="不合格"
              value="不合格"
            />
          </el-select>
        </div>
        <el-table v-loading="loading" :data="inspections" stripe border>
          <el-table-column prop="inspection_no" label="检验单号" width="180" />
          <el-table-column label="类型" width="70"
            ><template #default="{row}"
              ><el-tag
                :type="row.inspection_type==='IQC'?'':row.inspection_type==='PQC'?'warning':'success'"
                size="small"
                >{{ row.inspection_type }}</el-tag
              ></template
            ></el-table-column
          >
          <el-table-column prop="material_code" label="物料" width="120" />
          <el-table-column prop="material_name" label="物料型号" min-width="140" />
          <el-table-column prop="inspect_qty" label="检验数" width="80" />
          <el-table-column prop="pass_qty" label="合格" width="70" />
          <el-table-column prop="reject_qty" label="不合格" width="70" />
          <el-table-column label="结果" width="90"
            ><template #default="{row}"
              ><el-tag
                :type="resultTag(row.result)"
                size="small"
                >{{ row.result }}</el-tag
              ></template
            ></el-table-column
          >
          <el-table-column prop="inspector" label="检验员" width="90" />
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{row}">
              <el-button
                v-if="row.result==='待检'"
                link
                type="primary"
                size="small"
                @click="showResultDialog(row)"
                >录入结果</el-button
              >
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total,sizes,prev,pager,next"
          class="mt-3 justify-end"
          @change="fetchInspections"
        />
      </el-tab-pane>

      <!-- Tab 2: 检验标准 -->
      <el-tab-pane label="检验标准" name="standards">
        <div class="page-toolbar">
          <el-button type="primary" @click="showStdDialog"
            ><el-icon><Plus /></el-icon> 新建标准</el-button
          >
          <el-select
            v-model="stdTypeFilter"
            placeholder="类型"
            class="w-[100px]"
            clearable
            @change="fetchStandards"
          >
            <el-option label="IQC" value="IQC" /><el-option label="PQC" value="PQC" /><el-option
              label="OQC"
              value="OQC"
            />
          </el-select>
        </div>
        <el-table v-loading="stdLoading" :data="standards" stripe border>
          <el-table-column prop="standard_code" label="标准编码" width="130" />
          <el-table-column prop="standard_name" label="标准名称" width="160" />
          <el-table-column prop="material_name" label="物料" min-width="120" />
          <el-table-column label="类型" width="70"
            ><template #default="{row}"
              ><el-tag size="small">{{ row.inspection_type }}</el-tag></template
            ></el-table-column
          >
          <el-table-column prop="sampling_method" label="抽样方式" width="90" />
          <el-table-column prop="sample_size" label="样本量" width="80" />
          <el-table-column prop="accept_level" label="允收标准" width="90" />
          <el-table-column label="操作" width="100"
            ><template #default="{row}">
              <el-button link type="danger" size="small" @click="deleteStd(row)">删除</el-button>
            </template></el-table-column
          >
        </el-table>
      </el-tab-pane>

      <!-- Tab 3: NCR 不合格品处理 -->
      <el-tab-pane label="NCR 不合格品" name="ncr">
        <div class="page-toolbar">
          <el-button type="danger" @click="showNcrDialog"
            ><el-icon><Plus /></el-icon> 新建 NCR</el-button
          >
          <el-select
            v-model="ncrStatusFilter"
            placeholder="状态"
            class="w-[120px]"
            clearable
            @change="fetchNcr"
          >
            <el-option label="待处理" value="待处理" /><el-option
              label="评审中"
              value="评审中"
            /><el-option label="已处理" value="已处理" />
          </el-select>
        </div>
        <el-table v-loading="ncrLoading" :data="ncrs" stripe border>
          <el-table-column prop="ncr_no" label="NCR编号" width="160" />
          <el-table-column prop="material_name" label="物料" width="140" />
          <el-table-column prop="qty" label="数量" width="70" />
          <el-table-column prop="severity" label="严重度" width="80"
            ><template #default="{row}">
              <el-tag
                :type="row.severity==='致命'?'danger':row.severity==='严重'?'warning':'info'"
                size="small"
                >{{ row.severity }}</el-tag
              >
            </template></el-table-column
          >
          <el-table-column prop="disposition" label="处置方式" width="100" />
          <el-table-column prop="status" label="状态" width="80"
            ><template #default="{row}">
              <el-tag
                :type="row.status==='已处理'?'success':row.status==='评审中'?'warning':'danger'"
                size="small"
                >{{ row.status }}</el-tag
              >
            </template></el-table-column
          >
          <el-table-column prop="description" label="描述" min-width="140" show-overflow-tooltip />
          <el-table-column label="操作" width="110"
            ><template #default="{row}">
              <el-button
                v-if="row.status==='待处理'"
                link
                type="primary"
                size="small"
                @click="showDisposeDialog(row)"
                >处置</el-button
              >
            </template></el-table-column
          >
        </el-table>
      </el-tab-pane>

      <!-- Tab 4: 质量看板 -->
      <el-tab-pane label="质量看板" name="dashboard">
        <div v-if="!dash" class="text-center p-10 text-[var(--color-text-disabled)]">加载中...</div>
        <div v-else class="flex flex-col gap-5">
          <div class="flex gap-4">
            <div class="kpi-card bg-[#e6f1fb]">
              <span class="kpi-label">总检验次数</span
              ><span class="kpi-val">{{ dash.total_inspections }}</span>
            </div>
            <div class="kpi-card bg-[#f0f9eb]">
              <span class="kpi-label">合格率</span
              ><span class="kpi-val text-[#67c23a]">{{ dash.pass_rate }}%</span>
            </div>
            <div class="kpi-card bg-[#fcebeb]">
              <span class="kpi-label">待处理NCR</span
              ><span class="kpi-val text-[#f56c6c]">{{ dash.pending_ncr }}</span>
            </div>
            <div class="kpi-card bg-[#faeeda]">
              <span class="kpi-label">待检</span
              ><span class="kpi-val text-[#e6a23c]">{{ dash.pending_inspections }}</span>
            </div>
          </div>
          <el-table :data="typeData" stripe border size="small">
            <el-table-column label="类型"
              ><template #default="{row}">{{ row.type }}</template></el-table-column
            >
            <el-table-column label="次数" prop="count" width="80" />
            <el-table-column label="合格数" prop="pass_qty" width="90" />
            <el-table-column label="不合格数" prop="reject_qty" width="90" />
            <el-table-column label="合格率" width="90"
              ><template #default="{row}">{{ row.pass_rate }}%</template></el-table-column
            >
          </el-table>
        </div>
      </el-tab-pane>

      <!-- Tab 5: 盘点管理 -->
      <el-tab-pane label="盘点管理" name="stock">
        <div class="page-toolbar">
          <el-button type="primary" @click="showStockDialog"
            ><el-icon><Plus /></el-icon> 新建盘点</el-button
          >
        </div>
        <el-table v-loading="loading2" :data="stockCounts" stripe border>
          <el-table-column prop="count_no" label="盘点单号" width="180" />
          <el-table-column prop="material_code" label="物料编码" width="120" />
          <el-table-column prop="material_name" label="物料名称" min-width="140" />
          <el-table-column prop="system_qty" label="系统数" width="80" />
          <el-table-column label="实盘数" width="80"
            ><template #default="{row}">{{ row.actual_qty ?? '-' }}</template></el-table-column
          >
          <el-table-column label="差异" width="80"
            ><template #default="{row}"
              ><span
                :style="{color: row.difference > 0 ? '#67c23a' : row.difference < 0 ? '#f56c6c' : '#333', fontWeight:'bold'}"
                >{{ row.difference ?? '-' }}</span
              ></template
            ></el-table-column
          >
          <el-table-column label="状态" width="80"
            ><template #default="{row}"
              ><el-tag
                :type="row.status==='已调整'?'success':row.status==='已盘点'?'warning':'info'"
                size="small"
                >{{ row.status }}</el-tag
              ></template
            ></el-table-column
          >
          <el-table-column prop="counter" label="盘点人" width="80" />
          <el-table-column label="操作" width="130" fixed="right"
            ><template #default="{row}">
              <el-button
                v-if="row.status==='待盘点'"
                link
                type="primary"
                size="small"
                @click="showStockResult(row)"
                >录入结果</el-button
              >
              <el-button
                v-if="row.status==='已盘点'"
                link
                type="success"
                size="small"
                @click="adjustStock(row)"
                >确认调整</el-button
              >
            </template></el-table-column
          >
        </el-table>
        <el-pagination
          v-model:current-page="spage"
          v-model:page-size="spageSize"
          :total="stotal"
          layout="total,prev,pager,next"
          class="mt-3 justify-end"
          @change="fetchStock"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 创建检验弹窗 -->
    <el-dialog v-model="inspDialogVisible" title="创建检验" width="500px">
      <el-form ref="inspFormRef" :model="inspForm" label-width="100px">
        <el-form-item label="检验类型">
          <el-select v-model="inspForm.inspection_type" class="w-full">
            <el-option label="IQC 来料检验" value="IQC" /><el-option
              label="PQC 过程检验"
              value="PQC"
            /><el-option label="OQC 出货检验" value="OQC" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源类型">
          <el-select v-model="inspForm.source_type" class="w-full"
            ><el-option label="采购单" value="采购单"
          /></el-select>
        </el-form-item>
        <el-form-item label="来源单号" required>
          <el-select
            v-model="inspForm.source_id"
            filterable
            placeholder="选择采购单"
            class="w-full"
          >
            <el-option
              v-for="po in poOptions"
              :key="po.id"
              :label="`${po.po_number} - ${po.material_name} x${po.order_qty}`"
              :value="po.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="检验数量" required>
          <el-input-number v-model="inspForm.inspect_qty" :min="1" class="w-full" />
        </el-form-item>
        <el-form-item label="检验员"><el-input v-model="inspForm.inspector" /></el-form-item>
        <el-form-item label="备注"
          ><el-input v-model="inspForm.remark" type="textarea"
        /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="inspDialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="createInspection">创建</el-button>
      </template>
    </el-dialog>

    <!-- 录入检验结果弹窗 -->
    <el-dialog v-model="resultDialogVisible" title="录入检验结果" width="420px">
      <el-form :model="resultForm" label-width="100px">
        <el-form-item label="检验数量"
          ><b>{{ resultForm.inspect_qty }}</b></el-form-item
        >
        <el-form-item label="合格数量"
          ><el-input-number
            v-model="resultForm.pass_qty"
            :min="0"
            :max="resultForm.inspect_qty"
            class="w-full"
        /></el-form-item>
        <el-form-item label="不合格数量"
          ><el-input-number
            v-model="resultForm.reject_qty"
            :min="0"
            :max="resultForm.inspect_qty"
            class="w-full"
        /></el-form-item>
        <el-form-item label="不合格原因"
          ><el-input
            v-model="resultForm.ncr_reason"
            type="textarea"
            placeholder="不合格将自动创建NCR"
        /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resultDialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitResult">提交</el-button>
      </template>
    </el-dialog>

    <!-- 新建检验标准弹窗 -->
    <el-dialog v-model="stdDialogVisible" title="新建检验标准" width="500px">
      <el-form :model="stdForm" label-width="100px">
        <el-form-item label="物料" required>
          <el-select v-model="stdForm.item_id" filterable placeholder="选择物料" class="w-full">
            <el-option
              v-for="m in materialOptions"
              :key="m.id"
              :label="`${m.material_code} ${m.material_name}`"
              :value="m.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标准编码" required
          ><el-input v-model="stdForm.standard_code"
        /></el-form-item>
        <el-form-item label="标准名称"><el-input v-model="stdForm.standard_name" /></el-form-item>
        <el-form-item label="检验类型">
          <el-select v-model="stdForm.inspection_type" class="w-full"
            ><el-option label="IQC" value="IQC" /><el-option label="PQC" value="PQC" /><el-option
              label="OQC"
              value="OQC"
          /></el-select>
        </el-form-item>
        <el-form-item label="抽样方式">
          <el-select v-model="stdForm.sampling_method" class="w-full"
            ><el-option label="全检" value="全检" /><el-option label="AQL" value="AQL" /><el-option
              label="百分比"
              value="百分比"
          /></el-select>
        </el-form-item>
        <el-form-item label="样本量"
          ><el-input-number v-model="stdForm.sample_size" :min="0" class="w-full"
        /></el-form-item>
        <el-form-item label="允收标准"
          ><el-input-number v-model="stdForm.accept_level" :min="0" class="w-full"
        /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stdDialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="createStandard">创建</el-button>
      </template>
    </el-dialog>

    <!-- NCR 处置弹窗 -->
    <el-dialog v-model="disposeVisible" title="NCR 处置" width="420px">
      <el-form :model="disposeForm" label-width="90px">
        <el-form-item label="NCR编号"
          ><b>{{ disposeForm.ncr_no }}</b></el-form-item
        >
        <el-form-item label="处置方式">
          <el-select v-model="disposeForm.disposition" class="w-full">
            <el-option label="退货" value="退货" /><el-option label="让步接收" value="让步接收" />
            <el-option label="返工" value="返工" /><el-option label="报废" value="报废" /><el-option
              label="降级"
              value="降级"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="处置数量"
          ><el-input-number v-model="disposeForm.disposition_qty" :min="0" class="w-full"
        /></el-form-item>
        <el-form-item label="评审人"><el-input v-model="disposeForm.reviewer" /></el-form-item>
        <el-form-item label="批准人"><el-input v-model="disposeForm.approver" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="disposeVisible=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitDispose">提交处置</el-button>
      </template>
    </el-dialog>

    <!-- 创建盘点弹窗 -->
    <el-dialog v-model="stockDialogVisible" title="新建盘点" width="420px">
      <el-form ref="stockFormRef" :model="stockForm" label-width="80px">
        <el-form-item label="物料" required>
          <el-select v-model="stockForm.item_id" filterable placeholder="选择物料" class="w-full">
            <el-option
              v-for="m in materialOptions"
              :key="m.id"
              :label="`${m.material_code} ${m.material_name}`"
              :value="m.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="盘点人"><el-input v-model="stockForm.counter" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stockDialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="createStockCount">创建</el-button>
      </template>
    </el-dialog>

    <!-- 录入盘点结果弹窗 -->
    <el-dialog v-model="stockResultVisible" title="录入盘点结果" width="400px">
      <el-form :model="stockResultForm" label-width="80px">
        <el-form-item label="系统数"
          ><b>{{ stockResultForm.system_qty }}</b></el-form-item
        >
        <el-form-item label="实盘数"
          ><el-input-number v-model="stockResultForm.actual_qty" :min="0" class="w-full"
        /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stockResultVisible=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitStockResult">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const tab = ref('inspection')
const loading = ref(false); const loading2 = ref(false); const saving = ref(false)
const inspections = ref([]); const total = ref(0); const page = ref(1); const pageSize = ref(20)
const filterResult = ref(''); const filterType = ref('')
const stockCounts = ref([]); const stotal = ref(0); const spage = ref(1); const spageSize = ref(20)

// Standards
const standards = ref([]); const stdLoading = ref(false); const stdTypeFilter = ref('')
const stdDialogVisible = ref(false)
const stdForm = reactive({ item_id: null, standard_code: '', standard_name: '', inspection_type: 'IQC', sampling_method: '全检', sample_size: 0, accept_level: 0 })

// NCR
const ncrs = ref([]); const ncrLoading = ref(false); const ncrStatusFilter = ref('')
const disposeVisible = ref(false)
const disposeForm = reactive({ id: null, ncr_no: '', disposition: '退货', disposition_qty: 0, reviewer: '', approver: '' })

// Dashboard
const dash = ref(null)
const typeData = computed(() => {
  if (!dash.value?.by_type) return []
  return Object.entries(dash.value.by_type).map(([type, data]) => ({ type, ...data }))
})

// Dialogs
const inspDialogVisible = ref(false)
const resultDialogVisible = ref(false)
const stockDialogVisible = ref(false)
const stockResultVisible = ref(false)
const inspFormRef = ref(null); const stockFormRef = ref(null)
const poOptions = ref([]); const materialOptions = ref([])

const inspForm = reactive({ inspection_type: 'IQC', source_type: '采购单', source_id: null, item_id: null, inspect_qty: 1, inspector: '', remark: '' })
const resultForm = reactive({ id: null, inspect_qty: 0, pass_qty: 0, reject_qty: 0, ncr_reason: '' })
const stockForm = reactive({ item_id: null, warehouse_id: 1, counter: '' })
const stockResultForm = reactive({ id: null, system_qty: 0, actual_qty: 0 })

function resultTag(r) {
  const map = { '待检': '', '合格': 'success', '部分合格': 'warning', '不合格': 'danger' }
  return map[r] || ''
}

function onTabChange(name) {
  if (name === 'inspection') fetchInspections()
  else if (name === 'standards') fetchStandards()
  else if (name === 'ncr') fetchNcr()
  else if (name === 'dashboard') fetchDashboard()
  else if (name === 'stock') fetchStock()
}

// ====== 检验记录 ======
async function fetchInspections() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterResult.value) params.result = filterResult.value
    if (filterType.value) params.inspection_type = filterType.value
    const res = await api.get('/inspection/inspections', { params })
    inspections.value = res.items; total.value = res.total
  } finally { loading.value = false }
}

async function showInspectionDialog() {
  const [poRes, matRes] = await Promise.all([
    api.get('/purchase/orders', { params: { page_size: 10000 } }),
    api.get('/materials/all'),
  ])
  poOptions.value = poRes.items || []
  materialOptions.value = matRes.items
  Object.assign(inspForm, { inspection_type: 'IQC', source_type: '采购单', source_id: null, item_id: null, inspect_qty: 1, inspector: '', remark: '' })
  inspDialogVisible.value = true
}

async function createInspection() {
  if (!inspForm.source_id) return ElMessage.warning('请选择来源单号')
  saving.value = true
  try {
    await api.post('/inspection/inspections', { ...inspForm })
    ElMessage.success('检验单已创建')
    inspDialogVisible.value = false
    fetchInspections()
  } finally { saving.value = false }
}

function showResultDialog(row) {
  Object.assign(resultForm, { id: row.id, inspect_qty: row.inspect_qty, pass_qty: 0, reject_qty: 0, ncr_reason: '' })
  resultDialogVisible.value = true
}

async function submitResult() {
  saving.value = true
  try {
    await api.put(`/inspection/inspections/${resultForm.id}/result`, {
      pass_qty: resultForm.pass_qty, reject_qty: resultForm.reject_qty,
      ncr_reason: resultForm.ncr_reason,
    })
    ElMessage.success('检验结果已提交')
    resultDialogVisible.value = false
    fetchInspections()
  } finally { saving.value = false }
}

// ====== 检验标准 ======
async function fetchStandards() {
  stdLoading.value = true
  try {
    const params = {}
    if (stdTypeFilter.value) params.inspection_type = stdTypeFilter.value
    const res = await api.get('/inspection/standards', { params })
    standards.value = res.items || []
  } finally { stdLoading.value = false }
}

async function showStdDialog() {
  const matRes = await api.get('/materials/all')
  materialOptions.value = matRes.items
  Object.assign(stdForm, { item_id: null, standard_code: '', standard_name: '', inspection_type: 'IQC', sampling_method: '全检', sample_size: 0, accept_level: 0 })
  stdDialogVisible.value = true
}

async function createStandard() {
  saving.value = true
  try {
    await api.post('/inspection/standards', { ...stdForm })
    ElMessage.success('检验标准已创建')
    stdDialogVisible.value = false
    fetchStandards()
  } finally { saving.value = false }
}

async function deleteStd(row) {
  await ElMessageBox.confirm('确定删除？', '提示')
  await api.delete(`/inspection/standards/${row.id}`)
  ElMessage.success('已删除')
  fetchStandards()
}

// ====== NCR ======
async function fetchNcr() {
  ncrLoading.value = true
  try {
    const params = {}
    if (ncrStatusFilter.value) params.status = ncrStatusFilter.value
    const res = await api.get('/inspection/ncr', { params })
    ncrs.value = res.items || []
  } finally { ncrLoading.value = false }
}

function showDisposeDialog(row) {
  Object.assign(disposeForm, { id: row.id, ncr_no: row.ncr_no, disposition: '退货', disposition_qty: row.qty, reviewer: '', approver: '' })
  disposeVisible.value = true
}

async function submitDispose() {
  saving.value = true
  try {
    await api.put(`/inspection/ncr/${disposeForm.id}/dispose`, {
      disposition: disposeForm.disposition, disposition_qty: disposeForm.disposition_qty,
      reviewer: disposeForm.reviewer, approver: disposeForm.approver,
    })
    ElMessage.success('NCR 已处置')
    disposeVisible.value = false
    fetchNcr()
  } finally { saving.value = false }
}

// ====== 质量看板 ======
async function fetchDashboard() {
  const res = await api.get('/inspection/dashboard')
  dash.value = res
}

// ====== 盘点 ======
async function fetchStock() {
  loading2.value = true
  try {
    const res = await api.get('/inspection/stock-counts', { params: { page: spage.value, page_size: spageSize.value } })
    stockCounts.value = res.items; stotal.value = res.total
  } finally { loading2.value = false }
}

async function showStockDialog() {
  const matRes = await api.get('/materials/all')
  materialOptions.value = matRes.items
  Object.assign(stockForm, { item_id: null, warehouse_id: 1, counter: '' })
  stockDialogVisible.value = true
}

async function createStockCount() {
  saving.value = true
  try {
    await api.post('/inspection/stock-counts', { ...stockForm })
    ElMessage.success('盘点计划已创建')
    stockDialogVisible.value = false
    fetchStock()
  } finally { saving.value = false }
}

function showStockResult(row) {
  Object.assign(stockResultForm, { id: row.id, system_qty: row.system_qty, actual_qty: row.system_qty })
  stockResultVisible.value = true
}

async function submitStockResult() {
  await api.put(`/inspection/stock-counts/${stockResultForm.id}/result`, { actual_qty: stockResultForm.actual_qty, counter: '' })
  ElMessage.success('盘点结果已提交')
  stockResultVisible.value = false
  fetchStock()
}

async function adjustStock(row) {
  await ElMessageBox.confirm(`确认调整库存？差异 ${row.difference} 件`, '提示')
  await api.post(`/inspection/stock-counts/${row.id}/adjust`, { operator: '系统' })
  ElMessage.success('库存已调整')
  fetchStock()
}

onMounted(fetchInspections)
</script>

<style scoped>
.page-container { padding: 0; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; flex-wrap:wrap; }
.kpi-card { flex:1; border-radius:10px; padding:18px; text-align:center; }
.kpi-label { font-size:13px; color:#666; display:block; margin-bottom:6px; }
.kpi-val { font-size:28px; font-weight:700; }
:deep(.el-table__body-wrapper) { overflow-x: auto; }
</style>
