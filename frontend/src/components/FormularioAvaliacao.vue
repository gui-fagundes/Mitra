<script setup lang="ts">
// Avaliação do cliente (nota + comentário opcional). Publicada, não pode ser editada.
import { ref } from 'vue'
import { avaliacaoApi, TAMANHO_MAXIMO_TEXTO_AVALIACAO } from '../api/avaliacao'
import { ErroApi } from '../api/client'

const props = defineProps<{ idcontratacao: number; nomePrestador: string; prazo: string | null }>()
const emit = defineEmits<{ avaliado: [] }>()

const nota = ref(0)
const destaque = ref(0)
const comentario = ref('')
const enviando = ref(false)
const erro = ref<string | null>(null)

const ROTULOS = ['', 'Ruim', 'Fraco', 'Ok', 'Bom', 'Excelente']

async function enviar() {
  if (!nota.value) {
    erro.value = 'Escolha uma nota de 1 a 5.'
    return
  }
  if (!confirm('Publicar a avaliação? Depois de publicada, ela não pode ser editada.')) return
  enviando.value = true
  erro.value = null
  try {
    await avaliacaoApi.avaliar(props.idcontratacao, nota.value, comentario.value)
    emit('avaliado')
  } catch (e) {
    erro.value = e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <form class="space-y-4 rounded-2xl border border-gold bg-surface p-5 md:p-6" @submit.prevent="enviar">
    <div>
      <div class="text-[15px] font-semibold">Como foi o serviço com {{ nomePrestador }}?</div>
      <div class="mt-0.5 text-[12px] text-muted">
        A avaliação é pública e não pode ser editada depois.
        <template v-if="prazo">Disponível até {{ new Date(prazo).toLocaleDateString('pt-BR') }}.</template>
      </div>
    </div>

    <div role="radiogroup" aria-label="Nota" class="flex items-center gap-1" @mouseleave="destaque = 0">
      <button
        v-for="n in 5"
        :key="n"
        type="button"
        role="radio"
        :aria-checked="nota === n"
        :aria-label="`${n} de 5: ${ROTULOS[n]}`"
        :class="['text-3xl leading-none transition-colors',
          n <= (destaque || nota) ? 'text-gold' : 'text-rule']"
        @mouseenter="destaque = n"
        @click="nota = n">
        ★
      </button>
      <span class="ml-2 text-[13px] text-ink-soft">{{ ROTULOS[destaque || nota] }}</span>
    </div>

    <label class="flex flex-col gap-1.5">
      <span class="mono-sm">Comentário (opcional)</span>
      <textarea
        v-model="comentario"
        rows="3"
        :maxlength="TAMANHO_MAXIMO_TEXTO_AVALIACAO"
        placeholder="O que foi bem? O que poderia melhorar?"
        class="resize-y rounded-lg border borda-campo bg-bg px-3 py-2 font-sans text-sm outline-none"></textarea>
    </label>

    <div class="flex items-center justify-between gap-3">
      <p v-if="erro" class="text-sm text-red-700">{{ erro }}</p>
      <span v-else></span>
      <button
        type="submit"
        :disabled="enviando"
        class="h-11 rounded-xl bg-gold px-6 text-sm font-semibold text-ink hover:opacity-90 disabled:opacity-60">
        {{ enviando ? 'Publicando…' : 'Publicar avaliação' }}
      </button>
    </div>
  </form>
</template>
