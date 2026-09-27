<script setup lang="ts">
/**
 * Pill com borda 1px preta indicando estado de uma contratação/serviço.
 * Cores de fundo carregam o significado; a borda ancora a badge na UI.
 *
 * Variantes:
 *   wait   → dourado (aguardando confirmação bilateral)
 *   done   → verde   (concluído, avaliado)
 *   active → cinza   (em conversa)
 *   info   → dourado forte (CNPJ ✓, selos de destaque)
 */
withDefaults(
  defineProps<{
    variant?: 'wait' | 'done' | 'active' | 'info'
  }>(),
  { variant: 'active' },
)

const styles: Record<string, string> = {
  wait: 'bg-gold-soft text-gold-ink',
  done: 'bg-good-soft text-good',
  active: 'bg-surface-2 text-ink-soft',
  info: 'bg-gold-soft text-gold-ink',
}
</script>

<template>
  <span
    class="inline-block whitespace-nowrap rounded-full border border-ink px-2 py-[3px] text-[10.5px] font-semibold uppercase tracking-[0.08em]"
    :class="styles[variant]"
  >
    <slot />
  </span>
</template>
