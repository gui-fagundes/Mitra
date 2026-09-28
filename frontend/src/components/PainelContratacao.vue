<script setup lang="ts">
// Faixa da contratação dentro da conversa: a proposta/serviço em andamento com as
// ações possíveis, ou o botão para propor um serviço.
import { computed, ref, watch } from 'vue'
import { ErroApi } from '../api/client'
import {
  contratacaoApi,
  estaAberta,
  ROTULO_ESTADO,
  situacao,
  type Contratacao,
  type PropostaEntrada,
} from '../api/contratacao'
import { formatarData, formatarFaixaPreco } from '../utils/formatacao'
import FormularioProposta from './FormularioProposta.vue'

const props = defineProps<{
  idconversa: number
  idprestador: number
  /** Muda quando chega evento novo na conversa: recarrega o painel. */
  versao: number
}>()

const emit = defineEmits<{ mudou: [] }>()

const aberta = ref<Contratacao | null>(null)
const modo = ref<'resumo' | 'propor' | 'editar'>('resumo')
const trabalhando = ref(false)
const erro = ref<string | null>(null)

function textoDoErro(e: unknown): string {
  return e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
}

async function carregar() {
  try {
    const lista = await contratacaoApi.daConversa(props.idconversa)
    aberta.value = lista.find(estaAberta) ?? null
  } catch (e) {
    erro.value = textoDoErro(e)
  }
}

watch(() => [props.idconversa, props.versao], carregar, { immediate: true })
watch(
  () => props.idconversa,
  () => {
    modo.value = 'resumo'
    erro.value = null
  },
)

async function executar(acao: () => Promise<Contratacao>) {
  trabalhando.value = true
  erro.value = null
  try {
    const resultado = await acao()
    aberta.value = estaAberta(resultado) ? resultado : null
    modo.value = 'resumo'
    emit('mudou')
  } catch (e) {
    erro.value = textoDoErro(e)
  } finally {
    trabalhando.value = false
  }
}

function propor(dados: PropostaEntrada) {
  executar(() => contratacaoApi.propor(props.idconversa, dados))
}

function editar(dados: PropostaEntrada) {
  if (aberta.value) executar(() => contratacaoApi.editar(aberta.value!.idcontratacao, dados))
}

function aceitar() {
  if (aberta.value) executar(() => contratacaoApi.aceitar(aberta.value!.idcontratacao))
}

function cancelar() {
  if (!aberta.value) return
  const pergunta =
    aberta.value.estado === 'proposta'
      ? 'Recusar/cancelar esta proposta? Se quiser, diga o motivo:'
      : 'Cancelar o serviço combinado? Se quiser, diga o motivo:'
  const motivo = prompt(pergunta)
  if (motivo === null) return // desistiu
  executar(() => contratacaoApi.cancelar(aberta.value!.idcontratacao, motivo.trim()))
}

const resumoValores = computed(() => {
  const c = aberta.value
  if (!c) return ''
  const partes = [c.servico.nome]
  if (c.valor_final != null) partes.push(`cobrado ${formatarFaixaPreco(c.valor_final, c.valor_final)}`)
  else if (c.valor_estimado != null) partes.push(`estimado ${formatarFaixaPreco(c.valor_estimado, c.valor_estimado)}`)
  if (c.data_prevista) partes.push(formatarData(`${c.data_prevista}T12:00:00`))
  return partes.join(' · ')
})
</script>

<template>
  <div class="border-b border-rule-soft bg-gold-soft/60 px-4 py-2.5 text-[12px] text-gold-ink md:px-5">
    <FormularioProposta
      v-if="modo !== 'resumo'"
      :idprestador="idprestador"
      :atual="modo === 'editar' ? aberta : null"
      :enviando="trabalhando"
      class="py-1 text-ink"
      @salvar="modo === 'editar' ? editar($event) : propor($event)"
      @cancelar="modo = 'resumo'" />

    <div v-else-if="aberta" class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
      <div class="min-w-0">
        <div class="font-semibold">{{ ROTULO_ESTADO[aberta.estado] }} · {{ resumoValores }}</div>
        <div class="truncate text-gold-ink/80">{{ situacao(aberta) }}</div>
      </div>
      <div class="flex shrink-0 flex-wrap items-center gap-2">
        <button
          v-if="aberta.estado === 'proposta' && aberta.aguardando_voce"
          type="button"
          :disabled="trabalhando"
          class="rounded-md bg-ink px-3 py-1.5 font-semibold text-white disabled:opacity-60"
          @click="aceitar">
          Aceitar proposta
        </button>
        <button
          v-if="aberta.estado === 'proposta'"
          type="button"
          class="font-semibold underline"
          @click="modo = 'editar'">
          Editar
        </button>
        <router-link
          :to="{ name: 'confirmar-servico', params: { id: aberta.idcontratacao } }"
          :class="aberta.estado === 'combinado' && aberta.aguardando_voce
            ? 'rounded-md bg-ink px-3 py-1.5 font-semibold text-white'
            : 'font-semibold underline'">
          {{ aberta.estado === 'combinado' ? 'Confirmar conclusão' : 'Detalhes' }}
        </router-link>
        <button type="button" class="underline" @click="cancelar">
          {{ aberta.estado === 'proposta' ? 'Recusar' : 'Cancelar' }}
        </button>
      </div>
    </div>

    <div v-else class="flex items-center justify-between gap-3">
      <span>Combinaram algo? Registre a proposta aqui: valor, data e local ficam no histórico.</span>
      <button
        type="button"
        class="shrink-0 rounded-md bg-ink px-3 py-1.5 font-semibold text-white"
        @click="modo = 'propor'">
        Propor serviço
      </button>
    </div>

    <p v-if="erro" class="mt-1.5 text-red-700">{{ erro }}</p>
  </div>
</template>
