<template>
  <div class="animate-pulse space-y-3 p-4">
    <div v-for="i in rows" :key="i" class="flex gap-4">
      <div
        v-for="j in cols"
        :key="j"
        class="h-4 rounded bg-[var(--color-bg-hover)]"
        :style="{ width: widths[(i * cols + j) % widths.length] }"
      />
    </div>
  </div>
</template>

<script setup>
defineProps({
  rows: { type: Number, default: 5 },
  cols: { type: Number, default: 4 },
})

const widths = ['60%', '40%', '80%', '50%', '70%', '55%', '45%', '35%']
</script>
