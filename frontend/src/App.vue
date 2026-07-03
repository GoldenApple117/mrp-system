<template>
  <div id="app-container" class="flex h-screen overflow-hidden">
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
          :width="220"
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
                  <el-input-number v-model="timerHour" :min="0" :max="23" size="small" controls-position="right" style="width:48px" @change="saveSchedule" />
                  <span class="text-[var(--color-text-tertiary)]">:</span>
                  <el-input-number v-model="timerMinute" :min="0" :max="59" size="small" controls-position="right" style="width:48px" @change="saveSchedule" />
                </div>
              </div>
              <el-button size="small" class="w-full mt-2" @click="runMrpNow">立即执行 MRP</el-button>
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

        <!-- 系统状态 -->
        <div class="flex items-center gap-1.5 text-xs text-[var(--color-success-text)]">
          <span class="w-1.5 h-1.5 rounded-full bg-[var(--color-success)] shadow-[0_0_4px_var(--color-success)]"></span>
          <span class="text-[var(--color-text-tertiary)]">系统运行中</span>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="flex-1 overflow-y-auto bg-[var(--color-bg-base)] p-5">
        <router-view />
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

const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)
const importFileRef = ref(null)
const searchPaletteRef = ref(null)

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
  }
  return map[route.path] || 'MRP II 物料需求计划系统'
})
</script>

<style scoped>
/* ── 过渡动画 ── */
.logo-text-enter-active,
.logo-text-leave-active {
  transition: opacity 0.15s ease;
}
.logo-text-enter-from,
.logo-text-leave-to {
  opacity: 0;
}

/* ── 工具弹出框 ── */
:deep(.tools-popover) {
  background: var(--color-bg-overlay) !important;
  border: 1px solid var(--color-border-default) !important;
  border-radius: var(--radius-md) !important;
  padding: 0 !important;
  box-shadow: var(--shadow-elevated) !important;
}
</style>
