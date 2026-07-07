<template>
  <div class="page-container">
    <div class="flex items-center justify-between mb-5">
      <h2 class="m-0 text-xl">费用合计</h2>
      <el-tag type="success" size="large" effect="dark" class="text-base py-2 px-4">
        全部项目合计：¥{{ formatMoney(grandTotal) }}
      </el-tag>
    </div>

    <div v-loading="loading">
      <!-- 项目卡片 -->
      <div v-for="project in projects" :key="project.product_id" class="project-card">
        <div class="project-header" @click="toggleProject(project.product_id)">
          <div class="flex items-center gap-3">
            <span class="text-lg">{{ project.product_code }}</span>
            <span class="text-base font-semibold">{{ project.product_name }}</span>
            <el-tag size="small">{{ project.module_count }} 个模块</el-tag>
          </div>
          <div class="flex items-center gap-4">
            <span class="project-total">¥{{ formatMoney(project.project_total) }}</span>
            <el-icon
              :style="{transform: expanded[project.product_id] ? 'rotate(180deg)' : '', transition:'0.3s'}"
            >
              <ArrowDown />
            </el-icon>
          </div>
        </div>

        <el-collapse-transition>
          <div v-show="expanded[project.product_id]" class="project-body">
            <!-- 模块明细 -->
            <div v-for="mod in project.modules" :key="mod.module_code" class="module-section">
              <div class="module-header">
                <span
                  style="font-weight:600;color:var(--color-text-primary)"
                  >{{ mod.module_name }}</span
                >
                <span style="color:var(--color-text-tertiary);font-size:12px"
                  >{{ mod.part_count }} 项有定价</span
                >
                <span style="color:var(--color-warning);font-weight:bold;font-size:15px"
                  >¥{{ formatMoney(mod.total) }}</span
                >
              </div>

              <!-- 模块进度条 -->
              <div
                style="height:4px;background:var(--color-bg-overlay);border-radius:2px;margin:4px 0 8px"
              >
                <div
                  :style="{width: percent(mod.total, project.project_total) + '%', height:'100%', background: progressColor(mod.total, project.project_total), borderRadius:'2px', transition:'width 0.6s'}"
                />
              </div>

              <!-- 零件明细表 -->
              <el-table :data="mod.parts" size="small" stripe border class="mt-1">
                <el-table-column prop="material_code" label="物料编码" width="130" />
                <el-table-column prop="material_name" label="物料型号" min-width="150" />
                <el-table-column prop="brand" label="品牌" width="90" />
                <el-table-column label="单价" width="90" align="right">
                  <template #default="{row}">¥{{ formatMoney(row.unit_price) }}</template>
                </el-table-column>
                <el-table-column prop="quantity" label="数量" width="70" align="center" />
                <el-table-column label="金额" width="100" align="right">
                  <template #default="{row}">
                    <span style="font-weight:bold;color:var(--color-warning)"
                      >¥{{ formatMoney(row.cost) }}</span
                    >
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-collapse-transition>
      </div>

      <el-empty v-if="!loading && !projects.length" description="暂无项目数据">
        <template #image>
          <el-icon :size="48" color="var(--color-text-disabled)"><Box /></el-icon>
        </template>
        <router-link to="/bom">
          <el-button type="primary">导入BOM</el-button>
        </router-link>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/api'

const loading = ref(false)
const projects = ref([])
const grandTotal = ref(0)
const expanded = reactive({})

function toggleProject(id) {
  expanded[id] = !expanded[id]
}

function formatMoney(val) {
  if (val === null || val === undefined) return '0'
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 0 })
}

function percent(part, total) {
  if (!total) return 0
  return Math.min(100, (part / total) * 100)
}

function progressColor(part, total) {
  const p = percent(part, total)
  if (p > 50) return 'var(--color-accent)'
  if (p > 20) return 'var(--color-warning)'
  return 'var(--color-success)'
}

async function fetchData() {
  loading.value = true
  try {
    const res = await api.get('/cost/summary')
    projects.value = res.projects || []
    grandTotal.value = res.grand_total || 0
    // 默认展开第一个项目
    if (projects.value.length) {
      expanded[projects.value[0].product_id] = true
    }
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.page-container { padding: 0;; min-height:80vh }

.project-card {
  border:1px solid var(--color-border-light); border-radius:10px; margin-bottom:16px; overflow:hidden;
  transition: box-shadow 0.2s;
}
.project-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.3) }

.project-header {
  display:flex; align-items:center; justify-content:space-between;
  padding:16px 20px; cursor:pointer; background:var(--color-bg-overlay);
  border-bottom:1px solid var(--color-border-light);
  user-select:none;
}
.project-header:hover { background:var(--color-bg-hover) }

.project-total {
  font-size:22px; font-weight:bold; color:var(--color-accent);
  font-family:'Segoe UI', monospace;
}

.project-body { padding:16px 20px 20px }

.module-section {
  margin-bottom:16px; border:1px solid var(--color-border-light); border-radius:8px;
  padding:12px 14px; background:var(--color-bg-overlay);
}

.module-header {
  display:flex; align-items:center; justify-content:space-between;
  margin-bottom:4px
}
</style>
