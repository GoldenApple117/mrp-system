<template>
  <!-- 登录页：独立全屏，无侧边栏 -->
  <div v-if="isLoginPage" class="h-screen overflow-hidden">
    <router-view />
  </div>

  <!-- 正常布局：侧边栏 + 顶栏 + 内容 -->
  <div v-else id="app-container" class="flex h-screen overflow-hidden">
    <!-- ══════════ 侧边栏 ══════════ -->
    <aside
      :class="[
        'flex flex-col flex-shrink-0 transition-all duration-250 ease-in-out',
        'bg-[var(--color-bg-raised)] border-r border-[var(--color-border-light)]',
        isCollapse ? 'w-[56px]' : 'w-[232px]'
      ]"
    >
      <!-- Logo -->
      <div
        class="flex items-center h-12 flex-shrink-0 cursor-pointer select-none border-b border-[var(--color-border-subtle)]"
        :class="isCollapse ? 'justify-center' : 'px-4 gap-3'"
        @click="isCollapse = !isCollapse"
      >
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-sm">
          <span class="text-white text-xs font-bold">M</span>
        </div>
        <transition name="logo-text">
          <span v-if="!isCollapse" class="text-[var(--color-text-primary)] font-semibold text-[15px] tracking-wide whitespace-nowrap">MRP II</span>
        </transition>
      </div>

      <!-- 导航菜单 -->
      <nav class="flex-1 overflow-y-auto overflow-x-hidden py-2" :class="isCollapse ? 'px-1' : 'px-2'">
        <!-- Dashboard -->
        <div :class="isCollapse ? 'flex justify-center' : 'px-1 mb-1'">
          <router-link
            to="/dashboard"
            :class="[
              'flex items-center gap-3 h-9 rounded-md transition-all duration-150 text-[13px]',
              'hover:bg-[var(--color-bg-hover)]',
              isCollapse ? 'w-10 justify-center' : 'px-3 w-full',
              activeMenu === '/dashboard'
                ? 'bg-[var(--color-accent-muted)] text-[var(--color-accent)] font-medium'
                : 'text-[var(--color-text-secondary)]'
            ]"
          >
            <el-icon :size="16"><DataBoard /></el-icon>
            <span v-if="!isCollapse" class="truncate">仪表板</span>
          </router-link>
        </div>

        <div class="my-2 mx-3 border-t border-[var(--color-border-subtle)]" v-if="!isCollapse"></div>

        <!-- 基础数据 -->
        <NavGroup label="基础数据" :collapse="isCollapse">
          <NavItem to="/materials" icon="Box" label="物料管理" :collapse="isCollapse" :active="activeMenu === '/materials'" />
          <NavItem to="/bom" icon="Connection" label="BOM 管理" :collapse="isCollapse" :active="activeMenu === '/bom'" />
          <NavItem to="/inventory" icon="List" label="库存管理" :collapse="isCollapse" :active="activeMenu === '/inventory'" />
          <NavItem to="/routings" icon="Operation" label="工艺路线" :collapse="isCollapse" :active="activeMenu === '/routings'" />
        </NavGroup>

        <!-- 计划与执行 -->
        <NavGroup label="计划与执行" :collapse="isCollapse">
          <NavItem to="/mps" icon="Calendar" label="MPS 主计划" :collapse="isCollapse" :active="activeMenu === '/mps'" />
          <NavItem to="/mrp" icon="Cpu" label="MRP 运算" :collapse="isCollapse" :active="activeMenu === '/mrp'" />
          <NavItem to="/crp" icon="TrendCharts" label="CRP 计划" :collapse="isCollapse" :active="activeMenu === '/crp'" />
          <NavItem to="/sales" icon="Sell" label="销售管理" :collapse="isCollapse" :active="activeMenu === '/sales'" />
          <NavItem to="/purchase" icon="ShoppingCart" label="采购管理" :collapse="isCollapse" :active="activeMenu === '/purchase'" />
          <NavItem to="/production" icon="SetUp" label="生产管理" :collapse="isCollapse" :active="activeMenu === '/production'" />
        </NavGroup>

        <!-- 分析与监控 -->
        <NavGroup label="分析与监控" :collapse="isCollapse">
          <NavItem to="/reports" icon="DataAnalysis" label="报表分析" :collapse="isCollapse" :active="activeMenu === '/reports'" />
          <NavItem to="/exceptions" icon="WarningFilled" label="例外看板" :collapse="isCollapse" :active="activeMenu === '/exceptions'" />
          <NavItem to="/inspection" icon="Stamp" label="检验盘点" :collapse="isCollapse" :active="activeMenu === '/inspection'" />
        </NavGroup>

        <!-- 财务 -->
        <NavGroup label="财务" :collapse="isCollapse">
          <NavItem to="/finance" icon="CreditCard" label="财务管理" :collapse="isCollapse" :active="activeMenu === '/finance'" />
          <NavItem to="/cost" icon="Money" label="费用合计" :collapse="isCollapse" :active="activeMenu === '/cost'" />
        </NavGroup>
      </nav>

      <!-- 底部：系统工具 -->
      <div class="flex-shrink-0 border-t border-[var(--color-border-subtle)] p-2">
        <el-popover
          placement="right-start"
          :width="240"
          trigger="click"
          :offset="8"
          popper-class="tools-popover"
        >
          <template #reference>
            <button
              :class="[
                'flex items-center gap-3 w-full h-9 rounded-md transition-all duration-150',
                'text-[var(--color-text-tertiary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-secondary)]',
                isCollapse ? 'justify-center' : 'px-3'
              ]"
            >
              <el-icon :size="16"><Setting /></el-icon>
              <span v-if="!isCollapse" class="text-[13px] truncate">系统工具</span>
            </button>
          </template>

          <div class="p-3 space-y-3">
            <!-- 定时器 -->
            <div>
              <div class="text-2xs text-[var(--color-text-tertiary)] uppercase tracking-wider font-semibold mb-2">MRP 定时器</div>
              <div class="flex items-center justify-between mb-2 text-xs text-[var(--color-text-secondary)]">
                <span>启用</span>
                <el-switch v-model="timerEnabled" size="small" @change="saveSchedule" />
              </div>
              <div v-if="timerEnabled" class="flex items-center justify-between text-xs text-[var(--color-text-secondary)]">
                <span>执行时间</span>
                <div class="flex items-center gap-1">
                  <input type="number" min="0" max="23" v-model.number="timerHour" @change="saveSchedule"
                    class="timer-num-input" />
                  <span class="text-[var(--color-text-tertiary)] font-bold">:</span>
                  <input type="number" min="0" max="59" v-model.number="timerMinute" @change="saveSchedule"
                    class="timer-num-input" />
                </div>
              </div>
              <el-button size="small" class="w-full mt-2" @click="runMrpNow">立即执行 MRP</el-button>
            </div>

            <div class="border-t border-[var(--color-border-subtle)]"></div>

            <!-- 邮件通知 -->
            <div>
              <div class="text-2xs text-[var(--color-text-tertiary)] uppercase tracking-wider font-semibold mb-2">邮件通知</div>
              <div class="space-y-2">
                <div class="flex items-center gap-2">
                  <span class="text-2xs text-[var(--color-text-tertiary)] w-10 flex-shrink-0">收件</span>
                  <input v-model="emailTo" placeholder="your@email.com"
                    class="tool-text-input flex-1" />
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-2xs text-[var(--color-text-tertiary)] w-10 flex-shrink-0">服务器</span>
                  <input v-model="emailHost" placeholder="smtp.qq.com"
                    class="tool-text-input flex-1" />
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-2xs text-[var(--color-text-tertiary)] w-10 flex-shrink-0">端口</span>
                  <input v-model="emailPort" type="number" placeholder="587"
                    class="tool-text-input" style="width:72px" />
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-2xs text-[var(--color-text-tertiary)] w-10 flex-shrink-0">用户名</span>
                  <input v-model="emailUser" placeholder="2645174606@qq.com"
                    class="tool-text-input flex-1" />
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-2xs text-[var(--color-text-tertiary)] w-10 flex-shrink-0">密码</span>
                  <input v-model="emailPass" type="password" placeholder="QQ邮箱授权码"
                    class="tool-text-input flex-1" />
                </div>
              </div>
              <div class="flex gap-2 mt-2">
                <el-button size="small" class="flex-1 text-xs" @click="saveEmailConfig">保存配置</el-button>
                <el-button size="small" class="flex-1 text-xs" @click="sendTestEmail">测试邮件</el-button>
              </div>
            </div>

            <div class="border-t border-[var(--color-border-subtle)]"></div>

            <!-- 数据管理 -->
            <div>
              <div class="text-2xs text-[var(--color-text-tertiary)] uppercase tracking-wider font-semibold mb-2">数据管理</div>
              <div class="flex gap-2">
                <el-button size="small" class="flex-1 text-xs" @click="handleExport">导出</el-button>
                <el-button size="small" class="flex-1 text-xs" @click="handleImport">导入</el-button>
              </div>
              <input ref="importFileRef" type="file" accept=".json" style="display:none" @change="onImportFile" />
            </div>
          </div>
        </el-popover>
      </div>
    </aside>

    <!-- ══════════ 主区域 ══════════ -->
    <div class="flex flex-col flex-1 min-w-0">
      <!-- 顶栏 -->
      <header class="flex items-center h-12 flex-shrink-0 bg-[var(--color-bg-raised)] border-b border-[var(--color-border-light)] px-5 gap-4">
        <!-- 面包屑 -->
        <nav class="flex items-center gap-1.5 text-xs" aria-label="Breadcrumb">
          <router-link to="/dashboard" class="text-[var(--color-text-tertiary)] hover:text-[var(--color-accent)] transition-colors">
            <el-icon :size="14"><HomeFilled /></el-icon>
          </router-link>
          <span class="text-[var(--color-text-disabled)]">/</span>
          <span class="text-[var(--color-text-primary)] font-medium">{{ pageTitle }}</span>
        </nav>

        <div class="flex-1"></div>

        <!-- 全局搜索 -->
        <button
          class="flex items-center gap-1 h-7 px-2.5 rounded text-xs bg-transparent text-[var(--color-text-tertiary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-secondary)] border border-[var(--color-border-subtle)] transition-all duration-150 cursor-pointer"
          @click="searchPaletteRef?.open()"
          title="全局搜索 (Ctrl+K)"
        >
          <el-icon :size="13"><Search /></el-icon>
          <span class="hidden sm:inline">搜索</span>
          <kbd class="hidden sm:inline-flex items-center h-4 px-1 rounded text-2xs bg-[var(--color-bg-overlay)] border border-[var(--color-border-light)] text-[var(--color-text-disabled)] ml-0.5 font-mono">⌘K</kbd>
        </button>

        <!-- 快捷操作 -->
        <router-link to="/mrp" class="flex items-center gap-1 h-7 px-3 rounded text-xs bg-[var(--color-accent-muted)] text-[var(--color-accent-text)] hover:bg-[var(--color-accent)] hover:text-white transition-all duration-150 no-underline">
          <el-icon :size="13"><Cpu /></el-icon>
          MRP 运算
        </router-link>

        <!-- 导出Excel -->
        <button
          class="flex items-center gap-1 h-7 px-2.5 rounded text-xs bg-transparent text-[var(--color-text-tertiary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-secondary)] border border-[var(--color-border-subtle)] transition-all duration-150 cursor-pointer"
          @click="quickExport">{{ exportLoading ? '导出中...' : '📥 Excel导出' }}</button>

        <!-- 系统状态 -->
        <div class="flex items-center gap-1.5 text-xs text-[var(--color-success-text)]">
          <span class="w-1.5 h-1.5 rounded-full bg-[var(--color-success)] shadow-[0_0_4px_var(--color-success)]"></span>
          <span class="text-[var(--color-text-tertiary)]">系统运行中</span>
        </div>

        <!-- 用户 -->
        <div class="flex items-center gap-2 text-xs">
          <!-- 管理员：权限管理入口 + 待审批角标 -->
          <template v-if="auth.user?.role === 'admin'">
            <router-link
              to="/permissions"
              class="relative text-[var(--color-text-tertiary)] hover:text-[var(--color-accent)] transition-colors no-underline flex items-center gap-0.5"
            >
              <el-icon :size="14"><Setting /></el-icon>
              <span>权限</span>
              <span v-if="pendingCount > 0"
                class="absolute -top-1 -right-2 min-w-[16px] h-4 flex items-center justify-center rounded-full bg-red-500 text-white text-[10px] font-bold px-1"
              >{{ pendingCount }}</span>
            </router-link>
          </template>
          <span class="text-[var(--color-text-secondary)]">{{ auth.user?.username || 'admin' }}</span>
          <button
            class="text-[var(--color-text-tertiary)] hover:text-[var(--color-accent)] transition-colors cursor-pointer bg-transparent border-0 py-0.5 px-1 rounded"
            @click="handleLogout"
            title="退出登录"
          >
            <el-icon :size="14"><SwitchButton /></el-icon>
          </button>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="flex-1 overflow-y-auto bg-[var(--color-bg-base)] p-5 relative">
        <!-- 页面标题 -->
        <div class="mb-4">
          <h1 class="text-lg font-semibold text-[var(--color-text-primary)]">{{ pageTitle }}</h1>
          <p class="text-xs text-[var(--color-text-tertiary)] mt-0.5">{{ pageSubtitle }}</p>
        </div>
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
        <PermissionOverlay />
      </main>
    </div>

    <!-- 全局搜索面板 -->
    <SearchPalette ref="searchPaletteRef" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import NavGroup from '@/components/NavGroup.vue'
import NavItem from '@/components/NavItem.vue'
import SearchPalette from '@/components/SearchPalette.vue'
import PermissionOverlay from '@/components/PermissionOverlay.vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const isCollapse = ref(false)
const importFileRef = ref(null)
const searchPaletteRef = ref(null)
const exportLoading = ref(false)

// ====== 快速导出 ======
async function quickExport() {
  const routeName = route.path.replace('/', '') || 'dashboard'
  const entityMap = {
    'materials': '/api/system/export-excel/materials',
    'bom': '/api/system/export-excel/bom',
    'inventory': '/api/system/export-excel/inventory',
    'production': '/api/system/export-excel/work-orders',
  }
  const url = entityMap[routeName]
  if (!url) {
    ElMessage.info('当前页面暂无导出功能，点击"数据管理→导出"导出全部JSON')
    return
  }
  exportLoading.value = true
  try {
    const token = localStorage.getItem('token') || ''
    const resp = await fetch(url, { headers: { 'Authorization': 'Bearer ' + token } })
    if (!resp.ok) throw new Error(resp.statusText)
    const blob = await resp.blob()
    const blobUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = routeName + '.xlsx'
    a.click()
    URL.revokeObjectURL(blobUrl)
    ElMessage.success('导出完成')
  } catch { ElMessage.error('导出失败') }
  finally { setTimeout(() => exportLoading.value = false, 1000) }
}

// ====== 键盘快捷键 ======
function handleGlobalKeydown(e) {
  // Ctrl+K / Cmd+K → 全局搜索
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    searchPaletteRef.value?.open()
    return
  }
  // Ctrl+M → MRP 运算
  if ((e.ctrlKey || e.metaKey) && e.key === 'm') {
    e.preventDefault()
    router.push('/mrp')
    return
  }
  // Ctrl+D → 仪表板
  if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
    e.preventDefault()
    router.push('/dashboard')
    return
  }
  // Ctrl+B → BOM 管理
  if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
    e.preventDefault()
    router.push('/bom')
    return
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
  loadSchedule()
  loadEmailConfig()
  if (auth.user?.role === 'admin') fetchPendingCount()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})

async function loadSchedule() {
  try {
    const r = await fetch('/api/system/schedule')
    const d = await r.json()
    timerEnabled.value = d.enabled
    timerHour.value = d.hour
    timerMinute.value = d.minute
  } catch {}
}

const timerEnabled = ref(false)
const timerHour = ref(6)
const timerMinute = ref(0)

const saveSchedule = async () => {
  await fetch('/api/system/schedule', {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled: timerEnabled.value, hour: timerHour.value, minute: timerMinute.value })
  })
}

const runMrpNow = async () => {
  try {
    await ElMessageBox.confirm('立即执行 MRP 运算？', '确认', { type: 'info' })
    const r = await fetch('/api/system/schedule/run-now', { method: 'POST' })
    const d = await r.json()
    ElMessage[d.success ? 'success' : 'error'](d.message)
  } catch {}
}

function handleLogout() {
  auth.logout()
  router.push('/login')
  ElMessage.success('已退出登录')
}

// ====== 邮件配置 ======
const emailTo = ref('')
const emailHost = ref('')
const emailPort = ref(587)
const emailUser = ref('')
const emailPass = ref('')

async function loadEmailConfig() {
  try {
    const r = await fetch('/api/system/email-config')
    const d = await r.json()
    emailTo.value = d.to_email || ''
    emailHost.value = d.host || ''
    emailPort.value = d.port || 587
    emailUser.value = d.username || ''
    // password 返回 *** 脱敏，不清除已有值
  } catch {}
}

async function saveEmailConfig() {
  try {
    const body = {
      to_email: emailTo.value,
      host: emailHost.value,
      port: emailPort.value,
      username: emailUser.value,
      password: emailPass.value,
      from_addr: emailUser.value,
    }
    const r = await fetch('/api/system/email-config', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const d = await r.json()
    if (d.success) {
      ElMessage.success('邮件配置已保存')
      emailPass.value = ''  // 保存后清空密码框
    }
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

async function sendTestEmail() {
  if (!emailTo.value) {
    ElMessage.warning('请先填写接收邮箱')
    return
  }
  try {
    const r = await fetch('/api/system/email-test', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ to_email: emailTo.value }),
    })
    const d = await r.json()
    ElMessage[d.success ? 'success' : 'error'](d.message)
  } catch {
    ElMessage.error('发送失败')
  }
}

// ====== 权限管理 ======
const pendingCount = ref(0)

async function fetchPendingCount() {
  try {
    const r = await fetch('/api/permissions/pending-count', {
      headers: { Authorization: `Bearer ${auth.token}` },
    })
    const d = await r.json()
    pendingCount.value = d.count || 0
  } catch {}
}

const handleExport = async () => {
  try {
    const resp = await fetch('/api/system/export')
    const blob = await resp.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `mrp_backup_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('数据已导出')
  } catch { ElMessage.error('导出失败') }
}

const handleImport = () => { importFileRef.value?.click() }

const onImportFile = (e) => {
  const file = e.target.files[0]
  if (!file) return
  ElMessageBox.confirm('导入将覆盖现有数据，确定继续？', '确认导入', { type: 'warning' }).then(() => {
    const reader = new FileReader()
    reader.onload = async (ev) => {
      try {
        const data = JSON.parse(ev.target.result)
        const resp = await fetch('/api/system/import', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        })
        const result = await resp.json()
        if (result.success) {
          ElMessage.success(result.message)
          setTimeout(() => location.reload(), 500)
        } else {
          ElMessage.error(result.message)
        }
      } catch (ex) { ElMessage.error('导入失败: ' + ex.message) }
    }
    reader.readAsText(file)
  }).catch(() => {})
  e.target.value = ''
}

// ====== 路由 ======
const activeMenu = computed(() => route.path)
const isLoginPage = computed(() => route.path === '/login')

const pageTitle = computed(() => {
  const map = {
    '/dashboard': '仪表板',
    '/materials': '物料主数据管理',
    '/bom': 'BOM 物料清单管理',
    '/inventory': '库存管理与出入库',
    '/mps': 'MPS 主生产计划',
    '/sales': '销售订单管理',
    '/mrp': 'MRP 物料需求计算',
    '/purchase': '采购管理',
    '/production': '生产车间管理',
    '/routings': '工艺路线管理',
    '/reports': '报表与分析',
    '/crp': 'CRP 产能需求计划',
    '/inspection': '检验与盘点管理',
    '/finance': '财务管理',
    '/cost': '费用合计',
    '/exceptions': '例外看板',
    '/suppliers': '供应商管理',
    '/permissions': '权限管理',
  }
  return map[route.path] || 'MRP II 物料需求计划系统'
})

const pageSubtitle = computed(() => {
  const map = {
    '/dashboard': '系统概览与关键指标',
    '/materials': '查看与管理所有物料基础数据',
    '/bom': '维护产品物料清单与组成结构',
    '/inventory': '实时库存监控与出入库操作',
    '/mps': '主生产计划制定与批量管理',
    '/sales': '销售订单跟踪与客户管理',
    '/mrp': '执行物料需求计划计算',
    '/purchase': '采购订单管理与供应商跟踪',
    '/production': '生产工单派发与进度跟踪',
    '/routings': '定义产品制造的工序流程',
    '/reports': 'OTD、库存、工单等数据报表',
    '/crp': '产能负荷分析与瓶颈识别',
    '/inspection': '来料检验与库存盘点',
    '/finance': '财务收款与出货管理',
    '/cost': '项目费用汇总与分析',
    '/exceptions': '例外事件监控与处理',
    '/suppliers': '供应商信息维护',
    '/permissions': '用户权限申请与审批',
  }
  return map[route.path] || ''
})
</script>

<style scoped>
/* ── 侧边栏过渡 ── */
.logo-text-enter-active,
.logo-text-leave-active {
  transition: opacity 0.15s ease;
}
.logo-text-enter-from,
.logo-text-leave-to {
  opacity: 0;
}

/* ── 侧边栏导航项收起优化 ── */
aside :deep(nav .truncate) {
  transition: opacity 0.2s ease;
}
</style>

<!-- ═══ 全局样式 ═══ -->
<style>
/* ── 页面切换动画 ── */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ── el-table 暗色增强 ── */
.el-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: var(--color-bg-overlay, rgba(255,255,255,0.03));
  --el-table-row-hover-bg-color: var(--color-bg-hover, rgba(255,255,255,0.04));
  --el-table-border-color: var(--color-border-light, rgba(255,255,255,0.06));
  --el-table-text-color: var(--color-text-primary, #e8ecf1);
  --el-table-header-text-color: var(--color-text-secondary, #94a3b8);
}
.el-table th.el-table__cell {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border-bottom: 2px solid var(--color-border-default, rgba(255,255,255,0.08));
}
.el-table .el-table__row:hover > td {
  background: var(--color-bg-hover, rgba(255,255,255,0.04)) !important;
  box-shadow: inset 0 0 0 1px var(--color-accent-muted, rgba(59,130,246,0.1));
}
.el-table--striped .el-table__body tr.el-table__row--striped td {
  background: var(--color-bg-overlay, rgba(255,255,255,0.015)) !important;
}

/* ── 分页暗色 ── */
.el-pagination {
  --el-pagination-bg-color: transparent;
  --el-pagination-text-color: var(--color-text-secondary);
  --el-pagination-button-bg-color: var(--color-bg-overlay);
  --el-pagination-hover-color: var(--color-accent);
}
.el-pagination button,
.el-pagination .el-pager li {
  color: var(--color-text-secondary) !important;
  background: var(--color-bg-overlay) !important;
  border-radius: 6px !important;
}
.el-pagination button:hover,
.el-pagination .el-pager li:hover {
  color: var(--color-accent) !important;
}
.el-pagination .el-pager li.is-active {
  background: var(--color-accent) !important;
  color: #fff !important;
}

/* ── 对话框暗色覆盖 ── */
.el-dialog {
  --el-dialog-bg-color: var(--color-bg-raised, #141826);
  --el-dialog-title-font-size: 16px;
  border: 1px solid var(--color-border-light);
  border-radius: 14px;
  box-shadow: 0 16px 64px rgba(0,0,0,0.5);
}
.el-dialog__header {
  border-bottom: 1px solid var(--color-border-subtle);
  padding: 18px 24px 14px;
}
.el-dialog__body {
  padding: 20px 24px;
}

/* ── 工具弹出框 ── */
:deep(.tools-popover) {
  background: var(--color-bg-overlay) !important;
  border: 1px solid var(--color-border-default) !important;
  border-radius: var(--radius-md) !important;
  padding: 0 !important;
  box-shadow: var(--shadow-elevated) !important;
  overflow: visible !important;
}
</style>

<!-- ═══ 全局样式：Popover 脱离 #app-container，scoped 无法命中 ═══ -->
<style>
/* MRP 定时器弹出框 */
.tools-popover {
  background: var(--color-bg-overlay, #2d2d2d) !important;
  border: 1px solid var(--color-border-default, #444) !important;
  border-radius: 8px !important;
  padding: 0 !important;
  box-shadow: 0 8px 24px rgba(0,0,0,0.45) !important;
}
/* 原生 input 数字输入框 — 完全可控，不依赖 Element Plus 样式 */
.timer-num-input {
  width: 56px;
  height: 30px;
  background: var(--color-bg-overlay, #2d2d2d) !important;
  color: var(--color-text-primary, #e8ecf1) !important;
  border: 1px solid var(--color-border-default, #444) !important;
  border-radius: 5px !important;
  text-align: center !important;
  font-size: 15px !important;
  font-weight: 700 !important;
  outline: none !important;
  -moz-appearance: textfield;
}
.timer-num-input::-webkit-inner-spin-button,
.timer-num-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.timer-num-input:focus {
  border-color: var(--color-accent, #3b82f6) !important;
  box-shadow: 0 0 0 2px rgba(59,130,246,0.3) !important;
}
/* 邮件配置文本输入框 */
.tool-text-input {
  height: 28px;
  background: var(--color-bg-overlay, #2d2d2d) !important;
  color: var(--color-text-primary, #e8ecf1) !important;
  border: 1px solid var(--color-border-default, #444) !important;
  border-radius: 4px !important;
  padding: 0 8px !important;
  font-size: 12px !important;
  outline: none !important;
}
.tool-text-input::placeholder {
  color: var(--color-text-disabled, #666) !important;
}
.tool-text-input:focus {
  border-color: var(--color-accent, #3b82f6) !important;
  box-shadow: 0 0 0 2px rgba(59,130,246,0.3) !important;
}
</style>
