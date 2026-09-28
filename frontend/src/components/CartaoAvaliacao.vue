<script setup lang="ts">
// Uma avaliação publicada, com a resposta do prestador quando houver.
import { formatarData } from '../utils/formatacao'
import StarRating from './StarRating.vue'

defineProps<{
  nota: number
  comentario: string | null
  criadoEm: string
  autor?: string
  servico?: string
  resposta: string | null
  respostaEm: string | null
}>()
</script>

<template>
  <article class="rounded-xl border border-rule bg-surface p-4 md:p-5">
    <div class="mb-1.5 flex items-baseline justify-between gap-3">
      <div class="text-[13px] font-semibold md:text-sm">{{ autor ?? 'Avaliação' }}</div>
      <StarRating :value="nota" />
    </div>
    <p v-if="comentario" class="whitespace-pre-line text-[13px] leading-[1.55] text-ink-soft md:text-sm">
      “{{ comentario }}”
    </p>
    <p v-else class="text-[13px] text-muted">Sem comentário.</p>
    <div class="mt-2.5 text-[11px] text-muted">
      {{ formatarData(criadoEm) }}<template v-if="servico"> · {{ servico }}</template>
    </div>
    <div v-if="resposta" class="mt-3 border-t border-dashed border-rule-soft pt-3 text-[13px] text-ink-soft">
      <div class="mono-sm mb-1">
        Resposta do prestador<template v-if="respostaEm"> · {{ formatarData(respostaEm) }}</template>
      </div>
      <p class="whitespace-pre-line">{{ resposta }}</p>
    </div>
    <slot />
  </article>
</template>
