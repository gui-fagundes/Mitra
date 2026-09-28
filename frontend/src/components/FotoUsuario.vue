<script setup lang="ts">
// Foto redonda do usuário. Sem foto, mostra a inicial do nome sobre o placeholder.
import { computed, ref, watch } from 'vue'
import { urlArquivo } from '../api/client'

const props = defineProps<{
  url: string | null | undefined
  nome?: string | null
  /** Classes de tamanho do Tailwind, ex.: "h-11 w-11". */
  tamanho?: string
}>()

const falhou = ref(false)
watch(
  () => props.url,
  () => (falhou.value = false),
)

const src = computed(() => (falhou.value ? null : urlArquivo(props.url)))
const inicial = computed(() => props.nome?.trim().charAt(0).toUpperCase() ?? '')
</script>

<template>
  <img
    v-if="src"
    :src="src"
    :alt="nome ? `Foto de ${nome}` : 'Foto do usuário'"
    :class="['shrink-0 rounded-full object-cover', tamanho ?? 'h-11 w-11']"
    @error="falhou = true"
  />
  <span
    v-else
    :class="[
      'flex shrink-0 items-center justify-center rounded-full bg-ph font-semibold text-ink-soft',
      tamanho ?? 'h-11 w-11',
    ]"
    aria-hidden="true"
  >
    {{ inicial }}
  </span>
</template>
