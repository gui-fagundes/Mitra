<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter, type LocationQuery } from 'vue-router'
import { cidadeApi, rotuloCidade, type Cidade } from '../api/cidade'
import { ErroApi } from '../api/client'
import {
  prestadorApi,
  TAMANHO_PAGINA,
  type CartaoPrestador,
  type FiltrosBusca,
  type OrdemBusca,
} from '../api/prestador'
import { taxonomiaApi, type Categoria } from '../api/taxonomia'
import { useSessaoStore } from '../stores/sessao'
import { formatarFaixaPreco } from '../utils/formatacao'
import CategoryChip from '../components/CategoryChip.vue'
import FotoUsuario from '../components/FotoUsuario.vue'
import PublicNav from '../components/PublicNav.vue'
import StarRating from '../components/StarRating.vue'

const route = useRoute()
const router = useRouter()
const sessao = useSessaoStore()

const cidades = ref<Cidade[]>([])
const categorias = ref<Categoria[]>([])

const itens = ref<CartaoPrestador[]>([])
const total = ref(0)
const carregando = ref(false)
const carregandoMais = ref(false)
const erro = ref<string | null>(null)
const filtrosAbertos = ref(false)

// Campos de texto só viram filtro ao confirmar (Enter / sair do campo).
const termoDigitado = ref('')
const precoMinDigitado = ref<number | ''>('')
const precoMaxDigitado = ref<number | ''>('')

const OPCOES_NOTA = [
  { v: 0, estrelas: '', label: 'Qualquer nota' },
  { v: 3, estrelas: '★★★', label: '3,0 ou mais' },
  { v: 4, estrelas: '★★★★', label: '4,0 ou mais' },
  { v: 5, estrelas: '★★★★★', label: '5,0' },
]

// --- Filtros ⇄ URL ----------------------------------------------------------
// A URL é a fonte da verdade: dá para recarregar, voltar e compartilhar a busca.

function texto(valor: LocationQuery[string]): string | undefined {
  const v = Array.isArray(valor) ? valor[0] : valor
  return v ? String(v) : undefined
}

function numero(valor: LocationQuery[string]): number | undefined {
  const v = texto(valor)
  return v !== undefined && v !== '' && !Number.isNaN(Number(v)) ? Number(v) : undefined
}

function lerFiltros(query: LocationQuery): FiltrosBusca {
  const servicos = ([] as unknown[])
    .concat(query.servicos ?? [])
    .map(Number)
    .filter((n) => !Number.isNaN(n))
  return {
    termo: texto(query.termo),
    idcidade: numero(query.idcidade),
    categoria: texto(query.categoria),
    servicos: servicos.length ? servicos : undefined,
    somente_cnpj: texto(query.somente_cnpj) === 'true' || undefined,
    preco_min: numero(query.preco_min),
    preco_max: numero(query.preco_max),
    nota_min: numero(query.nota_min) || undefined,
    ordem: (texto(query.ordem) as OrdemBusca | undefined) ?? undefined,
  }
}

const filtros = computed(() => lerFiltros(route.query))

function aplicar(mudancas: Partial<FiltrosBusca>) {
  const novos = { ...filtros.value, ...mudancas }
  const query: Record<string, string | string[]> = {}
  for (const [chave, valor] of Object.entries(novos)) {
    if (valor === undefined || valor === null || valor === '' || valor === false) continue
    if (Array.isArray(valor)) {
      if (valor.length) query[chave] = valor.map(String)
    } else {
      query[chave] = String(valor)
    }
  }
  router.replace({ name: 'buscar', query })
}

function aplicarTermo() {
  aplicar({ termo: termoDigitado.value.trim() || undefined })
}

function aplicarPrecos() {
  aplicar({
    preco_min: precoMinDigitado.value === '' ? undefined : Number(precoMinDigitado.value),
    preco_max: precoMaxDigitado.value === '' ? undefined : Number(precoMaxDigitado.value),
  })
}

function escolherCategoria(slug: string) {
  // Os serviços marcados eram da categoria anterior.
  aplicar({ categoria: slug || undefined, servicos: undefined })
}

function alternarServico(idservico: number) {
  const atuais = new Set(filtros.value.servicos ?? [])
  if (atuais.has(idservico)) atuais.delete(idservico)
  else atuais.add(idservico)
  aplicar({ servicos: [...atuais] })
}

function limpar() {
  router.replace({
    name: 'buscar',
    query: filtros.value.idcidade ? { idcidade: String(filtros.value.idcidade) } : {},
  })
}

// --- Busca ------------------------------------------------------------------

async function buscar(maisResultados = false) {
  erro.value = null
  if (maisResultados) carregandoMais.value = true
  else carregando.value = true
  try {
    const resultado = await prestadorApi.buscar({
      ...filtros.value,
      limite: TAMANHO_PAGINA,
      deslocamento: maisResultados ? itens.value.length : 0,
    })
    itens.value = maisResultados ? [...itens.value, ...resultado.itens] : resultado.itens
    total.value = resultado.total
  } catch (e) {
    erro.value = e instanceof ErroApi ? e.detalhe : 'Não foi possível buscar agora.'
  } finally {
    carregando.value = false
    carregandoMais.value = false
  }
}

watch(
  () => route.query,
  () => {
    termoDigitado.value = filtros.value.termo ?? ''
    precoMinDigitado.value = filtros.value.preco_min ?? ''
    precoMaxDigitado.value = filtros.value.preco_max ?? ''
    buscar()
  },
  { deep: true },
)

onMounted(async () => {
  termoDigitado.value = filtros.value.termo ?? ''
  precoMinDigitado.value = filtros.value.preco_min ?? ''
  precoMaxDigitado.value = filtros.value.preco_max ?? ''

  // Preferências de quem está logado valem só na primeira abertura, sem sobrescrever a URL.
  const padrao: Partial<FiltrosBusca> = {}
  if (route.query.somente_cnpj === undefined && sessao.usuario?.busca_somente_cnpj) {
    padrao.somente_cnpj = true
  }
  if (route.query.idcidade === undefined && sessao.usuario?.cidade) {
    padrao.idcidade = sessao.usuario.cidade.idcidade
  }

  const [listaCidades, listaCategorias] = await Promise.allSettled([
    cidadeApi.listar(),
    taxonomiaApi.listarCategorias(),
  ])
  if (listaCidades.status === 'fulfilled') cidades.value = listaCidades.value
  if (listaCategorias.status === 'fulfilled') categorias.value = listaCategorias.value

  if (Object.keys(padrao).length) aplicar(padrao) // o watch dispara a busca
  else buscar()
})

// --- Apresentação -----------------------------------------------------------

const cidadeAtual = computed(() =>
  cidades.value.find((c) => c.idcidade === filtros.value.idcidade),
)
const categoriaAtual = computed(() =>
  categorias.value.find((c) => c.slug === filtros.value.categoria),
)

const titulo = computed(() => {
  const base = filtros.value.termo
    ? `“${filtros.value.termo}”`
    : (categoriaAtual.value?.nome ?? 'Prestadores')
  return cidadeAtual.value ? `${base} em ${cidadeAtual.value.nome}` : base
})

const chipsAtivos = computed(() => {
  const f = filtros.value
  const chips: Array<{ rotulo: string; remover: Partial<FiltrosBusca> }> = []
  if (f.termo) chips.push({ rotulo: `“${f.termo}”`, remover: { termo: undefined } })
  if (categoriaAtual.value) {
    chips.push({
      rotulo: categoriaAtual.value.nome,
      remover: { categoria: undefined, servicos: undefined },
    })
  }
  for (const id of f.servicos ?? []) {
    const servico = categoriaAtual.value?.servicos.find((s) => s.idservico === id)
    if (servico) {
      chips.push({
        rotulo: servico.nome,
        remover: { servicos: (f.servicos ?? []).filter((s) => s !== id) },
      })
    }
  }
  if (f.nota_min) {
    chips.push({ rotulo: `Nota ≥ ${f.nota_min}`, remover: { nota_min: undefined } })
  }
  if (f.somente_cnpj) chips.push({ rotulo: 'CNPJ validado', remover: { somente_cnpj: undefined } })
  if (f.preco_min !== undefined || f.preco_max !== undefined) {
    chips.push({
      rotulo: formatarFaixaPreco(f.preco_min ?? null, f.preco_max ?? null),
      remover: { preco_min: undefined, preco_max: undefined },
    })
  }
  return chips
})

const temMais = computed(() => itens.value.length < total.value)
</script>

<template>
  <div class="min-h-screen bg-bg">
    <div class="hidden md:block">
      <PublicNav />
      <div class="border-b border-rule-soft bg-surface px-16 py-3">
        <form
          class="mx-auto flex max-w-[640px] gap-2 rounded-xl border border-rule bg-bg p-1.5"
          @submit.prevent="aplicarTermo">
          <input
            v-model="termoDigitado"
            placeholder="Serviço, nome ou palavra-chave"
            class="flex-1 border-0 bg-transparent px-3 py-2 text-sm outline-none" />
          <span class="my-1.5 w-px bg-rule-soft"></span>
          <select
            :value="filtros.idcidade ?? ''"
            class="flex-1 border-0 bg-transparent px-3 py-2 text-sm outline-none"
            @change="aplicar({ idcidade: Number(($event.target as HTMLSelectElement).value) || undefined })">
            <option value="">Todas as cidades</option>
            <option v-for="c in cidades" :key="c.idcidade" :value="c.idcidade">{{ rotuloCidade(c) }}</option>
          </select>
          <button type="submit" class="rounded-md bg-gold px-5 text-sm font-semibold text-ink hover:opacity-90">Buscar</button>
        </form>
      </div>
    </div>

    <div class="border-b border-rule-soft bg-surface px-5 py-3.5 md:hidden">
      <form class="mb-3 flex items-center gap-3" @submit.prevent="aplicarTermo">
        <button type="button" aria-label="Voltar" class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-rule" @click="router.back()">
          <i class="fa fa-arrow-left"></i>
        </button>
        <input
          v-model="termoDigitado"
          placeholder="O que você precisa?"
          class="h-9 min-w-0 flex-1 rounded-lg border border-rule bg-bg px-3 text-sm outline-none" />
        <button type="submit" aria-label="Buscar" class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-rule">
          <i class="fa fa-search"></i>
        </button>
      </form>
      <div v-if="chipsAtivos.length" class="-mx-1 flex gap-2 overflow-x-auto pb-1">
        <button
          v-for="chip in chipsAtivos"
          :key="chip.rotulo"
          class="whitespace-nowrap rounded-full border border-ink bg-ink px-3.5 py-2 text-[13px] text-white"
          @click="aplicar(chip.remover)">
          {{ chip.rotulo }} ×
        </button>
      </div>
    </div>

    <div class="flex items-baseline justify-between gap-4 px-5 py-4 md:px-16 md:py-6">
      <div>
        <h1 class="text-lg font-semibold md:text-2xl md:tracking-[-0.015em]">
          <span class="hidden md:inline">{{ titulo }}</span>
          <span class="text-[13px] font-normal text-ink-soft md:hidden">
            <strong>{{ total }} {{ total === 1 ? 'prestador' : 'prestadores' }}</strong> {{ total === 1 ? 'encontrado' : 'encontrados' }}
          </span>
        </h1>
        <div class="mt-1 hidden text-[13px] text-muted md:block">
          <strong>{{ total }} {{ total === 1 ? 'prestador' : 'prestadores' }}</strong> · resultado orgânico, sem posições pagas
        </div>
      </div>
      <div class="mono md:hidden">Sem posições pagas</div>
      <div class="hidden items-center gap-3 md:flex">
        <span class="mono">Ordenar por</span>
        <select
          :value="filtros.ordem ?? 'reputacao'"
          class="rounded-lg border border-rule bg-surface px-3 py-2 text-sm"
          @change="aplicar({ ordem: ($event.target as HTMLSelectElement).value as OrdemBusca })">
          <option value="reputacao">Reputação + atividade</option>
          <option value="melhor">Melhor avaliados</option>
          <option value="muitas">Mais avaliações</option>
          <option value="recentes">Mais recentes</option>
        </select>
      </div>
    </div>

    <div class="grid gap-8 px-5 pb-24 md:grid-cols-[280px_1fr] md:px-16 md:pb-16">
      <aside
        :class="['self-start rounded-xl border border-rule bg-surface p-5 md:block',
          filtrosAbertos ? 'block' : 'hidden']">
        <div class="mb-4 flex items-baseline justify-between">
          <div class="text-[15px] font-semibold">Filtros</div>
          <button type="button" class="text-xs text-ink-soft underline" @click="limpar">Limpar</button>
        </div>

        <fieldset class="mb-4 border-b border-rule-soft pb-4 md:hidden">
          <legend class="mb-2.5 text-xs font-semibold uppercase tracking-wide text-ink">Ordenar por</legend>
          <select
            :value="filtros.ordem ?? 'reputacao'"
            class="w-full rounded-md border border-rule bg-bg px-2.5 py-2 text-[13px]"
            @change="aplicar({ ordem: ($event.target as HTMLSelectElement).value as OrdemBusca })">
            <option value="reputacao">Reputação + atividade</option>
            <option value="melhor">Melhor avaliados</option>
            <option value="muitas">Mais avaliações</option>
            <option value="recentes">Mais recentes</option>
          </select>
        </fieldset>

        <fieldset class="mb-4 border-b border-rule-soft pb-4">
          <legend class="mb-2.5 text-xs font-semibold uppercase tracking-wide text-ink">Categoria</legend>
          <select
            :value="filtros.categoria ?? ''"
            class="w-full rounded-md border border-rule bg-bg px-2.5 py-2 text-[13px]"
            @change="escolherCategoria(($event.target as HTMLSelectElement).value)">
            <option value="">Todas</option>
            <option v-for="c in categorias" :key="c.slug" :value="c.slug">{{ c.nome }}</option>
          </select>
          <div v-if="categoriaAtual" class="mt-2">
            <label
              v-for="s in categoriaAtual.servicos"
              :key="s.idservico"
              class="flex items-center gap-2.5 py-1.5 text-sm text-ink-soft">
              <input
                type="checkbox"
                :checked="filtros.servicos?.includes(s.idservico) ?? false"
                @change="alternarServico(s.idservico)" />
              {{ s.nome }}
            </label>
          </div>
        </fieldset>

        <fieldset class="mb-4 border-b border-rule-soft pb-4">
          <legend class="mb-2.5 text-xs font-semibold uppercase tracking-wide text-ink">Reputação mínima</legend>
          <label v-for="op in OPCOES_NOTA" :key="op.v" class="flex items-center gap-2.5 py-1.5 text-sm text-ink-soft">
            <input
              type="radio"
              name="nota-minima"
              :checked="(filtros.nota_min ?? 0) === op.v"
              @change="aplicar({ nota_min: op.v || undefined })" />
            <span v-if="op.estrelas" class="text-gold">{{ op.estrelas }}</span>
            {{ op.label }}
          </label>
        </fieldset>

        <fieldset class="mb-4 border-b border-rule-soft pb-4">
          <legend class="mb-2.5 text-xs font-semibold uppercase tracking-wide text-ink">Verificação</legend>
          <label class="flex items-center gap-2.5 py-1.5 text-sm text-ink-soft">
            <input
              type="checkbox"
              :checked="filtros.somente_cnpj ?? false"
              @change="aplicar({ somente_cnpj: ($event.target as HTMLInputElement).checked || undefined })" />
            CNPJ validado
          </label>
          <!-- "Já contratado por outros" volta com a etapa de contratação. -->
        </fieldset>

        <fieldset>
          <legend class="mb-2.5 text-xs font-semibold uppercase tracking-wide text-ink">Faixa de preço</legend>
          <div class="flex items-center gap-2">
            <input
              v-model.number="precoMinDigitado"
              type="number"
              min="0"
              placeholder="R$ mín"
              class="w-full rounded-md border border-rule bg-bg px-2.5 py-2 text-[13px]"
              @change="aplicarPrecos" />
            <span class="text-muted">—</span>
            <input
              v-model.number="precoMaxDigitado"
              type="number"
              min="0"
              placeholder="R$ máx"
              class="w-full rounded-md border border-rule bg-bg px-2.5 py-2 text-[13px]"
              @change="aplicarPrecos" />
          </div>
          <div class="mt-1.5 text-[11px] text-muted">Quem cobra "sob consulta" sempre aparece.</div>
        </fieldset>
      </aside>

      <div>
        <div v-if="erro" class="rounded-xl border border-rule bg-surface p-6 text-center text-sm text-red-700">
          {{ erro }}
        </div>

        <div v-else-if="carregando" class="py-10 text-center text-sm text-muted">Buscando…</div>

        <div v-else-if="!itens.length" class="rounded-xl border border-dashed border-rule bg-surface p-8 text-center">
          <div class="text-[15px] font-semibold">Nenhum prestador encontrado</div>
          <p class="mt-1 text-[13px] text-muted">Tente outro termo ou tire algum filtro.</p>
          <button
            v-if="chipsAtivos.length"
            type="button"
            class="mt-3 text-[13px] text-ink underline underline-offset-[3px]"
            @click="limpar">
            Limpar filtros
          </button>
        </div>

        <template v-else>
          <div class="grid gap-3 md:grid-cols-2 md:gap-4">
            <router-link
              v-for="p in itens"
              :key="p.idusuario"
              :to="{ name: 'prestador', params: { id: p.idusuario } }"
              class="flex gap-3.5 rounded-xl border border-rule bg-surface p-3.5 transition-shadow hover:shadow-sm md:gap-4 md:p-5">
              <FotoUsuario
                :url="p.foto_url"
                :nome="p.nome"
                tamanho="h-16 w-16 text-2xl md:h-20 md:w-20" />
              <div class="min-w-0 flex-1">
                <div class="line-clamp-2 break-words text-[15px] font-semibold md:text-base">{{ p.nome }}</div>
                <div class="mt-0.5 text-xs text-ink-soft">
                  {{ formatarFaixaPreco(p.preco_min, p.preco_max) }}
                </div>
                <div class="mt-1 flex items-center gap-1.5">
                  <template v-if="p.qtd_avaliacoes && p.nota_media != null">
                    <StarRating :value="p.nota_media" />
                    <span class="text-xs text-ink-soft">
                      {{ p.nota_media.toFixed(1).replace('.', ',') }} · {{ p.qtd_avaliacoes }} avaliações
                    </span>
                  </template>
                  <span v-else class="text-xs text-muted">
                    Novo no Mitra{{ p.cidade ? ` · ${rotuloCidade(p.cidade)}` : '' }}
                  </span>
                </div>
                <div v-if="p.bio" class="mt-1.5 line-clamp-2 hidden text-xs text-muted md:block">{{ p.bio }}</div>
                <div class="mt-2 flex flex-wrap gap-1.5">
                  <CategoryChip v-for="s in p.servicos" :key="s.idservico">{{ s.nome }}</CategoryChip>
                  <CategoryChip v-if="p.cnpj_validado" tone="gold">CNPJ ✓</CategoryChip>
                </div>
              </div>
            </router-link>
          </div>

          <div class="mt-6 flex flex-col items-center gap-2">
            <button
              v-if="temMais"
              type="button"
              :disabled="carregandoMais"
              class="h-11 rounded-lg border border-ink bg-surface px-6 text-sm font-semibold disabled:opacity-60"
              @click="buscar(true)">
              {{ carregandoMais ? 'Carregando…' : 'Carregar mais' }}
            </button>
            <div class="text-[12px] text-muted">
              Mostrando {{ itens.length }} de {{ total }}
            </div>
          </div>
        </template>
      </div>
    </div>

    <div class="fixed inset-x-0 bottom-0 flex gap-2.5 border-t border-rule-soft bg-bg p-3.5 md:hidden">
      <button
        type="button"
        class="flex h-12 flex-1 items-center justify-center rounded-lg border border-ink bg-surface text-sm font-semibold"
        @click="filtrosAbertos = !filtrosAbertos">
        <i class="fa fa-sliders mr-2"></i>
        {{ filtrosAbertos ? 'Ver resultados' : `Filtros${chipsAtivos.length ? ` (${chipsAtivos.length})` : ''}` }}
      </button>
    </div>
  </div>
</template>
