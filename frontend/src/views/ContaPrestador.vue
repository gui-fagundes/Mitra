<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { cidadeApi, rotuloCidade, type Cidade } from '../api/cidade'
import { ErroApi, urlArquivo } from '../api/client'
import { contratacaoApi, estaAberta, type Contratacao } from '../api/contratacao'
import { contaApi } from '../api/conta'
import { LIMITE_SERVICOS, prestadorApi, type Vitrine } from '../api/prestador'
import { taxonomiaApi, type Categoria, type Servico } from '../api/taxonomia'
import { formatarCnpj } from '../utils/formatacao'
import { useSessaoStore } from '../stores/sessao'
import CartaoCnpj from '../components/CartaoCnpj.vue'
import FormularioDadosConta from '../components/FormularioDadosConta.vue'
import ListaContratacoes from '../components/ListaContratacoes.vue'
import FotoUsuario from '../components/FotoUsuario.vue'
import GerenciadorPortfolio from '../components/GerenciadorPortfolio.vue'
import PublicNav from '../components/PublicNav.vue'

const router = useRouter()
const sessao = useSessaoStore()

type Aba = 'contratacoes' | 'vitrine' | 'portfolio' | 'dados'
const aba = ref<Aba>('vitrine')

const abas: Array<{ id: Aba; label: string; curto: string }> = [
  { id: 'contratacoes', label: 'Contratações', curto: 'Contratações' },
  { id: 'vitrine', label: 'Vitrine (perfil público)', curto: 'Vitrine' },
  { id: 'portfolio', label: 'Portfólio', curto: 'Portfólio' },
  { id: 'dados', label: 'Dados da conta', curto: 'Dados' },
]

// Reputação vem da etapa de avaliações.
const contratacoesRecebidas = ref<Contratacao[]>([])
const kpis = computed(() => [
  { label: 'Reputação', valor: '—', detalhe: 'Sem avaliações ainda' },
  {
    label: 'Contratações em andamento',
    valor: String(contratacoesRecebidas.value.filter(estaAberta).length),
  },
  {
    label: 'Serviços concluídos (total)',
    valor: String(contratacoesRecebidas.value.filter((c) => c.estado === 'concluido').length),
  },
])

const SUGESTOES_DISPONIBILIDADE = ['Seg a Sáb · 8h–18h', 'Somente à tarde', 'Sob consulta']

const carregando = ref(true)
const semVitrine = ref(false)
const vitrine = ref<Vitrine | null>(null)
const categorias = ref<Categoria[]>([])
const cidades = ref<Cidade[]>([])

// Formulário da vitrine (nome e cidade são da conta; o resto, da vitrine)
const nome = ref('')
const idcidade = ref<number | null>(null)
const bio = ref('')
const disponibilidade = ref('')
const precoMin = ref<number | ''>('')
const precoMax = ref<number | ''>('')
const servicosSelecionados = ref<Servico[]>([])

const salvando = ref(false)
const mensagem = ref<{ tipo: 'ok' | 'erro'; texto: string } | null>(null)

const portfolio = computed(() => vitrine.value?.portfolio ?? [])
const idsSelecionados = computed(() => new Set(servicosSelecionados.value.map((s) => s.idservico)))
const podeAdicionarServico = computed(() => servicosSelecionados.value.length < LIMITE_SERVICOS)

function preencher() {
  const usuario = sessao.usuario
  nome.value = usuario?.nome ?? ''
  idcidade.value = usuario?.cidade?.idcidade ?? null
  bio.value = vitrine.value?.bio ?? ''
  disponibilidade.value = vitrine.value?.disponibilidade ?? ''
  precoMin.value = vitrine.value?.preco_min ?? ''
  precoMax.value = vitrine.value?.preco_max ?? ''
  servicosSelecionados.value = [...(vitrine.value?.servicos ?? [])]
  mensagem.value = null
}

function adicionarServico(evento: Event) {
  const campo = evento.target as HTMLSelectElement
  const id = Number(campo.value)
  campo.value = ''
  const servico = categorias.value.flatMap((c) => c.servicos).find((s) => s.idservico === id)
  if (servico && podeAdicionarServico.value && !idsSelecionados.value.has(id)) {
    servicosSelecionados.value.push(servico)
  }
}

function removerServico(id: number) {
  servicosSelecionados.value = servicosSelecionados.value.filter((s) => s.idservico !== id)
}

function numeroOuNulo(valor: number | ''): number | null {
  return valor === '' ? null : Number(valor)
}

function textoDoErro(e: unknown): string {
  return e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
}

async function salvar() {
  mensagem.value = null
  const min = numeroOuNulo(precoMin.value)
  const max = numeroOuNulo(precoMax.value)
  if (min != null && max != null && min > max) {
    mensagem.value = { tipo: 'erro', texto: 'O preço mínimo não pode ser maior que o máximo.' }
    return
  }

  salvando.value = true
  try {
    const usuario = await contaApi.atualizar({ nome: nome.value, idcidade: idcidade.value })
    sessao.definirUsuario(usuario)
    vitrine.value = await prestadorApi.atualizarVitrine({
      bio: bio.value || null,
      disponibilidade: disponibilidade.value || null,
      preco_min: min,
      preco_max: max,
      servicos: servicosSelecionados.value.map((s) => s.idservico),
    })
    preencher()
    mensagem.value = { tipo: 'ok', texto: 'Vitrine salva.' }
  } catch (e) {
    mensagem.value = { tipo: 'erro', texto: textoDoErro(e) }
  } finally {
    salvando.value = false
  }
}

const ativando = ref(false)

async function ativarVitrine() {
  ativando.value = true
  try {
    vitrine.value = await prestadorApi.criarVitrine()
    semVitrine.value = false
    sessao.definirUsuario(await contaApi.obter())
    preencher()
  } catch (e) {
    mensagem.value = { tipo: 'erro', texto: textoDoErro(e) }
  } finally {
    ativando.value = false
  }
}

onMounted(async () => {
  try {
    const [usuario, listaCategorias, listaCidades] = await Promise.all([
      contaApi.obter(),
      taxonomiaApi.listarCategorias(),
      cidadeApi.listar(),
    ])
    sessao.definirUsuario(usuario)
    categorias.value = listaCategorias
    cidades.value = listaCidades
    if (usuario.e_prestador) {
      vitrine.value = await prestadorApi.obterVitrine()
      contratacoesRecebidas.value = await contratacaoApi.minhas({ papel: 'prestador' })
    } else {
      semVitrine.value = true
    }
    preencher()
  } catch (e) {
    mensagem.value = { tipo: 'erro', texto: textoDoErro(e) }
  } finally {
    carregando.value = false
  }
})

async function sair() {
  try {
    await contaApi.sair()
  } finally {
    sessao.limparUsuario()
    router.push('/login')
  }
}
</script>

<template>
  <div class="min-h-screen bg-bg">
    <div class="hidden md:block"><PublicNav /></div>

    <div class="flex items-center justify-between border-b border-rule-soft bg-surface px-5 py-3.5 md:hidden">
      <router-link to="/" class="text-[15px] font-semibold">Mitra</router-link>
      <div class="flex items-center gap-3">
        <router-link to="/mensagens" aria-label="Mensagens">
          <i class="fa fa-envelope-o text-lg"></i>
        </router-link>
        <button class="text-[13px] text-ink-soft" @click="sair">Sair</button>
      </div>
    </div>

    <!-- Chip "área do prestador" no desktop -->
    <div class="hidden items-center justify-between gap-3 border-b border-rule-soft bg-surface px-16 py-3 md:flex">
      <span class="mono-sm rounded-full bg-surface-2 px-2.5 py-1 text-ink-soft">
        Área do prestador
      </span>
      <router-link
        v-if="vitrine && sessao.usuario"
        :to="{ name: 'prestador', params: { id: sessao.usuario.idusuario } }"
        class="text-[13px] text-ink-soft underline underline-offset-[3px]">
        Ver meu perfil público
      </router-link>
    </div>

    <!-- Header prestador (mobile) -->
    <div class="flex items-center gap-3.5 border-b border-rule-soft bg-surface px-5 py-4 md:hidden">
      <FotoUsuario
        :url="sessao.usuario?.foto_url"
        :nome="sessao.usuario?.nome"
        tamanho="h-14 w-14 text-lg" />
      <div class="min-w-0 flex-1">
        <div class="text-[15px] font-semibold">{{ sessao.usuario?.nome }}</div>
        <div class="mt-0.5 text-xs text-muted">Sem avaliações ainda</div>
      </div>
    </div>

    <!-- KPIs (desktop) -->
    <div class="hidden grid-cols-3 gap-3.5 px-16 pt-6 md:grid">
      <div v-for="k in kpis" :key="k.label" class="rounded-xl border border-rule bg-surface p-4">
        <div class="num text-[22px] font-semibold">{{ k.valor }}</div>
        <div class="mono-sm mt-0.5">{{ k.label }}</div>
        <div v-if="k.detalhe" class="mt-0.5 text-[11px] text-muted">{{ k.detalhe }}</div>
      </div>
    </div>

    <div class="md:grid md:grid-cols-[240px_1fr] md:gap-8 md:px-16 md:py-6">
      <!-- Sidebar desktop -->
      <aside class="hidden self-start rounded-xl border border-rule bg-surface p-3 md:block">
        <div class="mono-sm mb-2 px-3.5">Sua área</div>
        <nav class="flex flex-col gap-0.5">
          <button
            v-for="item in abas"
            :key="item.id"
            :class="['rounded-lg px-3.5 py-2.5 text-left text-sm',
              aba === item.id ? 'bg-ink font-medium text-white' : 'text-ink-soft hover:bg-bg']"
            @click="aba = item.id">
            {{ item.label }}
          </button>
        </nav>
        <div class="mt-3 flex flex-col items-start gap-2 border-t border-rule-soft px-3.5 pt-3">
          <router-link
            :to="{ name: 'conta-cliente' }"
            class="text-[13px] text-ink-soft underline underline-offset-[3px]">
            Ir para a área do cliente
          </router-link>
          <button class="text-[13px] text-ink-soft underline" @click="sair">Sair</button>
        </div>
      </aside>

      <!-- Abas mobile -->
      <div class="flex gap-1 overflow-x-auto border-b border-rule bg-surface px-5 pt-3 md:hidden">
        <button
          v-for="a in abas"
          :key="a.id"
          :style="aba === a.id ? 'bottom:-1px' : ''"
          :class="['relative -mb-px whitespace-nowrap rounded-t-lg border border-b-0 px-3 py-[7px] text-[13px]',
            aba === a.id ? 'border-rule bg-surface font-semibold text-ink' : 'border-transparent text-muted']"
          @click="aba = a.id">
          {{ a.curto }}
        </button>
      </div>

      <!-- Conteúdo -->
      <main class="p-5 md:p-0">
        <div v-if="carregando" class="py-10 text-center text-sm text-muted">Carregando…</div>

        <!-- VITRINE -->
        <template v-else-if="aba === 'vitrine'">
          <div class="mb-5 flex flex-col gap-1 md:mb-6">
            <h1 class="text-xl font-semibold tracking-[-0.01em] md:text-2xl md:tracking-[-0.02em]">
              Sua vitrine pública
            </h1>
            <div class="text-[13px] text-muted">
              É o que aparece quando alguém encontra você numa busca.
            </div>
          </div>

          <!-- Quem se cadastrou só para contratar ativa a vitrine aqui -->
          <section v-if="semVitrine" class="rounded-2xl border border-rule bg-surface p-6 md:p-8">
            <div class="text-base font-semibold">Você ainda não oferece serviços no Mitra</div>
            <p class="mt-1.5 max-w-[52ch] text-[13px] leading-[1.55] text-ink-soft">
              Ative sua vitrine para aparecer nas buscas, montar seu portfólio e receber contatos.
              Sua conta continua podendo contratar normalmente.
            </p>
            <button
              :disabled="ativando"
              class="mt-4 h-11 rounded-lg bg-gold px-5 text-sm font-semibold text-ink hover:opacity-90 disabled:opacity-60"
              @click="ativarVitrine">
              {{ ativando ? 'Ativando…' : 'Ativar minha vitrine' }}
            </button>
            <p v-if="mensagem?.tipo === 'erro'" class="mt-3 text-sm text-red-700">{{ mensagem.texto }}</p>
          </section>

          <template v-else>
            <div class="mb-4 rounded-lg bg-surface-2 px-3 py-2.5 text-[12px] leading-[1.5] text-ink-soft md:hidden">
              É isto que aparece no seu perfil público quando alguém encontra você numa busca.
            </div>

            <section class="rounded-2xl border border-rule bg-surface p-5 md:p-7">
              <div class="grid gap-4 md:grid-cols-2">
                <label class="col-span-full flex flex-col gap-1.5">
                  <span class="mono-sm">Nome público</span>
                  <input v-model="nome" class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
                </label>

                <label class="col-span-full flex flex-col gap-1.5">
                  <span class="mono-sm">Bio (aparece no topo do perfil)</span>
                  <textarea
                    v-model="bio"
                    rows="4"
                    maxlength="400"
                    placeholder="Conte sua experiência, os tipos de serviço que faz e o seu diferencial."
                    class="resize-y rounded-lg border border-rule bg-bg px-3 py-2.5 font-sans text-sm"></textarea>
                  <div class="text-right text-[11px] text-muted">{{ bio.length }} / 400 caracteres</div>
                </label>

                <label class="flex flex-col gap-1.5">
                  <span class="mono-sm">Cidade</span>
                  <select v-model="idcidade" class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm">
                    <option :value="null">—</option>
                    <option v-for="c in cidades" :key="c.idcidade" :value="c.idcidade">
                      {{ rotuloCidade(c) }}
                    </option>
                  </select>
                </label>
                <label class="flex flex-col gap-1.5">
                  <span class="mono-sm">Disponibilidade</span>
                  <input
                    v-model="disponibilidade"
                    list="sugestoes-disponibilidade"
                    maxlength="120"
                    placeholder="Ex.: Seg a Sáb · 8h–18h"
                    class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
                  <datalist id="sugestoes-disponibilidade">
                    <option v-for="s in SUGESTOES_DISPONIBILIDADE" :key="s" :value="s" />
                  </datalist>
                </label>

                <label class="flex flex-col gap-1.5">
                  <span class="mono-sm">Faixa de preço · mínimo (R$)</span>
                  <input
                    v-model.number="precoMin"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="Sob consulta"
                    class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
                </label>
                <label class="flex flex-col gap-1.5">
                  <span class="mono-sm">Faixa de preço · máximo (R$)</span>
                  <input
                    v-model.number="precoMax"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="Sob consulta"
                    class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
                </label>

                <div class="col-span-full">
                  <div class="mono-sm mb-2">
                    Serviços que você atende
                    <span class="ml-1 font-normal normal-case tracking-normal text-muted"> · até {{ LIMITE_SERVICOS }}</span>
                  </div>
                  <div class="flex flex-wrap items-center gap-1.5">
                    <button
                      v-for="s in servicosSelecionados"
                      :key="s.idservico"
                      type="button"
                      :aria-label="`Remover ${s.nome}`"
                      class="rounded-full border border-ink bg-ink px-3 py-1 text-[13px] text-white"
                      @click="removerServico(s.idservico)">
                      {{ s.nome }} ×
                    </button>
                    <select
                      v-if="podeAdicionarServico"
                      class="rounded-full border border-rule bg-surface px-3 py-1 text-[13px] text-ink-soft"
                      @change="adicionarServico">
                      <option value="">+ adicionar serviço</option>
                      <optgroup v-for="c in categorias" :key="c.idcategoria" :label="c.nome">
                        <option
                          v-for="s in c.servicos"
                          :key="s.idservico"
                          :value="s.idservico"
                          :disabled="idsSelecionados.has(s.idservico)">
                          {{ s.nome }}
                        </option>
                      </optgroup>
                    </select>
                  </div>
                  <div v-if="!servicosSelecionados.length" class="mt-1.5 text-[12px] text-muted">
                    Sem ao menos um serviço, sua vitrine não aparece nas buscas.
                  </div>
                </div>
              </div>
            </section>

            <section class="mt-6 rounded-2xl border border-rule bg-surface p-5 md:p-7">
              <div class="mb-3 flex items-baseline justify-between">
                <div>
                  <div class="text-base font-semibold">Portfólio</div>
                  <div class="mt-0.5 text-[12px] text-muted">
                    {{ portfolio.length }} {{ portfolio.length === 1 ? 'imagem' : 'imagens' }}
                  </div>
                </div>
                <button class="text-[13px] text-ink underline underline-offset-[3px]" @click="aba = 'portfolio'">
                  {{ portfolio.length ? 'Gerenciar portfólio' : 'Adicionar fotos' }}
                </button>
              </div>
              <div v-if="portfolio.length" class="grid grid-cols-3 gap-2 md:grid-cols-6">
                <img
                  v-for="item in portfolio.slice(0, 6)"
                  :key="item.idprestadorportfolio"
                  :src="urlArquivo(item.imagem_url) ?? ''"
                  :alt="item.legenda ?? 'Imagem do portfólio'"
                  class="aspect-square w-full rounded-lg object-cover" />
              </div>
              <p v-else class="text-[13px] text-muted">
                Fotos de trabalhos feitos ajudam o cliente a decidir. Você pode enviar até 10.
              </p>
            </section>

            <section class="mt-6 flex items-center gap-4 rounded-2xl border border-rule bg-surface p-5 md:p-6">
              <div
                :class="['flex h-12 w-12 shrink-0 items-center justify-center rounded-xl text-2xl font-semibold',
                  vitrine?.cnpj_validado ? 'bg-gold-soft text-gold-ink' : 'bg-surface-2 text-muted']">
                <i class="fa fa-check"></i>
              </div>
              <div class="min-w-0 flex-1">
                <div class="text-[15px] font-semibold">
                  {{ vitrine?.cnpj_validado ? 'Selo CNPJ validado · ativo' : 'Ganhe o selo "CNPJ validado"' }}
                </div>
                <div class="mt-0.5 text-[13px] text-muted">
                  <template v-if="vitrine?.cnpj">
                    CNPJ {{ formatarCnpj(vitrine.cnpj) }} · aparece como badge dourado no seu perfil público.
                  </template>
                  <template v-else>
                    Cadastre um CNPJ ativo na Receita e seu perfil ganha o badge dourado.
                  </template>
                </div>
              </div>
              <button
                type="button"
                class="shrink-0 rounded-lg border border-rule px-3.5 py-2 text-[13px] text-ink-soft"
                @click="aba = 'dados'">
                {{ vitrine?.cnpj ? 'Gerenciar' : 'Cadastrar CNPJ' }}
              </button>
            </section>

            <div class="mt-6 flex flex-col items-end gap-2">
              <div class="flex gap-2.5">
                <button
                  type="button"
                  class="h-11 rounded-lg border border-rule px-5 text-sm text-ink-soft"
                  @click="preencher">
                  Descartar alterações
                </button>
                <button
                  :disabled="salvando"
                  class="h-11 rounded-lg bg-gold px-6 text-sm font-semibold text-ink hover:opacity-90 disabled:opacity-60"
                  @click="salvar">
                  {{ salvando ? 'Salvando…' : 'Salvar alterações' }}
                </button>
              </div>
              <span
                v-if="mensagem"
                :class="['text-[13px]', mensagem.tipo === 'ok' ? 'text-good' : 'text-red-700']">
                {{ mensagem.texto }}
              </span>
            </div>
          </template>
        </template>

        <template v-else-if="aba === 'contratacoes'">
          <ListaContratacoes papel="prestador" />
        </template>

        <template v-else-if="aba === 'portfolio'">
          <div class="mb-5">
            <h1 class="text-xl font-semibold md:text-2xl">Portfólio</h1>
            <div class="mt-0.5 text-[13px] text-muted">
              Suas fotos de trabalho — arraste (ou use ◀ ▶) para reordenar.
            </div>
          </div>
          <p v-if="semVitrine" class="text-sm text-muted">
            Ative sua vitrine na aba Vitrine para montar o portfólio.
          </p>
          <GerenciadorPortfolio v-else-if="vitrine" v-model="vitrine.portfolio" />
        </template>

        <template v-else>
          <div class="mb-5">
            <h1 class="text-xl font-semibold md:text-2xl">Dados da conta</h1>
            <div class="mt-0.5 text-[13px] text-muted">
              Informações privadas de identificação e CNPJ.
            </div>
          </div>
          <FormularioDadosConta />
          <CartaoCnpj v-if="vitrine" v-model="vitrine" />
        </template>
      </main>
    </div>
  </div>
</template>
