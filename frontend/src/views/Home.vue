<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../api/auth'
import { ApiError } from '../api/client'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const me = await authApi.me()
    auth.setUser(me)
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) {
      auth.clearUser()
      router.push('/login')
      return
    }
    error.value = e instanceof ApiError ? e.detail : 'Erro inesperado'
  }
})

async function logout() {
  try {
    await authApi.logout()
  } finally {
    auth.clearUser()
    router.push('/login')
  }
}
</script>

<template>
  <div class="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-800/50">
    <h1 class="mb-6 text-2xl font-semibold text-slate-900 dark:text-white">
      Bem-vindo{{ auth.user ? `, ${auth.user.nome}` : '' }}
    </h1>

    <pre
      v-if="auth.user"
      class="mb-4 overflow-x-auto rounded-md bg-slate-100 p-3 font-mono text-xs text-slate-900 dark:bg-slate-900 dark:text-slate-100"
    >{{ JSON.stringify(auth.user, null, 2) }}</pre>

    <p v-if="error" class="mb-4 text-sm text-red-600 dark:text-red-400">{{ error }}</p>

    <button
      class="rounded-md bg-accent px-4 py-2.5 font-medium text-white transition-opacity hover:opacity-90"
      @click="logout"
    >
      Sair
    </button>
  </div>
</template>
