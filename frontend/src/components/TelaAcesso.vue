<script setup lang="ts">
// Moldura das telas de acesso (esqueci/redefinir senha): mesmo layout do Login —
// painel institucional à esquerda no desktop, formulário centralizado à direita.
import { useRouter } from 'vue-router'
import BrandMark from './BrandMark.vue'

defineProps<{ titulo: string; subtitulo?: string }>()

const router = useRouter()
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

    <!-- Painel esquerdo (só desktop) -->
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

    <!-- Painel direito: conteúdo -->
    <main class="flex flex-1 items-center justify-center px-6 py-8 md:px-16 md:py-16">
      <div class="w-full max-w-[400px] space-y-5">
        <div class="hidden md:block">
          <router-link to="/"><BrandMark size="lg" /></router-link>
        </div>

        <div>
          <h1 class="mb-1 text-[26px] font-semibold tracking-[-0.02em] md:text-[28px]">
            {{ titulo }}
          </h1>
          <p v-if="subtitulo" class="text-sm text-muted">{{ subtitulo }}</p>
        </div>

        <slot />
      </div>
    </main>
  </div>
</template>
