<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../api/auth'
import { useAuthStore } from '../stores/auth'
import PublicNav from '../components/PublicNav.vue'
import StatusBadge from '../components/StatusBadge.vue'
import StarRating from '../components/StarRating.vue'

const router = useRouter()
const auth = useAuthStore()

type Aba = 'contratacoes' | 'dados' | 'preferencias'
const aba = ref<Aba>('contratacoes')

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
    await authApi.logout()
  } finally {
    auth.clearUser()
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
      <div class="ph h-14 w-14 shrink-0 rounded-full"></div>
      <div class="min-w-0 flex-1">
        <div class="text-base font-semibold">{{ auth.user?.nome ?? '[Seu nome]' }}</div>
        <div class="text-xs text-muted">Rio Grande, RS · cliente</div>
      </div>
    </div>

    <!-- Layout desktop: sidebar + main -->
    <div class="md:grid md:min-h-[calc(100vh-72px)] md:grid-cols-[240px_1fr]">
      <!-- Sidebar desktop -->
      <aside class="hidden flex-col gap-6 border-r border-rule-soft bg-surface p-6 md:flex">
        <div class="flex items-center gap-3 px-1.5">
          <div class="ph h-11 w-11 shrink-0 rounded-full"></div>
          <div class="min-w-0">
            <div class="truncate text-sm font-semibold">{{ auth.user?.nome ?? '[Seu nome]' }}</div>
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
            <div class="grid gap-4 md:grid-cols-2">
              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">Nome completo</span>
                <input
                  :value="auth.user?.nome ?? '[Seu nome]'"
                  class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
              </label>
              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">E-mail</span>
                <input
                  :value="auth.user?.email ?? 'voce@exemplo.com'"
                  class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
              </label>
              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">Cidade</span>
                <select class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm">
                  <option>Rio Grande, RS</option>
                </select>
              </label>
              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">Telefone</span>
                <input
                  value="(53) 99999-9999"
                  class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
              </label>
            </div>
            <div class="mt-5 flex flex-col items-start justify-between gap-3 border-t border-dashed border-rule-soft pt-4 md:flex-row md:items-center">
              <a href="#" class="text-[13px] text-ink-soft underline">
                Exportar meus dados · LGPD
              </a>
              <button class="rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-white">
                Salvar alterações
              </button>
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
              <input type="checkbox" checked />
            </label>
            <label class="flex items-center justify-between border-b border-rule-soft py-3">
              <span class="text-sm">Somente prestadores com CNPJ validado</span>
              <input type="checkbox" />
            </label>
            <label class="flex items-center justify-between py-3">
              <span class="text-sm">Manter histórico de buscas</span>
              <input type="checkbox" checked />
            </label>
          </div>
        </template>
      </main>
    </div>
  </div>
</template>
