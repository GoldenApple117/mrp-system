<template>
  <aside
    :class="[
      'flex flex-col flex-shrink-0 transition-all duration-250 ease-in-out',
      'bg-[var(--color-bg-raised)] border-r border-[var(--color-border-light)]',
      isCollapse ? 'w-[56px]' : 'w-[232px]',
    ]"
  >
    <!-- Logo -->
    <div
      class="flex items-center h-12 flex-shrink-0 cursor-pointer select-none border-b border-[var(--color-border-subtle)]"
      :class="isCollapse ? 'justify-center' : 'px-4 gap-3'"
      @click="$emit('toggle-collapse')"
    >
      <div
        class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-sm"
      >
        <span class="text-white text-xs font-bold">M</span>
      </div>
      <transition name="logo-text">
        <span
          v-if="!isCollapse"
          class="text-[var(--color-text-primary)] font-semibold text-[15px] tracking-wide whitespace-nowrap"
          >MRP II</span
        >
      </transition>
    </div>

    <!-- 导航菜单 -->
    <nav
      class="flex-1 overflow-y-auto overflow-x-hidden py-2"
      :class="isCollapse ? 'px-1' : 'px-2'"
      aria-label="主导航菜单"
    >
      <div :class="isCollapse ? 'flex justify-center' : 'px-1 mb-1'">
        <router-link to="/dashboard" :class="navLinkClass('/dashboard')">
          <el-icon :size="16"><DataBoard /></el-icon>
          <span v-if="!isCollapse" class="truncate">仪表板</span>
        </router-link>
      </div>

      <div v-if="!isCollapse" class="my-2 mx-3 border-t border-[var(--color-border-subtle)]" />

      <NavGroup label="基础数据" :collapse="isCollapse">
        <NavItem v-if="auth.hasModule('materials')"
          to="/materials"
          icon="Box"
          label="物料管理"
          :collapse="isCollapse"
          :active="activeMenu === '/materials'"
        />
        <NavItem v-if="auth.hasModule('bom')"
          to="/bom"
          icon="Connection"
          label="BOM 管理"
          :collapse="isCollapse"
          :active="activeMenu === '/bom'"
        />
        <NavItem v-if="auth.hasModule('inventory')"
          to="/inventory"
          icon="List"
          label="库存管理"
          :collapse="isCollapse"
          :active="activeMenu === '/inventory'"
        />
        <NavItem v-if="auth.hasModule('routings')"
          to="/routings"
          icon="Operation"
          label="工艺路线"
          :collapse="isCollapse"
          :active="activeMenu === '/routings'"
        />
      </NavGroup>

      <NavGroup label="计划与执行" :collapse="isCollapse">
        <NavItem v-if="auth.hasModule('mps')"
          to="/mps"
          icon="Calendar"
          label="MPS 主计划"
          :collapse="isCollapse"
          :active="activeMenu === '/mps'"
        />
        <NavItem v-if="auth.hasModule('mrp')"
          to="/mrp"
          icon="Cpu"
          label="MRP 运算"
          :collapse="isCollapse"
          :active="activeMenu === '/mrp'"
        />
        <NavItem v-if="auth.hasModule('crp')"
          to="/crp"
          icon="TrendCharts"
          label="CRP 计划"
          :collapse="isCollapse"
          :active="activeMenu === '/crp'"
        />
        <NavItem v-if="auth.hasModule('sales')"
          to="/sales"
          icon="Sell"
          label="销售管理"
          :collapse="isCollapse"
          :active="activeMenu === '/sales'"
        />
        <NavItem v-if="auth.hasModule('purchase')"
          to="/purchase"
          icon="ShoppingCart"
          label="采购管理"
          :collapse="isCollapse"
          :active="activeMenu === '/purchase'"
        />
        <NavItem v-if="auth.hasModule('production')"
          to="/production"
          icon="SetUp"
          label="生产管理"
          :collapse="isCollapse"
          :active="activeMenu === '/production'"
        />
      </NavGroup>

      <NavGroup label="分析与监控" :collapse="isCollapse">
        <NavItem
          to="/reports"
          icon="DataAnalysis"
          label="报表中心"
          :collapse="isCollapse"
          :active="activeMenu === '/reports'"
        />
        <NavItem v-if="auth.hasModule('exceptions')"
          to="/exceptions"
          icon="WarningFilled"
          label="例外看板"
          :collapse="isCollapse"
          :active="activeMenu === '/exceptions'"
        />
        <NavItem v-if="auth.hasModule('inspection')"
          to="/inspection"
          icon="Stamp"
          label="检验盘点"
          :collapse="isCollapse"
          :active="activeMenu === '/inspection'"
        />
      </NavGroup>

      <NavGroup label="财务" :collapse="isCollapse">
        <NavItem v-if="auth.hasModule('finance')"
          to="/finance"
          icon="CreditCard"
          label="财务管理"
          :collapse="isCollapse"
          :active="activeMenu === '/finance'"
        />
        <NavItem v-if="auth.hasModule('cost')"
          to="/cost"
          icon="Money"
          label="费用合计"
          :collapse="isCollapse"
          :active="activeMenu === '/cost'"
        />
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
          <button :class="toolBtnClass">
            <el-icon :size="16"><Setting /></el-icon>
            <span v-if="!isCollapse" class="text-[13px] truncate">系统工具</span>
          </button>
        </template>

        <div class="p-3 space-y-3">
          <!-- MRP 定时器 -->
          <div>
            <div
              class="text-2xs text-[var(--color-text-tertiary)] uppercase tracking-wider font-semibold mb-2"
            >
              MRP 定时器
            </div>
            <div
              class="flex items-center justify-between mb-2 text-xs text-[var(--color-text-secondary)]"
            >
              <span>启用</span>
              <el-switch
                :model-value="timerEnabled"
                size="small"
                @update:model-value="$emit('toggle-timer', $event)"
              />
            </div>
            <div
              v-if="timerEnabled"
              class="flex items-center justify-between text-xs text-[var(--color-text-secondary)]"
            >
              <span>执行时间</span>
              <div class="flex items-center gap-1">
                <input
                  :value="timerHour"
                  type="number"
                  min="0"
                  max="23"
                  class="timer-num-input"
                  @input="$emit('update:timer-hour', Number($event.target.value))"
                  @change="$emit('save-schedule')"
                />
                <span class="text-[var(--color-text-tertiary)] font-bold">:</span>
                <input
                  :value="timerMinute"
                  type="number"
                  min="0"
                  max="59"
                  class="timer-num-input"
                  @input="$emit('update:timer-minute', Number($event.target.value))"
                  @change="$emit('save-schedule')"
                />
              </div>
            </div>
            <el-button size="small" class="w-full mt-2" @click="$emit('run-mrp')"
              >立即执行 MRP</el-button
            >
          </div>

          <div class="border-t border-[var(--color-border-subtle)]" />

          <!-- 邮件通知 -->
          <div>
            <div
              class="text-2xs text-[var(--color-text-tertiary)] uppercase tracking-wider font-semibold mb-2"
            >
              邮件通知
            </div>
            <div class="space-y-2">
              <div class="flex items-center gap-2">
                <span class="text-2xs text-[var(--color-text-tertiary)] w-10 flex-shrink-0"
                  >收件</span
                >
                <input
                  :value="emailTo"
                  placeholder="your@email.com"
                  class="tool-text-input flex-1"
                  @input="$emit('update:email-to', $event.target.value)"
                />
              </div>
              <div class="flex items-center gap-2">
                <span class="text-2xs text-[var(--color-text-tertiary)] w-10 flex-shrink-0"
                  >服务器</span
                >
                <input
                  :value="emailHost"
                  placeholder="smtp.qq.com"
                  class="tool-text-input flex-1"
                  @input="$emit('update:email-host', $event.target.value)"
                />
              </div>
              <div class="flex items-center gap-2">
                <span class="text-2xs text-[var(--color-text-tertiary)] w-10 flex-shrink-0"
                  >端口</span
                >
                <input
                  :value="emailPort"
                  type="number"
                  placeholder="587"
                  class="tool-text-input"
                  style="width:72px"
                  @input="$emit('update:email-port', Number($event.target.value))"
                />
              </div>
              <div class="flex items-center gap-2">
                <span class="text-2xs text-[var(--color-text-tertiary)] w-10 flex-shrink-0"
                  >用户名</span
                >
                <input
                  :value="emailUser"
                  placeholder="请输入邮箱地址"
                  class="tool-text-input flex-1"
                  @input="$emit('update:email-user', $event.target.value)"
                />
              </div>
              <div class="flex items-center gap-2">
                <span class="text-2xs text-[var(--color-text-tertiary)] w-10 flex-shrink-0"
                  >密码</span
                >
                <input
                  :value="emailPass"
                  type="password"
                  placeholder="QQ邮箱授权码"
                  class="tool-text-input flex-1"
                  @input="$emit('update:email-pass', $event.target.value)"
                />
              </div>
            </div>
            <div class="flex gap-2 mt-2">
              <el-button size="small" class="flex-1 text-xs" @click="saveEmailConfig"
                >保存配置</el-button
              >
              <el-button size="small" class="flex-1 text-xs" @click="sendTestEmail"
                >测试邮件</el-button
              >
            </div>
          </div>

          <div class="border-t border-[var(--color-border-subtle)]" />

          <!-- 数据管理 -->
          <div>
            <div
              class="text-2xs text-[var(--color-text-tertiary)] uppercase tracking-wider font-semibold mb-2"
            >
              数据管理
            </div>
            <div class="flex gap-2">
              <el-button size="small" class="flex-1 text-xs" @click="$emit('export-data')"
                >导出</el-button
              >
              <el-button size="small" class="flex-1 text-xs" @click="$emit('import-data')"
                >导入</el-button
              >
            </div>
          </div>
        </div>
      </el-popover>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import NavGroup from '@/components/navigation/NavGroup.vue'
import NavItem from '@/components/navigation/NavItem.vue'

const auth = useAuthStore()

const props = defineProps({
  isCollapse: { type: Boolean, default: false },
  timerEnabled: { type: Boolean, default: false },
  timerHour: { type: Number, default: 6 },
  timerMinute: { type: Number, default: 0 },
  emailTo: { type: String, default: '' },
  emailHost: { type: String, default: '' },
  emailPort: { type: Number, default: 587 },
  emailUser: { type: String, default: '' },
  emailPass: { type: String, default: '' },
})

const emit = defineEmits([
  'toggle-collapse', 'save-schedule', 'run-mrp',
  'save-email', 'test-email', 'export-data', 'import-data',
  'toggle-timer', 'update:timer-hour', 'update:timer-minute',
  'update:email-to', 'update:email-host', 'update:email-port',
  'update:email-user', 'update:email-pass',
])

function saveSchedule() { emit('save-schedule') }
function saveEmailConfig() { emit('save-email') }
function sendTestEmail() { emit('test-email') }

const route = useRoute()
const activeMenu = computed(() => route.path)

function navLinkClass(path) {
  return [
    'flex items-center gap-3 h-9 rounded-md transition-all duration-150 text-[13px]',
    'hover:bg-[var(--color-bg-hover)]',
    props.isCollapse ? 'w-10 justify-center' : 'px-3 w-full',
    activeMenu.value === path
      ? 'bg-[var(--color-accent-muted)] text-[var(--color-accent)] font-medium'
      : 'text-[var(--color-text-secondary)]',
  ]
}

function toolBtnClass() {
  return [
    'flex items-center gap-3 w-full h-9 rounded-md transition-all duration-150',
    'text-[var(--color-text-tertiary)] hover:bg-[var(--color-bg-hover)] hover:text-[var(--color-text-secondary)]',
    props.isCollapse ? 'justify-center' : 'px-3',
  ]
}
</script>
