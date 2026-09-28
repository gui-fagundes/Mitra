<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { rotuloCidade } from '../api/cidade'
import { contaApi, type ContaAtualizacao, type Usuario } from '../api/conta'
import { useSessaoStore } from '../stores/sessao'
import FormularioDadosConta from '../components/FormularioDadosConta.vue'
import FotoUsuario from '../components/FotoUsuario.vue'
import PublicNav from '../components/PublicNav.vue'
import ListaContratacoes from '../components/ListaContratacoes.vue'

const router = useRouter()
const sessao = useSessaoStore()

type Aba = 'contratacoes' | 'dados' | 'preferencias'
const aba = ref<Aba>('contratacoes')

// Preferências — PATCH /conta (os dados da conta ficam em FormularioDadosConta)
const notificarEmail = ref(true)
const buscaSomenteCnpj = ref(false)

function preencherPreferencias(usuario: Usuario) {
  notificarEmail.value = usuario.notificar_email ?? true
  buscaSomenteCnpj.value = usuario.busca_somente_cnpj ?? false
}

async function salvarPreferencia(dados: ContaAtualizacao) {
  try {
    const usuario = await contaApi.atualizar(dados)
    sessao.definirUsuario(usuario)
    preencherPreferencias(usuario)
  } catch {
    // Volta o checkbox para o valor salvo.
    if (sessao.usuario) preencherPreferencias(sessao.usuario)
  }
}

onMounted(async () => {
  if (sessao.usuario) preencherPreferencias(sessao.usuario)
  try {
    const usuario = await contaApi.obter()
    sessao.definirUsuario(usuario)
    preencherPreferencias(usuario)
  } catch {
    // Mantém o que veio do armazenamento local.
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
          <router-link
            :to="{ name: 'conta-prestador' }"
            class="mt-2 rounded-lg border border-dashed border-rule px-3.5 py-2.5 text-sm text-ink-soft hover:bg-bg">
            {{ sessao.usuario?.e_prestador ? 'Ir para a área do prestador' : 'Quero oferecer serviços' }}
          </router-link>
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
          <ListaContratacoes papel="cliente" />
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

          <FormularioDadosConta />
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
