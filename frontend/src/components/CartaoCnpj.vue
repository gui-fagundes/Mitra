<script setup lang="ts">
// CNPJ do prestador (RF-ID-07). Só é gravado se a Receita, via BrasilAPI, confirmar
// que está ativo — então ter CNPJ cadastrado já significa ter o selo.
import { ref } from 'vue'
import { ErroApi } from '../api/client'
import { prestadorApi, type Vitrine } from '../api/prestador'
import { formatarCnpj, formatarData } from '../utils/formatacao'

const vitrine = defineModel<Vitrine>({ required: true })

const cnpj = ref('')
const trocando = ref(false)
const consultando = ref(false)
const erro = ref<string | null>(null)

function textoDoErro(e: unknown): string {
  return e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
}

async function validar() {
  erro.value = null
  consultando.value = true
  try {
    vitrine.value = await prestadorApi.cadastrarCnpj(cnpj.value)
    cnpj.value = ''
    trocando.value = false
  } catch (e) {
    erro.value = textoDoErro(e)
  } finally {
    consultando.value = false
  }
}

async function remover() {
  if (!confirm('Remover o CNPJ? O selo sai do seu perfil público.')) return
  erro.value = null
  try {
    vitrine.value = await prestadorApi.removerCnpj()
  } catch (e) {
    erro.value = textoDoErro(e)
  }
}
</script>

<template>
  <section class="mt-6 rounded-2xl border border-rule bg-surface p-6">
    <div class="mb-1 text-base font-semibold">CNPJ e selo de verificação</div>
    <p class="mb-4 max-w-[60ch] text-[13px] leading-[1.55] text-muted">
      Consultamos a Receita Federal na hora. Com o CNPJ ativo, seu perfil ganha o selo
      dourado "CNPJ validado". O número em si não aparece para o público.
    </p>

    <div
      v-if="vitrine.cnpj && !trocando"
      class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gold-soft text-gold-ink">
          <i class="fa fa-check"></i>
        </div>
        <div>
          <div class="num text-[15px] font-semibold">{{ formatarCnpj(vitrine.cnpj) }}</div>
          <div class="text-[12px] text-muted">
            Ativo na Receita · validado em {{ vitrine.cnpj_validado_em ? formatarData(vitrine.cnpj_validado_em) : '—' }}
          </div>
        </div>
      </div>
      <div class="flex gap-3 text-[13px]">
        <button type="button" class="text-ink-soft underline underline-offset-[3px]" @click="trocando = true">
          Trocar CNPJ
        </button>
        <button type="button" class="text-ink-soft underline underline-offset-[3px]" @click="remover">
          Remover
        </button>
      </div>
    </div>

    <form v-else class="flex flex-col gap-2 md:flex-row md:items-start" @submit.prevent="validar">
      <input
        v-model="cnpj"
        required
        minlength="14"
        maxlength="18"
        placeholder="00.000.000/0000-00"
        autocomplete="off"
        class="num h-11 rounded-lg border borda-campo bg-bg px-3 text-sm uppercase outline-none md:w-64" />
      <button
        type="submit"
        :disabled="consultando"
        class="h-11 rounded-lg bg-ink px-4 text-sm font-semibold text-white disabled:opacity-60">
        {{ consultando ? 'Consultando a Receita…' : 'Validar na Receita' }}
      </button>
      <button
        v-if="trocando"
        type="button"
        class="h-11 px-2 text-[13px] text-ink-soft underline underline-offset-[3px]"
        @click="trocando = false; erro = null">
        Cancelar
      </button>
    </form>

    <p v-if="erro" class="mt-3 text-sm text-red-700">{{ erro }}</p>
  </section>
</template>
