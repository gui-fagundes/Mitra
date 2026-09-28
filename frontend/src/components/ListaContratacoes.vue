<script setup lang="ts">
// Aba "Contratações" das áreas do cliente e do prestador.
import { computed, onMounted, ref } from 'vue'
import { ErroApi } from '../api/client'
import {
  contratacaoApi,
  estaAberta,
  ROTULO_ESTADO,
  situacao,
  type Contratacao,
} from '../api/contratacao'
import { formatarData, formatarFaixaPreco } from '../utils/formatacao'
import FotoUsuario from './FotoUsuario.vue'
import StatusBadge from './StatusBadge.vue'

const props = defineProps<{ papel: 'cliente' | 'prestador' }>()

type Filtro = 'todos' | 'andamento' | 'concluidos' | 'cancelados'
const FILTROS: Array<{ id: Filtro; label: string }> = [
  { id: 'todos', label: 'Todos' },
  { id: 'andamento', label: 'Em andamento' },
  { id: 'concluidos', label: 'Concluídos' },
  { id: 'cancelados', label: 'Cancelados' },
]

const filtro = ref<Filtro>('todos')
const contratacoes = ref<Contratacao[]>([])
const carregando = ref(true)
const erro = ref<string | null>(null)

onMounted(async () => {
  try {
    contratacoes.value = await contratacaoApi.minhas({ papel: props.papel })
  } catch (e) {
    erro.value = e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
  } finally {
    carregando.value = false
  }
})

const visiveis = computed(() =>
  contratacoes.value.filter((c) => {
    if (filtro.value === 'andamento') return estaAberta(c)
    if (filtro.value === 'concluidos') return c.estado === 'concluido'
    if (filtro.value === 'cancelados') return c.estado === 'cancelado'
    return true
  }),
)

const aguardandoVoce = computed(() => contratacoes.value.filter((c) => c.aguardando_voce).length)

function variante(c: Contratacao): 'wait' | 'done' | 'active' {
  if (c.aguardando_voce) return 'wait'
  return c.estado === 'concluido' ? 'done' : 'active'
}

function valor(c: Contratacao): string | null {
  const v = c.valor_final ?? c.valor_estimado
  return v == null ? null : formatarFaixaPreco(v, v)
}
</script>

<template>
  <div>
    <div class="mb-5 flex flex-col gap-3 md:mb-6 md:flex-row md:items-baseline md:justify-between">
      <div>
        <h1 class="text-xl font-semibold tracking-[-0.01em] md:text-2xl md:tracking-[-0.02em]">
          {{ papel === 'cliente' ? 'Suas contratações' : 'Contratações recebidas' }}
        </h1>
        <div class="mt-0.5 text-[13px] text-muted">
          <template v-if="aguardandoVoce">
            <strong class="text-gold-ink">{{ aguardandoVoce }} aguardando você</strong> ·
          </template>
          Propostas e serviços combinados nas conversas do Mitra.
        </div>
      </div>
      <div class="flex gap-2 overflow-x-auto">
        <button
          v-for="f in FILTROS"
          :key="f.id"
          :class="['whitespace-nowrap rounded-lg border px-3.5 py-2 text-[13px]',
            filtro === f.id ? 'border-ink bg-ink text-white' : 'border-rule bg-surface']"
          @click="filtro = f.id">
          {{ f.label }}
        </button>
      </div>
    </div>

    <div v-if="carregando" class="py-8 text-center text-sm text-muted">Carregando…</div>
    <div v-else-if="erro" class="text-sm text-red-700">{{ erro }}</div>
    <div
      v-else-if="!visiveis.length"
      class="rounded-2xl border border-dashed border-rule bg-surface p-8 text-center text-[13px] text-muted">
      <template v-if="contratacoes.length">Nada neste filtro.</template>
      <template v-else-if="papel === 'cliente'">
        Nenhuma contratação ainda. Converse com um prestador e registre a proposta pela conversa.
      </template>
      <template v-else>
        Nenhuma contratação ainda. As propostas combinadas nas suas conversas aparecem aqui.
      </template>
    </div>

    <div v-else class="flex flex-col gap-3">
      <article
        v-for="c in visiveis"
        :key="c.idcontratacao"
        :class="['rounded-xl border bg-surface p-3.5 md:grid md:grid-cols-[56px_1fr_auto] md:items-center md:gap-4 md:p-4',
          c.aguardando_voce ? 'border-gold' : 'border-rule']">
        <FotoUsuario
          :url="c.outra_parte.foto_url"
          :nome="c.outra_parte.nome"
          tamanho="mb-3 h-14 w-14 text-lg md:mb-0" />
        <div class="mb-3 min-w-0 md:mb-0">
          <div class="flex flex-wrap items-baseline gap-2.5">
            <div class="text-[15px] font-semibold">{{ c.outra_parte.nome }}</div>
            <StatusBadge :variant="variante(c)">{{ ROTULO_ESTADO[c.estado] }}</StatusBadge>
          </div>
          <div class="mt-1 text-[13px] text-muted">
            {{ c.servico.nome }}<template v-if="valor(c)"> · {{ valor(c) }}</template>
            · {{ situacao(c) }}
          </div>
          <div class="mt-0.5 text-[11px] text-muted">Atualizado em {{ formatarData(c.atualizado_em) }}</div>
        </div>
        <div class="flex gap-2">
          <router-link
            :to="{ name: 'mensagem', params: { id: c.idconversa } }"
            class="rounded-lg border border-rule px-3.5 py-2 text-[13px]">
            Abrir chat
          </router-link>
          <router-link
            :to="{ name: 'confirmar-servico', params: { id: c.idcontratacao } }"
            :class="c.aguardando_voce
              ? 'rounded-lg bg-ink px-3.5 py-2 text-[13px] font-semibold text-white'
              : 'rounded-lg border border-rule px-3.5 py-2 text-[13px]'">
            {{ c.aguardando_voce ? (c.estado === 'proposta' ? 'Ver proposta' : 'Confirmar') : 'Detalhes' }}
          </router-link>
        </div>
      </article>
    </div>
  </div>
</template>
