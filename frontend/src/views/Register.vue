<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { cidadeApi, rotuloCidade, type Cidade } from '../api/cidade'
import { contaApi } from '../api/conta'
import { ErroApi } from '../api/client'
import { useSessaoStore } from '../stores/sessao'
import BrandMark from '../components/BrandMark.vue'

const router = useRouter()
const sessao = useSessaoStore()

// O papel ainda não é enviado: passa a valer com o perfil do prestador.
type Papel = 'cliente' | 'prestador' | 'ambos'
const papel = ref<Papel>('cliente')

const nome = ref('')
const email = ref('')
const cidades = ref<Cidade[]>([])
const idcidade = ref<number | null>(null)
const telefone = ref('')
const senha = ref('')
const senha2 = ref('')
const aceito = ref(false)
const loading = ref(false)
const error = ref<string | null>(null)

async function submit() {
  error.value = null
  if (senha.value !== senha2.value) {
    error.value = 'As senhas não coincidem.'
    return
  }
  if (!aceito.value) {
    error.value = 'É preciso aceitar os Termos e a Política de Privacidade.'
    return
  }
  loading.value = true
  try {
    const usuario = await contaApi.cadastrar({
      nome: nome.value,
      email: email.value,
      senha: senha.value,
      aceite_termos: aceito.value,
      idcidade: idcidade.value,
      telefone: telefone.value || null,
    })
    sessao.definirUsuario(usuario)
    router.push('/')
  } catch (e) {
    error.value = e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    cidades.value = await cidadeApi.listar()
    // Piloto em uma cidade só: já vem selecionada.
    idcidade.value = cidades.value[0]?.idcidade ?? null
  } catch {
    // Sem a lista, o cadastro segue sem cidade (campo opcional).
  }
})

const papeis: Array<{ id: Papel; t: string; d: string }> = [
  { id: 'cliente', t: 'Contratar', d: 'Pesquisar, contatar e avaliar prestadores.' },
  { id: 'prestador', t: 'Oferecer', d: 'Criar vitrine, portfólio e receber contatos.' },
  { id: 'ambos', t: 'Os dois', d: 'Uma conta com cliente e prestador ativados.' },
]
</script>

<template>
  <div class="flex min-h-screen flex-col bg-bg md:flex-row">
    <!-- Topo mobile -->
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

    <!-- Painel esquerdo (só desktop) -->
    <aside
      class="hidden bg-surface-2 p-16 md:flex md:w-1/2 md:flex-col md:gap-8"
    >
      <div class="mono">Criar conta no Mitra</div>
      <div>
        <h2 class="mb-4 text-[34px] font-semibold leading-[1.15] tracking-[-0.02em]">
          Uma conta, os dois lados.
        </h2>
        <p class="max-w-[44ch] text-[15px] leading-[1.55] text-ink-soft">
          Você pode contratar um serviço hoje e oferecer o seu amanhã — mesmo
          cadastro, mesmo histórico de reputação.
        </p>
      </div>

      <ul class="flex flex-col gap-3">
        <li
          v-for="b in [
            'Escolha do papel na conta — cliente, prestador ou ambos.',
            'Verificação de CNPJ opcional, com selo visível no perfil.',
            'Seus dados são seus — exportação e exclusão pela LGPD.',
          ]"
          :key="b"
          class="flex items-start gap-3"
        >
          <span
            class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-ink text-[13px] font-semibold"
          >
            <i class="fa fa-check text-[11px]"></i>
          </span>
          <div class="text-[13px] leading-[1.45] text-ink-soft">{{ b }}</div>
        </li>
      </ul>

      <div class="mt-auto text-[12px] text-muted">Piloto em Rio Grande, RS · 2026</div>
    </aside>

    <!-- Formulário -->
    <main class="flex flex-1 justify-center overflow-y-auto px-6 py-8 md:px-20 md:py-14">
      <div class="w-full max-w-[520px] space-y-6">
        <div class="hidden md:block">
          <router-link to="/"><BrandMark size="lg" /></router-link>
        </div>

        <div>
          <h1 class="mb-1 text-[26px] font-semibold tracking-[-0.02em] md:text-[28px]">
            Criar conta
          </h1>
          <p class="text-sm text-muted">
            Escolha como quer usar o Mitra — pode mudar depois.
          </p>
        </div>

        <form class="space-y-6" @submit.prevent="submit">
          <!-- Papel -->
          <fieldset>
            <legend class="mono mb-3 block">Como você vai usar?</legend>
            <div class="grid grid-cols-1 gap-2 md:grid-cols-2">
              <label
                v-for="op in papeis"
                :key="op.id"
                :class="[
                  'flex cursor-pointer gap-3 rounded-xl border p-4 text-left transition-shadow',
                  papel === op.id
                    ? 'border-ink shadow-[inset_0_0_0_1px_var(--color-ink)]'
                    : 'border-rule bg-surface',
                  op.id === 'ambos' ? 'md:col-span-2' : '',
                ]"
              >
                <input
                  v-model="papel"
                  type="radio"
                  :value="op.id"
                  class="sr-only"
                />
                <span
                  :class="[
                    'mt-0.5 h-[18px] w-[18px] shrink-0 rounded-full border',
                    papel === op.id ? 'border-ink bg-ink ring-4 ring-inset ring-bg' : 'border-rule',
                  ]"
                ></span>
                <span>
                  <span class="block text-[15px] font-semibold">{{ op.t }}</span>
                  <span class="mt-0.5 block text-[13px] leading-[1.45] text-muted">
                    {{ op.d }}
                  </span>
                </span>
              </label>
            </div>
          </fieldset>

          <!-- Campos -->
          <div class="grid gap-4 md:grid-cols-2">
            <label class="col-span-full flex flex-col gap-1.5">
              <span class="text-[13px] font-medium text-ink-soft">Nome completo</span>
              <input
                v-model="nome"
                type="text"
                required
                placeholder="Como devemos te chamar"
                class="h-[46px] rounded-lg border border-rule bg-surface px-3 text-[15px] outline-none focus:border-ink"
              />
            </label>

            <label class="col-span-full flex flex-col gap-1.5">
              <span class="text-[13px] font-medium text-ink-soft">E-mail</span>
              <input
                v-model="email"
                type="email"
                required
                autocomplete="email"
                placeholder="voce@exemplo.com"
                class="h-[46px] rounded-lg border border-rule bg-surface px-3 text-[15px] outline-none focus:border-ink"
              />
            </label>

            <label class="flex flex-col gap-1.5">
              <span class="text-[13px] font-medium text-ink-soft">Cidade</span>
              <select
                v-model="idcidade"
                class="h-[46px] appearance-none rounded-lg border border-rule bg-surface px-3 text-[15px] outline-none focus:border-ink"
              >
                <option v-for="c in cidades" :key="c.idcidade" :value="c.idcidade">
                  {{ rotuloCidade(c) }}
                </option>
              </select>
            </label>

            <label class="flex flex-col gap-1.5">
              <span class="text-[13px] font-medium text-ink-soft">
                Telefone (opcional)
              </span>
              <input
                v-model="telefone"
                type="tel"
                placeholder="(53) 99999-9999"
                class="h-[46px] rounded-lg border border-rule bg-surface px-3 text-[15px] outline-none focus:border-ink"
              />
            </label>

            <label class="flex flex-col gap-1.5">
              <span class="text-[13px] font-medium text-ink-soft">Senha</span>
              <input
                v-model="senha"
                type="password"
                required
                minlength="8"
                autocomplete="new-password"
                placeholder="Mínimo 8 caracteres"
                class="h-[46px] rounded-lg border border-rule bg-surface px-3 text-[15px] outline-none focus:border-ink"
              />
            </label>

            <label class="flex flex-col gap-1.5">
              <span class="text-[13px] font-medium text-ink-soft">Confirmar senha</span>
              <input
                v-model="senha2"
                type="password"
                required
                minlength="8"
                placeholder="Repita a senha"
                class="h-[46px] rounded-lg border border-rule bg-surface px-3 text-[15px] outline-none focus:border-ink"
              />
            </label>
          </div>

          <!-- LGPD -->
          <label class="flex items-start gap-2.5 text-[13px] leading-[1.5] text-ink-soft">
            <input v-model="aceito" type="checkbox" class="mt-1" />
            <span>
              Li e concordo com os
              <a href="#" class="text-ink underline">Termos de uso</a>
              e a
              <a href="#" class="text-ink underline">Política de Privacidade</a>
              (LGPD).
            </span>
          </label>

          <button
            type="submit"
            :disabled="loading"
            class="h-[52px] w-full rounded-lg bg-gold text-[15px] font-semibold text-ink transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {{ loading ? 'Cadastrando…' : 'Criar conta' }}
          </button>

          <p v-if="error" class="text-sm text-red-700">{{ error }}</p>
        </form>

        <p class="text-center text-[13px] text-ink-soft">
          Já tem conta?
          <router-link
            to="/login"
            class="font-semibold text-ink underline underline-offset-[3px]"
          >
            Entrar
          </router-link>
        </p>
      </div>
    </main>
  </div>
</template>
