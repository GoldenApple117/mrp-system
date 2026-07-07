<template>
  <div class="animate-pulse grid grid-cols-2 lg:grid-cols-4 gap-3">
    <div v-for="i in count" :key="i" class="h-[80px] rounded-lg bg-[var(--color-bg-overlay)]" />
  </div>
</template>

<script setup>
defineProps({
  count: { type: Number, default: 4 },
})
</script>
