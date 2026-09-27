<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PublicNav from '../components/PublicNav.vue'

const route = useRoute()
const router = useRouter()

type Conversa = {
  id: number
  nome: string
  online: boolean
  ultimaMsg: string
  quando: string
  contexto?: { servico: string; combinado: string }
}

const conversas: Conversa[] = [
  {
    id: 1,
    nome: '[Prestador]',
    online: true,
    ultimaMsg: 'Serviço concluído! Deixei…',
    quando: 'agora',
    contexto: { servico: 'Instalação elétrica', combinado: '18/09' },
  },
  {
    id: 2,
    nome: '[Professora L.]',
    online: false,
    ultimaMsg: 'Podemos remarcar para quinta?',
    quando: '2h',
  },
  {
    id: 3,
    nome: '[Adestrador R.]',
    online: false,
    ultimaMsg: 'Obrigado pelo retorno.',
    quando: '5d',
  },
]

const conversaId = ref<number>(Number(route.params.id) || conversas[0].id)
const conversaAtiva = computed(
  () => conversas.find((c) => c.id === conversaId.value) ?? conversas[0],
)

// Mock de mensagens da conversa ativa
type Mensagem = { texto: string; enviada: boolean; hora: string; grupo?: string }
const mensagens: Mensagem[] = [
  { texto: 'Olá! Vi seu contato pelo Mitra. Preciso instalar dois pontos de tomada na cozinha.', enviada: true, hora: '09:12', grupo: 'Hoje · 09:12' },
  { texto: 'Boa tarde! Consigo passar aí amanhã à tarde para orçar. Serve das 14h?', enviada: false, hora: '09:34' },
  { texto: 'Perfeito, 14h está ótimo. Endereço: Rua X, 123.', enviada: true, hora: '09:36' },
  { texto: 'Passei aí, cheguei bem. O orçamento fica R$ 240 pelos dois pontos, com material.', enviada: false, hora: '15:40', grupo: 'Ontem' },
  { texto: 'Fechado. Consegue vir dia 18 então?', enviada: true, hora: '16:02' },
  { texto: 'Serviço concluído! Deixei a nota fiscal por e-mail. Se puder confirmar aí no Mitra 🙏', enviada: false, hora: '11:20', grupo: 'Hoje · agora' },
]

const novaMsg = ref('')

function enviar() {
  if (!novaMsg.value.trim()) return
  mensagens.push({ texto: novaMsg.value, enviada: true, hora: 'agora' })
  novaMsg.value = ''
}

function abrirConfirmacao() {
  router.push({ name: 'confirmar-servico', params: { id: conversaId.value } })
}
</script>

<template>
  <div class="min-h-screen bg-bg">
    <div class="hidden md:block"><PublicNav /></div>

    <!-- Layout desktop: lista + conversa -->
    <div class="hidden md:grid md:h-[calc(100vh-72px)] md:grid-cols-[280px_1fr]">
      <!-- Lista lateral -->
      <aside class="flex flex-col border-r border-rule-soft bg-surface">
        <div class="border-b border-rule-soft px-4 py-3.5 text-[15px] font-semibold">
          Mensagens
        </div>
        <div class="flex-1 overflow-y-auto">
          <button
            v-for="c in conversas"
            :key="c.id"
            :class="['flex w-full items-center gap-2.5 border-b border-rule-soft px-3.5 py-3 text-left',
              c.id === conversaAtiva.id
                ? 'bg-bg shadow-[inset_3px_0_0_var(--color-ink)]'
                : 'hover:bg-bg']"
            @click="conversaId = c.id">
            <div class="ph h-9 w-9 shrink-0 rounded-full"></div>
            <div class="min-w-0 flex-1">
              <div class="flex justify-between text-[13px] font-semibold">
                <span class="truncate">{{ c.nome }}</span>
                <span class="text-[10px] font-normal text-muted">{{ c.quando }}</span>
              </div>
              <div class="truncate text-xs text-muted">{{ c.ultimaMsg }}</div>
            </div>
          </button>
        </div>
      </aside>

      <!-- Conversa ativa -->
      <div class="flex flex-col bg-surface">
        <!-- Header -->
        <div class="flex items-center gap-3 border-b border-rule-soft px-5 py-3">
          <div class="ph h-9 w-9 shrink-0 rounded-full"></div>
          <div class="min-w-0 flex-1">
            <div class="text-sm font-semibold">{{ conversaAtiva.nome }}</div>
            <div v-if="conversaAtiva.online" class="text-[11px] text-good">● Online</div>
            <div v-else class="text-[11px] text-muted">Offline</div>
          </div>
          <a href="#" class="text-xs text-ink-soft underline">Ver perfil</a>
        </div>

        <!-- Banner contexto -->
        <div
          v-if="conversaAtiva.contexto"
          class="flex items-center justify-between gap-3 border-b border-rule-soft bg-gold-soft px-5 py-2.5 text-[12px] text-gold-ink">
          <div>
            <strong>{{ conversaAtiva.contexto.servico }}</strong> · pronto para confirmar
          </div>
          <button class="font-semibold underline" @click="abrirConfirmacao">
            Confirmar
          </button>
        </div>

        <!-- Mensagens -->
        <div class="flex flex-1 flex-col gap-1.5 overflow-y-auto p-4">
          <template v-for="(m, i) in mensagens" :key="i">
            <div v-if="m.grupo" class="my-1 text-center text-[10px] text-muted">
              {{ m.grupo }}
            </div>
            <div
              :class="[
                'max-w-[82%] px-3 py-2 text-[13px] leading-[1.45]',
                m.enviada
                  ? 'self-end rounded-[14px_14px_4px_14px] bg-ink text-white'
                  : 'self-start rounded-[14px_14px_14px_4px] border border-rule-soft bg-bg text-ink',
              ]">
              {{ m.texto }}
            </div>
          </template>
        </div>

        <!-- Composer -->
        <div class="flex items-end gap-2 border-t border-rule-soft px-3 py-2.5">
          <button
            aria-label="Anexar"
            class="flex h-9 w-9 items-center justify-center rounded-lg border border-rule bg-bg">
            <i class="fa fa-plus"></i>
          </button>
          <textarea
            v-model="novaMsg"
            rows="1"
            placeholder="Escrever mensagem…"
            class="flex-1 resize-none rounded-lg border border-rule bg-bg px-3 py-2 text-[13px] font-sans"
            @keydown.enter.exact.prevent="enviar"></textarea>
          <button
            aria-label="Enviar"
            class="flex h-9 w-9 items-center justify-center rounded-lg bg-gold text-ink font-semibold hover:opacity-90"
            @click="enviar">
            <i class="fa fa-paper-plane"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Layout mobile: tela cheia da conversa ativa -->
    <div class="flex min-h-screen flex-col md:hidden">
      <!-- Top bar -->
      <div class="flex items-center gap-3 border-b border-rule-soft bg-surface px-4 py-3">
        <button
          aria-label="Voltar"
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-rule bg-surface"
          @click="router.back()">
          <i class="fa fa-arrow-left"></i>
        </button>
        <div class="ph h-10 w-10 shrink-0 rounded-full"></div>
        <div class="min-w-0 flex-1">
          <div class="text-[15px] font-semibold">{{ conversaAtiva.nome }}</div>
          <div v-if="conversaAtiva.online" class="text-xs text-good">● Online agora</div>
        </div>
        <button
          aria-label="Mais"
          class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-rule bg-surface">
          <i class="fa fa-ellipsis-h"></i>
        </button>
      </div>

      <!-- Banner contexto -->
      <div
        v-if="conversaAtiva.contexto"
        class="flex items-center justify-between gap-3 border-b border-rule-soft bg-gold-soft px-4 py-2.5 text-xs text-gold-ink">
        <div>
          <strong>{{ conversaAtiva.contexto.servico }}</strong>
          · combinado dia {{ conversaAtiva.contexto.combinado }}
        </div>
        <button class="font-semibold underline" @click="abrirConfirmacao">
          Confirmar
        </button>
      </div>

      <!-- Mensagens -->
      <div class="flex flex-1 flex-col gap-2 overflow-y-auto p-4">
        <template v-for="(m, i) in mensagens" :key="i">
          <div v-if="m.grupo" class="my-1 text-center text-[10px] text-muted">
            {{ m.grupo }}
          </div>
          <div
            :class="[
              'max-w-[78%] px-3.5 py-2.5 text-sm leading-[1.45]',
              m.enviada
                ? 'self-end rounded-[14px_14px_4px_14px] bg-ink text-white'
                : 'self-start rounded-[14px_14px_14px_4px] border border-rule-soft bg-surface',
            ]">
            {{ m.texto }}
          </div>
        </template>
      </div>

      <!-- Composer -->
      <div class="flex items-end gap-2 border-t border-rule bg-surface px-3 py-3">
        <button
          aria-label="Anexar"
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-rule bg-bg">
          <i class="fa fa-plus"></i>
        </button>
        <textarea
          v-model="novaMsg"
          rows="1"
          placeholder="Escrever mensagem…"
          class="flex-1 resize-none rounded-lg border border-rule bg-bg px-3.5 py-3 text-sm font-sans"
          @keydown.enter.exact.prevent="enviar"></textarea>
        <button
          aria-label="Enviar"
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-gold text-ink font-semibold hover:opacity-90"
          @click="enviar">
          <i class="fa fa-paper-plane"></i>
        </button>
      </div>
    </div>
  </div>
</template>
