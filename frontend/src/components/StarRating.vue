<script setup lang="ts">
import { computed } from 'vue'

/**
 * Exibição de nota (não interativa).
 *   value    — número de 0 a 5 (aceita fração; 4,6 vira ★★★★☆)
 *   size     — 'sm' | 'md' — controla o tamanho do glyph
 */
const props = withDefaults(
  defineProps<{
    value: number
    size?: 'sm' | 'md'
  }>(),
  { size: 'sm' },
)

const filled = computed(() => Math.round(props.value))
const stars = computed(() =>
  Array.from({ length: 5 }, (_, i) => (i < filled.value ? '★' : '☆')).join(''),
)
</script>

<template>
  <span
    class="text-gold"
    :class="size === 'md' ? 'text-base' : 'text-[13px]'"
    aria-label="Nota"
  >
    {{ stars }}
  </span>
</template>
