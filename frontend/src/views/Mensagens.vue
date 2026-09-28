<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ErroApi } from '../api/client'
import {
  conversaApi,
  estaOnline,
  TAMANHO_MAXIMO_MENSAGEM,
  type Conversa,
  type Mensagem,
  type Participante,
} from '../api/conversa'
import { prestadorApi } from '../api/prestador'
import { useSessaoStore } from '../stores/sessao'
import { atividadeRelativa, formatarHora, quandoCurto, rotuloDia } from '../utils/formatacao'
import FotoUsuario from '../components/FotoUsuario.vue'
import PublicNav from '../components/PublicNav.vue'

const INTERVALO_CONVERSA_MS = 5_000
const INTERVALO_LISTA_MS = 30_000

const route = useRoute()
const router = useRouter()
const sessao = useSessaoStore()

const conversas = ref<Conversa[]>([])
const carregandoLista = ref(true)

// Conversa aberta — ou um rascunho de primeiro contato (conversa ainda não existe).
const ativa = ref<Conversa | null>(null)
const rascunhoPara = ref<Participante | null>(null)
const mensagens = ref<Mensagem[]>([])
const temMaisAntigas = ref(false)
const carregandoConversa = ref(false)
const carregandoAntigas = ref(false)

const texto = ref('')
const enviando = ref(false)
const erro = ref<string | null>(null)
const areaMensagens = ref<HTMLElement | null>(null)

const idAtiva = computed(() => (route.params.id ? Number(route.params.id) : null))
const interlocutor = computed(() => ativa.value?.outra_parte ?? rascunhoPara.value)
const temConversaAberta = computed(() => !!interlocutor.value)

function textoDoErro(e: unknown): string {
  return e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
}

function statusPresenca(p: Participante): string {
  return estaOnline(p) ? '● Online' : `Visto ${atividadeRelativa(p.ultimo_acesso_em)}`
}

/** Mensagens com o separador de dia quando o dia muda. */
const linhas = computed(() =>
  mensagens.value.map((m, i) => ({
    mensagem: m,
    minha: m.idautor === sessao.usuario?.idusuario,
    dia:
      i === 0 || rotuloDia(m.criado_em) !== rotuloDia(mensagens.value[i - 1].criado_em)
        ? rotuloDia(m.criado_em)
        : null,
  })),
)

async function rolarParaFim() {
  await nextTick()
  if (areaMensagens.value) areaMensagens.value.scrollTop = areaMensagens.value.scrollHeight
}

// --- Carregamento ---------------------------------------------------------------

async function carregarLista() {
  try {
    conversas.value = await conversaApi.listar()
  } catch {
    // Mantém a lista anterior; o próximo ciclo tenta de novo.
  } finally {
    carregandoLista.value = false
  }
}

async function abrirConversa(idconversa: number) {
  rascunhoPara.value = null
  carregandoConversa.value = true
  erro.value = null
  try {
    const [conversa, pagina] = await Promise.all([
      conversaApi.obter(idconversa),
      conversaApi.mensagens(idconversa),
    ])
    ativa.value = conversa
    mensagens.value = pagina.itens
    temMaisAntigas.value = pagina.tem_mais_antigas
    rolarParaFim()
  } catch (e) {
    ativa.value = null
    mensagens.value = []
    erro.value = textoDoErro(e)
  } finally {
    carregandoConversa.value = false
  }
}

/** Primeiro contato vindo do perfil (?para=idusuario): reaproveita a conversa se já existir. */
async function abrirRascunho(idprestador: number) {
  const existente = conversas.value.find(
    (c) => c.papel === 'cliente' && c.outra_parte.idusuario === idprestador,
  )
  if (existente) {
    router.replace({ name: 'mensagem', params: { id: existente.idconversa } })
    return
  }
  ativa.value = null
  mensagens.value = []
  temMaisAntigas.value = false
  try {
    const perfil = await prestadorApi.obterPublico(idprestador)
    rascunhoPara.value = {
      idusuario: perfil.idusuario,
      nome: perfil.nome,
      foto_url: perfil.foto_url,
      ultimo_acesso_em: perfil.ultimo_acesso_em,
    }
  } catch (e) {
    erro.value = textoDoErro(e)
  }
}

async function carregarAntigas() {
  if (!ativa.value || !mensagens.value.length) return
  carregandoAntigas.value = true
  const area = areaMensagens.value
  const alturaAntes = area?.scrollHeight ?? 0
  try {
    const pagina = await conversaApi.mensagens(ativa.value.idconversa, {
      antesDe: mensagens.value[0].idmensagem,
    })
    mensagens.value = [...pagina.itens, ...mensagens.value]
    temMaisAntigas.value = pagina.tem_mais_antigas
    // Mantém a posição de leitura em vez de pular para o topo.
    await nextTick()
    if (area) area.scrollTop = area.scrollHeight - alturaAntes
  } catch (e) {
    erro.value = textoDoErro(e)
  } finally {
    carregandoAntigas.value = false
  }
}

async function buscarNovas() {
  if (!ativa.value || document.hidden) return
  const ultima = mensagens.value.at(-1)?.idmensagem
  try {
    const pagina = await conversaApi.mensagens(ativa.value.idconversa, { depoisDe: ultima })
    if (pagina.itens.length) {
      const area = areaMensagens.value
      const estavaNoFim = !area || area.scrollHeight - area.scrollTop - area.clientHeight < 80
      mensagens.value = [...mensagens.value, ...pagina.itens]
      if (estavaNoFim) rolarParaFim()
    }
  } catch {
    // Falha de rede no polling é silenciosa; tenta no próximo ciclo.
  }
}

async function sincronizarRota() {
  erro.value = null
  if (idAtiva.value) {
    await abrirConversa(idAtiva.value)
  } else if (route.query.para) {
    await abrirRascunho(Number(route.query.para))
  } else {
    ativa.value = null
    rascunhoPara.value = null
    mensagens.value = []
  }
}

// --- Envio ------------------------------------------------------------------------

async function enviar() {
  const conteudo = texto.value.trim()
  if (!conteudo || enviando.value) return
  enviando.value = true
  erro.value = null
  try {
    if (ativa.value) {
      const mensagem = await conversaApi.enviar(ativa.value.idconversa, conteudo)
      mensagens.value = [...mensagens.value, mensagem]
      rolarParaFim()
    } else if (rascunhoPara.value) {
      // Primeira mensagem cria a conversa.
      const conversa = await conversaApi.iniciar(rascunhoPara.value.idusuario, conteudo)
      router.replace({ name: 'mensagem', params: { id: conversa.idconversa } })
    }
    texto.value = ''
    carregarLista()
  } catch (e) {
    erro.value = textoDoErro(e)
  } finally {
    enviando.value = false
  }
}

// --- Ciclo de vida ------------------------------------------------------------

let pollingConversa: ReturnType<typeof setInterval> | undefined
let pollingLista: ReturnType<typeof setInterval> | undefined

onMounted(async () => {
  await carregarLista()
  await sincronizarRota()
  pollingConversa = setInterval(buscarNovas, INTERVALO_CONVERSA_MS)
  pollingLista = setInterval(() => !document.hidden && carregarLista(), INTERVALO_LISTA_MS)
})

onBeforeUnmount(() => {
  clearInterval(pollingConversa)
  clearInterval(pollingLista)
})

watch(() => [route.params.id, route.query.para], sincronizarRota)
</script>

<template>
  <div class="min-h-screen bg-bg">
    <div class="hidden md:block"><PublicNav /></div>

    <div class="md:grid md:h-[calc(100vh-72px)] md:grid-cols-[300px_1fr]">
      <!-- Lista de conversas (no celular, só quando não há conversa aberta) -->
      <aside
        :class="['flex-col border-r border-rule-soft bg-surface md:flex',
          temConversaAberta ? 'hidden' : 'flex min-h-screen md:min-h-0']">
        <div class="flex items-center gap-3 border-b border-rule-soft px-4 py-3.5">
          <router-link to="/" aria-label="Início" class="md:hidden"><i class="fa fa-arrow-left"></i></router-link>
          <div class="text-[15px] font-semibold">Mensagens</div>
        </div>
        <div class="flex-1 overflow-y-auto">
          <div v-if="carregandoLista" class="p-4 text-[13px] text-muted">Carregando…</div>
          <div v-else-if="!conversas.length" class="p-5 text-[13px] leading-[1.5] text-muted">
            Nenhuma conversa ainda. Encontre um prestador na
            <router-link to="/buscar" class="text-ink underline underline-offset-[3px]">busca</router-link>
            e clique em "Iniciar contato".
          </div>
          <router-link
            v-for="c in conversas"
            :key="c.idconversa"
            :to="{ name: 'mensagem', params: { id: c.idconversa } }"
            :class="['flex w-full items-center gap-2.5 border-b border-rule-soft px-3.5 py-3 text-left',
              c.idconversa === ativa?.idconversa
                ? 'bg-bg shadow-[inset_3px_0_0_var(--color-ink)]'
                : 'hover:bg-bg']">
            <FotoUsuario :url="c.outra_parte.foto_url" :nome="c.outra_parte.nome" tamanho="h-9 w-9 text-sm" />
            <div class="min-w-0 flex-1">
              <div class="flex justify-between gap-2 text-[13px] font-semibold">
                <span class="truncate">{{ c.outra_parte.nome }}</span>
                <span class="shrink-0 text-[10px] font-normal text-muted">{{ quandoCurto(c.atualizado_em) }}</span>
              </div>
              <div class="truncate text-xs text-muted">
                <template v-if="c.ultima_mensagem">
                  {{ c.ultima_mensagem.idautor === sessao.usuario?.idusuario ? 'Você: ' : '' }}{{ c.ultima_mensagem.texto }}
                </template>
              </div>
              <div class="mt-0.5 text-[10px] uppercase tracking-wide text-muted">
                {{ c.papel === 'cliente' ? 'Você contratando' : 'Cliente' }}
              </div>
            </div>
          </router-link>
        </div>
      </aside>

      <!-- Conversa aberta -->
      <section
        :class="['flex-col bg-surface md:flex',
          temConversaAberta ? 'flex h-[100dvh] md:h-auto' : 'hidden']">
        <template v-if="interlocutor">
          <div class="flex items-center gap-3 border-b border-rule-soft px-4 py-3 md:px-5">
            <router-link :to="{ name: 'mensagens' }" aria-label="Voltar às conversas" class="md:hidden">
              <i class="fa fa-arrow-left"></i>
            </router-link>
            <FotoUsuario :url="interlocutor.foto_url" :nome="interlocutor.nome" tamanho="h-9 w-9 text-sm" />
            <div class="min-w-0 flex-1">
              <div class="truncate text-sm font-semibold">{{ interlocutor.nome }}</div>
              <div :class="['text-[11px]', estaOnline(interlocutor) ? 'text-good' : 'text-muted']">
                {{ statusPresenca(interlocutor) }}
              </div>
            </div>
            <router-link
              v-if="rascunhoPara || ativa?.papel === 'cliente'"
              :to="{ name: 'prestador', params: { id: interlocutor.idusuario } }"
              class="text-xs text-ink-soft underline">
              Ver perfil
            </router-link>
          </div>

          <div ref="areaMensagens" class="flex flex-1 flex-col gap-1.5 overflow-y-auto p-4">
            <div v-if="carregandoConversa" class="py-6 text-center text-[13px] text-muted">Carregando…</div>
            <template v-else>
              <button
                v-if="temMaisAntigas"
                type="button"
                :disabled="carregandoAntigas"
                class="mx-auto mb-2 rounded-full border border-rule px-3 py-1 text-[12px] text-ink-soft disabled:opacity-60"
                @click="carregarAntigas">
                {{ carregandoAntigas ? 'Carregando…' : 'Carregar mensagens anteriores' }}
              </button>

              <div v-if="rascunhoPara" class="m-auto max-w-[36ch] text-center text-[13px] leading-[1.5] text-muted">
                Escreva sua primeira mensagem para {{ rascunhoPara.nome }}: conte o que você precisa.
                A conversa fica registrada no Mitra.
              </div>

              <template v-for="linha in linhas" :key="linha.mensagem.idmensagem">
                <div v-if="linha.dia" class="my-1 text-center text-[10px] text-muted">{{ linha.dia }}</div>
                <div
                  v-if="linha.mensagem.tipo === 'evento'"
                  class="my-1 self-center rounded-full bg-surface-2 px-3 py-1 text-center text-[12px] text-ink-soft">
                  {{ linha.mensagem.texto }} · {{ formatarHora(linha.mensagem.criado_em) }}
                </div>
                <div
                  v-else
                  :class="['max-w-[82%] whitespace-pre-line break-words px-3 py-2 text-[13px] leading-[1.45]',
                    linha.minha
                      ? 'self-end rounded-[14px_14px_4px_14px] bg-ink text-white'
                      : 'self-start rounded-[14px_14px_14px_4px] border border-rule-soft bg-bg text-ink']">
                  {{ linha.mensagem.texto }}
                  <div :class="['mt-0.5 text-right text-[10px]', linha.minha ? 'text-white/60' : 'text-muted']">
                    {{ formatarHora(linha.mensagem.criado_em) }}
                  </div>
                </div>
              </template>
            </template>
          </div>

          <p v-if="erro" class="px-4 pb-1 text-[12px] text-red-700">{{ erro }}</p>
          <form class="flex items-end gap-2 border-t border-rule-soft px-3 py-2.5" @submit.prevent="enviar">
            <textarea
              v-model="texto"
              rows="1"
              :maxlength="TAMANHO_MAXIMO_MENSAGEM"
              placeholder="Escrever mensagem…"
              class="max-h-32 flex-1 resize-none rounded-lg border borda-campo bg-bg px-3 py-2 font-sans text-[13px] outline-none"
              @keydown.enter.exact.prevent="enviar"></textarea>
            <button
              type="submit"
              aria-label="Enviar"
              :disabled="enviando || !texto.trim()"
              class="flex h-9 w-9 items-center justify-center rounded-lg bg-gold font-semibold text-ink hover:opacity-90 disabled:opacity-50">
              <i class="fa fa-paper-plane"></i>
            </button>
          </form>
        </template>

        <div v-else class="m-auto max-w-[40ch] p-8 text-center text-[13px] text-muted">
          <template v-if="erro">{{ erro }}</template>
          <template v-else>Escolha uma conversa ao lado.</template>
        </div>
      </section>
    </div>
  </div>
</template>
