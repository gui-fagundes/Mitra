<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../api/auth'
import { ApiError } from '../api/client'
import { useAuthStore } from '../stores/auth'
import BrandMark from '../components/BrandMark.vue'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const senha = ref('')
const manterConectado = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)

async function submit() {
  error.value = null
  loading.value = true
  try {
    const user = await authApi.login(email.value, senha.value)
    auth.setUser(user)
    router.push('/')
  } catch (e) {
    error.value = e instanceof ApiError ? e.detail : 'Erro inesperado'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen flex-col bg-bg md:flex-row">
    <!-- Barra topo mobile -->
    <div
      class="flex items-center justify-between border-b border-rule-soft px-5 py-3.5 md:hidden"
    >
      <button
        type="button"
        aria-label="Voltar"
        class="flex h-9 w-9 items-center justify-center rounded-lg border border-rule bg-surface"
        @click="router.back()"
      >
        <i class="fa fa-arrow-left"></i>
      </button>
      <router-link to="/">
        <BrandMark />
      </router-link>
      <div class="w-9"></div>
    </div>

    <!-- Painel esquerdo (só desktop): posicionamento do Mitra -->
    <aside
      class="hidden bg-surface-2 p-16 md:flex md:w-1/2 md:flex-col md:justify-between"
    >
      <div class="mono">Mitra · plataforma de serviços</div>
      <div>
        <h2 class="mb-3 text-[34px] font-semibold leading-[1.15] tracking-[-0.02em]">
          O prestador aparece por conta do trabalho — não do orçamento.
        </h2>
        <p class="max-w-[44ch] text-[15px] leading-[1.55] text-ink-soft">
          Ordenação orgânica por reputação, atividade e proximidade. Sem posições
          vendidas.
        </p>
      </div>
      <div class="text-[12px] text-muted">Piloto em Rio Grande, RS</div>
    </aside>

    <!-- Painel direito: formulário -->
    <main class="flex flex-1 items-center justify-center px-6 py-8 md:px-16 md:py-16">
      <div class="w-full max-w-[400px] space-y-5">
        <div class="hidden md:block">
          <router-link to="/"><BrandMark size="lg" /></router-link>
        </div>

        <div>
          <h1 class="mb-1 text-[26px] font-semibold tracking-[-0.02em] md:text-[28px]">
            Entrar no Mitra
          </h1>
          <p class="text-sm text-muted">Use seu e-mail e senha cadastrados.</p>
        </div>

        <form class="space-y-5" @submit.prevent="submit">
          <label class="block">
            <span class="mb-1.5 block text-[13px] font-medium text-ink-soft">
              E-mail
            </span>
            <input
              v-model="email"
              type="email"
              required
              autocomplete="email"
              placeholder="voce@exemplo.com"
              class="h-[46px] w-full rounded-lg border border-rule bg-surface px-3 text-[15px] outline-none focus:border-ink"
            />
          </label>

          <label class="block">
            <div class="mb-1.5 flex items-center justify-between">
              <span class="text-[13px] font-medium text-ink-soft">Senha</span>
              <a
                href="#"
                class="text-xs text-ink-soft underline underline-offset-[3px]"
                @click.prevent
              >
                Esqueci minha senha
              </a>
            </div>
            <input
              v-model="senha"
              type="password"
              required
              minlength="8"
              autocomplete="current-password"
              placeholder="••••••••"
              class="h-[46px] w-full rounded-lg border border-rule bg-surface px-3 text-[15px] outline-none focus:border-ink"
            />
          </label>

          <label class="flex items-center gap-2 text-[13px] text-ink-soft">
            <input v-model="manterConectado" type="checkbox" />
            Manter-me conectado neste dispositivo
          </label>

          <button
            type="submit"
            :disabled="loading"
            class="h-[50px] w-full rounded-lg bg-gold text-[15px] font-semibold text-ink transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {{ loading ? 'Entrando…' : 'Entrar' }}
          </button>

          <p v-if="error" class="text-sm text-red-700">{{ error }}</p>
        </form>

        <div class="flex items-center gap-3">
          <span class="h-px flex-1 bg-rule"></span>
          <span class="mono-sm">ou</span>
          <span class="h-px flex-1 bg-rule"></span>
        </div>

        <router-link
          to="/register"
          class="block rounded-lg border border-ink py-3.5 text-center text-sm font-semibold"
        >
          Criar uma conta nova
        </router-link>

        <p class="pt-2 text-center text-[11px] text-muted">
          Ao entrar você concorda com os Termos e a Política de Privacidade.
        </p>
      </div>
    </main>
  </div>
</template>
