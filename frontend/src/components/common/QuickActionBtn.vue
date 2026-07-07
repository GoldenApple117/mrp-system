<template>
  <router-link
    :to="to"
    :class="[
      'flex items-center gap-2.5 p-2.5 rounded-md transition-all duration-150 no-underline',
      'hover:bg-[var(--color-bg-hover)] group',
      colorClasses.bg
    ]"
  >
    <div
      :class="['w-7 h-7 rounded flex items-center justify-center flex-shrink-0', colorClasses.iconBg]"
    >
      <el-icon :size="13" :color="colorClasses.iconColor">
        <component :is="iconComponent" />
      </el-icon>
    </div>
    <div class="flex-1 min-w-0">
      <div class="text-xs font-medium text-[var(--color-text-primary)]">{{ label }}</div>
      <div class="text-2xs text-[var(--color-text-tertiary)] truncate">{{ desc }}</div>
    </div>
    <el-icon
      :size="12"
      color="var(--color-text-disabled)"
      class="opacity-0 group-hover:opacity-100 transition-opacity"
    >
      <ArrowRight />
    </el-icon>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'
import {
  Cpu, Plus, Connection, ShoppingCart, SetUp, DataAnalysis, ArrowRight
} from '@element-plus/icons-vue'

const iconMap = { Cpu, Plus, Connection, ShoppingCart, SetUp, DataAnalysis, ArrowRight }

const props = defineProps({
  to: { type: String, required: true },
  icon: { type: String, required: true },
  label: { type: String, required: true },
  desc: { type: String, default: '' },
  color: { type: String, default: 'blue' },
})

const iconComponent = computed(() => iconMap[props.icon])

const colorClasses = computed(() => {
  const map = {
    blue:    { bg: '', iconBg: 'bg-blue-500/10', iconColor: '#3b82f6' },
    emerald: { bg: '', iconBg: 'bg-emerald-500/10', iconColor: '#22c55e' },
    amber:   { bg: '', iconBg: 'bg-amber-500/10', iconColor: '#f59e0b' },
    purple:  { bg: '', iconBg: 'bg-purple-500/10', iconColor: '#8b5cf6' },
    cyan:    { bg: '', iconBg: 'bg-cyan-500/10', iconColor: '#06b6d4' },
    rose:    { bg: '', iconBg: 'bg-rose-500/10', iconColor: '#f43f5e' },
  }
  return map[props.color] || map.blue
})
</script>
