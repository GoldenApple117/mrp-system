<template>
  <div class="page-container">
    <h3 style="margin-bottom:16px;font-size:16px">报表与分析</h3>
    <el-row :gutter="16">
      <!-- 订单准时率 -->
      <el-col :span="12" style="margin-bottom:16px">
        <el-card>
          <template #header><span style="font-weight:500">订单准时交付率 (OTD)</span></template>
          <div ref="otdChart" style="height:300px"></div>
        </el-card>
      </el-col>

      <!-- 库存周转 -->
      <el-col :span="12" style="margin-bottom:16px">
        <el-card>
          <template #header><span style="font-weight:500">库存概览</span></template>
          <div ref="inventoryChart" style="height:300px"></div>
        </el-card>
      </el-col>

      <!-- 缺料统计 -->
      <el-col :span="12" style="margin-bottom:16px">
        <el-card>
          <template #header><span style="font-weight:500">缺料/低库存物料</span></template>
          <el-table :data="lowStockItems" stripe border size="small" max-height="260">
            <el-table-column prop="material_code" label="物料编码" width="120" />
            <el-table-column prop="material_name" label="物料名称" min-width="140" />
            <el-table-column prop="on_hand" label="现有库存" width="90" />
            <el-table-column prop="safety_stock" label="安全库存" width="90" />
            <el-table-column prop="available" label="可用量" width="90" />
            <el-table-column label="状态" width="80">
              <template #default="{row}">
                <el-tag :type="row.is_low?'danger':'success'" size="small">{{ row.is_low?'偏低':'正常' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 工单状态 -->
      <el-col :span="12" style="margin-bottom:16px">
        <el-card>
          <template #header><span style="font-weight:500">工单状态分布</span></template>
          <div ref="woChart" style="height:300px"></div>
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

function initOtdChart() {
  if (!otdChart.value) return
  const chart = echarts.init(otdChart.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['按时完成', '逾期完成', '未完成'] },
    xAxis: { type: 'category', data: ['第1周','第2周','第3周','第4周','第5周','第6周'] },
    yAxis: { type: 'value' },
    series: [
      { name: '按时完成', type: 'bar', stack: 'total', data: [45,52,38,60,55,48], color: '#67c23a' },
      { name: '逾期完成', type: 'bar', stack: 'total', data: [5,3,8,2,4,6], color: '#e6a23c' },
      { name: '未完成', type: 'bar', stack: 'total', data: [3,2,5,1,2,3], color: '#f56c6c' },
    ],
  })
}

function initInventoryChart() {
  if (!inventoryChart.value) return
  const chart = echarts.init(inventoryChart.value)
  chart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: [
        { value: 35, name: '原材料', itemStyle: { color: '#409eff' } },
        { value: 25, name: '半成品', itemStyle: { color: '#e6a23c' } },
        { value: 20, name: '零件', itemStyle: { color: '#67c23a' } },
        { value: 15, name: '成品', itemStyle: { color: '#f56c6c' } },
        { value: 5, name: '呆滞/过期', itemStyle: { color: '#909399' } },
      ],
      label: { formatter: '{b}\n{d}%' },
    }],
  })
}

function initWoChart() {
  if (!woChart.value) return
  const chart = echarts.init(woChart.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: ['待下达','已下达','进行中','已完成','已关闭'] },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      data: [
        { value: 8, itemStyle: { color: '#909399' } },
        { value: 12, itemStyle: { color: '#e6a23c' } },
        { value: 15, itemStyle: { color: '#409eff' } },
        { value: 30, itemStyle: { color: '#67c23a' } },
        { value: 3, itemStyle: { color: '#f56c6c' } },
      ],
    }],
  })
}

async function fetchLowStock() {
  try {
    const res = await api.get('/inventory/summary')
    lowStockItems.value = (res.items || []).filter(i => i.is_low).slice(0, 20)
  } catch {}
}

onMounted(async () => {
  await fetchLowStock()
  await nextTick()
  initOtdChart()
  initInventoryChart()
  initWoChart()
})
</script>

<style scoped>
.page-container { background:#fff; padding:20px; border-radius:8px; }
</style>
