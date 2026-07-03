<template>
  <div class="mb-1">
    <!-- 分组标题 (折叠时隐藏) -->
    <div
      v-if="!collapse"
      class="px-3 pt-3 pb-1 text-2xs text-[var(--color-text-tertiary)] uppercase tracking-widest font-semibold select-none"
    >
      {{ label }}
    </div>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  collapse: { type: Boolean, default: false },
})
</script>
