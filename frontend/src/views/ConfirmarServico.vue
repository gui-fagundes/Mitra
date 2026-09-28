<script setup lang="ts">
// Detalhe de uma contratação: resumo do que foi combinado, confirmação bilateral da
// fase atual (aceite da proposta ou conclusão) e o ciclo completo.
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { avaliacaoApi, TAMANHO_MAXIMO_TEXTO_AVALIACAO } from '../api/avaliacao'
import { ErroApi } from '../api/client'
import {
  contratacaoApi,
  estaAberta,
  marcasDaFase,
  ROTULO_ESTADO,
  type Contratacao,
} from '../api/contratacao'
import { useSessaoStore } from '../stores/sessao'
import { formatarData, formatarFaixaPreco, formatarHora } from '../utils/formatacao'
import CartaoAvaliacao from '../components/CartaoAvaliacao.vue'
import FormularioAvaliacao from '../components/FormularioAvaliacao.vue'
import PublicNav from '../components/PublicNav.vue'

const route = useRoute()
const router = useRouter()
const sessao = useSessaoStore()

const contratacao = ref<Contratacao | null>(null)
const carregando = ref(true)
const trabalhando = ref(false)
const erro = ref<string | null>(null)
const valorFinal = ref<number | ''>('')

function textoDoErro(e: unknown): string {
  return e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
}

function preencher(c: Contratacao) {
  contratacao.value = c
  valorFinal.value = c.valor_final ?? c.valor_estimado ?? ''
}

async function carregar(id: number) {
  carregando.value = true
  erro.value = null
  try {
    preencher(await contratacaoApi.obter(id))
  } catch (e) {
    contratacao.value = null
    erro.value = textoDoErro(e)
  } finally {
    carregando.value = false
  }
}

watch(() => Number(route.params.id), carregar, { immediate: true })

async function executar(acao: () => Promise<Contratacao>) {
  trabalhando.value = true
  erro.value = null
  try {
    preencher(await acao())
  } catch (e) {
    erro.value = textoDoErro(e)
  } finally {
    trabalhando.value = false
  }
}

const c = computed(() => contratacao.value)
const id = computed(() => contratacao.value?.idcontratacao ?? 0)

function aceitar() {
  executar(() => contratacaoApi.aceitar(id.value))
}

function confirmarConclusao() {
  if (valorFinal.value === '') {
    erro.value = 'Informe o preço cobrado.'
    return
  }
  const valor = Number(valorFinal.value)
  // Só manda o valor se mudou: reenviar o mesmo não derruba a confirmação do outro.
  executar(() =>
    contratacaoApi.confirmarConclusao(id.value, valor === c.value?.valor_final ? undefined : valor),
  )
}

const resposta = ref('')

function responder() {
  const avaliacao = c.value?.avaliacao
  if (!avaliacao || !resposta.value.trim()) return
  if (!confirm('Publicar a resposta? Ela fica visível no seu perfil e não pode ser editada.')) return
  executar(async () => {
    await avaliacaoApi.responder(avaliacao.idavaliacao, resposta.value.trim())
    resposta.value = ''
    return contratacaoApi.obter(id.value)
  })
}

function aposAvaliar() {
  carregar(id.value)
}

function cancelar() {
  const motivo = prompt('Cancelar esta contratação? Se quiser, diga o motivo:')
  if (motivo === null) return
  executar(() => contratacaoApi.cancelar(id.value, motivo.trim()))
}

function dataHora(iso: string | null): string {
  return iso ? `${formatarData(iso)} · ${formatarHora(iso)}` : ''
}

function reais(valor: number | null): string {
  return valor == null ? '—' : formatarFaixaPreco(valor, valor)
}

const titulo = computed(() => {
  switch (c.value?.estado) {
    case 'proposta':
      return 'Proposta de serviço'
    case 'combinado':
      return 'Confirmar que o serviço foi realizado'
    case 'concluido':
      return 'Serviço concluído'
    default:
      return 'Contratação cancelada'
  }
})

const marcas = computed(() => (c.value ? marcasDaFase(c.value) : { minha: null, dela: null }))

const ciclo = computed(() => {
  const x = c.value
  if (!x) return []
  const passos = [
    { label: `Proposta enviada · ${formatarData(x.criado_em)}`, feito: true },
    {
      label: x.combinado_em ? `Plano combinado · ${formatarData(x.combinado_em)}` : 'Plano combinado pelos dois',
      feito: !!x.combinado_em,
    },
    {
      label: x.concluido_em ? `Conclusão confirmada · ${formatarData(x.concluido_em)}` : 'Conclusão confirmada pelos dois',
      feito: !!x.concluido_em,
    },
    {
      label: x.avaliacao ? `Avaliado com ${x.avaliacao.nota}★ · ${formatarData(x.avaliacao.criado_em)}` : 'Avaliação do cliente',
      feito: !!x.avaliacao,
    },
  ]
  const atual = x.estado === 'cancelado' ? -1 : passos.findIndex((p) => !p.feito)
  return passos.map((p, i) => ({ ...p, agora: i === atual }))
})

const nomeCancelou = computed(() => {
  const x = c.value
  if (!x?.idcancelado_por) return ''
  return x.idcancelado_por === sessao.usuario?.idusuario ? 'Você' : x.outra_parte.nome
})
</script>

<template>
  <div class="min-h-screen bg-bg">
    <div class="hidden md:block"><PublicNav /></div>

    <div class="flex items-center justify-between border-b border-rule-soft bg-surface px-5 py-3.5 md:hidden">
      <button
        aria-label="Voltar"
        class="flex h-9 w-9 items-center justify-center rounded-lg border border-rule bg-surface"
        @click="router.back()">
        <i class="fa fa-arrow-left"></i>
      </button>
      <div class="text-sm font-semibold">Serviço</div>
      <div class="w-9"></div>
    </div>

    <div v-if="carregando" class="px-5 py-16 text-center text-sm text-muted">Carregando…</div>

    <div v-else-if="!c" class="px-5 py-16 text-center">
      <div class="text-lg font-semibold">Não foi possível abrir esta contratação</div>
      <p class="mt-1 text-sm text-muted">{{ erro }}</p>
    </div>

    <template v-else>
      <div class="hidden px-16 py-4 text-[13px] text-muted md:block">
        <router-link
          :to="{ name: c.papel === 'cliente' ? 'conta-cliente' : 'conta-prestador' }"
          class="text-ink-soft">
          Suas contratações
        </router-link>
        <span class="mx-2">›</span>
        <span>Serviço #{{ c.idcontratacao }}</span>
      </div>

      <div class="grid gap-6 px-5 py-5 pb-32 md:grid-cols-[1fr_380px] md:gap-10 md:px-16 md:py-0 md:pb-10">
        <div class="space-y-6">
          <div>
            <div class="mono-sm mb-2">Serviço #{{ c.idcontratacao }} · {{ ROTULO_ESTADO[c.estado] }}</div>
            <h1 class="mb-2 text-[22px] font-semibold tracking-[-0.01em] md:text-[30px] md:tracking-[-0.02em]">
              {{ titulo }}
            </h1>
            <p v-if="c.estado === 'proposta'" class="max-w-[60ch] text-[13px] leading-[1.5] text-ink-soft md:text-[15px]">
              Quando os dois aceitarem esta versão, o plano fica combinado. Qualquer
              alteração volta para o outro lado aceitar de novo.
            </p>
            <p v-else-if="c.estado === 'combinado'" class="max-w-[60ch] text-[13px] leading-[1.5] text-ink-soft md:text-[15px]">
              Cliente e prestador confirmam, cada um, que o serviço foi feito e o preço cobrado.
              Com as duas confirmações, a avaliação pública é liberada.
            </p>
            <p v-else-if="c.estado === 'concluido'" class="max-w-[60ch] text-[13px] leading-[1.5] text-ink-soft md:text-[15px]">
              Os dois confirmaram. A avaliação pública está liberada.
            </p>
            <p v-else class="max-w-[60ch] text-[13px] leading-[1.5] text-ink-soft md:text-[15px]">
              {{ nomeCancelou }} cancelou em {{ dataHora(c.cancelado_em) }}.
              <template v-if="c.motivo_cancelamento">Motivo: “{{ c.motivo_cancelamento }}”.</template>
            </p>
          </div>

          <section class="rounded-2xl border border-rule bg-surface p-5 md:p-6">
            <div class="mono mb-3">Resumo</div>
            <div class="grid md:grid-cols-2 md:gap-x-8">
              <div class="flex justify-between gap-3 border-b border-rule-soft py-3 text-sm">
                <span class="text-muted">{{ c.papel === 'cliente' ? 'Prestador' : 'Cliente' }}</span>
                <span class="text-right">{{ c.outra_parte.nome }}</span>
              </div>
              <div class="flex justify-between gap-3 border-b border-rule-soft py-3 text-sm">
                <span class="text-muted">Serviço</span><span class="text-right">{{ c.servico.nome }}</span>
              </div>
              <div class="flex justify-between gap-3 border-b border-rule-soft py-3 text-sm md:col-span-2">
                <span class="shrink-0 text-muted">O que vai ser feito</span>
                <span class="whitespace-pre-line text-right">{{ c.descricao }}</span>
              </div>
              <div class="flex justify-between gap-3 border-b border-rule-soft py-3 text-sm">
                <span class="text-muted">Onde</span><span class="text-right">{{ c.local ?? '—' }}</span>
              </div>
              <div class="flex justify-between gap-3 border-b border-rule-soft py-3 text-sm">
                <span class="text-muted">Quando</span>
                <span>{{ c.data_prevista ? formatarData(`${c.data_prevista}T12:00:00`) : '—' }}</span>
              </div>
              <div class="flex justify-between gap-3 py-3 text-sm">
                <span class="text-muted">Valor estimado</span><span>{{ reais(c.valor_estimado) }}</span>
              </div>
              <div class="flex justify-between gap-3 py-3 text-sm">
                <span class="text-muted">Preço cobrado</span>
                <span><strong>{{ reais(c.valor_final) }}</strong></span>
              </div>
            </div>
          </section>

          <section v-if="estaAberta(c)">
            <div class="mono mb-3">
              {{ c.estado === 'proposta' ? 'Aceite da proposta' : 'Confirmação de conclusão' }}
            </div>
            <div class="grid gap-3.5 md:grid-cols-2">
              <div
                v-for="lado in [
                  { nome: `Você (${c.papel})`, marca: marcas.minha },
                  { nome: c.outra_parte.nome, marca: marcas.dela },
                ]"
                :key="lado.nome"
                :class="['flex items-center gap-3.5 rounded-xl border bg-surface p-4 md:p-5',
                  lado.marca ? 'border-rule' : 'border-dashed border-gold']">
                <div
                  :class="['flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-lg font-semibold',
                    lado.marca ? 'bg-good-soft text-good' : 'bg-gold-soft text-gold-ink']">
                  <i v-if="lado.marca" class="fa fa-check"></i>
                  <template v-else>…</template>
                </div>
                <div class="min-w-0 flex-1">
                  <div class="text-sm font-semibold">{{ lado.nome }}</div>
                  <div :class="['mt-0.5 text-xs', lado.marca ? 'text-good' : 'text-gold-ink']">
                    {{ lado.marca ? `Confirmou · ${dataHora(lado.marca)}` : 'Ainda não confirmou' }}
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section
            v-if="c.estado === 'combinado' && c.aguardando_voce"
            class="flex flex-col gap-4 rounded-2xl border border-rule bg-surface p-5 md:flex-row md:items-end md:justify-between md:p-6">
            <label class="flex flex-col gap-1.5">
              <span class="mono-sm">Preço cobrado (R$)</span>
              <input
                v-model.number="valorFinal"
                type="number"
                min="0"
                step="0.01"
                class="h-11 rounded-lg border borda-campo bg-bg px-3 text-sm outline-none md:w-48" />
              <span class="text-[12px] text-muted">
                Se você mudar o valor informado pelo outro lado, ele precisa confirmar de novo.
              </span>
            </label>
            <button
              :disabled="trabalhando"
              class="h-12 shrink-0 rounded-xl bg-gold px-6 text-[15px] font-semibold text-ink hover:opacity-90 disabled:opacity-60"
              @click="confirmarConclusao">
              Confirmar conclusão
            </button>
          </section>

          <section
            v-if="c.estado === 'proposta' && c.aguardando_voce"
            class="flex flex-col items-start gap-3 rounded-2xl border border-rule bg-surface p-5 md:flex-row md:items-center md:justify-between md:p-6">
            <div class="text-[13px] text-ink-soft">
              Concorda com a proposta como está? Para mudar algo, edite pela conversa.
            </div>
            <button
              :disabled="trabalhando"
              class="h-11 shrink-0 rounded-xl bg-gold px-6 text-sm font-semibold text-ink hover:opacity-90 disabled:opacity-60"
              @click="aceitar">
              Aceitar proposta
            </button>
          </section>

          <template v-if="c.estado === 'concluido'">
            <FormularioAvaliacao
              v-if="c.pode_avaliar"
              :idcontratacao="c.idcontratacao"
              :nome-prestador="c.outra_parte.nome"
              :prazo="c.avaliar_ate"
              @avaliado="aposAvaliar" />

            <section v-else-if="c.avaliacao">
              <div class="mono mb-3">
                {{ c.papel === 'cliente' ? 'Sua avaliação' : `Avaliação de ${c.outra_parte.nome}` }}
              </div>
              <CartaoAvaliacao
                :nota="c.avaliacao.nota"
                :comentario="c.avaliacao.comentario"
                :criado-em="c.avaliacao.criado_em"
                :resposta="c.avaliacao.resposta"
                :resposta-em="c.avaliacao.resposta_em">
                <form v-if="c.pode_responder" class="mt-3 space-y-2 border-t border-dashed border-rule-soft pt-3" @submit.prevent="responder">
                  <label class="flex flex-col gap-1.5">
                    <span class="mono-sm">Responder publicamente (uma vez)</span>
                    <textarea
                      v-model="resposta"
                      rows="2"
                      required
                      :maxlength="TAMANHO_MAXIMO_TEXTO_AVALIACAO"
                      placeholder="Agradeça ou esclareça algum ponto."
                      class="resize-y rounded-lg border borda-campo bg-bg px-3 py-2 font-sans text-sm outline-none"></textarea>
                  </label>
                  <button
                    type="submit"
                    :disabled="trabalhando || !resposta.trim()"
                    class="rounded-lg bg-ink px-4 py-2 text-[13px] font-semibold text-white disabled:opacity-60">
                    Publicar resposta
                  </button>
                </form>
              </CartaoAvaliacao>
            </section>

            <p v-else-if="c.papel === 'cliente'" class="text-[13px] text-muted">
              O prazo de 30 dias para avaliar este serviço terminou.
            </p>
            <p v-else class="text-[13px] text-muted">
              {{ c.outra_parte.nome }} ainda não avaliou este serviço.
            </p>
          </template>

          <p v-if="erro" class="text-sm text-red-700">{{ erro }}</p>

          <div class="flex flex-wrap gap-4 text-[13px]">
            <router-link
              :to="{ name: 'mensagem', params: { id: c.idconversa } }"
              class="text-ink underline underline-offset-[3px]">
              Abrir conversa com {{ c.outra_parte.nome }}
            </router-link>
            <button
              v-if="estaAberta(c)"
              type="button"
              class="text-ink-soft underline underline-offset-[3px]"
              @click="cancelar">
              {{ c.estado === 'proposta' ? 'Recusar proposta' : 'Cancelar serviço' }}
            </button>
          </div>
        </div>

        <aside class="self-start rounded-2xl border border-rule bg-surface p-6">
          <div class="mono mb-4">Ciclo do serviço</div>
          <div class="flex flex-col gap-3.5">
            <div v-for="(passo, i) in ciclo" :key="i" class="flex items-center gap-3">
              <span
                :class="['flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold',
                  passo.feito ? 'bg-good-soft text-good'
                  : passo.agora ? 'bg-gold text-ink'
                  : 'bg-surface-2 text-muted']">
                {{ passo.feito ? '✓' : i + 1 }}
              </span>
              <span
                :class="['text-[13px]',
                  passo.feito ? 'text-good' : passo.agora ? 'font-semibold text-ink' : 'text-muted']">
                {{ passo.label }}
              </span>
            </div>
          </div>
          <div v-if="c.estado === 'cancelado'" class="mt-4 text-[12px] text-muted">
            Ciclo interrompido: a contratação foi cancelada.
          </div>
        </aside>
      </div>
    </template>
  </div>
</template>
