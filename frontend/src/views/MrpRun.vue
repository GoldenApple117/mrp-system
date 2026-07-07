<template>
  <div class="page-container space-y-5">
    <!-- ═══════ 第一部分：数据就绪状态 ═══════ -->
    <div class="grid grid-cols-4 gap-4">
      <div class="stat-card flex items-center justify-between">
        <div>
          <div class="text-xs text-[var(--color-text-tertiary)] mb-0.5">MPS 计划</div>
          <div class="text-xl font-semibold text-[var(--color-text-primary)] tabular-nums">
            <span v-if="!readyChecked" class="text-[var(--color-text-disabled)]">—</span>
            <span v-else>{{ readiness.mpsCount }}</span>
          </div>
        </div>
        <div
          :class="['w-9 h-9 rounded-lg flex items-center justify-center', readiness.mpsCount > 0 ? 'bg-emerald-500/10' : 'bg-amber-500/10']"
        >
          <el-icon :size="18" :color="readiness.mpsCount > 0 ? '#22c55e' : '#f59e0b'"
            ><Calendar
          /></el-icon>
        </div>
      </div>

      <div class="stat-card flex items-center justify-between">
        <div>
          <div class="text-xs text-[var(--color-text-tertiary)] mb-0.5">BOM 物料清单</div>
          <div class="text-xl font-semibold text-[var(--color-text-primary)] tabular-nums">
            <span v-if="!readyChecked" class="text-[var(--color-text-disabled)]">—</span>
            <span v-else>{{ readiness.bomCount }}</span>
          </div>
        </div>
        <div
          :class="['w-9 h-9 rounded-lg flex items-center justify-center', readiness.bomCount > 0 ? 'bg-emerald-500/10' : 'bg-amber-500/10']"
        >
          <el-icon :size="18" :color="readiness.bomCount > 0 ? '#22c55e' : '#f59e0b'"
            ><Connection
          /></el-icon>
        </div>
      </div>

      <div class="stat-card flex items-center justify-between">
        <div>
          <div class="text-xs text-[var(--color-text-tertiary)] mb-0.5">库存记录</div>
          <div class="text-xl font-semibold text-[var(--color-text-primary)] tabular-nums">
            <span v-if="!readyChecked" class="text-[var(--color-text-disabled)]">—</span>
            <span v-else>{{ readiness.invCount }}</span>
          </div>
        </div>
        <div
          :class="['w-9 h-9 rounded-lg flex items-center justify-center', readiness.invCount > 0 ? 'bg-emerald-500/10' : 'bg-amber-500/10']"
        >
          <el-icon :size="18" :color="readiness.invCount > 0 ? '#22c55e' : '#f59e0b'"
            ><List
          /></el-icon>
        </div>
      </div>

      <div
        class="stat-card flex items-center justify-between"
        :class="readiness.allReady ? 'border-[var(--color-success)]/30' : 'border-[var(--color-warning)]/30'"
      >
        <div>
          <div class="text-xs text-[var(--color-text-tertiary)] mb-0.5">就绪状态</div>
          <div class="flex items-center gap-1.5 mt-0.5">
            <span
              class="w-1.5 h-1.5 rounded-full"
              :class="readiness.allReady ? 'bg-[var(--color-success)]' : 'bg-[var(--color-warning)]'"
            ></span>
            <span
              class="text-sm font-medium"
              :class="readiness.allReady ? 'text-[var(--color-success-text)]' : 'text-[var(--color-warning-text)]'"
            >
              {{ readiness.allReady ? '可以运算' : '缺少数据' }}
            </span>
          </div>
        </div>
        <el-button size="small" text :loading="checking" @click="checkReadiness">
          <el-icon :size="14"><Refresh /></el-icon>
        </el-button>
      </div>

      <!-- 缺少数据的引导提示 -->
      <div
        v-if="readyChecked && !readiness.allReady"
        class="col-span-4 py-3 px-4 rounded-lg bg-[var(--color-warning-muted)] border border-[var(--color-warning)]/20"
      >
        <div class="flex items-center gap-2 text-sm text-[var(--color-warning-text)]">
          <el-icon :size="14"><WarningFilled /></el-icon>
          <span>数据不完整，请先补充：</span>
          <template v-if="readiness.mpsCount === 0">
            <router-link to="/mps" class="text-[var(--color-accent)] hover:underline text-xs"
              >录入 MPS 计划</router-link
            >
            <span class="text-[var(--color-text-disabled)]">|</span>
          </template>
          <template v-if="readiness.bomCount === 0">
            <router-link to="/bom" class="text-[var(--color-accent)] hover:underline text-xs"
              >创建 BOM</router-link
            >
            <span class="text-[var(--color-text-disabled)]">|</span>
          </template>
          <template v-if="readiness.invCount === 0">
            <router-link to="/inventory" class="text-[var(--color-accent)] hover:underline text-xs"
              >录入库存</router-link
            >
          </template>
        </div>
      </div>
    </div>

    <!-- ═══════ 第二部分：参数配置 + 执行 ═══════ -->
    <div class="stat-card">
      <div class="flex items-end gap-6">
        <!-- 展望期 -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs text-[var(--color-text-tertiary)] font-medium">展望期（天）</label>
          <div class="flex items-center gap-2">
            <el-slider
              v-model="horizonDays"
              :min="7"
              :max="180"
              :step="1"
              :show-tooltip="true"
              class="w-[200px]"
            />
            <el-input-number
              v-model="horizonDays"
              :min="7"
              :max="180"
              size="small"
              controls-position="right"
              class="w-[72px]"
            />
          </div>
        </div>

        <!-- 时界 -->
        <div class="flex flex-col gap-1.5">
          <label class="text-xs text-[var(--color-text-tertiary)] font-medium">时界（天）</label>
          <div class="flex items-center gap-2">
            <el-slider
              v-model="timeFenceDays"
              :min="0"
              :max="30"
              :step="1"
              :show-tooltip="true"
              class="w-[160px]"
            />
            <el-input-number
              v-model="timeFenceDays"
              :min="0"
              :max="30"
              size="small"
              controls-position="right"
              class="w-[64px]"
            />
          </div>
        </div>

        <!-- CTA -->
        <button
          class="flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-semibold text-white
                 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700
                 transition-all duration-200 shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30
                 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="running || !readiness.allReady"
          @click="runMrp"
        >
          <span
            v-if="running"
            class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"
          ></span>
          <el-icon v-else :size="16"><Cpu /></el-icon>
          {{ running ? '计算中...' : '一键 MRP 运算' }}
        </button>

        <div v-if="running" class="flex-1">
          <div class="flex items-center gap-3">
            <div class="flex-1 h-1.5 bg-[var(--color-bg-overlay)] rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full transition-all duration-700 ease-out"
                :style="{ width: progressPct + '%' }"
              ></div>
            </div>
            <span
              class="text-xs text-[var(--color-text-tertiary)] font-mono min-w-[60px]"
              >{{ progressStep }}</span
            >
          </div>
        </div>
      </div>

      <!-- 参数说明 -->
      <div
        class="mt-3 pt-3 border-t border-[var(--color-border-subtle)] flex items-center gap-4 text-xs text-[var(--color-text-tertiary)]"
      >
        <span class="flex items-center gap-1"
          ><el-icon :size="12"><InfoFilled /></el-icon>基于 MPS 主计划 + BOM 物料清单 +
          库存现存量，按时间倒推计算各层级物料需求</span
        >
      </div>
    </div>

    <!-- ═══════ 第三部分：运算结果 ═══════ -->
    <template v-if="summary">
      <!-- KPI 结果卡片 -->
      <div class="grid grid-cols-4 gap-4">
        <div class="stat-card flex flex-col gap-1">
          <div class="text-xs text-[var(--color-text-tertiary)]">计划订单</div>
          <div class="text-2xl font-bold text-[var(--color-text-primary)] tabular-nums">
            {{ summary.total_orders }}
          </div>
          <div class="flex items-center gap-1.5 text-xs">
            <span class="text-[var(--color-accent-text)]"
              >{{ summary.production_orders }} 生产</span
            >
            <span class="text-[var(--color-text-disabled)]">·</span>
            <span class="text-[var(--color-warning-text)]">{{ summary.purchase_orders }} 采购</span>
          </div>
        </div>

        <div class="stat-card flex flex-col gap-1">
          <div class="text-xs text-[var(--color-text-tertiary)]">例外信息</div>
          <div
            class="text-2xl font-bold tabular-nums"
            :class="summary.error_count > 0 ? 'text-[var(--color-danger)]' : 'text-[var(--color-warning-text)]'"
          >
            {{ summary.exceptions_count }}
          </div>
          <div class="flex items-center gap-1.5 text-xs">
            <span v-if="summary.error_count > 0" class="text-[var(--color-danger-text)]"
              >{{ summary.error_count }} 错误</span
            >
            <span v-if="summary.warning_count > 0" class="text-[var(--color-warning-text)]"
              >{{ summary.warning_count }} 警告</span
            >
            <span
              v-if="summary.error_count === 0 && summary.warning_count === 0"
              class="text-[var(--color-success-text)]"
              >无异常</span
            >
          </div>
        </div>

        <div class="stat-card flex flex-col gap-1">
          <div class="text-xs text-[var(--color-text-tertiary)]">运算耗时</div>
          <div class="text-2xl font-bold text-[var(--color-text-primary)] tabular-nums">
            {{ summary.run_time_ms }}
          </div>
          <div class="text-xs text-[var(--color-text-tertiary)]">毫秒完成</div>
        </div>

        <div class="stat-card flex flex-col gap-1">
          <div class="text-xs text-[var(--color-text-tertiary)]">展望范围</div>
          <div class="text-2xl font-bold text-[var(--color-text-primary)] tabular-nums">
            {{ summary.horizon_days }}
          </div>
          <div class="text-xs text-[var(--color-text-tertiary)]">
            天 {{ stepFrozen ? '· 时界: ' + stepFrozen + '天 冻结' : '' }}
          </div>
        </div>
      </div>

      <!-- 例外信息 -->
      <div v-if="exceptions.length" class="stat-card">
        <div
          class="flex items-center justify-between mb-3 cursor-pointer"
          @click="exceptionsOpen = !exceptionsOpen"
        >
          <h3 class="flex items-center gap-2 text-sm font-medium">
            <span
              class="w-2 h-2 rounded-full"
              :class="summary.error_count > 0 ? 'bg-[var(--color-danger)]' : 'bg-[var(--color-warning)]'"
            ></span>
            例外信息（{{ exceptions.length }}）
          </h3>
          <el-icon
            :size="14"
            color="var(--color-text-tertiary)"
            class="transition-transform duration-200"
            :style="{ transform: exceptionsOpen ? 'rotate(180deg)' : '' }"
          >
            <ArrowDown />
          </el-icon>
        </div>
        <div v-show="exceptionsOpen" class="space-y-1.5">
          <div
            v-for="(ex, i) in exceptions"
            :key="i"
            :class="[
              'flex items-start gap-3 px-3 py-2.5 rounded-md text-sm',
              ex.severity === 'ERROR'
                ? 'bg-red-500/5 border border-red-500/15'
                : 'bg-amber-500/5 border border-amber-500/15'
            ]"
          >
            <el-tag
              :type="ex.severity === 'ERROR' ? 'danger' : 'warning'"
              size="small"
              effect="dark"
              class="flex-shrink-0 mt-px"
            >
              {{ ex.severity }}
            </el-tag>
            <span class="text-[var(--color-text-secondary)] leading-relaxed">{{ ex.message }}</span>
          </div>
        </div>
      </div>

      <!-- 计划订单结果 -->
      <div class="stat-card">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-medium text-[var(--color-text-primary)]">
            计划订单结果（{{ plannedOrders.length }}）
          </h3>
          <el-button
            type="primary"
            size="small"
            :loading="converting"
            :disabled="!plannedOrders.length"
            @click="convertToOrders"
          >
            一键转为采购/工单
          </el-button>
        </div>

        <el-table
          :data="plannedOrders"
          stripe
          max-height="440"
          size="small"
          empty-text="暂无计划订单"
        >
          <el-table-column prop="item_code" label="物料编码" width="120" />
          <el-table-column
            prop="material_name"
            label="物料型号"
            min-width="140"
            show-overflow-tooltip
          />
          <el-table-column label="订单类型" width="90" align="center">
            <template #default="{ row }">
              <el-tag
                :type="row.order_type === 'PURCHASE' ? 'warning' : 'primary'"
                size="small"
                effect="dark"
              >
                {{ row.order_type === 'PURCHASE' ? '采购' : '生产' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="level" label="BOM层级" width="80" align="center" />
          <el-table-column prop="release_date" label="建议下达" width="110" />
          <el-table-column prop="required_date" label="需求日期" width="110" />
          <el-table-column prop="quantity" label="数量" width="90" align="right">
            <template #default="{ row }">
              <span class="font-mono text-sm tabular-nums">{{ row.quantity }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </template>

    <!-- ═══════ 空状态：引导式空白 ═══════ -->
    <div
      v-if="!running && !summary && readyChecked"
      class="stat-card flex flex-col items-center justify-center py-16 space-y-4"
    >
      <div class="w-16 h-16 rounded-full bg-blue-500/10 flex items-center justify-center">
        <el-icon :size="28" color="#3b82f6"><Cpu /></el-icon>
      </div>
      <div class="text-center space-y-1">
        <h3 class="text-[var(--color-text-primary)] font-medium text-sm">准备开始物料需求计算</h3>
        <p class="text-xs text-[var(--color-text-tertiary)]">
          配置参数后，点击「一键 MRP 运算」生成采购/生产建议
        </p>
      </div>
    </div>

    <div
      v-if="!readyChecked && !running && !summary"
      class="stat-card flex items-center justify-center py-10"
    >
      <div
        class="w-5 h-5 border-2 border-[var(--color-accent)] border-t-transparent rounded-full animate-spin"
      ></div>
      <span class="ml-3 text-sm text-[var(--color-text-tertiary)]">检查数据状态...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Cpu, WarningFilled, InfoFilled } from '@element-plus/icons-vue'
import api from '@/api'

// ====== 参数 ======
const horizonDays = ref(90)
const timeFenceDays = ref(7)

// ====== 就绪状态 ======
const readyChecked = ref(false)
const checking = ref(false)
const readiness = ref({ mpsCount: 0, bomCount: 0, invCount: 0, allReady: false })

async function checkReadiness() {
  checking.value = true
  try {
    const [mps, bom, inv] = await Promise.all([
      api.get('/mps', { params: { page_size: 1 } }).then(r => r.total || 0).catch(() => 0),
      api.get('/bom/headers', { params: { page_size: 1 } }).then(r => r.total || 0).catch(() => 0),
      api.get('/inventory', { params: { page_size: 1 } }).then(r => r.total || 0).catch(() => 0),
    ])
    readiness.value = {
      mpsCount: mps,
      bomCount: bom,
      invCount: inv,
      allReady: mps > 0 && bom > 0 && inv > 0,
    }
    readyChecked.value = true
  } finally {
    checking.value = false
  }
}

// ====== 运算 ======
const running = ref(false)
const summary = ref(null)
const plannedOrders = ref([])
const exceptions = ref([])
const exceptionsOpen = ref(true)
const stepFrozen = ref(false)
const progressPct = ref(0)
const progressStep = ref('')

const progressSteps = [
  { pct: 15, label: '展开 BOM...' },
  { pct: 35, label: '计算净需求...' },
  { pct: 55, label: '生成计划订单...' },
  { pct: 75, label: '检测例外...' },
  { pct: 90, label: '汇总结果...' },
]

let progressTimer = null

function startProgress() {
  progressPct.value = 0
  let i = 0
  progressTimer = setInterval(() => {
    if (i < progressSteps.length) {
      progressPct.value = progressSteps[i].pct
      progressStep.value = progressSteps[i].label
      i++
    }
  }, 600)
}

function finishProgress() {
  clearInterval(progressTimer)
  progressPct.value = 100
  progressStep.value = '完成'
  setTimeout(() => { progressPct.value = 0; progressStep.value = '' }, 1500)
}

async function runMrp() {
  running.value = true
  plannedOrders.value = []
  exceptions.value = []
  summary.value = null
  stepFrozen.value = false
  startProgress()

  try {
    const res = await api.post('/mrp/run', {
      horizon_days: horizonDays.value,
      time_fence_days: timeFenceDays.value,
    })
    finishProgress()

    if (res.success) {
      plannedOrders.value = res.data.planned_orders || []
      exceptions.value = res.data.exceptions || []
      summary.value = res.data.summary
      exceptionsOpen.value = true
      ElMessage.success(res.message || `完成${res.data.summary.total_orders}个计划订单`)
    } else {
      ElMessage.warning(res.message)
    }
  } catch {
    finishProgress()
    ElMessage.error('MRP 运算失败，请检查数据完整性')
  } finally {
    running.value = false
  }
}

// ====== 转换 ======
const converting = ref(false)

async function convertToOrders() {
  converting.value = true
  try {
    const res = await api.post('/mrp/convert-to-orders', {
      planned_orders: plannedOrders.value,
    })
    ElMessage.success(res.message)
  } catch {
    ElMessage.error('转换失败')
  } finally {
    converting.value = false
  }
}

// ====== 初始化 ======
onMounted(() => {
  checkReadiness()
})
</script>

<style scoped>
/* ── 旋转动画 ── */
@keyframes spin {
  to { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 0.8s linear infinite;
}
</style>
