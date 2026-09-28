<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { rotuloCidade } from '../api/cidade'
import { avaliacaoApi, formatarNota, type Avaliacao } from '../api/avaliacao'
import { ErroApi, urlArquivo } from '../api/client'
import { conversaApi } from '../api/conversa'
import { prestadorApi, type PrestadorPublico } from '../api/prestador'
import { useSessaoStore } from '../stores/sessao'
import { atividadeRelativa, formatarFaixaPreco, tempoDesde } from '../utils/formatacao'
import CartaoAvaliacao from '../components/CartaoAvaliacao.vue'
import CategoryChip from '../components/CategoryChip.vue'
import FotoUsuario from '../components/FotoUsuario.vue'
import PublicNav from '../components/PublicNav.vue'
import StarRating from '../components/StarRating.vue'
import Tabs from '../components/Tabs.vue'

const route = useRoute()
const router = useRouter()
const sessao = useSessaoStore()

type Aba = 'sobre' | 'portfolio' | 'avaliacoes'
const aba = ref<Aba>('sobre')

const prestador = ref<PrestadorPublico | null>(null)
const carregando = ref(true)
const naoEncontrado = ref(false)
const erro = ref<string | null>(null)

const abas = computed(() => [
  { id: 'sobre' as const, label: 'Sobre' },
  { id: 'portfolio' as const, label: 'Portfólio' },
  { id: 'avaliacoes' as const, label: `Avaliações (${prestador.value?.qtd_avaliacoes ?? 0})` },
])

const cidade = computed(() =>
  prestador.value?.cidade ? rotuloCidade(prestador.value.cidade) : null,
)
const temNota = computed(() => prestador.value?.nota_media != null)

const TAMANHO_PAGINA_AVALIACOES = 10
const avaliacoes = ref<Avaliacao[]>([])
const totalAvaliacoes = ref(0)
const carregandoAvaliacoes = ref(false)

async function carregarMaisAvaliacoes() {
  if (!prestador.value) return
  carregandoAvaliacoes.value = true
  try {
    const pagina = await avaliacaoApi.doPrestador(prestador.value.idusuario, {
      limite: TAMANHO_PAGINA_AVALIACOES,
      deslocamento: avaliacoes.value.length,
    })
    avaliacoes.value = [...avaliacoes.value, ...pagina.itens]
    totalAvaliacoes.value = pagina.total
  } finally {
    carregandoAvaliacoes.value = false
  }
}

async function carregar(id: number) {
  carregando.value = true
  naoEncontrado.value = false
  erro.value = null
  try {
    prestador.value = await prestadorApi.obterPublico(id)
    const pagina = await avaliacaoApi.doPrestador(id, { limite: TAMANHO_PAGINA_AVALIACOES })
    avaliacoes.value = pagina.itens
    totalAvaliacoes.value = pagina.total
  } catch (e) {
    prestador.value = null
    if (e instanceof ErroApi && e.status === 404) naoEncontrado.value = true
    else erro.value = e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
  } finally {
    carregando.value = false
  }
}

watch(
  () => Number(route.params.id),
  (id) => {
    aba.value = 'sobre'
    carregar(id)
  },
  { immediate: true },
)

const ehMeuPerfil = computed(
  () => !!prestador.value && sessao.usuario?.idusuario === prestador.value.idusuario,
)

// Abre a conversa existente com este prestador ou um rascunho (a conversa só é
// criada com a primeira mensagem). Sem login, passa pelo login e volta para cá.
async function iniciarContato() {
  if (!prestador.value) return
  const destinoNovo = { name: 'mensagens', query: { para: String(prestador.value.idusuario) } }
  if (!sessao.logado) {
    router.push({ name: 'login', query: { redirect: router.resolve(destinoNovo).fullPath } })
    return
  }
  try {
    const existente = (await conversaApi.listar()).find(
      (c) => c.papel === 'cliente' && c.outra_parte.idusuario === prestador.value!.idusuario,
    )
    router.push(existente ? { name: 'mensagem', params: { id: existente.idconversa } } : destinoNovo)
  } catch {
    router.push(destinoNovo)
  }
}
</script>

<template>
  <div class="min-h-screen bg-bg pb-24 lg:pb-0">
    <div class="hidden md:block">
      <PublicNav />
      <div class="px-16 py-4 text-[13px] text-muted">
        <router-link to="/buscar" class="text-ink-soft">Buscar prestadores</router-link>
        <template v-if="prestador">
          <span class="mx-2">›</span>
          <span>{{ prestador.nome }}</span>
        </template>
      </div>
    </div>

    <div class="flex items-center justify-between border-b border-rule-soft bg-surface px-5 py-3.5 md:hidden">
      <button aria-label="Voltar" class="flex h-9 w-9 items-center justify-center rounded-lg border border-rule" @click="router.back()">
        <i class="fa fa-arrow-left"></i>
      </button>
    </div>

    <div v-if="carregando" class="px-5 py-16 text-center text-sm text-muted md:px-16">Carregando…</div>

    <div v-else-if="naoEncontrado || erro" class="px-5 py-16 text-center md:px-16">
      <div class="text-lg font-semibold">{{ naoEncontrado ? 'Prestador não encontrado' : 'Não foi possível carregar o perfil' }}</div>
      <p class="mt-1 text-sm text-muted">
        {{ naoEncontrado ? 'O perfil pode ter sido desativado ou o link está incorreto.' : erro }}
      </p>
      <router-link to="/buscar" class="mt-4 inline-block text-sm text-ink underline underline-offset-[3px]">
        Buscar outros prestadores
      </router-link>
    </div>

    <div v-else-if="prestador" class="grid gap-8 px-0 lg:grid-cols-[1fr_360px] md:gap-12 md:px-16 md:pb-10">
      <div>
        <div class="border-b border-rule-soft bg-surface px-5 py-6 md:rounded-2xl md:border md:border-rule md:p-8">
          <div class="flex items-start gap-4 md:gap-7">
            <FotoUsuario
              :url="prestador.foto_url"
              :nome="prestador.nome"
              tamanho="h-[88px] w-[88px] text-3xl md:h-[140px] md:w-[140px] md:text-5xl" />
            <div class="min-w-0 flex-1">
              <h1 class="mb-1 text-[22px] font-semibold tracking-[-0.01em] md:text-[30px] md:tracking-[-0.02em]">
                {{ prestador.nome }}
              </h1>
              <div class="text-[13px] text-muted md:text-sm">
                <span v-if="cidade">{{ cidade }} · </span>no Mitra há {{ tempoDesde(prestador.prestador_desde) }}
              </div>

              <div class="mt-4 hidden items-center gap-6 border-y border-rule-soft py-4 md:flex">
                <div>
                  <div v-if="temNota" class="flex items-center gap-1.5">
                    <StarRating :value="prestador.nota_media!" size="md" />
                    <span class="text-base font-semibold">
                      {{ prestador.nota_media!.toFixed(1).replace('.', ',') }}
                    </span>
                  </div>
                  <div v-else class="text-base font-semibold">—</div>
                  <div class="mono-sm">{{ prestador.qtd_avaliacoes }} {{ prestador.qtd_avaliacoes === 1 ? 'avaliação' : 'avaliações' }}</div>
                </div>
                <span class="h-8 w-px bg-rule-soft"></span>
                <div>
                  <div class="num text-[22px] font-semibold">{{ prestador.servicos_concluidos }}</div>
                  <div class="mono-sm">Serviços concluídos</div>
                </div>
              </div>

              <div class="mt-2 text-xs text-muted md:hidden">
                {{ temNota ? `${prestador.nota_media!.toFixed(1).replace('.', ',')} · ` : '' }}{{ prestador.qtd_avaliacoes }} {{ prestador.qtd_avaliacoes === 1 ? 'avaliação' : 'avaliações' }}
              </div>

              <div class="mt-3.5 flex flex-wrap gap-1.5">
                <CategoryChip v-for="s in prestador.servicos" :key="s.idservico">{{ s.nome }}</CategoryChip>
                <CategoryChip v-if="prestador.cnpj_validado" tone="gold">CNPJ validado ✓</CategoryChip>
              </div>
            </div>
          </div>

          <div v-if="!ehMeuPerfil" class="mt-4 lg:hidden">
            <button class="h-[50px] w-full rounded-xl bg-gold text-[15px] font-semibold text-ink hover:opacity-90" @click="iniciarContato">
              Iniciar contato
            </button>
            <div class="mt-2 text-center text-xs text-muted">
              A conversa fica registrada no Mitra
            </div>
          </div>
        </div>

        <div class="mt-4 md:mt-8">
          <Tabs v-model="aba" :items="abas" size="md" />
        </div>

        <div class="space-y-8 px-5 py-6 md:px-0 md:py-8">
          <template v-if="aba === 'sobre'">
            <section>
              <div class="mono mb-2">Apresentação</div>
              <p v-if="prestador.bio" class="max-w-[60ch] whitespace-pre-line text-[14px] leading-[1.6] text-ink-soft md:text-[15px]">
                {{ prestador.bio }}
              </p>
              <p v-else class="text-sm text-muted">Este prestador ainda não escreveu uma apresentação.</p>
            </section>

            <section v-if="prestador.portfolio.length">
              <div class="mb-3 flex items-baseline justify-between">
                <div class="mono">Portfólio · {{ prestador.portfolio.length }} {{ prestador.portfolio.length === 1 ? 'imagem' : 'imagens' }}</div>
                <button class="text-[13px] text-ink-soft underline underline-offset-[3px]" @click="aba = 'portfolio'">
                  Ver galeria
                </button>
              </div>
              <div class="grid grid-cols-3 gap-1.5 md:grid-cols-6 md:gap-2">
                <button
                  v-for="(item, i) in prestador.portfolio.slice(0, 6)"
                  :key="item.idprestadorportfolio"
                  type="button"
                  class="relative aspect-square overflow-hidden rounded-lg md:rounded-xl"
                  @click="aba = 'portfolio'">
                  <img
                    :src="urlArquivo(item.imagem_url) ?? ''"
                    :alt="item.legenda ?? `Trabalho ${i + 1}`"
                    class="h-full w-full object-cover" />
                  <span
                    v-if="i === 5 && prestador.portfolio.length > 6"
                    class="absolute inset-0 flex items-center justify-center bg-black/40 text-base font-semibold text-white">
                    +{{ prestador.portfolio.length - 5 }}
                  </span>
                </button>
              </div>
            </section>

            <section class="lg:hidden">
              <div class="mono mb-2">Atendimento</div>
              <ul class="space-y-2 text-[13px]">
                <li class="flex justify-between"><span class="text-muted">Preço</span><span>{{ formatarFaixaPreco(prestador.preco_min, prestador.preco_max) }}</span></li>
                <li v-if="prestador.disponibilidade" class="flex justify-between"><span class="text-muted">Disponibilidade</span><span>{{ prestador.disponibilidade }}</span></li>
                <li class="flex justify-between"><span class="text-muted">Última atividade</span><span>{{ atividadeRelativa(prestador.ultimo_acesso_em) }}</span></li>
              </ul>
            </section>

            <section>
              <div class="mb-3 flex items-baseline justify-between">
                <div class="mono">Últimas avaliações</div>
                <button
                  v-if="totalAvaliacoes > 2"
                  class="text-[13px] text-ink-soft underline underline-offset-[3px]"
                  @click="aba = 'avaliacoes'">
                  Ver todas
                </button>
              </div>
              <div v-if="avaliacoes.length" class="grid gap-3 md:grid-cols-2">
                <CartaoAvaliacao
                  v-for="a in avaliacoes.slice(0, 2)"
                  :key="a.idavaliacao"
                  :nota="a.nota"
                  :comentario="a.comentario"
                  :criado-em="a.criado_em"
                  :autor="a.autor"
                  :servico="a.servico"
                  :resposta="a.resposta"
                  :resposta-em="a.resposta_em" />
              </div>
              <p v-else class="text-sm text-muted">Ainda sem avaliações.</p>
            </section>
          </template>

          <template v-else-if="aba === 'portfolio'">
            <div v-if="prestador.portfolio.length" class="grid grid-cols-2 gap-3 md:grid-cols-3">
              <figure v-for="(item, i) in prestador.portfolio" :key="item.idprestadorportfolio">
                <a :href="urlArquivo(item.imagem_url) ?? '#'" target="_blank" rel="noopener">
                  <img
                    :src="urlArquivo(item.imagem_url) ?? ''"
                    :alt="item.legenda ?? `Trabalho ${i + 1}`"
                    class="aspect-square w-full rounded-xl object-cover" />
                </a>
                <figcaption v-if="item.legenda" class="mt-1.5 text-[12px] text-ink-soft">
                  {{ item.legenda }}
                </figcaption>
              </figure>
            </div>
            <p v-else class="text-sm text-muted">Ainda sem imagens no portfólio.</p>
          </template>

          <template v-else>
            <template v-if="avaliacoes.length">
              <div class="mono mb-3">
                {{ totalAvaliacoes }} {{ totalAvaliacoes === 1 ? 'avaliação' : 'avaliações' }}
                <template v-if="temNota"> · média {{ formatarNota(prestador.nota_media!) }}</template>
              </div>
              <div class="grid gap-3 md:grid-cols-2">
                <CartaoAvaliacao
                  v-for="a in avaliacoes"
                  :key="a.idavaliacao"
                  :nota="a.nota"
                  :comentario="a.comentario"
                  :criado-em="a.criado_em"
                  :autor="a.autor"
                  :servico="a.servico"
                  :resposta="a.resposta"
                  :resposta-em="a.resposta_em" />
              </div>
              <button
                v-if="avaliacoes.length < totalAvaliacoes"
                :disabled="carregandoAvaliacoes"
                class="mt-4 rounded-lg border border-ink px-4 py-2 text-sm font-semibold disabled:opacity-60"
                @click="carregarMaisAvaliacoes">
                {{ carregandoAvaliacoes ? 'Carregando…' : 'Carregar mais' }}
              </button>
            </template>
            <p v-else class="text-sm text-muted">
              Ainda sem avaliações. Elas aparecem aqui depois que cliente e prestador
              confirmam a conclusão de um serviço.
            </p>
          </template>
        </div>
      </div>

      <aside class="sticky top-6 hidden self-start rounded-2xl border border-rule bg-surface p-6 lg:block">
        <template v-if="ehMeuPerfil">
          <div class="mono mb-2">Este é o seu perfil</div>
          <p class="mb-3 text-[13px] leading-[1.5] text-ink-soft">É assim que os clientes veem sua vitrine.</p>
          <router-link
            :to="{ name: 'conta-prestador' }"
            class="block rounded-xl border border-ink py-3 text-center text-sm font-semibold">
            Editar minha vitrine
          </router-link>
        </template>
        <template v-else>
          <div class="mb-3">
            <div class="mono mb-2">Entrar em contato</div>
            <div class="text-[13px] leading-[1.5] text-ink-soft">
              A conversa acontece dentro do Mitra e fica registrada para viabilizar a avaliação depois.
            </div>
          </div>
          <button class="h-13 w-full rounded-xl bg-gold py-3.5 text-[15px] font-semibold text-ink hover:opacity-90" @click="iniciarContato">
            Iniciar contato
          </button>
        </template>

        <div class="my-4 h-px bg-rule-soft"></div>

        <ul class="space-y-2.5 text-[13px]">
          <li v-if="cidade" class="flex justify-between"><span class="text-muted">Cidade</span><span>{{ cidade }}</span></li>
          <li class="flex justify-between gap-3"><span class="text-muted">Preço</span><span class="text-right">{{ formatarFaixaPreco(prestador.preco_min, prestador.preco_max) }}</span></li>
          <li v-if="prestador.disponibilidade" class="flex justify-between gap-3"><span class="text-muted">Disponibilidade</span><span class="text-right">{{ prestador.disponibilidade }}</span></li>
          <li v-if="prestador.cnpj_validado" class="flex justify-between"><span class="text-muted">CNPJ</span><span class="text-gold-ink">Validado ✓</span></li>
          <li class="flex justify-between"><span class="text-muted">Última atividade</span><span>{{ atividadeRelativa(prestador.ultimo_acesso_em) }}</span></li>
        </ul>

        <div class="my-4 h-px bg-rule-soft"></div>
        <a href="#" class="text-[12px] text-muted underline underline-offset-[3px]">Reportar perfil</a>
      </aside>
    </div>

    <div v-if="prestador && !ehMeuPerfil" class="fixed inset-x-0 bottom-0 border-t border-rule bg-surface px-5 py-3 lg:hidden">
      <button class="h-12 w-full rounded-lg bg-gold text-[15px] font-semibold text-ink hover:opacity-90" @click="iniciarContato">
        Iniciar contato
      </button>
    </div>
  </div>
</template>
