<template>
  <div class="page-container space-y-4">
    <!-- 工具栏 + 标签切换 -->
    <div class="flex items-center gap-3 flex-wrap">
      <el-input v-model="keyword" placeholder="搜索型号/编码" style="width:220px" size="default" clearable @clear="onSearch" @keyup.enter="onSearch">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <span class="flex-1"></span>

      <!-- Pill 风格标签切换 -->
      <div class="flex rounded-lg bg-[var(--color-bg-overlay)] border border-[var(--color-border-light)] p-0.5">
        <button
          v-for="t in tabs"
          :key="t.key"
          :class="[
            'px-3.5 py-1.5 rounded-md text-xs font-medium transition-all duration-150 border-none cursor-pointer',
            tab === t.key
              ? 'bg-[var(--color-accent)] text-white shadow-sm'
              : 'bg-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
          ]"
          @click="switchTab(t.key)"
        >{{ t.label }}</button>
      </div>
    </div>

    <!-- ═══════ 零件管理 ═══════ -->
    <div v-if="tab === 'parts'" v-loading="loading">
      <!-- 批量操作 -->
      <div v-if="selectedIds.length" class="batch-bar">
        <span class="text-xs text-[var(--color-text-secondary)]">已选 <b>{{ selectedIds.length }}</b> 项</span>
        <div class="w-px h-4 bg-[var(--color-accent)]/30"></div>
        <span class="text-xs text-[var(--color-text-tertiary)]">安全库存</span>
        <el-input-number v-model="batchSafetyStock" :min="0" size="small" style="width:100px" />
        <el-button size="small" type="primary" @click="batchUpdateSafetyStock" :disabled="batchSafetyStock === null">批量更新</el-button>
        <span class="flex-1"></span>
        <el-button size="small" text @click="selectedIds = []">取消</el-button>
      </div>

      <!-- 三级折叠视图 -->
      <div v-if="projects.length" class="space-y-3">
        <div v-for="p in projects" :key="p.product_code" class="proj-card">
          <div class="proj-header" @click="p._open = !p._open">
            <span class="font-semibold text-[15px] text-[var(--color-text-primary)]">{{ p.product_name }}</span>
            <span class="text-xs text-[var(--color-text-tertiary)] ml-2">{{ p.module_count }} 模块</span>
            <span class="flex-1"></span>
            <el-icon :size="12" color="var(--color-text-tertiary)" class="transition-transform duration-200" :style="{ transform: p._open ? 'rotate(180deg)' : '' }">
              <ArrowDown />
            </el-icon>
          </div>
          <div v-show="p._open" class="px-3 pb-3 space-y-2">
            <div v-for="m in p.modules" :key="m.module_code" class="mod-card">
              <div class="mod-header" @click="m._open = !m._open">
                <span class="font-medium text-[var(--color-text-primary)]">{{ m.module_name }}</span>
                <span class="text-xs text-[var(--color-text-tertiary)] ml-2">{{ m.parts.length }} 项零件</span>
                <span class="flex-1"></span>
                <el-icon :size="11" color="var(--color-text-tertiary)" class="transition-transform duration-200" :style="{ transform: m._open ? 'rotate(180deg)' : '' }">
                  <ArrowDown />
                </el-icon>
              </div>
              <div v-show="m._open">
                <el-table
                  :data="getParts(m)"
                  size="small"
                  stripe
                  @selection-change="(rows) => onTableSel(rows, m.module_code)"
                  max-height="400"
                >
                  <el-table-column type="selection" width="38" />
                  <el-table-column prop="material_code" label="物料编码" width="120" />
                  <el-table-column prop="material_name" label="物料型号" min-width="120" show-overflow-tooltip />
                  <el-table-column prop="unit" label="单位" width="50" align="center" />

                  <!-- 库存 + 进度条 -->
                  <el-table-column label="库存" width="140" align="center">
                    <template #default="{ row }">
                      <div class="flex items-center gap-2">
                        <span class="text-sm font-semibold tabular-nums" :class="row.on_hand > 0 ? 'text-[var(--color-text-primary)]' : 'text-[var(--color-text-disabled)]'">
                          {{ row.on_hand || 0 }}
                        </span>
                        <div v-if="row.safety_stock > 0" class="flex-1 h-1.5 bg-[var(--color-bg-overlay)] rounded-full overflow-hidden">
                          <div
                            class="h-full rounded-full transition-all duration-300"
                            :class="stockLevelClass(row)"
                            :style="{ width: Math.min(100, ((row.on_hand || 0) / Math.max(row.safety_stock, 0.01)) * 100) + '%' }"
                          ></div>
                        </div>
                      </div>
                    </template>
                  </el-table-column>

                  <el-table-column prop="safety_stock" label="安全库存" width="70" align="center" />
                  <el-table-column label="最近入库" width="140">
                    <template #default="{ row }">
                      <div v-if="row.last_received_date" class="text-xs space-y-0.5">
                        <span class="text-[var(--color-success-text)]">+{{ row.last_received_qty }} {{ row.unit }}</span>
                        <span class="block text-[var(--color-text-tertiary)]">{{ row.last_received_date?.slice(0, 16) }}</span>
                      </div>
                      <span v-else class="text-xs text-[var(--color-text-disabled)]">—</span>
                    </template>
                  </el-table-column>

                  <el-table-column label="操作" width="120" fixed="right" align="center">
                    <template #default="{ row }">
                      <el-button size="small" type="success" link @click="quickIn(row)">入库</el-button>
                      <el-button size="small" type="danger" link @click="quickOut(row)">出库</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <el-empty v-if="!loading && !projects.length" description="暂无库存数据" />
    </div>

    <!-- ═══════ 产品管理 ═══════ -->
    <div v-if="tab === 'products'" v-loading="loading">
      <el-table :data="productStock" size="small" stripe empty-text="暂无产品库存">
        <el-table-column prop="material_code" label="产品编码" width="130" />
        <el-table-column prop="material_name" label="产品名称" min-width="150" show-overflow-tooltip />
        <el-table-column label="库存" width="100" align="center">
          <template #default="{ row }">
            <span class="font-semibold tabular-nums" :class="row.on_hand > 0 ? 'text-[var(--color-success-text)]' : 'text-[var(--color-text-disabled)]'">
              {{ row.on_hand || 0 }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" align="center">
          <template #default="{ row }">
            <el-button size="small" type="success" link @click="quickIn(row)">入库</el-button>
            <el-button size="small" type="danger" link @click="quickOut(row)">出库</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ═══════ 呆滞料预警 ═══════ -->
    <div v-if="tab === 'obsolete'" v-loading="loading" class="space-y-4">
      <!-- 摘要卡片 -->
      <div class="grid grid-cols-3 gap-3">
        <div class="stat-card flex items-center justify-between">
          <div>
            <div class="text-xs text-[var(--color-text-tertiary)]">⚠️ 严重呆滞</div>
            <div class="text-xl font-bold text-[var(--color-danger)] tabular-nums">
              {{ obsoleteSummary.severity_counts?.['严重'] || 0 }}
            </div>
          </div>
          <div class="w-9 h-9 rounded-lg bg-red-500/10 flex items-center justify-center">
            <el-icon :size="18" color="#ef4444"><WarningFilled /></el-icon>
          </div>
        </div>
        <div class="stat-card flex items-center justify-between">
          <div>
            <div class="text-xs text-[var(--color-text-tertiary)]">⚡ 需要关注</div>
            <div class="text-xl font-bold text-[var(--color-warning)] tabular-nums">
              {{ obsoleteSummary.severity_counts?.['关注'] || 0 }}
            </div>
          </div>
          <div class="w-9 h-9 rounded-lg bg-amber-500/10 flex items-center justify-center">
            <el-icon :size="18" color="#f59e0b"><Warning /></el-icon>
          </div>
        </div>
        <div class="stat-card flex items-center justify-between">
          <div>
            <div class="text-xs text-[var(--color-text-tertiary)]">提醒</div>
            <div class="text-xl font-bold text-[var(--color-info)] tabular-nums">
              {{ obsoleteSummary.severity_counts?.['提醒'] || 0 }}
            </div>
          </div>
          <div class="w-9 h-9 rounded-lg bg-cyan-500/10 flex items-center justify-center">
            <el-icon :size="18" color="#06b6d4"><InfoFilled /></el-icon>
          </div>
        </div>
      </div>

      <!-- 查询 -->
      <div class="flex items-center gap-3">
        <span class="text-sm text-[var(--color-text-secondary)]">呆滞天数阈值</span>
        <el-input-number v-model="obsoleteDays" :min="1" :max="365" size="small" style="width:100px" />
        <span class="text-xs text-[var(--color-text-tertiary)]">天未操作</span>
        <el-button type="primary" size="small" @click="fetchObsolete">查询</el-button>
      </div>

      <!-- 表格 -->
      <el-table :data="obsoleteData" stripe size="small" max-height="400" empty-text="暂无呆滞物料">
        <el-table-column prop="material_code" label="物料编码" width="120" />
        <el-table-column prop="material_name" label="物料型号" min-width="130" show-overflow-tooltip />
        <el-table-column prop="on_hand" label="库存量" width="70" align="center" />
        <el-table-column label="闲置天数" width="100" align="center">
          <template #default="{ row }">
            <span
              class="font-bold text-lg tabular-nums"
              :class="row.idle_days > 180 ? 'text-[var(--color-danger)]' : row.idle_days > 90 ? 'text-[var(--color-warning)]' : 'text-[var(--color-text-tertiary)]'"
            >{{ row.idle_days }}</span>
            <span class="text-xs text-[var(--color-text-tertiary)] ml-0.5">天</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_action" label="最近操作" width="80" align="center" />
        <el-table-column label="最近日期" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.last_date" class="text-xs text-[var(--color-text-tertiary)]">{{ row.last_date.slice(0, 10) }}</span>
            <span v-else class="text-xs text-[var(--color-danger-text)]">从未操作</span>
          </template>
        </el-table-column>
        <el-table-column label="等级" width="85" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.level === '⚠️严重' ? 'danger' : row.level === '⚡关注' ? 'warning' : 'info'"
              size="small"
              effect="dark"
            >{{ row.level }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ═══════ 出入库流水 ═══════ -->
    <div v-if="tab === 'tx'">
      <el-table :data="txData" v-loading="loading" stripe size="small" max-height="500" empty-text="暂无流水记录">
        <el-table-column label="时间" width="145">
          <template #default="{ row }">
            <span class="text-xs text-[var(--color-text-tertiary)]">{{ row.created_at?.slice(0, 16)?.replace('T', ' ') }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="material_code" label="物料编码" width="110" />
        <el-table-column prop="material_name" label="物料型号" min-width="100" show-overflow-tooltip />
        <el-table-column label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.transaction_type.includes('出') ? 'danger' : 'success'" size="small" effect="dark">
              {{ row.transaction_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="数量" width="70" align="center">
          <template #default="{ row }">
            <span class="font-semibold tabular-nums" :class="row.quantity > 0 ? 'text-[var(--color-success-text)]' : 'text-[var(--color-danger-text)]'">
              {{ row.quantity > 0 ? '+' + row.quantity : row.quantity }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="单号" width="130">
          <template #default="{ row }">
            <el-tag v-if="row.reference_no" size="small" effect="plain">{{ row.reference_no }}</el-tag>
            <span v-else class="text-[var(--color-text-disabled)]">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="operator" label="操作人" width="70" align="center" />
        <el-table-column prop="remark" label="备注" min-width="80" show-overflow-tooltip />
      </el-table>
    </div>

    <!-- ═══ 快速出入库对话框 ═══ -->
    <el-dialog v-model="quickDialogVisible" :title="quickType === 'in' ? '快速入库' : '快速出库'" width="420px">
      <el-form label-width="80px" label-position="top">
        <el-form-item label="物料">
          <span class="text-sm font-medium text-[var(--color-text-primary)]">{{ quickForm.material_code }} {{ quickForm.material_name }}</span>
        </el-form-item>
        <el-form-item label="当前库存">
          <el-tag :type="quickForm.on_hand > 0 ? 'success' : 'danger'" size="large" effect="dark">
            {{ quickForm.on_hand }} {{ quickForm.unit }}
          </el-tag>
        </el-form-item>
        <el-form-item :label="quickType === 'in' ? '入库数量' : '出库数量'">
          <el-input-number v-model="quickForm.qty" :min="1" :max="quickType === 'out' ? quickForm.on_hand : 99999" size="large" style="width:160px" />
        </el-form-item>
        <el-form-item label="操作人">
          <el-input v-model="quickForm.operator" placeholder="操作人姓名" />
        </el-form-item>
        <el-form-item v-if="quickForm.qty > 0" :label="quickType === 'in' ? '入库后库存' : '出库后库存'">
          <span class="text-lg font-bold" :class="(quickType === 'in' ? quickForm.on_hand + quickForm.qty : quickForm.on_hand - quickForm.qty) > 0 ? 'text-[var(--color-success-text)]' : 'text-[var(--color-danger-text)]'">
            {{ quickType === 'in' ? quickForm.on_hand + quickForm.qty : quickForm.on_hand - quickForm.qty }}
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="quickDialogVisible = false">取消</el-button>
        <el-button :type="quickType === 'in' ? 'success' : 'danger'" @click="doQuickTx" :loading="quickSaving">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

// ====== Tab 管理 ======
const tabs = [
  { key: 'parts', label: '零件管理' },
  { key: 'products', label: '产品管理' },
  { key: 'obsolete', label: '呆滞料预警' },
  { key: 'tx', label: '出入库流水' },
]
const loading = ref(false)
const tab = ref('parts')
const keyword = ref('')

function switchTab(key) {
  tab.value = key
  if (key === 'obsolete') fetchObsolete()
  if (key === 'tx') fetchTx()
}

// ====== 库存进度条 ======
function stockLevelClass(row) {
  if (!row.safety_stock || row.safety_stock === 0) return 'bg-[var(--color-accent)]'
  const ratio = (row.on_hand || 0) / row.safety_stock
  if (ratio < 0.5) return 'bg-[var(--color-danger)]'
  if (ratio < 1) return 'bg-[var(--color-warning)]'
  return 'bg-[var(--color-success)]'
}

// ====== 呆滞料预警 ======
const obsoleteDays = ref(90)
const obsoleteData = ref([])
const obsoleteSummary = ref({ severity_counts: {} })

async function fetchObsolete() {
  loading.value = true
  try {
    const res = await api.get('/inventory/obsolete', { params: { days: obsoleteDays.value } })
    obsoleteData.value = res.items || []
    obsoleteSummary.value = res.summary || { severity_counts: {} }
  } finally {
    loading.value = false
  }
}

// ====== 零件库存 ======
const projects = ref([])
const selectedIds = ref([])
const batchSafetyStock = ref(null)
const _allTableSels = {}

function onTableSel(rows, tableKey) {
  _allTableSels[tableKey] = (rows || []).map(r => r.item_id)
  selectedIds.value = Object.values(_allTableSels).flat()
}

const productStock = ref([])
const inventoryMap = ref({})

async function loadData() {
  loading.value = true
  try {
    const [treeRes, invRes] = await Promise.all([
      api.get('/materials/tree'),
      api.get('/inventory/summary'),
    ])
    const invMap = {}
    ;(invRes.items || []).forEach(i => { invMap[i.material_code] = i })
    inventoryMap.value = invMap
    productStock.value = (invRes.items || []).filter(i => i.material_type === '成品')
    projects.value = (treeRes.projects || []).map(p => ({
      ...p,
      _open: true,
      modules: (p.modules || []).map(m => ({
        ...m,
        _open: false,
        _enriched: (m.parts || []).map(part => {
          const inv = invMap[part.material_code] || {}
          return {
            ...part,
            on_hand: inv.on_hand || 0,
            last_received_qty: inv.last_received_qty || 0,
            last_received_date: inv.last_received_date,
          }
        }),
      })),
    }))
  } finally {
    loading.value = false
  }
}

function getParts(mod) {
  const enriched = mod._enriched || []
  if (keyword.value) {
    const kw = keyword.value.toLowerCase()
    return enriched.filter(p =>
      (p.material_code || '').toLowerCase().includes(kw) ||
      (p.material_name || '').toLowerCase().includes(kw)
    )
  }
  return enriched
}

function onSearch() { loadData() }

async function batchUpdateSafetyStock() {
  if (batchSafetyStock.value === null) return
  try {
    await ElMessageBox.confirm(
      `将 ${selectedIds.value.length} 个物料的安全库存设为 ${batchSafetyStock.value}？`,
      '批量更新安全库存',
      { type: 'info' }
    )
    await api.put('/materials/batch/safety-stock', {
      item_ids: selectedIds.value,
      safety_stock: batchSafetyStock.value,
    })
    ElMessage.success('已更新')
    selectedIds.value = []
    batchSafetyStock.value = null
    loadData()
  } catch (e) { console.error('[MRP]', e) }
}

// ====== 快速出入库 ======
const quickDialogVisible = ref(false)
const quickType = ref('in')
const quickSaving = ref(false)
const quickForm = reactive({
  item_id: null, material_code: '', material_name: '',
  unit: '', on_hand: 0, qty: 1, operator: '',
})

function quickIn(row) {
  quickType.value = 'in'
  Object.assign(quickForm, {
    item_id: row.id || row.item_id,
    material_code: row.material_code,
    material_name: row.material_name,
    unit: row.unit || '个',
    on_hand: row.on_hand || 0,
    qty: 1,
    operator: '',
  })
  quickDialogVisible.value = true
}

function quickOut(row) {
  quickType.value = 'out'
  Object.assign(quickForm, {
    item_id: row.id || row.item_id,
    material_code: row.material_code,
    material_name: row.material_name,
    unit: row.unit || '个',
    on_hand: row.on_hand || 0,
    qty: 1,
    operator: '',
  })
  quickDialogVisible.value = true
}

async function doQuickTx() {
  if (!quickForm.qty || quickForm.qty <= 0) return
  if (quickType.value === 'out' && quickForm.qty > quickForm.on_hand) {
    return ElMessage.error('出库数量不能超过现有库存')
  }
  quickSaving.value = true
  try {
    const whRes = await api.get('/inventory/warehouses')
    const whId = whRes.items?.[0]?.id || 1
    const qty = quickType.value === 'in' ? quickForm.qty : -quickForm.qty
    await api.post('/inventory/transaction', {
      item_id: quickForm.item_id,
      warehouse_id: whId,
      transaction_type: quickType.value === 'in' ? '入库' : '出库',
      quantity: qty,
      operator: quickForm.operator,
      remark: quickType.value === 'in' ? '手动入库' : '手动出库',
    })
    ElMessage.success(`${quickType.value === 'in' ? '入库' : '出库'} ${quickForm.qty}`)
    quickDialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.message || ''))
  } finally {
    quickSaving.value = false
  }
}

// ====== 出入库流水 ======
const txData = ref([])
async function fetchTx() {
  loading.value = true
  try {
    const r = await api.get('/inventory/transactions', { params: { page_size: 200 } })
    txData.value = r.items || []
  } finally {
    loading.value = false
  }
}

onMounted(() => { loadData(); fetchTx() })
</script>

<style scoped>
.page-container { padding: 0; }
</style>
