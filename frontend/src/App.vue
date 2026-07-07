<template>
  <el-config-provider :locale="zhCn">
    <!-- 登录页：独立全屏，无侧边栏 -->
    <div v-if="isLoginPage" class="h-screen overflow-hidden">
      <router-view />
    </div>

    <!-- 正常布局 -->
    <div v-else id="app-container" class="flex h-screen overflow-hidden">
      <!-- 桌面/平板：固定侧边栏 -->
      <AppSidebar
        v-if="!isMobile"
        :is-collapse="sidebarCollapsed"
        :timer-enabled="timerEnabled"
        :timer-hour="timerHour"
        :timer-minute="timerMinute"
        :email-to="emailTo"
        :email-host="emailHost"
        :email-port="emailPort"
        :email-user="emailUser"
        :email-pass="emailPass"
        @toggle-collapse="toggleSidebar"
        @save-schedule="saveSchedule"
        @run-mrp="runMrpNow"
        @save-email="saveEmailConfig"
        @test-email="sendTestEmail"
        @export-data="handleExport"
        @import-data="handleImport"
        @toggle-timer="timerEnabled = $event"
        @update:timer-hour="timerHour = $event"
        @update:timer-minute="timerMinute = $event"
        @update:email-to="emailTo = $event"
        @update:email-host="emailHost = $event"
        @update:email-port="emailPort = $event"
        @update:email-user="emailUser = $event"
        @update:email-pass="emailPass = $event"
      />

      <!-- 手机：抽屉式侧边栏 -->
      <el-drawer v-model="mobileMenuOpen" direction="ltr" size="232px" :with-header="false">
        <AppSidebar
          :is-collapse="false"
          :timer-enabled="timerEnabled"
          :timer-hour="timerHour"
          :timer-minute="timerMinute"
          :email-to="emailTo"
          :email-host="emailHost"
          :email-port="emailPort"
          :email-user="emailUser"
          :email-pass="emailPass"
          @toggle-collapse="mobileMenuOpen = false"
          @save-schedule="saveSchedule"
          @run-mrp="runMrpNow"
          @save-email="saveEmailConfig"
          @test-email="sendTestEmail"
          @export-data="handleExport"
          @import-data="handleImport"
          @toggle-timer="timerEnabled = $event"
          @update:timer-hour="timerHour = $event"
          @update:timer-minute="timerMinute = $event"
          @update:email-to="emailTo = $event"
          @update:email-host="emailHost = $event"
          @update:email-port="emailPort = $event"
          @update:email-user="emailUser = $event"
          @update:email-pass="emailPass = $event"
        />
      </el-drawer>

      <!-- 主区域 -->
      <div class="flex flex-col flex-1 min-w-0">
        <!-- 顶栏 -->
        <header
          class="flex items-center h-12 flex-shrink-0 bg-[var(--color-bg-raised)] border-b border-[var(--color-border-light)] px-5 gap-4"
        >
          <!-- 移动端汉堡菜单 -->
          <button
            v-if="isMobile"
            class="md:hidden flex items-center justify-center w-8 h-8 rounded text-[var(--color-text-tertiary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-primary)] transition-colors cursor-pointer bg-transparent border-0"
            @click="mobileMenuOpen = true"
          >
            <span class="text-lg leading-none">☰</span>
          </button>
          <nav class="flex items-center gap-1.5 text-xs" aria-label="Breadcrumb">
            <router-link
              to="/dashboard"
              class="text-[var(--color-text-tertiary)] hover:text-[var(--color-accent)] transition-colors"
            >
              <el-icon :size="14"><HomeFilled /></el-icon>
            </router-link>
            <span class="text-[var(--color-text-disabled)]">/</span>
            <span class="text-[var(--color-text-primary)] font-medium">{{ pageTitle }}</span>
          </nav>

          <div class="flex-1"></div>

          <button
            class="flex items-center gap-1 h-7 px-2.5 rounded text-xs bg-transparent text-[var(--color-text-tertiary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-secondary)] border border-[var(--color-border-subtle)] transition-all duration-150 cursor-pointer"
            title="全局搜索 (Ctrl+K)"
            @click="searchPaletteRef?.open()"
          >
            <el-icon :size="13"><Search /></el-icon>
            <span class="hidden sm:inline">搜索</span>
            <kbd
              class="hidden sm:inline-flex items-center h-4 px-1 rounded text-2xs bg-[var(--color-bg-overlay)] border border-[var(--color-border-light)] text-[var(--color-text-disabled)] ml-0.5 font-mono"
              >⌘K</kbd
            >
          </button>

          <router-link
            to="/mrp"
            class="flex items-center gap-1 h-7 px-3 rounded text-xs bg-[var(--color-accent-muted)] text-[var(--color-accent-text)] hover:bg-[var(--color-accent)] hover:text-white transition-all duration-150 no-underline"
          >
            <el-icon :size="13"><Cpu /></el-icon>
            MRP 运算
          </router-link>

          <button
            class="flex items-center gap-1 h-7 px-2.5 rounded text-xs bg-transparent text-[var(--color-text-tertiary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-secondary)] border border-[var(--color-border-subtle)] transition-all duration-150 cursor-pointer"
            @click="quickExport"
          >
            {{ exportLoading ? '导出中...' : '📥 Excel导出' }}
          </button>

          <div class="flex items-center gap-1.5 text-xs text-[var(--color-success-text)]">
            <span
              class="w-1.5 h-1.5 rounded-full bg-[var(--color-success)] shadow-[0_0_4px_var(--color-success)]"
            ></span>
            <span class="text-[var(--color-text-tertiary)]">系统运行中</span>
          </div>

          <div class="flex items-center gap-2 text-xs">
            <template v-if="auth.user?.role === 'admin'">
              <router-link
                to="/permissions"
                class="relative text-[var(--color-text-tertiary)] hover:text-[var(--color-accent)] transition-colors no-underline flex items-center gap-0.5"
              >
                <el-icon :size="14"><Setting /></el-icon>
                <span>权限</span>
                <span
                  v-if="pendingCount > 0"
                  class="absolute -top-1 -right-2 min-w-[16px] h-4 flex items-center justify-center rounded-full bg-red-500 text-white text-[10px] font-bold px-1"
                  >{{ pendingCount }}</span
                >
              </router-link>
            </template>
            <span
              class="text-[var(--color-text-secondary)]"
              >{{ auth.user?.username || 'admin' }}</span
            >
            <button
              class="text-[var(--color-text-tertiary)] hover:text-[var(--color-accent)] transition-colors cursor-pointer bg-transparent border-0 py-0.5 px-1 rounded"
              title="退出登录"
              @click="handleLogout"
            >
              <el-icon :size="14"><SwitchButton /></el-icon>
            </button>
          </div>
        </header>

        <!-- 内容区 -->
        <main
          id="main-content"
          class="flex-1 overflow-y-auto bg-[var(--color-bg-base)] p-5 relative"
        >
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

      <SearchPalette ref="searchPaletteRef" />
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import api from '@/api'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import SearchPalette from '@/components/navigation/SearchPalette.vue'
import PermissionOverlay from '@/components/common/PermissionOverlay.vue'
import { useAuthStore } from '@/stores/auth'
import { useMRPScheduler } from '@/composables/useMRPScheduler'
import { useEmailConfig } from '@/composables/useEmailConfig'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

// ====== 响应式断点 ======
const screenWidth = ref(window.innerWidth)
const mobileMenuOpen = ref(false)

function onResize() { screenWidth.value = window.innerWidth }
const isMobile = computed(() => screenWidth.value < 768)
const isTablet = computed(() => screenWidth.value >= 768 && screenWidth.value < 1024)

// 桌面端手动折叠，平板/手机端自动折叠
const sidebarCollapsed = computed(() => isTablet.value || isMobile.value || manualCollapse.value)
const manualCollapse = ref(false)
function toggleSidebar() {
  if (isMobile.value) { mobileMenuOpen.value = !mobileMenuOpen.value; return }
  manualCollapse.value = !manualCollapse.value
}
const searchPaletteRef = ref(null)
const exportLoading = ref(false)
const pendingCount = ref(0)

const { timerEnabled, timerHour, timerMinute, loadSchedule, saveSchedule } = useMRPScheduler()
const { emailTo, emailHost, emailPort, emailUser, emailPass, loadEmailConfig, saveEmailConfig, sendTestEmail } = useEmailConfig()

// ====== 快速导出 ======
async function quickExport() {
  const routeName = route.path.replace('/', '') || 'dashboard'
  const entityMap = {
    materials: '/api/system/export-excel/materials',
    bom: '/api/system/export-excel/bom',
    inventory: '/api/system/export-excel/inventory',
    production: '/api/system/export-excel/work-orders',
  }
  const url = entityMap[routeName]
  if (!url) {
    ElMessage.info('当前页面暂无导出功能，点击"数据管理→导出"导出全部JSON')
    return
  }
  exportLoading.value = true
  try {
    const apiUrl = url.replace('/api/', '/')
    const blob = await api.get(apiUrl, { responseType: 'blob' })
    const blobUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = routeName + '.xlsx'
    a.click()
    URL.revokeObjectURL(blobUrl)
    ElMessage.success('导出完成')
  } catch { ElMessage.error('导出失败') }
  finally { setTimeout(() => (exportLoading.value = false), 1000) }
}

// ====== 键盘快捷键 ======
function handleGlobalKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); searchPaletteRef.value?.open(); return }
  if ((e.ctrlKey || e.metaKey) && e.key === 'm') { e.preventDefault(); router.push('/mrp'); return }
  if ((e.ctrlKey || e.metaKey) && e.key === 'd') { e.preventDefault(); router.push('/dashboard'); return }
  if ((e.ctrlKey || e.metaKey) && e.key === 'b') { e.preventDefault(); router.push('/bom'); return }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
  window.addEventListener('resize', onResize)
  loadSchedule()
  loadEmailConfig()
  if (auth.user?.role === 'admin') fetchPendingCount()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
  window.removeEventListener('resize', onResize)
})

function handleLogout() {
  auth.logout()
  router.push('/login')
  ElMessage.success('已退出登录')
}

// ====== 执行 MRP ======
const runMrpNow = async () => {
  try {
    await ElMessageBox.confirm('立即执行 MRP 运算？', '确认', { type: 'info' })
    const d = await api.post('/system/schedule/run-now')
    ElMessage[d.success ? 'success' : 'error'](d.message)
  } catch (e) { if (e !== 'cancel') console.error('[MRP] 手动执行MRP失败', e) }
}

// ====== 权限管理 ======
async function fetchPendingCount() {
  try {
    const d = await api.get('/permissions/pending-count')
    pendingCount.value = d.count || 0
  } catch (e) { console.error('[MRP] 加载待审批数失败', e) }
}

// ====== 数据导入导出 ======
const handleExport = async () => {
  try {
    const blob = await api.get('/system/export', { responseType: 'blob' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `mrp_backup_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('数据已导出')
  } catch { ElMessage.error('导出失败') }
}

const importFileRef = ref(null)
const handleImport = () => { importFileRef.value?.click() }

const onImportFile = (e) => {
  const file = e.target.files[0]
  if (!file) return
  ElMessageBox.confirm('导入将覆盖现有数据，确定继续？', '确认导入', { type: 'warning' })
    .then(() => {
      const reader = new FileReader()
      reader.onload = async (ev) => {
        try {
          const data = JSON.parse(ev.target.result)
          const result = await api.post('/system/import', data)
          if (result.success) {
            ElMessage.success(result.message)
            setTimeout(() => location.reload(), 500)
          } else {
            ElMessage.error(result.message)
          }
        } catch (ex) { ElMessage.error('导入失败: ' + ex.message) }
      }
      reader.readAsText(file)
    })
    .catch(() => {})
  e.target.value = ''
}

// ====== 路由 ======
const isLoginPage = computed(() => route.path === '/login')

const pageTitle = computed(() => {
  const map = {
    '/dashboard': '生产驾驶舱', '/materials': '物料主数据管理',
    '/bom': 'BOM 物料清单管理', '/inventory': '库存管理与出入库',
    '/mps': 'MPS 主生产计划', '/sales': '销售订单管理',
    '/mrp': 'MRP 物料需求计算', '/purchase': '采购管理',
    '/production': '生产车间管理', '/routings': '工艺路线管理',
    '/reports': '报表中心', '/crp': 'CRP 产能需求计划',
    '/inspection': '检验与盘点管理', '/finance': '财务管理',
    '/cost': '费用合计', '/exceptions': '例外看板',
    '/suppliers': '供应商管理', '/permissions': '权限管理',
  }
  return map[route.path] || 'MRP II 物料需求计划系统'
})

const pageSubtitle = computed(() => {
  const map = {
    '/dashboard': 'KPI 指标 / 工单看板 / 实时监控',
    '/materials': '查看与管理所有物料基础数据',
    '/bom': '维护产品物料清单与组成结构',
    '/inventory': '实时库存监控与出入库操作',
    '/mps': '主生产计划制定与批量管理',
    '/sales': '销售订单跟踪与客户管理',
    '/mrp': '执行物料需求计划计算',
    '/purchase': '采购订单管理与供应商跟踪',
    '/production': '生产工单派发与进度跟踪',
    '/routings': '定义产品制造的工序流程',
    '/reports': '历史数据查询与可视化分析',
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
.logo-text-enter-active,
.logo-text-leave-active {
  transition: opacity 0.15s ease;
}
.logo-text-enter-from,
.logo-text-leave-to {
  opacity: 0;
}
</style>

<style>
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
  font-size: 11px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase;
  border-bottom: 2px solid var(--color-border-default, rgba(255,255,255,0.08));
}
.el-table .el-table__row:hover > td {
  background: var(--color-bg-hover, rgba(255,255,255,0.04)) !important;
  box-shadow: inset 0 0 0 1px var(--color-accent-muted, rgba(59,130,246,0.1));
}
.el-table--striped .el-table__body tr.el-table__row--striped td {
  background: var(--color-bg-overlay, rgba(255,255,255,0.015)) !important;
}
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
.el-pagination .el-pager li:hover { color: var(--color-accent) !important; }
.el-pagination .el-pager li.is-active {
  background: var(--color-accent) !important; color: #fff !important;
}
.el-dialog {
  --el-dialog-bg-color: var(--color-bg-raised, #141826);
  --el-dialog-title-font-size: 16px;
  border: 1px solid var(--color-border-light);
  border-radius: 14px;
  box-shadow: 0 16px 64px rgba(0,0,0,0.5);
}
.el-dialog__header { border-bottom: 1px solid var(--color-border-subtle); padding: 18px 24px 14px; }
.el-dialog__body { padding: 20px 24px; }
:deep(.tools-popover) {
  background: var(--color-bg-overlay) !important;
  border: 1px solid var(--color-border-default) !important;
  border-radius: var(--radius-md) !important;
  padding: 0 !important;
  box-shadow: var(--shadow-elevated) !important;
  overflow: visible !important;
}
.tools-popover {
  background: var(--color-bg-overlay, #2d2d2d) !important;
  border: 1px solid var(--color-border-default, #444) !important;
  border-radius: 8px !important;
  padding: 0 !important;
  box-shadow: 0 8px 24px rgba(0,0,0,0.45) !important;
}
.timer-num-input {
  width: 56px; height: 30px;
  background: var(--color-bg-overlay, #2d2d2d) !important;
  color: var(--color-text-primary, #e8ecf1) !important;
  border: 1px solid var(--color-border-default, #444) !important;
  border-radius: 5px !important;
  text-align: center !important;
  font-size: 15px !important; font-weight: 700 !important;
  outline: none !important;
  -moz-appearance: textfield;
}
.timer-num-input::-webkit-inner-spin-button,
.timer-num-input::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
.timer-num-input:focus {
  border-color: var(--color-accent, #3b82f6) !important;
  box-shadow: 0 0 0 2px rgba(59,130,246,0.3) !important;
}
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
.tool-text-input::placeholder { color: var(--color-text-disabled, #666) !important; }
.tool-text-input:focus {
  border-color: var(--color-accent, #3b82f6) !important;
  box-shadow: 0 0 0 2px rgba(59,130,246,0.3) !important;
}

/* ── 表格响应式：小屏水平滚动 ── */
@media (max-width: 1023px) {
  .el-table {
    display: block !important;
    overflow-x: auto !important;
  }
}

/* ── 移动端触摸优化 ── */
@media (max-width: 767px) {
  /* 最小触控区域 44x44px */
  .el-button--small { min-height: 36px; min-width: 36px; }
  .el-pagination button { min-width: 36px; min-height: 36px; }

  /* 防 iOS 缩放 */
  input[type="text"],
  input[type="number"],
  input[type="password"],
  input[type="search"],
  textarea,
  select {
    font-size: 16px !important;
  }

  /* 移动端侧边栏抽屉触摸滑动 */
  .el-drawer { -webkit-overflow-scrolling: touch; }

  /* 移动端页面内边距 */
  main { padding: 12px !important; }
  .page-container { padding: 0 !important; }
}

/* ── 微交互增强 ── */

/* 表格行悬停：左侧色条 */
.el-table .el-table__row {
  transition: background 0.15s ease;
  position: relative;
}
.el-table .el-table__row:hover {
  box-shadow: inset 3px 0 0 var(--color-accent);
}

/* 按钮按压反馈 */
.el-button { transition: transform 0.1s ease, box-shadow 0.1s ease; }
.el-button:active { transform: scale(0.97); }

/* 侧边栏菜单项活跃指示器滑入 */
.nav-active-indicator {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

/* 输入框聚焦增强 */
.el-input .el-input__wrapper {
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

/* 卡片悬停微浮 */
.el-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.el-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

/* 标签/徽章悬浮 */
.el-tag {
  transition: transform 0.15s ease;
}
.el-tag:hover {
  transform: scale(1.05);
}

/* 分页按钮反馈 */
.el-pager li {
  transition: all 0.15s ease;
}

/* 进度条过渡 */
.el-progress-bar__inner {
  transition: width 0.6s ease;
}

/* 链接下划线动画 */
a.underline-anim {
  background-image: linear-gradient(var(--color-accent), var(--color-accent));
  background-size: 0% 1px;
  background-position: 0% 100%;
  background-repeat: no-repeat;
  transition: background-size 0.3s ease;
}
a.underline-anim:hover {
  background-size: 100% 1px;
}

/* ── 无障碍增强 ── */

/* 聚焦可见样式 */
:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
  border-radius: 2px;
}

/* 跳过导航链接受聚焦 */
.skip-link:focus {
  top: 0;
}

/* 屏幕阅读器专用 */
.sr-only {
  position: absolute; width: 1px; height: 1px;
  padding: 0; margin: -1px; overflow: hidden;
  clip: rect(0, 0, 0, 0); white-space: nowrap;
  border-width: 0;
}
</style>
