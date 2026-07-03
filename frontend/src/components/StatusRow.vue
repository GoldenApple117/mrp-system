<template>
  <div class="flex items-center justify-between text-xs py-1">
    <span class="text-[var(--color-text-tertiary)]">{{ label }}</span>
    <div class="flex items-center gap-1.5">
      <span
        class="w-1.5 h-1.5 rounded-full"
        :class="dotClass"
      ></span>
      <span :class="textClass">{{ statusLabel }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, required: true },
  status: { type: String, default: 'disconnected' },
})

const statusMap = {
  connected: { dot: 'bg-[var(--color-success)] shadow-[0_0_4px_var(--color-success)]', text: 'text-[var(--color-success-text)]', label: '已连接' },
  active:    { dot: 'bg-[var(--color-success)] shadow-[0_0_4px_var(--color-success)]', text: 'text-[var(--color-success-text)]', label: '运行中' },
  ready:     { dot: 'bg-[var(--color-info)] shadow-[0_0_4px_var(--color-info)]', text: 'text-[var(--color-info-text)]', label: '就绪' },
  paused:    { dot: 'bg-[var(--color-warning)]', text: 'text-[var(--color-warning-text)]', label: '已暂停' },
  disconnected: { dot: 'bg-[var(--color-text-disabled)]', text: 'text-[var(--color-text-tertiary)]', label: '未连接' },
}

const dotClass = computed(() => statusMap[props.status]?.dot || statusMap.disconnected.dot)
const textClass = computed(() => statusMap[props.status]?.text || statusMap.disconnected.text)
const statusLabel = computed(() => statusMap[props.status]?.label || '未知')
</script>
