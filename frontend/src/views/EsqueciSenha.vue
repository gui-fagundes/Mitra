<script setup lang="ts">
import { ref } from 'vue'
import { ErroApi } from '../api/client'
import { contaApi } from '../api/conta'
import TelaAcesso from '../components/TelaAcesso.vue'

const email = ref('')
const enviando = ref(false)
const enviado = ref(false)
const erro = ref<string | null>(null)

async function enviar() {
  erro.value = null
  enviando.value = true
  try {
    await contaApi.esqueciSenha(email.value)
    enviado.value = true
  } catch (e) {
    erro.value = e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <TelaAcesso
    titulo="Esqueci minha senha"
    subtitulo="Informe o e-mail da sua conta e enviaremos um link para criar uma senha nova."
  >
    <!-- A resposta é a mesma exista ou não a conta: não revela quem é cadastrado. -->
    <div v-if="enviado" class="space-y-4 rounded-xl border border-rule bg-surface p-5">
      <p class="text-[15px] font-semibold">Confira seu e-mail</p>
      <p class="text-sm leading-[1.55] text-ink-soft">
        Se houver uma conta com <strong>{{ email }}</strong>, você vai receber um link
        para redefinir a senha. Ele vale por 30 minutos e pode ser usado uma vez.
      </p>
      <p class="text-[13px] text-muted">
        Não chegou? Veja a caixa de spam ou
        <button
          type="button"
          class="text-ink underline underline-offset-[3px]"
          @click="enviado = false"
        >
          tente de novo</button
        >.
      </p>
    </div>

    <form v-else class="space-y-5" @submit.prevent="enviar">
      <label class="block">
        <span class="mb-1.5 block text-[13px] font-medium text-ink-soft">E-mail</span>
        <input
          v-model="email"
          type="email"
          required
          autocomplete="email"
          placeholder="voce@exemplo.com"
          class="h-[46px] w-full rounded-lg border border-rule bg-surface px-3 text-[15px] outline-none focus:border-ink"
        />
      </label>

      <button
        type="submit"
        :disabled="enviando"
        class="h-[50px] w-full rounded-lg bg-gold text-[15px] font-semibold text-ink transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {{ enviando ? 'Enviando…' : 'Enviar link' }}
      </button>

      <p v-if="erro" class="text-sm text-red-700">{{ erro }}</p>
    </form>

    <router-link
      to="/login"
      class="block text-center text-[13px] text-ink-soft underline underline-offset-[3px]"
    >
      Voltar para o login
    </router-link>
  </TelaAcesso>
</template>
