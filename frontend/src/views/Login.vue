<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../api/auth'
import { ApiError } from '../api/client'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const senha = ref('')
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
  <div class="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-800/50">
    <h1 class="mb-6 text-2xl font-semibold text-slate-900 dark:text-white">Entrar</h1>

    <form class="flex flex-col gap-4" @submit.prevent="submit">
      <label class="flex flex-col gap-1.5 text-sm text-slate-900 dark:text-slate-100">
        Email
        <input
          v-model="email"
          type="email"
          required
          autocomplete="email"
          class="rounded-md border border-slate-300 bg-white px-3 py-2 text-base text-slate-900 focus:border-transparent focus:outline-2 focus:outline-accent dark:border-slate-700 dark:bg-slate-900 dark:text-white"
        />
      </label>

      <label class="flex flex-col gap-1.5 text-sm text-slate-900 dark:text-slate-100">
        Senha
        <input
          v-model="senha"
          type="password"
          required
          minlength="8"
          autocomplete="current-password"
          class="rounded-md border border-slate-300 bg-white px-3 py-2 text-base text-slate-900 focus:border-transparent focus:outline-2 focus:outline-accent dark:border-slate-700 dark:bg-slate-900 dark:text-white"
        />
      </label>

      <button
        type="submit"
        :disabled="loading"
        class="rounded-md bg-accent px-4 py-2.5 font-medium text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {{ loading ? 'Entrando...' : 'Entrar' }}
      </button>

      <p v-if="error" class="m-0 text-sm text-red-600 dark:text-red-400">{{ error }}</p>
    </form>

    <p class="mt-4 text-center text-sm">
      Não tem conta?
      <router-link to="/register" class="text-accent hover:underline">Cadastre-se</router-link>
    </p>
  </div>
</template>
