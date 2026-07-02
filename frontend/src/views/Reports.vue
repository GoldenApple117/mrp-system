<template>
  <div class="page-container">
    <h3 style="margin-bottom:16px;font-size:16px">报表与分析</h3>
    <el-row :gutter="16">
      <!-- 订单准时率 -->
      <el-col :span="12" style="margin-bottom:16px">
        <el-card>
          <template #header>
            <span style="font-weight:500">订单准时交付率 (OTD)</span>
            <el-tag size="small" type="info" style="margin-left:8px">{{ otdRate }}%</el-tag>
          </template>
          <div ref="otdChart" style="height:300px"></div>
          <div v-if="!otdData.length" style="text-align:center;color:#999;padding:40px 0">暂无订单数据</div>
        </el-card>
      </el-col>

      <!-- 库存概览 -->
      <el-col :span="12" style="margin-bottom:16px">
        <el-card>
          <template #header><span style="font-weight:500">库存概览（按物料类型）</span></template>
          <div ref="inventoryChart" style="height:300px"></div>
          <div v-if="!invData.length" style="text-align:center;color:#999;padding:40px 0">暂无库存数据</div>
        </el-card>
      </el-col>

      <!-- 缺料统计 -->
      <el-col :span="12" style="margin-bottom:16px">
        <el-card>
          <template #header><span style="font-weight:500">缺料/低库存物料</span></template>
          <el-table :data="lowStockItems" stripe border size="small" max-height="260">
            <el-table-column prop="material_code" label="物料编码" width="120" />
            <el-table-column prop="material_name" label="物料型号" min-width="140" />
            <el-table-column prop="on_hand" label="现有库存" width="90" />
            <el-table-column prop="safety_stock" label="安全库存" width="90" />
            <el-table-column prop="available" label="可用量" width="90" />
            <el-table-column label="状态" width="80">
              <template #default="{row}">
                <el-tag :type="row.is_low?'danger':'success'" size="small">{{ row.is_low?'偏低':'正常' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!lowStockItems.length" description="暂无低库存物料" />
        </el-card>
      </el-col>

      <!-- 工单状态 -->
      <el-col :span="12" style="margin-bottom:16px">
        <el-card>
          <template #header><span style="font-weight:500">工单状态分布</span></template>
          <div ref="woChart" style="height:300px"></div>
          <div v-if="!woData.length" style="text-align:center;color:#999;padding:40px 0">暂无工单数据</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import api from '@/api'

const otdChart = ref(null)
const inventoryChart = ref(null)
const woChart = ref(null)
const lowStockItems = ref([])
const otdData = ref([])
const invData = ref([])
const woData = ref([])
const otdRate = ref(0)

/* ---- 缺料/低库存 ---- */
async function fetchLowStock() {
  try {
    const res = await api.get('/inventory/summary')
    lowStockItems.value = (res.items || []).filter(i => i.is_low).slice(0, 20)
  } catch { lowStockItems.value = [] }
}

/* ---- 工单状态分布 ---- */
async function fetchWoData() {
  try {
    const res = await api.get('/production/orders', { params: { page_size: 1000 } })
    const orders = res.items || []
    const statusMap = {}
    for (const o of orders) {
      statusMap[o.status] = (statusMap[o.status] || 0) + 1
    }
    const statusOrder = ['待下达','已下达','进行中','已完成','已关闭']
    woData.value = statusOrder.map(s => ({ status: s, count: statusMap[s] || 0 })).filter(d => d.count > 0)
  } catch { woData.value = [] }
}

/* ---- 库存概览（按类型） ---- */
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

/* ---- OTD 准时率 ---- */
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

/* ---- 图表渲染 ---- */
function renderCharts() {
  if (otdData.value.length && otdChart.value) {
    const c = echarts.init(otdChart.value)
    c.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['按时完成', '逾期', '未完成'] },
      xAxis: { type: 'category', data: otdData.value.map(d => d.week) },
      yAxis: { type: 'value' },
      series: [
        { name: '按时完成', type: 'bar', stack: 'total', data: otdData.value.map(d => d.onTime), color: '#67c23a' },
        { name: '逾期', type: 'bar', stack: 'total', data: otdData.value.map(d => d.overdue), color: '#f56c6c' },
        { name: '未完成', type: 'bar', stack: 'total', data: otdData.value.map(d => d.incomplete), color: '#909399' },
      ],
    })
  }

  if (invData.value.length && inventoryChart.value) {
    const c = echarts.init(inventoryChart.value)
    const colors = { '原材料': '#409eff', '半成品': '#e6a23c', '零件': '#67c23a', '成品': '#f56c6c', '其他': '#909399' }
    c.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        data: invData.value.map(d => ({ value: d.value, name: d.name, itemStyle: { color: colors[d.name] || '#909399' } })),
        label: { formatter: '{b}\n{d}%' },
      }],
    })
  }

  if (woData.value.length && woChart.value) {
    const c = echarts.init(woChart.value)
    const colors = { '待下达': '#909399', '已下达': '#e6a23c', '进行中': '#409eff', '已完成': '#67c23a', '已关闭': '#f56c6c' }
    c.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: woData.value.map(d => d.status) },
      yAxis: { type: 'value' },
      series: [{
        type: 'bar',
        data: woData.value.map(d => ({ value: d.count, itemStyle: { color: colors[d.status] || '#909399' } })),
      }],
    })
  }
}

onMounted(async () => {
  await Promise.all([fetchLowStock(), fetchWoData(), fetchInvData(), fetchOtdData()])
  await nextTick()
  renderCharts()
})
</script>

<style scoped>
.page-container { background:#fff; padding:20px; border-radius:8px; }
</style>
