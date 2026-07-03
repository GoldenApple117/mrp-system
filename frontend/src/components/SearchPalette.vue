<template>
  <Teleport to="body">
    <Transition name="palette">
      <div v-if="visible" class="palette-overlay" @click.self="close">
        <div class="palette-dialog">
          <!-- 搜索框 -->
          <div class="flex items-center gap-2 px-4 py-3 border-b border-[var(--color-border-subtle)]">
            <el-icon :size="16" color="var(--color-text-tertiary)"><Search /></el-icon>
            <input
              ref="inputRef"
              v-model="query"
              type="text"
              class="flex-1 bg-transparent border-none outline-none text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-disabled)]"
              placeholder="搜索页面或输入命令..."
              @keydown="handleKeydown"
              autofocus
            />
            <kbd class="shortcut-kbd">Esc</kbd>
          </div>

          <!-- 无结果 -->
          <div v-if="query && !filtered.length" class="px-4 py-8 text-center text-xs text-[var(--color-text-tertiary)]">
            <el-icon :size="24" color="var(--color-text-disabled)"><Search /></el-icon>
            <p class="mt-2">未找到 "{{ query }}" 相关结果</p>
          </div>

          <!-- 初始提示 -->
          <div v-if="!query" class="px-4 py-3">
            <div class="text-2xs text-[var(--color-text-tertiary)] uppercase tracking-wider font-semibold mb-2 px-2">
              快捷键
            </div>
            <div class="space-y-0.5">
              <div class="flex items-center justify-between px-2 py-1.5 rounded text-xs">
                <span class="text-[var(--color-text-secondary)]">全局搜索</span>
                <kbd class="shortcut-kbd">Ctrl+K</kbd>
              </div>
              <div class="flex items-center justify-between px-2 py-1.5 rounded text-xs">
                <span class="text-[var(--color-text-secondary)]">MRP 运算</span>
                <kbd class="shortcut-kbd">Ctrl+M</kbd>
              </div>
              <div class="flex items-center justify-between px-2 py-1.5 rounded text-xs">
                <span class="text-[var(--color-text-secondary)]">仪表板</span>
                <kbd class="shortcut-kbd">Ctrl+D</kbd>
              </div>
            </div>
          </div>

          <!-- 搜索结果列表 -->
          <div v-if="query && filtered.length" class="max-h-[280px] overflow-y-auto py-1">
            <button
              v-for="(item, i) in filtered"
              :key="item.path"
              :ref="el => { if (el) itemRefs[i] = el }"
              :class="[
                'flex items-center gap-3 w-full px-4 py-2.5 text-left text-sm transition-colors duration-75 border-none cursor-pointer',
                i === activeIndex
                  ? 'bg-[var(--color-accent-muted)] text-[var(--color-accent)]'
                  : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-primary)]'
              ]"
              @click="navigateTo(item)"
              @mouseenter="activeIndex = i"
            >
              <el-icon :size="15" :color="i === activeIndex ? '#3b82f6' : '#888'">
                <component :is="item.icon" />
              </el-icon>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-1.5">
                  <span class="truncate">{{ item.label }}</span>
                  <el-tag v-if="item.section" size="small" effect="plain" class="!text-2xs !px-1 !py-0">{{ item.section }}</el-tag>
                </div>
                <div v-if="item.desc" class="text-xs text-[var(--color-text-tertiary)] truncate mt-0.5">
                  {{ item.desc }}
                </div>
              </div>
              <span v-if="i === activeIndex" class="text-2xs text-[var(--color-text-disabled)]">↵ 进入</span>
            </button>
          </div>

          <!-- 底部提示 -->
          <div class="flex items-center justify-between px-4 py-2 border-t border-[var(--color-border-subtle)] text-2xs text-[var(--color-text-disabled)]">
            <div class="flex items-center gap-3">
              <span>↑↓ 导航</span>
              <span>↵ 选择</span>
              <span>Esc 关闭</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  DataBoard, Box, Connection, List, Calendar, Cpu, ShoppingCart,
  SetUp, TrendCharts, Sell, DataAnalysis, WarningFilled, Stamp,
  CreditCard, Money, Operation, Search
} from '@element-plus/icons-vue'

const router = useRouter()
const visible = ref(false)
const query = ref('')
const activeIndex = ref(0)
const inputRef = ref(null)
const itemRefs = ref({})

// ====== 所有可搜索的页面 ======
const pages = [
  { path: '/dashboard', label: '仪表板', desc: 'KPI 总览与快捷入口', section: '首页', icon: DataBoard },
  { path: '/materials', label: '物料管理', desc: '物料主数据与三级折叠视图', section: '基础数据', icon: Box },
  { path: '/bom', label: 'BOM 管理', desc: '物料清单与树形编辑', section: '基础数据', icon: Connection },
  { path: '/inventory', label: '库存管理', desc: '库存、呆滞料与出入库流水', section: '基础数据', icon: List },
  { path: '/routings', label: '工艺路线', desc: '工艺路线与工作中心', section: '基础数据', icon: Operation },
  { path: '/mps', label: 'MPS 主计划', desc: '主生产计划与排程', section: '计划与执行', icon: Calendar },
  { path: '/mrp', label: 'MRP 运算', desc: '一键物料需求计算', section: '计划与执行', icon: Cpu },
  { path: '/crp', label: 'CRP 计划', desc: '产能需求计划分析', section: '计划与执行', icon: TrendCharts },
  { path: '/sales', label: '销售管理', desc: '销售订单与客户管理', section: '计划与执行', icon: Sell },
  { path: '/purchase', label: '采购管理', desc: '采购订单与供应商', section: '计划与执行', icon: ShoppingCart },
  { path: '/production', label: '生产管理', desc: '生产工单与车间管理', section: '计划与执行', icon: SetUp },
  { path: '/reports', label: '报表分析', desc: 'OTD、库存、工单统计图表', section: '分析与监控', icon: DataAnalysis },
  { path: '/exceptions', label: '例外看板', desc: 'MRP 例外信息监控', section: '分析与监控', icon: WarningFilled },
  { path: '/inspection', label: '检验盘点', desc: '物料检验与库存盘点', section: '分析与监控', icon: Stamp },
  { path: '/finance', label: '财务管理', desc: '收款记录与汇总', section: '财务', icon: CreditCard },
  { path: '/cost', label: '费用合计', desc: '项目-模块-零件三级成本', section: '财务', icon: Money },
]

// ====== 模糊搜索 ======
const filtered = computed(() => {
  if (!query.value.trim()) return []
  const q = query.value.toLowerCase()
  return pages
    .filter(p =>
      p.label.toLowerCase().includes(q) ||
      p.desc.toLowerCase().includes(q) ||
      p.section.toLowerCase().includes(q) ||
      p.path.toLowerCase().includes(q)
    )
    .slice(0, 8)
})

// ====== 导航 ======
function navigateTo(item) {
  router.push(item.path)
  close()
}

// ====== 键盘导航 ======
function handleKeydown(e) {
  if (e.key === 'Escape') {
    close()
    return
  }
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    activeIndex.value = Math.min(activeIndex.value + 1, filtered.value.length - 1)
    scrollToActive()
    return
  }
  if (e.key === 'ArrowUp') {
    e.preventDefault()
    activeIndex.value = Math.max(activeIndex.value - 1, 0)
    scrollToActive()
    return
  }
  if (e.key === 'Enter') {
    e.preventDefault()
    const item = filtered.value[activeIndex.value]
    if (item) navigateTo(item)
  }
}

function scrollToActive() {
  nextTick(() => {
    const el = itemRefs.value[activeIndex.value]
    if (el) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  })
}

// ====== 显示/隐藏 ======
let lastFocused = null

function open() {
  lastFocused = document.activeElement
  visible.value = true
  query.value = ''
  activeIndex.value = 0
  nextTick(() => inputRef.value?.focus())
}

function close() {
  visible.value = false
  lastFocused?.focus()
}

// ====== 暴露给父组件 ======
defineExpose({ open, close, visible })
</script>

<style scoped>
/* ── 遮罩层 ── */
.palette-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--z-dialog, 600);
  display: flex;
  justify-content: center;
  padding-top: 15vh;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

/* ── 弹窗 ── */
.palette-dialog {
  width: 480px;
  max-height: 440px;
  background: var(--color-bg-overlay);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-dialog), 0 0 0 1px rgba(255, 255, 255, 0.04);
  overflow: hidden;
  align-self: flex-start;
}

/* ── 快捷键标签 ── */
.shortcut-kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 18px;
  min-width: 18px;
  padding: 0 5px;
  border-radius: 3px;
  background: var(--color-bg-raised);
  border: 1px solid var(--color-border-light);
  color: var(--color-text-disabled);
  font-family: var(--font-mono);
  font-size: 10px;
  line-height: 1;
}

/* ── 进入/退出动画 ── */
.palette-enter-active {
  transition: opacity 120ms ease-out;
}
.palette-enter-active .palette-dialog {
  transition: transform 120ms ease-out, opacity 120ms ease-out;
}
.palette-leave-active {
  transition: opacity 80ms ease-in;
}
.palette-leave-active .palette-dialog {
  transition: transform 80ms ease-in, opacity 80ms ease-in;
}

.palette-enter-from {
  opacity: 0;
}
.palette-enter-from .palette-dialog {
  transform: scale(0.96) translateY(-8px);
  opacity: 0;
}

.palette-leave-to {
  opacity: 0;
}
.palette-leave-to .palette-dialog {
  transform: scale(0.96) translateY(-8px);
  opacity: 0;
}
</style>
