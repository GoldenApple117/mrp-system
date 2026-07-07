<template>
  <div class="stat-card group">
    <div class="flex items-start justify-between">
      <div class="flex-1 min-w-0">
        <p class="text-xs text-[var(--color-text-tertiary)] mb-1">{{ label }}</p>
        <div
          v-if="loading"
          class="h-7 w-16 bg-[var(--color-bg-overlay)] rounded animate-pulse mt-0.5"
        ></div>
        <p
          v-else
          class="text-2xl font-semibold text-[var(--color-text-primary)] tracking-tight tabular-nums"
        >
          {{ formattedValue }}
        </p>
        <div v-if="alert && !loading" class="mt-1.5">
          <span
            :class="[
              'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-2xs font-medium',
              alertColorClass
            ]"
          >
            <span class="w-1 h-1 rounded-full bg-current"></span>
            {{ alertLabel }}
          </span>
        </div>
      </div>
      <div
        :class="[
          'w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0',
          'transition-colors duration-200',
          iconBgClass
        ]"
      >
        <el-icon :size="18" :color="iconColor">
          <component :is="iconComponent" />
        </el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  Box, ShoppingCart, SetUp, WarningFilled, CircleCloseFilled
} from '@element-plus/icons-vue'

const iconMap = { Box, ShoppingCart, SetUp, WarningFilled, CircleCloseFilled }

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  icon: { type: String, required: true },
  color: { type: String, default: 'blue' },
  loading: { type: Boolean, default: false },
  alert: { type: Boolean, default: false },
  alertLabel: { type: String, default: '' },
})

const iconComponent = computed(() => iconMap[props.icon])

const formattedValue = computed(() => {
  const v = Number(props.value)
  if (isNaN(v)) return props.value
  if (v >= 10000) return (v / 10000).toFixed(1) + 'w'
  return v.toLocaleString()
})

const colorMap = {
  blue:    { bg: 'bg-blue-500/10 group-hover:bg-blue-500/15', color: '#3b82f6', alertBg: 'bg-blue-500/10 text-blue-300' },
  amber:   { bg: 'bg-amber-500/10 group-hover:bg-amber-500/15', color: '#f59e0b', alertBg: 'bg-amber-500/10 text-amber-300' },
  emerald: { bg: 'bg-emerald-500/10 group-hover:bg-emerald-500/15', color: '#22c55e', alertBg: 'bg-emerald-500/10 text-emerald-300' },
  red:     { bg: 'bg-red-500/10 group-hover:bg-red-500/15', color: '#ef4444', alertBg: 'bg-red-500/10 text-red-300' },
  purple:  { bg: 'bg-purple-500/10 group-hover:bg-purple-500/15', color: '#8b5cf6', alertBg: 'bg-purple-500/10 text-purple-300' },
}

const iconBgClass = computed(() => colorMap[props.color]?.bg || colorMap.blue.bg)
const iconColor = computed(() => colorMap[props.color]?.color || colorMap.blue.color)
const alertColorClass = computed(() => colorMap[props.color]?.alertBg || colorMap.blue.alertBg)
</script>
