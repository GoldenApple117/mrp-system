<template>
  <div class="page-container">
    <!-- 参数设置 -->
    <el-card style="margin-bottom:16px">
      <template #header><span style="font-size:15px;font-weight:500">MRP 运算参数</span></template>
      <el-row :gutter="20">
        <el-col :span="6">
          <span style="color:#606266">展望期(天)：</span>
          <el-input-number v-model="horizonDays" :min="1" :max="365" />
        </el-col>
        <el-col :span="6">
          <span style="color:#606266">时界(天)：</span>
          <el-input-number v-model="timeFenceDays" :min="0" :max="30" />
        </el-col>
        <el-col :span="12" style="display:flex;align-items:center;gap:12px">
          <el-button type="primary" size="large" @click="runMrp" :loading="running" :icon="Cpu">
            {{ running ? '计算中...' : '一键 MRP 运算' }}
          </el-button>
          <el-text type="info" size="small">基于 MPS + BOM + 库存，自动计算所有物料的采购/生产建议</el-text>
        </el-col>
      </el-row>
    </el-card>

    <!-- 结果摘要 -->
    <el-row :gutter="16" style="margin-bottom:16px" v-if="summary">
      <el-col :span="6">
        <el-statistic title="计划订单总数" :value="summary.total_orders" />
      </el-col>
      <el-col :span="6">
        <el-statistic title="采购建议" :value="summary.purchase_orders">
          <template #suffix><el-tag type="warning" size="small">需采购</el-tag></template>
        </el-statistic>
      </el-col>
      <el-col :span="6">
        <el-statistic title="生产建议" :value="summary.production_orders">
          <template #suffix><el-tag type="primary" size="small">需生产</el-tag></template>
        </el-statistic>
      </el-col>
      <el-col :span="6">
        <el-statistic title="例外信息" :value="summary.exceptions_count">
          <template #suffix>
            <el-tag :type="summary.error_count>0?'danger':'warning'" size="small">
              {{ summary.error_count }}错误 {{ summary.warning_count }}警告
            </el-tag>
          </template>
        </el-statistic>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-bottom:12px" v-if="summary">
      <el-col :span="24">
        <el-text type="info" size="small">运算耗时: {{ summary.run_time_ms }}ms | 展望期: {{ summary.horizon_days }}天</el-text>
      </el-col>
    </el-row>

    <!-- 例外信息 -->
    <el-card v-if="exceptions.length" style="margin-bottom:16px">
      <template #header>
        <span style="color:#f56c6c;font-weight:500">⚠ 例外信息 ({{ exceptions.length }})</span>
      </template>
      <div v-for="(ex,i) in exceptions" :key="i" style="padding:6px 0;border-bottom:1px solid #ebeef5">
        <el-tag :type="ex.severity==='ERROR'?'danger':'warning'" size="small" style="margin-right:8px">{{ ex.severity }}</el-tag>
        <span style="font-size:13px">{{ ex.message }}</span>
      </div>
    </el-card>

    <!-- 计划订单 -->
    <el-card v-if="plannedOrders.length">
      <template #header>
        <span style="font-weight:500">计划订单结果 ({{ plannedOrders.length }})</span>
        <el-button type="success" size="small" style="margin-left:12px" @click="convertToOrders" :loading="converting">
          一键转为采购申请/工单
        </el-button>
      </template>
      <el-table :data="plannedOrders" stripe border max-height="500">
        <el-table-column prop="item_code" label="物料编码" width="130" />
        <el-table-column prop="material_name" label="物料型号" min-width="150" />
        <el-table-column label="类型" width="100">
          <template #default="{row}">
            <el-tag :type="row.order_type==='PURCHASE'?'warning':'primary'" size="small">
              {{ row.order_type==='PURCHASE'?'采购':'生产' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="level" label="BOM层级" width="90" />
        <el-table-column prop="release_date" label="建议下达日" width="120" />
        <el-table-column prop="required_date" label="需求日期" width="120" />
        <el-table-column prop="quantity" label="数量" width="100" />
      </el-table>
    </el-card>

    <el-empty v-if="!running && !summary" description="请先录入MPS成品计划和BOM，然后点击「一键MRP运算」" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Cpu } from '@element-plus/icons-vue'
import api from '@/api'

const horizonDays = ref(90)
const timeFenceDays = ref(7)
const running = ref(false)
const converting = ref(false)
const summary = ref(null)
const plannedOrders = ref([])
const exceptions = ref([])

async function runMrp() {
  running.value = true
  plannedOrders.value = []
  exceptions.value = []
  summary.value = null
  try {
    const res = await api.post('/mrp/run', {
      horizon_days: horizonDays.value,
      time_fence_days: timeFenceDays.value,
    })
    if (res.success) {
      plannedOrders.value = res.data.planned_orders || []
      exceptions.value = res.data.exceptions || []
      summary.value = res.data.summary
      ElMessage.success(res.message)
    } else {
      ElMessage.warning(res.message)
    }
  } catch {
    ElMessage.error('MRP运算失败')
  } finally {
    running.value = false
  }
}

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
</script>

<style scoped>
.page-container { background:#fff; padding:20px; border-radius:8px; }
</style>
