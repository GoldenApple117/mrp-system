<template>
  <div class="sf-container">
    <!-- 顶部 KPI -->
    <div class="kpi-row">
      <div class="kpi-box" style="background:linear-gradient(135deg,#409eff,#3375d6)">
        <span class="kpi-num">{{ summary.active_orders }}</span>
        <span class="kpi-label">活动工单</span>
      </div>
      <div class="kpi-box" style="background:linear-gradient(135deg,#67c23a,#529b2e)">
        <span class="kpi-num">{{ summary.in_progress }}</span>
        <span class="kpi-label">进行中</span>
      </div>
      <div class="kpi-box" style="background:linear-gradient(135deg,#e6a23c,#cf9236)">
        <span class="kpi-num">{{ summary.today_reports }}</span>
        <span class="kpi-label">今日报工</span>
      </div>
      <div class="kpi-box" style="background:linear-gradient(135deg,#f56c6c,#d9534f)">
        <span class="kpi-num">{{ summary.pending_andon }}</span>
        <span class="kpi-label">待处理安灯</span>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- Kanban 看板 -->
      <el-col :span="16">
        <el-card shadow="never">
          <template #header><span class="font-semibold">工单看板</span></template>
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
      </el-col>

      <!-- OEE + 安灯 -->
      <el-col :span="8">
        <el-card shadow="never" class="mb-4">
          <template #header><span class="font-semibold">OEE 设备效率</span></template>
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
          <template #header><span class="font-semibold">工作中心负荷</span></template>
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
      </el-col>
    </el-row>

    <!-- 安灯事件列表 -->
    <el-card shadow="never" class="mt-4">
      <template #header>
        <div class="flex justify-between items-center">
          <span class="font-semibold">安灯事件</span>
          <el-button size="small" type="danger" @click="showAndonDialog">触发安灯</el-button>
        </div>
      </template>
      <el-table v-loading="aLoading" :data="andons" stripe border size="small">
        <el-table-column prop="event_no" label="编号" width="160" />
        <el-table-column prop="event_type" label="类型" width="90" />
        <el-table-column label="严重度" width="80"
          ><template #default="{row}">
            <el-tag
              :type="row.severity==='红色'?'danger':row.severity==='黄色'?'warning':'info'"
              size="small"
              >{{ row.severity }}</el-tag
            >
          </template></el-table-column
        >
        <el-table-column prop="description" label="描述" min-width="140" show-overflow-tooltip />
        <el-table-column prop="handler" label="响应人" width="80" />
        <el-table-column label="状态" width="80"
          ><template #default="{row}">
            <el-tag
              :type="row.status==='已解决'?'success':row.status==='处理中'?'warning':'danger'"
              size="small"
              >{{ row.status }}</el-tag
            >
          </template></el-table-column
        >
        <el-table-column label="操作" width="160"
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
    </el-card>

    <!-- 触发安灯弹窗 -->
    <el-dialog v-model="andonVisible" title="触发安灯" width="420px">
      <el-form :model="andonForm" label-width="80px">
        <el-form-item label="类型">
          <el-select v-model="andonForm.event_type" class="w-full">
            <el-option label="缺料" value="缺料" /><el-option label="设备故障" value="设备故障" />
            <el-option label="质量问题" value="质量问题" /><el-option
              label="安全"
              value="安全"
            /><el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="严重度">
          <el-select v-model="andonForm.severity" class="w-full">
            <el-option label="🔴 红色（停线）" value="红色" /><el-option
              label="🟡 黄色（预警）"
              value="黄色"
            /><el-option label="🔵 蓝色（请求）" value="蓝色" />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const saving = ref(false)
const aLoading = ref(false)
const summary = ref({})
const kanban = ref({ columns: {} })
const oee = ref({ items: [] })
const load = ref({ items: [] })
const andons = ref([])

// Andon
const andonVisible = ref(false)
const andonForm = reactive({ event_type: '缺料', severity: '红色', description: '' })

async function fetchAll() {
  const [s, k, o, l, a] = await Promise.all([
    api.get('/shop-floor/summary'),
    api.get('/shop-floor/kanban'),
    api.get('/shop-floor/oee', { params: { days: 30 } }),
    api.get('/shop-floor/work-center-load'),
    api.get('/shop-floor/andon'),
  ])
  summary.value = s
  kanban.value = k
  oee.value = o
  load.value = l
  andons.value = a.items || []
}

function showAndonDialog() {
  Object.assign(andonForm, { event_type: '缺料', severity: '红色', description: '' })
  andonVisible.value = true
}

async function createAndon() {
  saving.value = true
  try {
    await api.post('/shop-floor/andon', { ...andonForm })
    ElMessage.success('安灯已触发')
    andonVisible.value = false
    fetchAll()
  } finally { saving.value = false }
}

async function respondAndon(row) {
  await api.put(`/shop-floor/andon/${row.id}/respond`, { handler: '系统' })
  ElMessage.success('已响应')
  fetchAll()
}

async function resolveAndon(row) {
  await api.put(`/shop-floor/andon/${row.id}/resolve`)
  ElMessage.success('已解决')
  fetchAll()
}

onMounted(fetchAll)
</script>

<style scoped>
.sf-container { padding:0; }
.kpi-row { display:flex; gap:14px; margin-bottom:18px; }
.kpi-box { flex:1; border-radius:10px; padding:16px; color:#fff; display:flex; flex-direction:column; align-items:center; }
.kpi-num { font-size:32px; font-weight:800; line-height:1.2; }
.kpi-label { font-size:13px; opacity:0.85; margin-top:4px; }
.kanban-row { display:flex; gap:12px; min-height:200px; }
.kanban-col { flex:1; background:#f5f7fa; border-radius:8px; padding:10px; }
.kanban-header { font-weight:600; font-size:14px; margin-bottom:10px; color:#333; }
.kanban-count { background:#dcdfe6; color:#666; border-radius:10px; padding:1px 8px; font-size:12px; margin-left:6px; }
.kanban-card { background:#fff; border-radius:8px; padding:10px; margin-bottom:8px; border-left:3px solid #dcdfe6; box-shadow:0 1px 4px rgba(0,0,0,0.05); }
.kanban-card.priority-1 { border-left-color:#e6a23c; }
.kanban-card.priority-2 { border-left-color:#f56c6c; }
.kanban-wo { font-weight:600; font-size:13px; }
.kanban-mat { font-size:12px; color:#666; margin:2px 0 6px; }
.kanban-bar-bg { height:4px; background:#f0f0f0; border-radius:2px; margin-bottom:4px; }
.kanban-bar { height:100%; background:#409eff; border-radius:2px; transition:width 0.3s; }
.kanban-info { font-size:11px; color:#999; }
.kanban-wc { font-size:11px; color:#409eff; margin-top:2px; }
.kanban-empty { text-align:center; color:#bbb; padding:20px 0; font-size:13px; }
.oee-row { display:flex; align-items:center; gap:8px; margin-bottom:10px; }
.oee-name { width:100px; font-size:12px; color:#666; flex-shrink:0; }
.oee-bar-bg { flex:1; height:10px; background:#f0f0f0; border-radius:5px; overflow:hidden; }
.oee-bar { height:100%; border-radius:5px; transition:width 0.5s; }
.oee-val { width:40px; text-align:right; font-weight:600; font-size:13px; }
</style>
