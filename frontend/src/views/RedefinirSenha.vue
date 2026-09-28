<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ErroApi } from '../api/client'
import { contaApi } from '../api/conta'
import TelaAcesso from '../components/TelaAcesso.vue'

const route = useRoute()
const token = computed(() => (route.query.token as string | undefined) ?? '')

const senha = ref('')
const senha2 = ref('')
const salvando = ref(false)
const concluido = ref(false)
const erro = ref<string | null>(null)

async function redefinir() {
  erro.value = null
  if (senha.value !== senha2.value) {
    erro.value = 'As senhas não coincidem.'
    return
  }
  salvando.value = true
  try {
    await contaApi.redefinirSenha(token.value, senha.value)
    concluido.value = true
  } catch (e) {
    erro.value = e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
  } finally {
    salvando.value = false
  }
}
</script>

<template>
  <TelaAcesso titulo="Criar senha nova" subtitulo="Escolha a nova senha da sua conta.">
    <div v-if="concluido" class="space-y-4 rounded-xl border border-rule bg-surface p-5">
      <p class="text-[15px] font-semibold">Senha alterada</p>
      <p class="text-sm text-ink-soft">Já pode entrar no Mitra com a senha nova.</p>
      <router-link
        to="/login"
        class="block h-[46px] rounded-lg bg-gold text-center text-[15px] font-semibold leading-[46px] text-ink"
      >
        Entrar
      </router-link>
    </div>

    <div v-else-if="!token" class="space-y-3 rounded-xl border border-rule bg-surface p-5">
      <p class="text-[15px] font-semibold">Link incompleto</p>
      <p class="text-sm text-ink-soft">
        Abra o link exatamente como chegou no e-mail, ou peça um novo.
      </p>
      <router-link to="/esqueci-senha" class="text-sm text-ink underline underline-offset-[3px]">
        Pedir um novo link
      </router-link>
    </div>

    <form v-else class="space-y-5" @submit.prevent="redefinir">
      <label class="block">
        <span class="mb-1.5 block text-[13px] font-medium text-ink-soft">Nova senha</span>
        <input
          v-model="senha"
          type="password"
          required
          minlength="8"
          autocomplete="new-password"
          placeholder="Mínimo 8 caracteres"
          class="h-[46px] w-full rounded-lg border border-rule bg-surface px-3 text-[15px] outline-none focus:border-ink"
        />
      </label>

      <label class="block">
        <span class="mb-1.5 block text-[13px] font-medium text-ink-soft">Repita a senha</span>
        <input
          v-model="senha2"
          type="password"
          required
          minlength="8"
          autocomplete="new-password"
          placeholder="Repita a senha"
          class="h-[46px] w-full rounded-lg border border-rule bg-surface px-3 text-[15px] outline-none focus:border-ink"
        />
      </label>

      <button
        type="submit"
        :disabled="salvando"
        class="h-[50px] w-full rounded-lg bg-gold text-[15px] font-semibold text-ink transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {{ salvando ? 'Salvando…' : 'Salvar senha nova' }}
      </button>

      <div v-if="erro" class="space-y-1">
        <p class="text-sm text-red-700">{{ erro }}</p>
        <router-link
          to="/esqueci-senha"
          class="text-[13px] text-ink underline underline-offset-[3px]"
        >
          Pedir um novo link
        </router-link>
      </div>
    </form>
  </TelaAcesso>
</template>
