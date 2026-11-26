<script setup lang="ts">
// Destino do link enviado no cadastro (RF-ID-01). Confirma ao abrir; funciona com
// ou sem sessão. Com sessão, atualiza o usuário para a faixa de aviso sumir.
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ErroApi } from '../api/client'
import { contaApi } from '../api/conta'
import TelaAcesso from '../components/TelaAcesso.vue'
import { useSessaoStore } from '../stores/sessao'

const route = useRoute()
const sessao = useSessaoStore()
const token = computed(() => (route.query.token as string | undefined) ?? '')

const estado = ref<'confirmando' | 'confirmado' | 'erro'>('confirmando')
const erro = ref('')
const reenviado = ref(false)

async function reenviar() {
  try {
    await contaApi.reenviarVerificacao()
    reenviado.value = true
  } catch (e) {
    erro.value = e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
  }
}

onMounted(async () => {
  if (!token.value) {
    erro.value = 'Link incompleto. Abra o link exatamente como chegou no e-mail.'
    estado.value = 'erro'
    return
  }
  try {
    await contaApi.verificarEmail(token.value)
    estado.value = 'confirmado'
    if (sessao.logado) sessao.definirUsuario(await contaApi.obter())
  } catch (e) {
    erro.value = e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
    estado.value = 'erro'
  }
})
</script>

<template>
  <TelaAcesso titulo="Confirmação de e-mail">
    <p v-if="estado === 'confirmando'" class="text-sm text-ink-soft">Confirmando…</p>

    <div v-else-if="estado === 'confirmado'" class="space-y-4 rounded-xl border border-rule bg-surface p-5">
      <p class="text-[15px] font-semibold">E-mail confirmado</p>
      <p class="text-sm text-ink-soft">Agora você já pode conversar com clientes e prestadores.</p>
      <router-link
        :to="sessao.logado ? '/buscar' : '/login'"
        class="block h-[46px] rounded-lg bg-gold text-center text-[15px] font-semibold leading-[46px] text-ink"
      >
        {{ sessao.logado ? 'Buscar prestadores' : 'Entrar' }}
      </router-link>
    </div>

    <div v-else class="space-y-3 rounded-xl border border-rule bg-surface p-5">
      <p class="text-[15px] font-semibold">Não foi possível confirmar</p>
      <p class="text-sm text-ink-soft">{{ erro }}</p>
      <template v-if="sessao.logado">
        <p v-if="reenviado" class="text-sm text-good">Enviamos um link novo para {{ sessao.usuario?.email }}.</p>
        <button
          v-else
          type="button"
          class="text-sm text-ink underline underline-offset-[3px]"
          @click="reenviar"
        >
          Enviar um link novo
        </button>
      </template>
      <router-link v-else to="/login" class="block text-sm text-ink underline underline-offset-[3px]">
        Entre na sua conta para pedir um link novo
      </router-link>
    </div>
  </TelaAcesso>
</template>
