<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { cidadeApi, rotuloCidade, type Cidade } from '../api/cidade'
import { ErroApi } from '../api/client'
import { contaApi, type ContaAtualizacao, type Usuario } from '../api/conta'
import { useSessaoStore } from '../stores/sessao'
import FotoUsuario from '../components/FotoUsuario.vue'
import PublicNav from '../components/PublicNav.vue'
import StatusBadge from '../components/StatusBadge.vue'
import StarRating from '../components/StarRating.vue'

const router = useRouter()
const sessao = useSessaoStore()

type Aba = 'contratacoes' | 'dados' | 'preferencias'
const aba = ref<Aba>('contratacoes')

// Dados da conta e preferências — PATCH /conta
const cidades = ref<Cidade[]>([])
const formNome = ref('')
const formIdcidade = ref<number | null>(null)
const formTelefone = ref('')
const notificarEmail = ref(true)
const buscaSomenteCnpj = ref(false)
const salvando = ref(false)
const mensagemDados = ref<{ tipo: 'ok' | 'erro'; texto: string } | null>(null)

function preencherFormulario(usuario: Usuario) {
  formNome.value = usuario.nome
  formIdcidade.value = usuario.cidade?.idcidade ?? null
  formTelefone.value = usuario.telefone ?? ''
  notificarEmail.value = usuario.notificar_email ?? true
  buscaSomenteCnpj.value = usuario.busca_somente_cnpj ?? false
}

async function atualizarConta(dados: ContaAtualizacao) {
  const usuario = await contaApi.atualizar(dados)
  sessao.definirUsuario(usuario)
  preencherFormulario(usuario)
}

async function salvarDados() {
  mensagemDados.value = null
  salvando.value = true
  try {
    await atualizarConta({
      nome: formNome.value,
      idcidade: formIdcidade.value,
      telefone: formTelefone.value || null,
    })
    mensagemDados.value = { tipo: 'ok', texto: 'Alterações salvas.' }
  } catch (e) {
    mensagemDados.value = {
      tipo: 'erro',
      texto: e instanceof ErroApi ? e.detalhe : 'Erro inesperado',
    }
  } finally {
    salvando.value = false
  }
}

const enviandoFoto = ref(false)
const erroFoto = ref<string | null>(null)

async function enviarFoto(evento: Event) {
  const campo = evento.target as HTMLInputElement
  const arquivo = campo.files?.[0]
  campo.value = '' // permite escolher o mesmo arquivo de novo
  if (!arquivo) return

  erroFoto.value = null
  enviandoFoto.value = true
  try {
    sessao.definirUsuario(await contaApi.enviarFoto(arquivo))
  } catch (e) {
    erroFoto.value = e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
  } finally {
    enviandoFoto.value = false
  }
}

async function removerFoto() {
  erroFoto.value = null
  try {
    sessao.definirUsuario(await contaApi.removerFoto())
  } catch (e) {
    erroFoto.value = e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
  }
}

async function salvarPreferencia(dados: ContaAtualizacao) {
  try {
    await atualizarConta(dados)
  } catch {
    // Volta o checkbox para o valor salvo.
    if (sessao.usuario) preencherFormulario(sessao.usuario)
  }
}

onMounted(async () => {
  if (sessao.usuario) preencherFormulario(sessao.usuario)
  try {
    const [usuario, lista] = await Promise.all([contaApi.obter(), cidadeApi.listar()])
    sessao.definirUsuario(usuario)
    preencherFormulario(usuario)
    cidades.value = lista
  } catch {
    // Mantém o que veio do armazenamento local.
  }
})

type Filtro = 'todos' | 'andamento' | 'concluidos'
const filtro = ref<Filtro>('andamento')

// Mocks — trocar por chamadas à API na fase seguinte
const contratacoes = [
  {
    id: 1, prestador: '[Prestador]', servico: 'Instalação elétrica',
    estado: 'wait' as const, statusLabel: 'Aguardando confirmação bilateral',
    detalhe: 'Iniciado há 3 dias · você já confirmou',
    acoes: ['abrir-chat', 'ver-confirmacao'] as const,
  },
  {
    id: 2, prestador: '[Prestador]', servico: 'Aula particular',
    estado: 'active' as const, statusLabel: 'Em conversa',
    detalhe: 'Última mensagem há 2 horas',
    acoes: ['abrir-chat'] as const,
  },
  {
    id: 3, prestador: '[Prestador]', servico: 'Adestramento',
    estado: 'done' as const, statusLabel: 'Concluído · aguardando sua avaliação',
    detalhe: 'Finalizado há 5 dias',
    acoes: ['avaliar'] as const,
  },
  {
    id: 4, prestador: '[Prestador]', servico: 'Conserto',
    estado: 'done' as const, statusLabel: 'Avaliado',
    detalhe: 'Há 3 semanas · você avaliou',
    nota: 5,
    acoes: ['ver-avaliacao'] as const,
  },
]

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
      <router-link to="/"><div class="text-[15px] font-semibold">Mitra</div></router-link>
      <button class="text-[13px] text-ink-soft" @click="sair">Sair</button>
    </div>

    <!-- Header mobile: identidade -->
    <div class="flex items-center gap-3.5 border-b border-rule-soft bg-surface px-5 py-4 md:hidden">
      <FotoUsuario
        :url="sessao.usuario?.foto_url"
        :nome="sessao.usuario?.nome"
        tamanho="h-14 w-14 text-lg" />
      <div class="min-w-0 flex-1">
        <div class="text-base font-semibold">{{ sessao.usuario?.nome ?? '[Seu nome]' }}</div>
        <div class="text-xs text-muted">
          {{ sessao.usuario?.cidade ? `${rotuloCidade(sessao.usuario.cidade)} · ` : '' }}cliente
        </div>
      </div>
    </div>

    <!-- Layout desktop: sidebar + main -->
    <div class="md:grid md:min-h-[calc(100vh-72px)] md:grid-cols-[240px_1fr]">
      <!-- Sidebar desktop -->
      <aside class="hidden flex-col gap-6 border-r border-rule-soft bg-surface p-6 md:flex">
        <div class="flex items-center gap-3 px-1.5">
          <FotoUsuario :url="sessao.usuario?.foto_url" :nome="sessao.usuario?.nome" />
          <div class="min-w-0">
            <div class="truncate text-sm font-semibold">{{ sessao.usuario?.nome ?? '[Seu nome]' }}</div>
            <div class="text-xs text-muted">Cliente</div>
          </div>
        </div>
        <nav class="flex flex-col gap-0.5">
          <button
            :class="['flex items-center justify-between rounded-lg px-3.5 py-2.5 text-left text-sm',
              aba === 'contratacoes' ? 'bg-ink font-medium text-white' : 'text-ink-soft hover:bg-bg']"
            @click="aba = 'contratacoes'">
            Contratações
          </button>
          <router-link to="/mensagens" class="rounded-lg px-3.5 py-2.5 text-sm text-ink-soft hover:bg-bg">
            Mensagens
          </router-link>
          <button
            :class="['rounded-lg px-3.5 py-2.5 text-left text-sm',
              aba === 'dados' ? 'bg-ink font-medium text-white' : 'text-ink-soft hover:bg-bg']"
            @click="aba = 'dados'">
            Dados da conta
          </button>
          <button
            :class="['rounded-lg px-3.5 py-2.5 text-left text-sm',
              aba === 'preferencias' ? 'bg-ink font-medium text-white' : 'text-ink-soft hover:bg-bg']"
            @click="aba = 'preferencias'">
            Preferências
          </button>
          <a href="#" class="rounded-lg px-3.5 py-2.5 text-sm text-ink-soft hover:bg-bg">
            Termos e privacidade
          </a>
        </nav>
        <div class="mt-auto border-t border-rule-soft pt-5">
          <button class="text-[13px] text-ink-soft underline" @click="sair">Sair</button>
        </div>
      </aside>

      <!-- Abas (mobile) -->
      <div class="flex gap-5 border-b border-rule bg-surface px-5 md:hidden">
        <button
          v-for="a in [
            { id: 'contratacoes', label: 'Contratações' },
            { id: 'dados', label: 'Dados' },
            { id: 'preferencias', label: 'Preferências' },
          ]"
          :key="a.id"
          :class="['py-3 text-sm border-b-2',
            aba === (a.id as Aba) ? 'border-ink font-semibold text-ink' : 'border-transparent text-muted']"
          @click="aba = a.id as Aba">
          {{ a.label }}
        </button>
      </div>

      <!-- Conteúdo -->
      <main class="overflow-y-auto p-5 md:p-10">
        <!-- CONTRATAÇÕES -->
        <template v-if="aba === 'contratacoes'">
          <div class="mb-5 flex flex-col gap-3 md:mb-6 md:flex-row md:items-baseline md:justify-between">
            <div>
              <h1 class="text-xl font-semibold tracking-[-0.01em] md:text-2xl md:tracking-[-0.02em]">
                Suas contratações
              </h1>
              <div class="mt-0.5 text-[13px] text-muted">
                Todo contato feito pelo Mitra aparece aqui.
              </div>
            </div>
            <div class="flex gap-2 overflow-x-auto">
              <button
                v-for="f in [
                  { id: 'todos', label: 'Todos' },
                  { id: 'andamento', label: 'Em andamento' },
                  { id: 'concluidos', label: 'Concluídos' },
                ]"
                :key="f.id"
                :class="['whitespace-nowrap rounded-lg border px-3.5 py-2 text-[13px]',
                  filtro === (f.id as Filtro)
                    ? 'border-ink bg-ink text-white'
                    : 'border-rule bg-surface']"
                @click="filtro = f.id as Filtro">
                {{ f.label }}
              </button>
            </div>
          </div>

          <div class="flex flex-col gap-3">
            <article
              v-for="c in contratacoes"
              :key="c.id"
              class="rounded-xl border border-rule bg-surface p-3.5 md:grid md:grid-cols-[56px_1fr_auto] md:items-center md:gap-4 md:p-4.5">
              <div class="ph mb-3 h-14 w-14 shrink-0 rounded-xl md:mb-0"></div>
              <div class="mb-3 md:mb-0">
                <div class="flex flex-wrap items-baseline gap-2.5">
                  <div class="text-[15px] font-semibold">{{ c.prestador }}</div>
                  <StatusBadge :variant="c.estado">{{ c.statusLabel }}</StatusBadge>
                </div>
                <div class="mt-1 text-[13px] text-muted">
                  {{ c.servico }} · {{ c.detalhe }}
                  <template v-if="c.nota">
                    · <StarRating :value="c.nota" /> {{ c.nota }},0
                  </template>
                </div>
              </div>
              <div class="flex gap-2">
                <router-link
                  v-if="c.acoes.includes('abrir-chat')"
                  :to="{ name: 'mensagens' }"
                  class="rounded-lg border border-rule px-3.5 py-2 text-[13px]">
                  Abrir chat
                </router-link>
                <router-link
                  v-if="c.acoes.includes('ver-confirmacao')"
                  :to="{ name: 'confirmar-servico', params: { id: c.id } }"
                  class="rounded-lg bg-ink px-3.5 py-2 text-[13px] font-semibold text-white">
                  Ver confirmação
                </router-link>
                <button
                  v-if="c.acoes.includes('avaliar')"
                  class="rounded-lg bg-gold px-3.5 py-2 text-[13px] font-semibold text-ink">
                  Avaliar
                </button>
                <button
                  v-if="c.acoes.includes('ver-avaliacao')"
                  class="rounded-lg border border-rule px-3.5 py-2 text-[13px]">
                  Ver avaliação
                </button>
              </div>
            </article>
          </div>
        </template>

        <!-- DADOS -->
        <template v-else-if="aba === 'dados'">
          <div class="mb-5">
            <h1 class="text-xl font-semibold tracking-[-0.01em] md:text-2xl md:tracking-[-0.02em]">
              Dados da conta
            </h1>
            <div class="mt-0.5 text-[13px] text-muted">
              Só você vê essas informações.
            </div>
          </div>

          <div class="rounded-2xl border border-rule bg-surface p-6">
            <!-- Foto: upload direto, independente do "Salvar alterações" -->
            <div class="mb-5 flex items-center gap-4 border-b border-dashed border-rule-soft pb-5">
              <FotoUsuario
                :url="sessao.usuario?.foto_url"
                :nome="sessao.usuario?.nome"
                tamanho="h-16 w-16 text-xl" />
              <div class="flex flex-col gap-1.5">
                <div class="flex items-center gap-3">
                  <label
                    :class="['cursor-pointer rounded-lg border border-ink px-3 py-1.5 text-[13px] font-medium',
                      enviandoFoto ? 'pointer-events-none opacity-60' : '']">
                    {{ enviandoFoto ? 'Enviando…' : sessao.usuario?.foto_url ? 'Trocar foto' : 'Enviar foto' }}
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      class="sr-only"
                      @change="enviarFoto" />
                  </label>
                  <button
                    v-if="sessao.usuario?.foto_url"
                    type="button"
                    class="text-[13px] text-ink-soft underline underline-offset-[3px]"
                    @click="removerFoto">
                    Remover
                  </button>
                </div>
                <span v-if="erroFoto" class="text-[12px] text-red-700">{{ erroFoto }}</span>
                <span v-else class="text-[12px] text-muted">JPG, PNG ou WebP, até 5 MB.</span>
              </div>
            </div>

            <div class="grid gap-4 md:grid-cols-2">
              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">Nome completo</span>
                <input
                  v-model="formNome"
                  class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
              </label>
              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">E-mail</span>
                <input
                  :value="sessao.usuario?.email ?? ''"
                  disabled
                  title="A troca de e-mail ainda não está disponível."
                  class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm text-muted" />
              </label>
              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">Cidade</span>
                <select
                  v-model="formIdcidade"
                  class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm">
                  <option :value="null">—</option>
                  <option v-for="c in cidades" :key="c.idcidade" :value="c.idcidade">
                    {{ rotuloCidade(c) }}
                  </option>
                </select>
              </label>
              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">Telefone</span>
                <input
                  v-model="formTelefone"
                  type="tel"
                  placeholder="(53) 99999-9999"
                  class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
              </label>
            </div>
            <div class="mt-5 flex flex-col items-start justify-between gap-3 border-t border-dashed border-rule-soft pt-4 md:flex-row md:items-center">
              <!-- Exportação LGPD ainda não implementada no backend (GET /conta/exportar). -->
              <a href="#" class="text-[13px] text-ink-soft underline">
                Exportar meus dados · LGPD
              </a>
              <div class="flex items-center gap-3">
                <span
                  v-if="mensagemDados"
                  :class="['text-[13px]', mensagemDados.tipo === 'ok' ? 'text-good' : 'text-red-700']">
                  {{ mensagemDados.texto }}
                </span>
                <button
                  :disabled="salvando"
                  class="rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
                  @click="salvarDados">
                  {{ salvando ? 'Salvando…' : 'Salvar alterações' }}
                </button>
              </div>
            </div>
          </div>
        </template>

        <!-- PREFERÊNCIAS -->
        <template v-else>
          <div class="mb-5">
            <h1 class="text-xl font-semibold tracking-[-0.01em] md:text-2xl md:tracking-[-0.02em]">
              Preferências
            </h1>
            <div class="mt-0.5 text-[13px] text-muted">
              Como quer receber avisos e o que exibir por padrão.
            </div>
          </div>

          <div class="space-y-3 rounded-2xl border border-rule bg-surface p-6">
            <label class="flex items-center justify-between border-b border-rule-soft py-3">
              <span class="text-sm">Notificações por e-mail</span>
              <input
                v-model="notificarEmail"
                type="checkbox"
                @change="salvarPreferencia({ notificar_email: notificarEmail })" />
            </label>
            <label class="flex items-center justify-between py-3">
              <span class="text-sm">Somente prestadores com CNPJ validado</span>
              <input
                v-model="buscaSomenteCnpj"
                type="checkbox"
                @change="salvarPreferencia({ busca_somente_cnpj: buscaSomenteCnpj })" />
            </label>
          </div>
        </template>
      </main>
    </div>
  </div>
</template>
