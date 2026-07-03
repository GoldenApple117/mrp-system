<template>
  <div class="page-container space-y-4">
    <div class="flex items-center justify-between">
      <h3 class="text-[15px] font-semibold text-[var(--color-text-primary)]">报表与分析</h3>
      <span class="text-xs text-[var(--color-text-tertiary)]">数据实时刷新</span>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <!-- 订单准时率 -->
      <div class="stat-card">
        <div class="flex items-center justify-between mb-3">
          <h4 class="text-sm font-medium text-[var(--color-text-primary)]">订单准时交付率 (OTD)</h4>
          <el-tag size="small" effect="dark" :type="otdRate >= 80 ? 'success' : otdRate >= 60 ? 'warning' : 'danger'">
            {{ otdRate }}%
          </el-tag>
        </div>
        <div v-if="otdData.length" ref="otdChart" style="height: 300px"></div>
        <div v-else class="flex items-center justify-center h-[300px] text-xs text-[var(--color-text-tertiary)]">
          暂无订单数据
        </div>
      </div>

      <!-- 库存概览 -->
      <div class="stat-card">
        <h4 class="text-sm font-medium text-[var(--color-text-primary)] mb-3">库存概览（按物料类型）</h4>
        <div v-if="invData.length" ref="inventoryChart" style="height: 300px"></div>
        <div v-else class="flex items-center justify-center h-[300px] text-xs text-[var(--color-text-tertiary)]">
          暂无库存数据
        </div>
      </div>

      <!-- 缺料统计 -->
      <div class="stat-card">
        <h4 class="text-sm font-medium text-[var(--color-text-primary)] mb-3 flex items-center gap-2">
          <span class="w-1.5 h-1.5 rounded-full bg-[var(--color-danger)]"></span>
          缺料 / 低库存物料
        </h4>
        <el-table :data="lowStockItems" stripe size="small" max-height="260" v-if="lowStockItems.length">
          <el-table-column prop="material_code" label="物料编码" width="110" />
          <el-table-column prop="material_name" label="物料型号" min-width="130" show-overflow-tooltip />
          <el-table-column prop="on_hand" label="现有库存" width="80" align="center" />
          <el-table-column prop="safety_stock" label="安全库存" width="80" align="center" />
          <el-table-column prop="available" label="可用量" width="80" align="center" />
          <el-table-column label="状态" width="75" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_low ? 'danger' : 'success'" size="small" effect="dark">
                {{ row.is_low ? '偏低' : '正常' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无低库存物料" :image-size="60" />
      </div>

      <!-- 工单状态 -->
      <div class="stat-card">
        <h4 class="text-sm font-medium text-[var(--color-text-primary)] mb-3">工单状态分布</h4>
        <div v-if="woData.length" ref="woChart" style="height: 300px"></div>
        <div v-else class="flex items-center justify-center h-[300px] text-xs text-[var(--color-text-tertiary)]">
          暂无工单数据
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'
import { darkChartOptions, chartColors, woStatusColors, materialTypeColors } from '@/utils/echarts-theme'

const otdChart = ref(null)
const inventoryChart = ref(null)
const woChart = ref(null)
const lowStockItems = ref([])
const otdData = ref([])
const invData = ref([])
const woData = ref([])
const otdRate = ref(0)

// ====== 数据加载 ======
async function fetchLowStock() {
  try {
    const res = await api.get('/inventory/summary')
    lowStockItems.value = (res.items || []).filter(i => i.is_low).slice(0, 20)
  } catch { lowStockItems.value = [] }
}

async function fetchWoData() {
  try {
    const res = await api.get('/production/orders', { params: { page_size: 1000 } })
    const orders = res.items || []
    const statusMap = {}
    for (const o of orders) {
      statusMap[o.status] = (statusMap[o.status] || 0) + 1
    }
    const statusOrder = ['待下达', '已下达', '进行中', '已完成', '已关闭']
    woData.value = statusOrder
      .map(s => ({ status: s, count: statusMap[s] || 0 }))
      .filter(d => d.count > 0)
  } catch { woData.value = [] }
}

async function fetchInvData() {
  try {
    const res = await api.get('/inventory/summary', { params: { page_size: 1000 } })
    const items = res.items || []
    const typeMap = {}
    for (const i of items) {
      const t = i.material_type || '其他'
      typeMap[t] = (typeMap[t] || 0) + (i.on_hand || 0)
    }
    invData.value = Object.entries(typeMap).map(([k, v]) => ({ name: k, value: v }))
  } catch { invData.value = [] }
}

const today = new Date()
today.setHours(0, 0, 0, 0)

async function fetchOtdData() {
  try {
    const [poRes, woRes] = await Promise.all([
      api.get('/purchase/orders', { params: { page_size: 1000 } }),
      api.get('/production/orders', { params: { page_size: 1000 } }),
    ])
    const all = [...(poRes.items || []), ...(woRes.items || [])]
    const weekMap = {}
    for (const o of all) {
      const due = o.due_date || o.end_date || ''
      if (!due) continue
      const d = new Date(due)
      const weekStart = new Date(d)
      weekStart.setDate(d.getDate() - d.getDay())
      const key = weekStart.toISOString().slice(0, 10)
      if (!weekMap[key]) weekMap[key] = { total: 0, onTime: 0, overdue: 0 }
      weekMap[key].total++
      if (o.status === '已完成') {
        weekMap[key].onTime++
      } else if (d < today) {
        weekMap[key].overdue++
      }
    }
    otdData.value = Object.entries(weekMap)
      .sort(([a], [b]) => a.localeCompare(b))
      .slice(-8)
      .map(([week, v]) => ({
        week: week.slice(5),
        total: v.total,
        onTime: v.onTime,
        overdue: v.overdue,
        incomplete: v.total - v.onTime - v.overdue,
        rate: v.total > 0 ? Math.round(v.onTime / v.total * 100) : 0,
      }))
    const total = otdData.value.reduce((s, d) => s + d.total, 0)
    const onTime = otdData.value.reduce((s, d) => s + d.onTime, 0)
    otdRate.value = total > 0 ? Math.round(onTime / total * 100) : 0
  } catch { otdData.value = []; otdRate.value = 0 }
}

// ====== 图表渲染（暗色主题） ======
function renderOtdChart() {
  if (!otdData.value.length || !otdChart.value) return
  const c = echarts.init(otdChart.value)
  c.setOption({
    ...darkChartOptions({
      legend: { data: ['按时完成', '逾期', '未完成'], bottom: 0, orient: 'horizontal' },
      grid: { bottom: 40 },
    }),
    xAxis: {
      type: 'category',
      data: otdData.value.map(d => d.week),
    },
    yAxis: { type: 'value' },
    legend: {
      data: ['按时完成', '逾期', '未完成'],
      bottom: 0,
      textStyle: { color: '#888', fontSize: 11 },
    },
    series: [
      { name: '按时完成', type: 'bar', stack: 'total', data: otdData.value.map(d => d.onTime),
        itemStyle: { color: chartColors.green, borderRadius: [0, 0, 0, 0] }, barWidth: 28, emphasis: { itemStyle: { color: chartColors.green } } },
      { name: '逾期', type: 'bar', stack: 'total', data: otdData.value.map(d => d.overdue),
        itemStyle: { color: chartColors.red }, emphasis: { itemStyle: { color: chartColors.red } } },
      { name: '未完成', type: 'bar', stack: 'total', data: otdData.value.map(d => d.incomplete),
        itemStyle: { color: chartColors.gray }, emphasis: { itemStyle: { color: chartColors.gray } } },
    ],
  })
}

function renderInventoryChart() {
  if (!invData.value.length || !inventoryChart.value) return
  const c = echarts.init(inventoryChart.value)
  c.setOption({
    ...darkChartOptions(),
    tooltip: {
      trigger: 'item',
      backgroundColor: '#242429',
      borderColor: '#333',
      textStyle: { color: '#ccc', fontSize: 12 },
      formatter: '{b}: {c} ({d}%)',
    },
    legend: { bottom: 0, textStyle: { color: '#888', fontSize: 11 }, itemWidth: 8, itemHeight: 8 },
    series: [{
      type: 'pie',
      radius: ['50%', '75%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      itemStyle: { borderColor: '#1a1a1e', borderWidth: 2 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#e8e8ed' } },
      data: invData.value.map(d => ({
        value: d.value,
        name: d.name,
        itemStyle: { color: materialTypeColors[d.name] || chartColors.gray },
      })),
    }],
  })
}

function renderWoChart() {
  if (!woData.value.length || !woChart.value) return
  const c = echarts.init(woChart.value)
  c.setOption({
    ...darkChartOptions(),
    xAxis: { type: 'category', data: woData.value.map(d => d.status) },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      barWidth: 28,
      label: { show: true, position: 'top', color: '#a0a0a8', fontSize: 11 },
      data: woData.value.map(d => ({
        value: d.count,
        itemStyle: {
          color: woStatusColors[d.status] || '#6b7280',
          borderRadius: [4, 4, 0, 0],
        },
      })),
    }],
  })
}

function renderAll() {
  renderOtdChart()
  renderInventoryChart()
  renderWoChart()
}

// ====== 初始化 ======
onMounted(async () => {
  await Promise.all([fetchLowStock(), fetchWoData(), fetchInvData(), fetchOtdData()])
  await nextTick()
  renderAll()

  // 窗口 resize 时重绘
  window.addEventListener('resize', renderAll)
})
</script>

<style scoped>
.page-container { padding: 0; }
</style>
