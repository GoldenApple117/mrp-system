<template>
  <div class="page-container">
    <el-card class="mb-4">
      <template #header><span class="font-medium">CRP 产能需求计划</span></template>
      <el-row :gutter="16" align="middle">
        <el-col :span="6">
          <span class="text-[var(--color-text-secondary)]">展望期(周)：</span>
          <el-input-number v-model="horizonWeeks" :min="2" :max="52" />
        </el-col>
        <el-col :span="8">
          <el-button type="primary" size="large" :loading="loading" @click="calculateCrp">
            计算产能负荷
          </el-button>
          <el-text type="info" class="ml-3">基于工单+工艺路线→工作中心负荷</el-text>
        </el-col>
      </el-row>
    </el-card>

    <el-empty v-if="!loading && !summary" description="暂无产能数据">
      <template #image>
        <el-icon :size="48" color="var(--color-text-disabled)"><Box /></el-icon>
      </template>
      <router-link to="/mrp">
        <el-button type="primary">运行MRP</el-button>
      </router-link>
    </el-empty>

    <template v-if="summary">
      <!-- 摘要 -->
      <el-row v-if="summary" :gutter="16" class="mb-4">
        <el-col :span="6">
          <el-statistic title="工作中心" :value="summary.total_work_centers" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="总负荷(小时)" :value="summary.total_load_hours" :precision="1" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="总产能(小时)" :value="summary.total_capacity_hours" :precision="1" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="综合利用率" :value="summary.overall_utilization_pct" suffix="%">
            <template #suffix>
              <el-tag :type="summary.overall_utilization_pct>100?'danger':'success'" size="small">
                {{ summary.bottleneck_count }}个瓶颈
              </el-tag>
            </template>
          </el-statistic>
        </el-col>
      </el-row>

      <!-- 瓶颈工作中心 -->
      <el-card v-if="bottlenecks.length" class="mb-4">
        <template #header
          ><span class="text-[#f56c6c] font-medium"
            >瓶颈工作中心 ({{ bottlenecks.length }})</span
          ></template
        >
        <el-table :data="bottlenecks" stripe border size="small">
          <el-table-column prop="center_name" label="工作中心" width="150" />
          <el-table-column prop="week_start" label="周" width="120" />
          <el-table-column label="利用率" width="120">
            <template #default="{row}">
              <el-progress
                :percentage="Math.min(row.utilization_pct,200)"
                :color="row.utilization_pct>130?'#f56c6c':'#e6a23c'"
              />
            </template>
          </el-table-column>
          <el-table-column prop="overload_hours" label="超载(小时)" width="120" />
          <el-table-column prop="severity" label="严重程度" width="120">
            <template #default="{row}">
              <el-tag
                :type="row.severity==='CRITICAL'?'danger':'warning'"
                size="small"
                >{{ row.severity }}</el-tag
              >
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 产能负荷表 -->
      <el-card v-if="loadAnalysis.length">
        <template #header>
          <span class="font-medium">产能负荷明细</span>
          <el-tag class="ml-2" size="small">利用率 > 100% = 红色</el-tag>
        </template>
        <el-table :data="loadAnalysis" stripe border size="small" max-height="500">
          <el-table-column prop="center_name" label="工作中心" width="140" />
          <el-table-column prop="week_start" label="周起始" width="120" />
          <el-table-column prop="capacity_hours" label="产能(小时)" width="110" />
          <el-table-column prop="load_hours" label="负荷(小时)" width="110" />
          <el-table-column label="利用率" width="180">
            <template #default="{row}">
              <el-progress
                :percentage="Math.min(row.utilization_pct,200)"
                :color="utilColor(row.utilization_pct)"
                :text-inside="true"
                :stroke-width="18"
              />
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{row}">
              <el-tag
                :type="row.is_overloaded?'danger':'success'"
                size="small"
                >{{ row.is_overloaded?'超载':'正常' }}</el-tag
              >
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const horizonWeeks = ref(8)
const loadAnalysis = ref([])
const bottlenecks = ref([])
const summary = ref(null)

function utilColor(pct) {
  if (pct > 130) return '#f56c6c'
  if (pct > 100) return '#e6a23c'
  return '#67c23a'
}

async function calculateCrp() {
  loading.value = true
  try {
    const res = await api.post('/crp/calculate', { horizon_days: horizonWeeks.value * 7 })
    if (res.success) {
      loadAnalysis.value = res.data.load_analysis || []
      bottlenecks.value = res.data.bottlenecks || []
      summary.value = res.data.summary
      ElMessage.success(res.message)
    } else {
      ElMessage.warning(res.message)
    }
  } catch { ElMessage.error('CRP计算失败') }
  finally { loading.value = false }
}
</script>

<style scoped>
.page-container { padding: 0;; }
</style>
