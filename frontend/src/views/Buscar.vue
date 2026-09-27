<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PublicNav from '../components/PublicNav.vue'
import StarRating from '../components/StarRating.vue'
import CategoryChip from '../components/CategoryChip.vue'

const router = useRouter()
const route = useRoute()

const query = ref((route.query.q as string) ?? 'Eletricista')
const cidade = ref((route.query.cidade as string) ?? 'Rio Grande, RS')
const ordenacao = ref<'reputacao' | 'melhor' | 'muitas' | 'recentes'>('reputacao')

const notaMin = ref<'5' | '4' | '3' | '0'>('4')
const cnpjOnly = ref(false)
const jaContratado = ref(false)
const precoMin = ref('')
const precoMax = ref('')

const chipsAtivos = computed(() => {
  const list: string[] = ['Ordenar: Reputação', 'Categoria']
  if (notaMin.value !== '0') list.push(`Nota ≥ ${notaMin.value}`)
  if (cnpjOnly.value) list.push('Verificado')
  return list
})

type Prestador = {
  id: number
  nome: string
  categorias: string[]
  cnpj: boolean
  nota: number
  avaliacoes: number
  preco: string
  destaque: string
  tag?: 'Novo'
}
const resultados: Prestador[] = [
  {
    id: 1, nome: '[Nome do prestador]', categorias: ['Eletroeletrônicos'], cnpj: true,
    nota: 4.9, avaliacoes: 27, preco: 'R$ 80–150',
    destaque: '"Rápido e organizado. Deixou tudo em ordem." — cliente há 2 semanas',
  },
  {
    id: 2, nome: '[Nome do prestador]', categorias: ['Construção'], cnpj: false,
    nota: 4.6, avaliacoes: 14, preco: 'R$ 100–200',
    destaque: '"Atendeu no mesmo dia, preço justo." — cliente há 1 mês',
  },
  {
    id: 3, nome: '[Nome do prestador]', categorias: ['Eletroeletrônicos'], cnpj: false,
    nota: 4.4, avaliacoes: 9, preco: 'Sob consulta',
    destaque: '"Trabalho caprichado, comunicação boa." — cliente há 3 semanas',
  },
  {
    id: 4, nome: '[Nome do prestador]', categorias: [], cnpj: false,
    nota: 5, avaliacoes: 3, preco: 'R$ 60–120',
    destaque: 'Ainda com poucos serviços registrados na plataforma.', tag: 'Novo',
  },
  {
    id: 5, nome: '[Nome do prestador]', categorias: ['Eletroeletrônicos'], cnpj: true,
    nota: 4.3, avaliacoes: 18, preco: 'R$ 90–180',
    destaque: '"Cumpriu o prazo combinado." — cliente há 5 dias',
  },
  {
    id: 6, nome: '[Nome do prestador]', categorias: ['Eletroeletrônicos', 'Construção'], cnpj: false,
    nota: 4.8, avaliacoes: 41, preco: 'R$ 120–250',
    destaque: '"Cobrou o combinado, sem surpresa." — cliente há 2 meses',
  },
]

function abrir(p: Prestador) {
  router.push({ name: 'prestador', params: { id: p.id } })
}
</script>

<template>
  <div class="min-h-screen bg-bg">
    <div class="hidden md:block">
      <PublicNav />
      <div class="border-b border-rule-soft bg-surface px-16 py-3">
        <div class="mx-auto flex max-w-[640px] gap-2 rounded-xl border border-rule bg-bg p-1.5">
          <input v-model="query" class="flex-1 border-0 bg-transparent px-3 py-2 text-sm outline-none" />
          <span class="my-1.5 w-px bg-rule-soft"></span>
          <input v-model="cidade" class="flex-1 border-0 bg-transparent px-3 py-2 text-sm outline-none" />
          <button class="rounded-md bg-gold px-5 text-sm font-semibold text-ink hover:opacity-90">Buscar</button>
        </div>
      </div>
    </div>

    <div class="border-b border-rule-soft bg-surface px-5 py-3.5 md:hidden">
      <div class="mb-3 flex items-center gap-3">
        <button aria-label="Voltar" class="flex h-9 w-9 items-center justify-center rounded-lg border border-rule" @click="router.back()">
          <i class="fa fa-arrow-left"></i>
        </button>
        <div class="min-w-0 flex-1">
          <div class="truncate text-[15px] font-semibold">{{ query }}</div>
          <div class="text-xs text-muted">{{ cidade }}</div>
        </div>
        <button aria-label="Editar busca" class="flex h-9 w-9 items-center justify-center rounded-lg border border-rule">
          <i class="fa fa-search"></i>
        </button>
      </div>
      <div class="-mx-1 flex gap-2 overflow-x-auto pb-1">
        <button v-for="(chip, i) in chipsAtivos" :key="chip"
          :class="['whitespace-nowrap rounded-full px-3.5 py-2 text-[13px]',
            i === 0 ? 'border border-ink bg-ink text-white' : 'border border-rule bg-surface']">
          {{ chip }}
        </button>
        <button class="whitespace-nowrap rounded-full border border-rule bg-surface px-3.5 py-2 text-[13px]">Faixa de preço</button>
      </div>
    </div>

    <div class="flex items-baseline justify-between px-5 py-4 md:px-16 md:py-6">
      <div>
        <h1 class="text-lg font-semibold md:text-2xl md:tracking-[-0.015em]">
          <span class="hidden md:inline">{{ query }}s em {{ cidade.split(',')[0] }}</span>
          <span class="text-[13px] font-normal text-ink-soft md:hidden">
            <strong>{{ resultados.length }} prestadores</strong> encontrados
          </span>
        </h1>
        <div class="mt-1 hidden text-[13px] text-muted md:block">
          <strong>{{ resultados.length }} prestadores</strong> · resultado orgânico, sem posições pagas
        </div>
      </div>
      <div class="mono md:hidden">Sem posições pagas</div>
      <div class="hidden items-center gap-3 md:flex">
        <span class="mono">Ordenar por</span>
        <select v-model="ordenacao" class="rounded-lg border border-rule bg-surface px-3 py-2 text-sm">
          <option value="reputacao">Reputação + atividade</option>
          <option value="melhor">Melhor avaliados</option>
          <option value="muitas">Mais avaliações</option>
          <option value="recentes">Mais recentes</option>
        </select>
      </div>
    </div>

    <div class="grid gap-8 px-5 pb-24 md:grid-cols-[280px_1fr] md:px-16 md:pb-16">
      <aside class="hidden self-start rounded-xl border border-rule bg-surface p-5 md:block">
        <div class="mb-4 flex items-baseline justify-between">
          <div class="text-[15px] font-semibold">Filtros</div>
          <a href="#" class="text-xs text-ink-soft underline">Limpar</a>
        </div>

        <fieldset class="mb-4 border-b border-rule-soft pb-4">
          <legend class="mb-2.5 text-xs font-semibold uppercase tracking-wide text-ink">Categoria</legend>
          <label v-for="c in ['Eletroeletrônicos', 'Construção / manutenção', 'Móveis', 'Roupas / vestimenta']" :key="c"
            class="flex items-center gap-2.5 py-1.5 text-sm text-ink-soft">
            <input type="checkbox" :checked="c === 'Eletroeletrônicos'" />
            {{ c }}
          </label>
        </fieldset>

        <fieldset class="mb-4 border-b border-rule-soft pb-4">
          <legend class="mb-2.5 text-xs font-semibold uppercase tracking-wide text-ink">Reputação mínima</legend>
          <label v-for="op in [
            { v: '5', star: '★★★★★', label: '5,0' },
            { v: '4', star: '★★★★', label: '☆ 4,0 ou mais' },
            { v: '3', star: '★★★', label: '☆☆ 3,0 ou mais' },
            { v: '0', star: '', label: 'Qualquer nota' },
          ]" :key="op.v" class="flex items-center gap-2.5 py-1.5 text-sm text-ink-soft">
            <input v-model="notaMin" type="radio" :value="op.v" />
            <span v-if="op.star" class="text-gold">{{ op.star }}</span>
            {{ op.label }}
          </label>
        </fieldset>

        <fieldset class="mb-4 border-b border-rule-soft pb-4">
          <legend class="mb-2.5 text-xs font-semibold uppercase tracking-wide text-ink">Verificação</legend>
          <label class="flex items-center gap-2.5 py-1.5 text-sm text-ink-soft">
            <input v-model="cnpjOnly" type="checkbox" /> CNPJ validado
          </label>
          <label class="flex items-center gap-2.5 py-1.5 text-sm text-ink-soft">
            <input v-model="jaContratado" type="checkbox" /> Já contratado por outros
          </label>
        </fieldset>

        <fieldset>
          <legend class="mb-2.5 text-xs font-semibold uppercase tracking-wide text-ink">Faixa de preço</legend>
          <div class="flex items-center gap-2">
            <input v-model="precoMin" placeholder="R$ mín" class="w-full rounded-md border border-rule bg-bg px-2.5 py-2 text-[13px]" />
            <span class="text-muted">—</span>
            <input v-model="precoMax" placeholder="R$ máx" class="w-full rounded-md border border-rule bg-bg px-2.5 py-2 text-[13px]" />
          </div>
        </fieldset>
      </aside>

      <div class="grid gap-3 md:grid-cols-2 md:gap-4">
        <article v-for="p in resultados" :key="p.id"
          class="flex cursor-pointer gap-3.5 rounded-xl border border-rule bg-surface p-3.5 transition-shadow hover:shadow-sm md:gap-4 md:p-5"
          @click="abrir(p)">
          <div class="ph h-16 w-16 shrink-0 rounded-xl md:h-20 md:w-20"></div>
          <div class="min-w-0 flex-1">
            <div class="flex items-baseline justify-between gap-2">
              <div class="text-[15px] font-semibold md:text-base">{{ p.nome }}</div>
              <div class="whitespace-nowrap text-xs text-muted">{{ p.preco }}</div>
            </div>
            <div class="mt-1 flex items-center gap-1.5">
              <StarRating :value="p.nota" />
              <span class="text-xs text-ink-soft">
                {{ p.nota.toFixed(1).replace('.', ',') }} · {{ p.avaliacoes }} avaliações
              </span>
            </div>
            <div class="mt-1.5 hidden text-xs text-muted md:block">{{ p.destaque }}</div>
            <div class="mt-2 flex flex-wrap gap-1.5">
              <CategoryChip v-for="c in p.categorias" :key="c">{{ c }}</CategoryChip>
              <CategoryChip v-if="p.cnpj" tone="gold">CNPJ ✓</CategoryChip>
              <CategoryChip v-if="p.tag">{{ p.tag }}</CategoryChip>
            </div>
          </div>
        </article>
      </div>
    </div>

    <div class="fixed inset-x-0 bottom-0 flex gap-2.5 border-t border-rule-soft bg-bg p-3.5 md:hidden">
      <button class="flex h-12 flex-1 items-center justify-center rounded-lg border border-ink bg-surface text-sm font-semibold">
        <i class="fa fa-sliders mr-2"></i> Filtros (2)
      </button>
      <button class="flex h-12 w-12 items-center justify-center rounded-lg border border-rule bg-surface" aria-label="Ver no mapa">
        <i class="fa fa-map-o"></i>
      </button>
    </div>
  </div>
</template>
