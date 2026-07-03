<template>
  <div class="page-container space-y-5 animate-fade-in">

    <!-- ══════════ KPI 统计卡片 ══════════ -->
    <div class="grid grid-cols-5 gap-4">
      <KpiCard
        label="物料总数"
        :value="stats.materialCount"
        icon="Box"
        color="blue"
        :loading="loading"
      />
      <KpiCard
        label="待处理采购"
        :value="stats.pendingPurchase"
        icon="ShoppingCart"
        color="amber"
        :loading="loading"
        :alert="stats.pendingPurchase > 0"
        alertLabel="待审核"
      />
      <KpiCard
        label="进行中工单"
        :value="stats.activeProduction"
        icon="SetUp"
        color="emerald"
        :loading="loading"
      />
      <KpiCard
        label="低库存预警"
        :value="stats.lowStockCount"
        icon="WarningFilled"
        color="red"
        :loading="loading"
        :alert="stats.lowStockCount > 0"
        alertLabel="需补货"
      />
      <KpiCard
        label="MRP 例外项"
        :value="stats.exceptionCount"
        icon="CircleCloseFilled"
        color="purple"
        :loading="loading"
        :alert="stats.exceptionCount > 0"
        alertLabel="待处理"
      />
    </div>

    <!-- ══════════ 快捷操作 + 最近概况 ══════════ -->
    <div class="grid grid-cols-3 gap-4">
      <!-- 快捷操作 -->
      <div class="stat-card">
        <h3 class="text-[var(--color-text-primary)] font-medium text-sm mb-4 flex items-center gap-2">
          <el-icon :size="14" color="var(--color-accent)"><Promotion /></el-icon>
          快捷操作
        </h3>
        <div class="grid grid-cols-2 gap-2">
          <QuickActionBtn to="/mrp" icon="Cpu" label="MRP 运算" desc="物料需求计算" color="blue" />
          <QuickActionBtn to="/materials" icon="Plus" label="新增物料" desc="录入物料数据" color="emerald" />
          <QuickActionBtn to="/bom" icon="Connection" label="BOM 管理" desc="物料清单维护" color="amber" />
          <QuickActionBtn to="/purchase" icon="ShoppingCart" label="采购管理" desc="采购订单处理" color="purple" />
          <QuickActionBtn to="/production" icon="SetUp" label="生产管理" desc="工单下达跟踪" color="cyan" />
          <QuickActionBtn to="/reports" icon="DataAnalysis" label="报表分析" desc="数据可视化" color="rose" />
        </div>
      </div>

      <!-- 最近 MRP 运算 -->
      <div class="stat-card">
        <h3 class="text-[var(--color-text-primary)] font-medium text-sm mb-4 flex items-center gap-2">
          <el-icon :size="14" color="var(--color-accent)"><Timer /></el-icon>
          最近 MRP 运算
        </h3>
        <div v-if="loading" class="space-y-3">
          <div v-for="i in 3" :key="i" class="h-8 bg-[var(--color-bg-overlay)] rounded animate-pulse"></div>
        </div>
        <div v-else-if="lastMrpRuns.length === 0" class="flex flex-col items-center justify-center py-8 text-[var(--color-text-tertiary)]">
          <el-icon :size="32" color="var(--color-text-disabled)"><Cpu /></el-icon>
          <p class="mt-2 text-xs">暂无 MRP 运算记录</p>
          <router-link to="/mrp" class="mt-3 text-xs text-[var(--color-accent)] hover:underline">前往 MRP 运算 →</router-link>
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="(run, i) in lastMrpRuns"
            :key="i"
            class="flex items-center justify-between py-2 px-3 rounded-md bg-[var(--color-bg-overlay)] text-xs"
          >
            <div class="flex items-center gap-2">
              <span
                class="w-1.5 h-1.5 rounded-full"
                :class="run.status === 'success' ? 'bg-[var(--color-success)]' : 'bg-[var(--color-danger)]'"
              ></span>
              <span class="text-[var(--color-text-secondary)]">{{ run.time }}</span>
            </div>
            <div class="flex items-center gap-3 text-[var(--color-text-tertiary)]">
              <span>{{ run.orders }} 计划订单</span>
              <span>{{ run.exceptions }} 例外</span>
              <span class="text-[var(--color-text-disabled)]">{{ run.duration }}ms</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 系统状态 -->
      <div class="stat-card">
        <h3 class="text-[var(--color-text-primary)] font-medium text-sm mb-4 flex items-center gap-2">
          <el-icon :size="14" color="var(--color-success)"><Monitor /></el-icon>
          系统状态
        </h3>
        <div class="space-y-3">
          <StatusRow label="数据库" status="connected" />
          <StatusRow label="定时任务" :status="timerEnabled ? 'active' : 'paused'" />
          <StatusRow label="MRP 引擎" status="ready" />
          <StatusRow label="API 服务" status="connected" />
        </div>
        <div class="mt-4 pt-4 border-t border-[var(--color-border-subtle)]">
          <div class="flex items-center justify-between text-xs">
            <span class="text-[var(--color-text-tertiary)]">定时 MRP</span>
            <span
              :class="timerEnabled ? 'text-[var(--color-success-text)]' : 'text-[var(--color-text-tertiary)]'"
            >
              {{ timerEnabled ? '已启用' : '已暂停' }}
            </span>
          </div>
          <div v-if="timerEnabled" class="flex items-center justify-between text-xs mt-1">
            <span class="text-[var(--color-text-tertiary)]">下次执行</span>
            <span class="text-[var(--color-text-secondary)] font-mono">{{ timerHour }}:{{ String(timerMinute).padStart(2, '0') }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ══════════ 图表区域 ══════════ -->
    <div class="grid grid-cols-2 gap-4">
      <!-- 库存概览图 -->
      <div class="stat-card">
        <h3 class="text-[var(--color-text-primary)] font-medium text-sm mb-3">库存概览（按物料类型）</h3>
        <div ref="inventoryChart" style="height: 280px"></div>
        <div v-if="!invData.length && !loading" class="flex items-center justify-center h-[280px] text-[var(--color-text-tertiary)] text-xs">
          暂无库存数据
        </div>
      </div>

      <!-- 工单状态分布 -->
      <div class="stat-card">
        <h3 class="text-[var(--color-text-primary)] font-medium text-sm mb-3">工单状态分布</h3>
        <div ref="woChart" style="height: 280px"></div>
        <div v-if="!woData.length && !loading" class="flex items-center justify-center h-[280px] text-[var(--color-text-tertiary)] text-xs">
          暂无工单数据
        </div>
      </div>
    </div>

    <!-- ══════════ 低库存预警 ══════════ -->
    <div class="stat-card" v-if="lowStockItems.length > 0">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-[var(--color-text-primary)] font-medium text-sm flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-[var(--color-danger)] shadow-[0_0_6px_var(--color-danger)]"></span>
          低库存预警
        </h3>
        <router-link to="/inventory" class="text-xs text-[var(--color-accent)] hover:underline">查看全部 →</router-link>
      </div>
      <el-table :data="lowStockItems.slice(0, 5)" stripe size="small">
        <el-table-column prop="material_code" label="物料编码" width="120" />
        <el-table-column prop="material_name" label="物料型号" min-width="160" show-overflow-tooltip />
        <el-table-column prop="on_hand" label="现有库存" width="90" align="center" />
        <el-table-column prop="safety_stock" label="安全库存" width="90" align="center" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.available <= 0 ? 'danger' : 'warning'" size="small" effect="dark">
              {{ row.available <= 0 ? '缺料' : '偏低' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import api from '@/api'
import KpiCard from '@/components/KpiCard.vue'
import QuickActionBtn from '@/components/QuickActionBtn.vue'
import StatusRow from '@/components/StatusRow.vue'

const route = useRoute()
const loading = ref(true)

// ====== 统计数据 ======
const stats = ref({
  materialCount: 0,
  pendingPurchase: 0,
  activeProduction: 0,
  lowStockCount: 0,
  exceptionCount: 0,
})

// ====== MRP 运行记录 ======
const lastMrpRuns = ref([])

// ====== 定时器状态 ======
const timerEnabled = ref(false)
const timerHour = ref(6)
const timerMinute = ref(0)

// ====== 图表数据 ======
const inventoryChart = ref(null)
const woChart = ref(null)
const invData = ref([])
const woData = ref([])
const lowStockItems = ref([])

// ====== 数据加载 ======
async function loadDashboard() {
  loading.value = true
  try {
    await Promise.all([
      loadStats(),
      loadMrpHistory(),
      loadInventory(),
      loadWorkOrders(),
      loadTimer(),
    ])
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const [materials, purchases, productions, inventory, exceptions] = await Promise.all([
      api.get('/materials', { params: { page_size: 1 } }),
      api.get('/purchase/orders', { params: { page_size: 1 } }),
      api.get('/production/orders', { params: { page_size: 1 } }),
      api.get('/inventory/summary'),
      api.get('/exceptions', { params: { page_size: 1 } }),
    ])
    stats.value.materialCount = materials.total || 0
    stats.value.pendingPurchase = purchases.total || 0
    stats.value.activeProduction = productions.total || 0
    stats.value.lowStockCount = (inventory.items || []).filter(i => i.is_low).length
    stats.value.exceptionCount = exceptions.total || 0
  } catch (e) {
    console.error('加载统计数据失败:', e)
  }
}

async function loadMrpHistory() {
  try {
    const res = await api.get('/exceptions', { params: { page_size: 5 } })
    // 从例外记录反推 MRP 运行历史
    const items = res.items || []
    if (items.length > 0) {
      // 按创建时间分组
      const grouped = {}
      items.forEach(item => {
        const key = item.created_at ? item.created_at.slice(0, 16) : 'unknown'
        if (!grouped[key]) grouped[key] = { time: key, orders: 0, exceptions: 0, status: 'success', duration: 0 }
        grouped[key].exceptions++
      })
      lastMrpRuns.value = Object.values(grouped).slice(0, 3)
    }
  } catch {
    lastMrpRuns.value = []
  }
}

async function loadInventory() {
  try {
    const res = await api.get('/inventory/summary', { params: { page_size: 1000 } })
    const items = res.items || []
    lowStockItems.value = items.filter(i => i.is_low).slice(0, 5)

    // 按物料类型分组
    const typeMap = {}
    items.forEach(i => {
      const t = i.material_type || '其他'
      typeMap[t] = (typeMap[t] || 0) + (i.on_hand || 0)
    })
    invData.value = Object.entries(typeMap).map(([name, value]) => ({ name, value }))
    renderInventoryChart()
  } catch {
    lowStockItems.value = []
    invData.value = []
  }
}

async function loadWorkOrders() {
  try {
    const res = await api.get('/production/orders', { params: { page_size: 1000 } })
    const orders = res.items || []
    const statusMap = {}
    orders.forEach(o => {
      statusMap[o.status] = (statusMap[o.status] || 0) + 1
    })
    const statusOrder = ['待下达', '已下达', '进行中', '已完成', '已关闭']
    woData.value = statusOrder.map(s => ({ name: s, value: statusMap[s] || 0 }))
    renderWoChart()
  } catch {
    woData.value = []
  }
}

async function loadTimer() {
  try {
    const r = await fetch('/api/system/schedule')
    const d = await r.json()
    timerEnabled.value = d.enabled
    timerHour.value = d.hour
    timerMinute.value = d.minute
  } catch {}
}

// ====== 图表渲染 ======
function renderInventoryChart() {
  if (!inventoryChart.value || !invData.value.length) return
  const chart = echarts.init(inventoryChart.value)
  chart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1a1a1e',
      borderColor: '#333',
      textStyle: { color: '#ccc', fontSize: 12 },
    },
    legend: {
      bottom: 0,
      textStyle: { color: '#888', fontSize: 11 },
      itemWidth: 8,
      itemHeight: 8,
    },
    series: [{
      type: 'pie',
      radius: ['50%', '75%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      itemStyle: { borderColor: '#1a1a1e', borderWidth: 2 },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#e8e8ed' },
      },
      data: invData.value.map(d => ({
        ...d,
        itemStyle: {
          color: getTypeColor(d.name),
        },
      })),
    }],
  })
  window.addEventListener('resize', () => chart.resize())
}

function renderWoChart() {
  if (!woChart.value || !woData.value.length) return
  const chart = echarts.init(woChart.value)
  chart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1a1a1e',
      borderColor: '#333',
      textStyle: { color: '#ccc', fontSize: 12 },
    },
    grid: { left: 8, right: 16, top: 8, bottom: 24 },
    xAxis: {
      type: 'category',
      data: woData.value.map(d => d.name),
      axisLine: { lineStyle: { color: '#333' } },
      axisLabel: { color: '#888', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#2a2a2e' } },
      axisLabel: { color: '#888', fontSize: 11 },
    },
    series: [{
      type: 'bar',
      data: woData.value.map((d, i) => ({
        value: d.value,
        itemStyle: {
          color: ['#3b82f6', '#f59e0b', '#22c55e', '#06b6d4', '#6b7280'][i],
          borderRadius: [4, 4, 0, 0],
        },
      })),
      barWidth: 32,
      label: {
        show: true,
        position: 'top',
        color: '#a0a0a8',
        fontSize: 11,
      },
    }],
  })
  window.addEventListener('resize', () => chart.resize())
}

function getTypeColor(type) {
  const map = {
    '成品': '#3b82f6',
    '半成品': '#8b5cf6',
    '零件': '#22c55e',
    '原材料': '#f59e0b',
    '模块': '#06b6d4',
  }
  return map[type] || '#6b7280'
}

// ====== 路由切换时重新加载 ======
watch(() => route.path, (newPath) => {
  if (newPath === '/dashboard') {
    loadDashboard()
  }
})

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped>
/* 动画脉冲 */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
