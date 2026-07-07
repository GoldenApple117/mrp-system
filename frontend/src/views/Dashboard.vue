<template>
  <div class="page-container space-y-5 animate-fade-in">
    <!-- ══════════ KPI 统计卡片 ══════════ -->
    <SkeletonCard v-if="loading" :count="8" />
    <div v-else class="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <div class="kpi-box" style="background:linear-gradient(135deg,#409eff,#3375d6)">
        <span class="kpi-num">{{ stats.materialCount }}</span>
        <span class="kpi-label">物料总数</span>
      </div>
      <div class="kpi-box" style="background:linear-gradient(135deg,#e6a23c,#cf9236)">
        <span class="kpi-num">{{ stats.pendingPurchase }}</span>
        <span class="kpi-label">待处理采购</span>
      </div>
      <div class="kpi-box" style="background:linear-gradient(135deg,#67c23a,#529b2e)">
        <span class="kpi-num">{{ stats.activeProduction }}</span>
        <span class="kpi-label">进行中工单</span>
      </div>
      <div class="kpi-box" style="background:linear-gradient(135deg,#f56c6c,#d9534f)">
        <span class="kpi-num">{{ stats.lowStockCount }}</span>
        <span class="kpi-label">低库存预警</span>
      </div>
      <div class="kpi-box" style="background:linear-gradient(135deg,#8b5cf6,#6d28d9)">
        <span class="kpi-num">{{ stats.exceptionCount }}</span>
        <span class="kpi-label">MRP 例外项</span>
      </div>
      <div class="kpi-box" style="background:linear-gradient(135deg,#06b6d4,#0891b2)">
        <span class="kpi-num">{{ sfSummary.active_orders }}</span>
        <span class="kpi-label">活动工单</span>
      </div>
      <div class="kpi-box" style="background:linear-gradient(135deg,#22c55e,#16a34a)">
        <span class="kpi-num">{{ sfSummary.today_reports }}</span>
        <span class="kpi-label">今日报工</span>
      </div>
      <div class="kpi-box" style="background:linear-gradient(135deg,#ef4444,#dc2626)">
        <span class="kpi-num">{{ sfSummary.pending_andon }}</span>
        <span class="kpi-label">待处理安灯</span>
      </div>
    </div>

    <!-- ══════════ 预警卡片 ══════════ -->
    <div v-if="dashAlerts.length > 0" style="display:flex;gap:12px;flex-wrap:wrap;">
      <div
        v-for="a in dashAlerts"
        :key="a.title"
        style="flex:1;min-width:200px;display:flex;align-items:center;gap:12px;border-radius:8px;padding:12px 16px;cursor:pointer;background:var(--color-bg-overlay);border:1px solid var(--color-border-subtle);"
        @click="$router.push(a.type==='danger'?'/production':a.type==='warning'?'/inventory':'/mrp')"
      >
        <el-icon :size="20"
          ><component :is="a.type==='danger'?'WarningFilled':a.type==='warning'?'Box':'Setting'"
        /></el-icon>
        <div class="w-full lg:w-1/3">
          <div style="font-size:13px;font-weight:600;color:var(--color-text-primary)">
            {{ a.title }}
          </div>
          <div style="font-size:12px;color:var(--color-text-tertiary)">{{ a.detail }}</div>
        </div>
        <span style="font-size:18px;font-weight:700;color:var(--color-danger)">{{ a.count }}</span>
      </div>
    </div>

    <!-- ══════════ 工单看板 + OEE + 负荷 ══════════ -->
    <div class="flex flex-col lg:flex-row gap-4">
      <div class="w-full lg:w-2/3">
        <el-card shadow="never">
          <template #header><span style="font-weight:600">工单看板</span></template>
          <div class="kanban-row">
            <div v-for="(wos, status) in kanban.columns" :key="status" class="kanban-col">
              <div class="kanban-header">
                {{ status }} <span class="kanban-count">{{ wos.length }}</span>
              </div>
              <div
                v-for="w in wos"
                :key="w.id"
                :class="['kanban-card', `priority-${w.priority || 0}`]"
              >
                <div class="kanban-wo">{{ w.wo_number }}</div>
                <div class="kanban-mat">{{ w.material_name }}</div>
                <div class="kanban-bar-bg">
                  <div class="kanban-bar" :style="{width: w.progress + '%'}"></div>
                </div>
                <div class="kanban-info">{{ w.completed_qty }}/{{ w.plan_qty }}</div>
                <div v-if="w.work_center_name" class="kanban-wc">{{ w.work_center_name }}</div>
              </div>
              <div v-if="!wos.length" class="kanban-empty">暂无</div>
            </div>
          </div>
        </el-card>
      </div>
      <div class="w-full lg:w-1/3">
        <el-card shadow="never" style="margin-bottom:16px">
          <template #header><span style="font-weight:600">OEE 设备效率</span></template>
          <div v-for="o in oee.items" :key="o.work_center_id" class="oee-row">
            <div class="oee-name">{{ o.center_name }}</div>
            <div class="oee-bar-bg">
              <div
                class="oee-bar"
                :style="{width: o.oee + '%', background: o.oee < 50 ? '#f56c6c' : o.oee < 75 ? '#e6a23c' : '#67c23a'}"
              ></div>
            </div>
            <div class="oee-val">{{ o.oee }}%</div>
          </div>
        </el-card>
        <el-card shadow="never">
          <template #header><span style="font-weight:600">工作中心负荷</span></template>
          <div v-for="w in load.items" :key="w.work_center_id" class="oee-row">
            <div class="oee-name">{{ w.center_name }}</div>
            <div class="oee-bar-bg">
              <div
                class="oee-bar"
                :style="{width: Math.min(w.load_pct, 100) + '%', background: w.load_pct > 100 ? '#f56c6c' : w.load_pct > 80 ? '#e6a23c' : '#67c23a'}"
              ></div>
            </div>
            <div class="oee-val">{{ w.load_pct }}%</div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- ══════════ 快捷操作 + 最近 MRP + 系统状态 ══════════ -->
    <div class="flex flex-col lg:flex-row gap-4">
      <div class="stat-card flex-1">
        <h3
          style="font-weight:600;font-size:14px;margin-bottom:16px;display:flex;align-items:center;gap:8px;"
        >
          <el-icon :size="14" color="var(--color-accent)"><Promotion /></el-icon> 快捷操作
        </h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
          <QuickActionBtn to="/mrp" icon="Cpu" label="MRP 运算" desc="物料需求计算" color="blue" />
          <QuickActionBtn
            to="/materials"
            icon="Plus"
            label="新增物料"
            desc="录入物料数据"
            color="emerald"
          />
          <QuickActionBtn
            to="/bom"
            icon="Connection"
            label="BOM 管理"
            desc="物料清单维护"
            color="amber"
          />
          <QuickActionBtn
            to="/purchase"
            icon="ShoppingCart"
            label="采购管理"
            desc="采购订单处理"
            color="purple"
          />
          <QuickActionBtn
            to="/production"
            icon="SetUp"
            label="生产管理"
            desc="工单下达跟踪"
            color="cyan"
          />
          <QuickActionBtn
            to="/reports"
            icon="DataAnalysis"
            label="报表中心"
            desc="数据可视化"
            color="rose"
          />
        </div>
      </div>

      <div class="stat-card flex-1">
        <h3
          style="font-weight:600;font-size:14px;margin-bottom:16px;display:flex;align-items:center;gap:8px;"
        >
          <el-icon :size="14" color="var(--color-accent)"><Timer /></el-icon> 最近 MRP 运算
        </h3>
        <div v-if="loading" style="display:flex;flex-direction:column;gap:12px;">
          <div
            v-for="i in 3"
            :key="i"
            style="height:32px;border-radius:6px;background:var(--color-bg-overlay);animation:pulse 2s infinite;"
          ></div>
        </div>
        <div
          v-else-if="lastMrpRuns.length === 0"
          style="display:flex;flex-direction:column;align-items:center;padding:32px 0;color:var(--color-text-tertiary)"
        >
          <el-icon :size="32" color="var(--color-text-disabled)"><Cpu /></el-icon>
          <p style="margin-top:8px;font-size:13px;">暂无 MRP 运算记录</p>
          <router-link to="/mrp" style="margin-top:12px;font-size:13px;color:var(--color-accent)"
            >前往 MRP 运算 →</router-link
          >
        </div>
        <div v-else style="display:flex;flex-direction:column;gap:8px;">
          <div
            v-for="(run, i) in lastMrpRuns"
            :key="i"
            style="display:flex;align-items:center;justify-content:space-between;padding:8px 12px;border-radius:6px;background:var(--color-bg-overlay);font-size:13px;"
          >
            <div style="display:flex;align-items:center;gap:8px;">
              <span
                :style="{width:'6px',height:'6px',borderRadius:'50%',background:run.status==='success'?'var(--color-success)':'var(--color-danger)'}"
              ></span>
              <span style="color:var(--color-text-secondary)">{{ run.time }}</span>
            </div>
            <div style="display:flex;gap:12px;color:var(--color-text-tertiary)">
              <span>{{ run.orders }} 订单</span>
              <span>{{ run.exceptions }} 例外</span>
              <span style="color:var(--color-text-disabled)">{{ run.duration }}ms</span>
            </div>
          </div>
        </div>
      </div>

      <div class="stat-card flex-1">
        <h3
          style="font-weight:600;font-size:14px;margin-bottom:16px;display:flex;align-items:center;gap:8px;"
        >
          <el-icon :size="14" color="var(--color-success)"><Monitor /></el-icon> 系统状态
        </h3>
        <div style="display:flex;flex-direction:column;gap:12px;">
          <StatusRow label="数据库" status="connected" />
          <StatusRow label="定时任务" :status="timerEnabled ? 'active' : 'paused'" />
          <StatusRow label="MRP 引擎" status="ready" />
          <StatusRow label="API 服务" status="connected" />
        </div>
        <div
          style="margin-top:16px;padding-top:16px;border-top:1px solid var(--color-border-subtle);"
        >
          <div style="display:flex;justify-content:space-between;font-size:13px;">
            <span style="color:var(--color-text-tertiary)">定时 MRP</span>
            <span
              :style="{color:timerEnabled?'var(--color-success)':'var(--color-text-tertiary)'}"
              >{{ timerEnabled ? '已启用' : '已暂停' }}</span
            >
          </div>
          <div
            v-if="timerEnabled"
            style="display:flex;justify-content:space-between;font-size:13px;margin-top:4px;"
          >
            <span style="color:var(--color-text-tertiary)">下次执行</span>
            <span style="color:var(--color-text-secondary);font-family:monospace;"
              >{{ timerHour }}:{{ String(timerMinute).padStart(2, '0') }}</span
            >
          </div>
        </div>
      </div>
    </div>

    <!-- ══════════ 图表区域 ══════════ -->
    <div class="flex flex-col lg:flex-row gap-4">
      <div class="stat-card flex-1">
        <h3 class="font-semibold text-sm mb-3">库存概览（按模块）</h3>
        <div v-if="loading" class="h-[280px] rounded-md bg-[var(--color-bg-hover)] animate-pulse" />
        <div v-else ref="inventoryChart" style="height:280px"></div>
        <div
          v-if="!loading && !invData.length"
          class="flex items-center justify-center h-[280px] text-[var(--color-text-tertiary)] text-[13px]"
        >
          暂无库存数据
        </div>
      </div>
      <div class="stat-card flex-1">
        <h3 class="font-semibold text-sm mb-3">工单状态分布</h3>
        <div v-if="loading" class="h-[280px] rounded-md bg-[var(--color-bg-hover)] animate-pulse" />
        <div v-else ref="woChart" style="height:280px"></div>
        <div
          v-if="!loading && !woData.length"
          class="flex items-center justify-center h-[280px] text-[var(--color-text-tertiary)] text-[13px]"
        >
          暂无工单数据
        </div>
      </div>
    </div>

    <!-- ══════════ 安灯事件 + 低库存预警 ══════════ -->
    <div class="flex flex-col lg:flex-row gap-4">
      <div class="stat-card flex-1">
        <div
          style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;"
        >
          <h3 style="font-weight:600;font-size:14px;">安灯事件</h3>
          <el-button size="small" type="danger" @click="showAndonDialog">触发安灯</el-button>
        </div>
        <el-table v-loading="aLoading" :data="andons" stripe border size="small">
          <el-table-column prop="event_no" label="编号" width="160" />
          <el-table-column prop="event_type" label="类型" width="80" />
          <el-table-column label="严重度" width="70"
            ><template #default="{row}">
              <el-tag
                :type="row.severity==='红色'?'danger':row.severity==='黄色'?'warning':'info'"
                size="small"
                >{{ row.severity }}</el-tag
              >
            </template></el-table-column
          >
          <el-table-column prop="description" label="描述" min-width="120" show-overflow-tooltip />
          <el-table-column prop="handler" label="响应人" width="70" />
          <el-table-column label="状态" width="70"
            ><template #default="{row}">
              <el-tag
                :type="row.status==='已解决'?'success':row.status==='处理中'?'warning':'danger'"
                size="small"
                >{{ row.status }}</el-tag
              >
            </template></el-table-column
          >
          <el-table-column label="操作" width="120"
            ><template #default="{row}">
              <el-button
                v-if="row.status==='待响应'"
                link
                size="small"
                type="primary"
                @click="respondAndon(row)"
                >响应</el-button
              >
              <el-button
                v-if="row.status==='处理中'"
                link
                size="small"
                type="success"
                @click="resolveAndon(row)"
                >解决</el-button
              >
            </template></el-table-column
          >
        </el-table>
      </div>
      <div v-if="lowStockItems.length > 0" class="stat-card flex-1">
        <div
          style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;"
        >
          <h3 style="font-weight:600;font-size:14px;display:flex;align-items:center;gap:8px;">
            <span
              style="width:8px;height:8px;border-radius:50%;background:var(--color-danger);"
            ></span>
            低库存预警
          </h3>
          <router-link to="/inventory" style="font-size:13px;color:var(--color-accent)"
            >查看全部 →</router-link
          >
        </div>
        <el-table :data="lowStockItems.slice(0, 5)" stripe size="small">
          <el-table-column prop="material_code" label="编码" width="100" />
          <el-table-column
            prop="material_name"
            label="物料型号"
            min-width="140"
            show-overflow-tooltip
          />
          <el-table-column prop="on_hand" label="库存" width="60" align="center" />
          <el-table-column prop="safety_stock" label="安全" width="60" align="center" />
          <el-table-column label="状态" width="60" align="center"
            ><template #default="{ row }">
              <el-tag
                :type="row.available <= 0 ? 'danger' : 'warning'"
                size="small"
                effect="dark"
                >{{ row.available <= 0 ? '缺料' : '偏低' }}</el-tag
              >
            </template></el-table-column
          >
        </el-table>
      </div>
    </div>

    <!-- 安灯触发弹窗 -->
    <el-dialog v-model="andonVisible" title="触发安灯" width="420px">
      <el-form :model="andonForm" label-width="80px">
        <el-form-item label="类型">
          <el-select v-model="andonForm.event_type" style="width:100%">
            <el-option label="缺料" value="缺料" /><el-option label="设备故障" value="设备故障" />
            <el-option label="质量问题" value="质量问题" /><el-option
              label="安全"
              value="安全"
            /><el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重度">
          <el-select v-model="andonForm.severity" style="width:100%">
            <el-option label="红色（停线）" value="红色" /><el-option
              label="黄色（预警）"
              value="黄色"
            /><el-option label="蓝色（请求）" value="蓝色" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述"
          ><el-input v-model="andonForm.description" type="textarea"
        /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="andonVisible=false">取消</el-button>
        <el-button type="danger" :loading="saving" @click="createAndon">触发</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { echarts, darkChartOptions } from '@/utils/echarts-theme'
import { ElMessage } from 'element-plus'
import api from '@/api'
import KpiCard from '@/components/common/KpiCard.vue'
import QuickActionBtn from '@/components/common/QuickActionBtn.vue'
import StatusRow from '@/components/common/StatusRow.vue'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import SkeletonTable from '@/components/common/SkeletonTable.vue'

const route = useRoute()
const loading = ref(true)
const aLoading = ref(false)
const saving = ref(false)

// ====== 统计数据 ======
const stats = ref({ materialCount: 0, pendingPurchase: 0, activeProduction: 0, lowStockCount: 0, exceptionCount: 0 })

// ====== 生产看板数据 ======
const sfSummary = ref({ active_orders: 0, in_progress: 0, today_reports: 0, pending_andon: 0 })
const kanban = ref({ columns: {} })
const oee = ref({ items: [] })
const load = ref({ items: [] })
const andons = ref([])

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
const dashAlerts = ref([])

// ====== 安灯 ======
const andonVisible = ref(false)
const andonForm = ref({ event_type: '缺料', severity: '红色', description: '' })

// ====== 数据加载 ======
async function loadAll() {
  loading.value = true
  try {
    await Promise.all([
      loadStats(), loadMrpHistory(), loadInventory(), loadWorkOrders(), loadTimer(), loadAlerts(),
      loadShopFloor(),
    ])
  } finally { loading.value = false }
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
    stats.value = {
      materialCount: materials.total || 0,
      pendingPurchase: purchases.total || 0,
      activeProduction: productions.total || 0,
      lowStockCount: (inventory.items || []).filter(i => i.is_low).length,
      exceptionCount: exceptions.total || 0,
    }
  } catch {}
}

async function loadShopFloor() {
  try {
    const [s, k, o, l, a] = await Promise.all([
      api.get('/shop-floor/summary'),
      api.get('/shop-floor/kanban'),
      api.get('/shop-floor/oee', { params: { days: 30 } }),
      api.get('/shop-floor/work-center-load'),
      api.get('/shop-floor/andon'),
    ])
    sfSummary.value = s
    kanban.value = k
    oee.value = o
    load.value = l
    andons.value = a.items || []
  } catch {}
}

async function loadMrpHistory() {
  try {
    const res = await api.get('/exceptions', { params: { page_size: 5 } })
    const items = res.items || []
    if (items.length) {
      const grouped = {}
      items.forEach(item => {
        const key = item.created_at ? item.created_at.slice(0, 16) : 'unknown'
        if (!grouped[key]) grouped[key] = { time: key, orders: 0, exceptions: 0, status: 'success', duration: 0 }
        grouped[key].exceptions++
      })
      lastMrpRuns.value = Object.values(grouped).slice(0, 3)
    }
  } catch { lastMrpRuns.value = [] }
}

async function loadInventory() {
  try {
    const modRes = await api.get('/system/dashboard/modules')
    invData.value = (modRes || []).map(d => ({ name: d.module_name, value: d.total_qty, count: d.material_count }))
    nextTick(() => renderInventoryChart())
    const res = await api.get('/inventory/summary', { params: { page_size: 1000 } })
    lowStockItems.value = (res.items || []).filter(i => i.is_low).slice(0, 5)
  } catch { lowStockItems.value = []; invData.value = [] }
}

async function loadAlerts() {
  try { const res = await api.get('/system/dashboard/alerts'); dashAlerts.value = res.alerts || [] }
  catch { dashAlerts.value = [] }
}

async function loadWorkOrders() {
  try {
    const res = await api.get('/production/orders', { params: { page_size: 1000 } })
    const orders = res.items || []
    const statusMap = {}
    orders.forEach(o => { statusMap[o.status] = (statusMap[o.status] || 0) + 1 })
    woData.value = ['待下达', '已下达', '进行中', '已完成', '已关闭'].map(s => ({ name: s, value: statusMap[s] || 0 }))
    nextTick(() => renderWoChart())
  } catch { woData.value = [] }
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

// ====== 安灯操作 ======
function showAndonDialog() { andonForm.value = { event_type: '缺料', severity: '红色', description: '' }; andonVisible.value = true }

async function createAndon() {
  saving.value = true
  try { await api.post('/shop-floor/andon', { ...andonForm.value }); ElMessage.success('安灯已触发'); andonVisible.value = false; loadShopFloor() }
  finally { saving.value = false }
}

async function respondAndon(row) { await api.put(`/shop-floor/andon/${row.id}/respond`, { handler: '系统' }); ElMessage.success('已响应'); loadShopFloor() }
async function resolveAndon(row) { await api.put(`/shop-floor/andon/${row.id}/resolve`); ElMessage.success('已解决'); loadShopFloor() }

// ====== 图表渲染 ======
function renderInventoryChart() {
  if (!inventoryChart.value || !invData.value.length) return
  const chart = echarts.init(inventoryChart.value)
  const names = invData.value.map(d => d.name)
  const values = invData.value.map(d => d.value)
  const colors = ['#3b82f6', '#8b5cf6', '#22c55e', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#14b8a6']
  chart.setOption({
    ...darkChartOptions({ grid: { left: 100, right: 40, top: 8, bottom: 8 } }),
    tooltip: { trigger: 'axis', formatter: (params) => { const d = invData.value[params[0].dataIndex]; return `${d.name}<br/>库存: ${d.value}<br/>物料: ${d.count}` } },
    xAxis: { type: 'value', axisLabel: {}, splitLine: { lineStyle: { color: '#2a2a2e' } } },
    yAxis: { type: 'category', data: names, axisLabel: { fontSize: 12 }, inverse: true },
    series: [{ type: 'bar', data: values.map((v, i) => ({ value: v, itemStyle: { color: colors[i % colors.length], borderRadius: [0, 4, 4, 0] } })), barWidth: 20, label: { show: true, position: 'right', color: '#a0a0a8', fontSize: 11, formatter: '{c}' } }],
  })
  chart._resizeHandler = () => chart.resize()
  window.addEventListener('resize', chart._resizeHandler)
}

function renderWoChart() {
  if (!woChart.value || !woData.value.length) return
  const chart = echarts.init(woChart.value)
  const barColors = ['#3b82f6', '#f59e0b', '#22c55e', '#06b6d4', '#6b7280']
  chart.setOption({
    ...darkChartOptions(),
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: woData.value.map(d => d.name) },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: woData.value.map((d, i) => ({ value: d.value, itemStyle: { color: barColors[i], borderRadius: [4, 4, 0, 0] } })), barWidth: 32, label: { show: true, position: 'top', color: '#a0a0a8', fontSize: 11 } }],
  })
  chart._resizeHandler = () => chart.resize()
  window.addEventListener('resize', chart._resizeHandler)
}

// ====== 路由切换时重新加载 ======
watch(() => route.path, (newPath) => { if (newPath === '/dashboard') loadAll() })
onMounted(() => loadAll())
onBeforeUnmount(() => {
  ;[inventoryChart.value, woChart.value].forEach(el => {
    if (!el) return
    const instance = echarts.getInstanceByDom(el)
    if (instance) { if (instance._resizeHandler) window.removeEventListener('resize', instance._resizeHandler); instance.dispose() }
  })
})
</script>

<style scoped>
/* KPI 卡片行 */
.kpi-box { flex:1; min-width:100px; border-radius:10px; padding:14px 12px; color:#fff; display:flex; flex-direction:column; align-items:center; text-align:center; }
.kpi-num { font-size:24px; font-weight:800; line-height:1.2; }
.kpi-label { font-size:12px; opacity:0.85; margin-top:4px; }

/* 看板 */
.kanban-row { display:flex; gap:10px; min-height:180px; }
.kanban-col { flex:1; background:var(--color-bg-raised); border-radius:8px; padding:10px; }
.kanban-header { font-weight:600; font-size:14px; margin-bottom:10px; color:var(--color-text-primary); }
.kanban-count { background:var(--color-bg-hover); color:var(--color-text-secondary); border-radius:10px; padding:1px 8px; font-size:12px; margin-left:6px; }
.kanban-card { background:var(--color-bg-overlay); border-radius:8px; padding:10px; margin-bottom:8px; border-left:3px solid var(--color-border-light); box-shadow:0 1px 4px rgba(0,0,0,0.15); }
.kanban-card.priority-1 { border-left-color:#e6a23c; }
.kanban-card.priority-2 { border-left-color:#f56c6c; }
.kanban-wo { font-weight:600; font-size:13px; }
.kanban-mat { font-size:12px; color:var(--color-text-tertiary); margin:2px 0 6px; }
.kanban-bar-bg { height:4px; background:var(--color-bg-hover); border-radius:2px; margin-bottom:4px; }
.kanban-bar { height:100%; background:var(--color-accent); border-radius:2px; transition:width 0.3s; }
.kanban-info { font-size:11px; color:var(--color-text-tertiary); }
.kanban-wc { font-size:11px; color:var(--color-accent); margin-top:2px; }
.kanban-empty { text-align:center; color:var(--color-text-disabled); padding:20px 0; font-size:13px; }

/* OEE/负荷 */
.oee-row { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
.oee-name { width:90px; font-size:12px; color:var(--color-text-secondary); flex-shrink:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.oee-bar-bg { flex:1; height:10px; background:var(--color-bg-hover); border-radius:5px; overflow:hidden; }
.oee-bar { height:100%; border-radius:5px; transition:width 0.5s; }
.oee-val { width:36px; text-align:right; font-weight:600; font-size:13px; }

/* 通用 */
.stat-card { border:1px solid var(--color-border-light); border-radius:12px; padding:16px; background:var(--color-bg-elevated); }
</style>
