<script setup lang="ts">
/**
 * Barra de navegação superior usada nas páginas públicas e logadas.
 *   - Sem sessão: mostra links de navegação + "Entrar" / "Criar conta".
 *   - Com sessão: mostra "Mensagens (N)" e chip com nome do usuário.
 *
 * A prop `compact` (default true no mobile) esconde os links do meio no mobile.
 */
import { useAuthStore } from '../stores/auth'
import BrandMark from './BrandMark.vue'

const auth = useAuthStore()
</script>

<template>
  <header
    class="flex items-center justify-between border-b border-rule-soft bg-surface px-5 py-4 md:px-16"
  >
    <router-link to="/" class="focus:outline-none">
      <BrandMark size="lg" class="hidden md:flex" />
      <BrandMark size="sm" class="flex md:hidden" />
    </router-link>

    <!-- Links do meio (só desktop) -->
    <nav class="hidden items-center gap-8 md:flex">
      <router-link to="/buscar" class="text-sm font-medium text-ink-soft hover:text-ink"
        >Buscar</router-link
      >
      <router-link
        v-if="!auth.isLogged"
        to="/#como-funciona"
        class="text-sm font-medium text-ink-soft hover:text-ink"
        >Como funciona</router-link
      >
      <router-link
        v-if="!auth.isLogged"
        to="/register"
        class="text-sm font-medium text-ink-soft hover:text-ink"
        >Sou prestador</router-link
      >
    </nav>

    <!-- Ações à direita -->
    <div class="flex items-center gap-2 md:gap-4">
      <template v-if="!auth.isLogged">
        <router-link
          to="/login"
          class="rounded-lg border border-rule px-3 py-1.5 text-sm font-medium md:px-4 md:py-2"
        >
          Entrar
        </router-link>
        <router-link
          to="/register"
          class="hidden rounded-lg bg-ink px-4 py-2 text-sm font-medium text-white md:inline-block"
        >
          Criar conta
        </router-link>
      </template>
      <template v-else>
        <router-link
          to="/mensagens"
          class="text-sm font-medium text-ink-soft hover:text-ink"
          aria-label="Mensagens"
        >
          <i class="fa fa-envelope-o mr-1"></i>
          <span class="hidden md:inline">Mensagens</span>
        </router-link>
        <div class="flex items-center gap-2 rounded-full border border-rule px-3 py-1.5">
          <span class="h-6 w-6 rounded-full bg-ph"></span>
          <span class="hidden text-sm md:inline">{{ auth.user?.nome ?? 'Você' }}</span>
        </div>
      </template>
    </div>
  </header>
</template>
