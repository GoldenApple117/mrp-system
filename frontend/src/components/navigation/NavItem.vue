<template>
  <router-link
    :to="to"
    :class="[
      'flex items-center gap-3 h-9 rounded-md transition-all duration-150 text-[13px] no-underline',
      'hover:bg-[var(--color-bg-hover)]',
      collapse ? 'w-10 justify-center mx-auto' : 'px-3 w-full',
      active
        ? 'bg-[var(--color-accent-muted)] text-[var(--color-accent)] font-medium'
        : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
    ]"
    :title="collapse ? label : ''"
  >
    <el-icon :size="16">
      <component :is="iconComponent" />
    </el-icon>
    <span v-if="!collapse" class="truncate">{{ label }}</span>
    <!-- 活跃指示器 -->
    <span
      v-if="active && !collapse"
      class="ml-auto w-1.5 h-1.5 rounded-full bg-[var(--color-accent)]"
    ></span>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'
import {
  Box, Connection, List, Calendar, Cpu, ShoppingCart, SetUp,
  TrendCharts, Sell, DataAnalysis, WarningFilled, Stamp,
  CreditCard, Money, Operation, DataBoard, HomeFilled
} from '@element-plus/icons-vue'

const iconMap = {
  Box, Connection, List, Calendar, Cpu, ShoppingCart, SetUp,
  TrendCharts, Sell, DataAnalysis, WarningFilled, Stamp,
  CreditCard, Money, Operation, DataBoard, HomeFilled
}

const props = defineProps({
  to: { type: String, required: true },
  icon: { type: String, required: true },
  label: { type: String, required: true },
  collapse: { type: Boolean, default: false },
  active: { type: Boolean, default: false },
})

const iconComponent = computed(() => iconMap[props.icon])
</script>
