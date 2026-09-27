<script setup lang="ts">
/**
 * Tag pill neutra para categorias de serviço nos cards e perfis.
 * Sempre com borda 1px preta.
 */
withDefaults(
  defineProps<{
    tone?: 'neutral' | 'gold'
  }>(),
  { tone: 'neutral' },
)
</script>

<template>
  <span
    class="inline-block whitespace-nowrap rounded-full border border-ink px-2.5 py-0.5 text-[11px]"
    :class="tone === 'gold' ? 'bg-gold-soft text-gold-ink' : 'bg-surface-2 text-ink-soft'"
  >
    <slot />
  </span>
</template>
