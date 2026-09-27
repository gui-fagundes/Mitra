<script setup lang="ts" generic="T extends string">
/**
 * Faixa de abas em formato folder-tab:
 *   - Cantos superiores arredondados.
 *   - Aba ativa ganha fundo surface + borda superior + laterais.
 *   - Bottom da ativa se sobrepõe em 1px na borda do container, "encaixando".
 *
 * Uso:
 *   const tab = ref<'sobre' | 'portfolio' | 'avaliacoes'>('sobre')
 *   <Tabs v-model="tab" :items="[
 *     { id: 'sobre', label: 'Sobre' },
 *     { id: 'portfolio', label: 'Portfólio' },
 *     { id: 'avaliacoes', label: 'Avaliações (27)' }
 *   ]" />
 */
defineProps<{
  items: Array<{ id: T; label: string }>
  size?: 'sm' | 'md'
  scrollable?: boolean
}>()

const model = defineModel<T>({ required: true })
</script>

<template>
  <div
    class="flex gap-1 border-b border-rule px-5 pt-3 md:px-0"
    :class="scrollable ? 'overflow-x-auto' : ''"
  >
    <button
      v-for="item in items"
      :key="item.id"
      type="button"
      class="relative -mb-px whitespace-nowrap rounded-t-lg border border-transparent border-b-0 bg-transparent text-muted transition-colors"
      :class="[
        size === 'md'
          ? 'px-4 py-[9px] text-[15px]'
          : 'px-3.5 py-[7px] text-sm',
        model === item.id ? 'border-rule bg-surface font-semibold text-ink' : 'hover:text-ink-soft',
      ]"
      :style="model === item.id ? 'bottom:-1px' : ''"
      @click="model = item.id"
    >
      {{ item.label }}
    </button>
  </div>
</template>
