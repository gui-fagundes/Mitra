<script setup lang="ts">
/**
 * Barra de navegação superior usada nas páginas públicas e logadas.
 *   - Sem sessão: mostra links de navegação + "Entrar" / "Criar conta".
 *   - Com sessão: mostra "Mensagens (N)" e chip com nome do usuário.
 *
 * A prop `compact` (default true no mobile) esconde os links do meio no mobile.
 */
import { useSessaoStore } from '../stores/sessao'
import BrandMark from './BrandMark.vue'
import FotoUsuario from './FotoUsuario.vue'

const sessao = useSessaoStore()
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
        v-if="!sessao.logado"
        to="/#como-funciona"
        class="text-sm font-medium text-ink-soft hover:text-ink"
        >Como funciona</router-link
      >
      <router-link
        v-if="!sessao.logado"
        to="/register"
        class="text-sm font-medium text-ink-soft hover:text-ink"
        >Sou prestador</router-link
      >
    </nav>

    <!-- Ações à direita -->
    <div class="flex items-center gap-2 md:gap-4">
      <template v-if="!sessao.logado">
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
        <router-link
          :to="{ name: sessao.usuario?.e_prestador ? 'conta-prestador' : 'conta-cliente' }"
          class="flex items-center gap-2 rounded-full border border-rule px-3 py-1.5 hover:bg-bg"
        >
          <FotoUsuario
            :url="sessao.usuario?.foto_url"
            :nome="sessao.usuario?.nome"
            tamanho="h-6 w-6 text-[11px]"
          />
          <span class="hidden text-sm md:inline">{{ sessao.usuario?.nome ?? 'Você' }}</span>
        </router-link>
      </template>
    </div>
  </header>
</template>
