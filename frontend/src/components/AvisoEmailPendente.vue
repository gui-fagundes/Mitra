<script setup lang="ts">
// Faixa no topo de todas as telas enquanto o e-mail da conta não foi confirmado
// (RF-ID-01). Sem confirmar, a API recusa iniciar contato e mandar mensagens.
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ErroApi } from '../api/client'
import { contaApi } from '../api/conta'
import { useSessaoStore } from '../stores/sessao'

const sessao = useSessaoStore()
const route = useRoute()

const estado = ref<'parado' | 'enviando' | 'enviado' | 'erro'>('parado')
const erro = ref('')

// `=== null`: um usuário guardado antes deste campo existir (undefined) não vê a faixa
// até a sessão ser atualizada.
const pendente = computed(
  () => sessao.usuario?.email_verificado_em === null && route.name !== 'verificar-email',
)

async function reenviar() {
  estado.value = 'enviando'
  try {
    await contaApi.reenviarVerificacao()
    estado.value = 'enviado'
  } catch (e) {
    if (e instanceof ErroApi && e.status === 409) {
      // Já confirmado em outro lugar: atualiza a sessão e a faixa some.
      sessao.definirUsuario(await contaApi.obter())
      return
    }
    erro.value = e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
    estado.value = 'erro'
  }
}

onMounted(async () => {
  // O usuário em cache pode estar desatualizado (ex.: confirmou pelo celular).
  if (!pendente.value) return
  try {
    sessao.definirUsuario(await contaApi.obter())
  } catch {
    // Sem rede ou sessão expirada: mantém o que há.
  }
})
</script>

<template>
  <div
    v-if="pendente"
    role="status"
    class="flex flex-col gap-2 border-b border-rule bg-gold-soft px-5 py-2.5 text-[13px] text-ink md:flex-row md:items-center md:justify-between md:px-16"
  >
    <span>
      <i class="fa fa-envelope-o mr-1.5"></i>
      Confirme seu e-mail para enviar mensagens. Enviamos um link para
      <strong>{{ sessao.usuario?.email }}</strong>.
    </span>
    <span class="flex items-center gap-3">
      <span v-if="estado === 'enviado'" class="text-good">Link reenviado. Confira a caixa de entrada e o spam.</span>
      <span v-else-if="estado === 'erro'" class="text-red-700">{{ erro }}</span>
      <button
        v-if="estado !== 'enviado'"
        type="button"
        :disabled="estado === 'enviando'"
        class="font-medium underline underline-offset-[3px] disabled:opacity-60"
        @click="reenviar"
      >
        {{ estado === 'enviando' ? 'Enviando…' : 'Reenviar e-mail' }}
      </button>
    </span>
  </div>
</template>
