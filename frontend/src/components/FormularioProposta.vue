<script setup lang="ts">
// Proposta de prestação: criar (dentro da conversa) ou editar (enquanto em negociação).
import { computed, onMounted, ref } from 'vue'
import type { Contratacao, PropostaEntrada } from '../api/contratacao'
import { prestadorApi } from '../api/prestador'
import { taxonomiaApi, type Categoria, type Servico } from '../api/taxonomia'

const props = defineProps<{
  /** Prestador da conversa: os serviços dele aparecem primeiro. */
  idprestador: number
  /** Ao editar, os valores atuais. */
  atual?: Contratacao | null
  enviando?: boolean
}>()

const emit = defineEmits<{ salvar: [dados: PropostaEntrada]; cancelar: [] }>()

const categorias = ref<Categoria[]>([])
const servicosDoPrestador = ref<Servico[]>([])

const idservico = ref<number | ''>(props.atual?.servico.idservico ?? '')
const descricao = ref(props.atual?.descricao ?? '')
const local = ref(props.atual?.local ?? '')
const dataPrevista = ref(props.atual?.data_prevista ?? '')
const valorEstimado = ref<number | ''>(props.atual?.valor_estimado ?? '')

const idsDoPrestador = computed(() => new Set(servicosDoPrestador.value.map((s) => s.idservico)))

onMounted(async () => {
  const [lista, perfil] = await Promise.allSettled([
    taxonomiaApi.listarCategorias(),
    prestadorApi.obterPublico(props.idprestador),
  ])
  if (lista.status === 'fulfilled') categorias.value = lista.value
  if (perfil.status === 'fulfilled') {
    servicosDoPrestador.value = perfil.value.servicos
    if (idservico.value === '' && perfil.value.servicos.length === 1) {
      idservico.value = perfil.value.servicos[0].idservico
    }
  }
})

function salvar() {
  if (idservico.value === '' || !descricao.value.trim()) return
  emit('salvar', {
    idservico: Number(idservico.value),
    descricao: descricao.value.trim(),
    local: local.value.trim() || null,
    data_prevista: dataPrevista.value || null,
    valor_estimado: valorEstimado.value === '' ? null : Number(valorEstimado.value),
  })
}
</script>

<template>
  <form class="grid gap-3 md:grid-cols-2" @submit.prevent="salvar">
    <label class="flex flex-col gap-1 md:col-span-2">
      <span class="mono-sm">Serviço</span>
      <select
        v-model="idservico"
        required
        class="h-10 rounded-lg border borda-campo bg-bg px-2.5 text-sm outline-none">
        <option value="" disabled>Escolha o serviço</option>
        <optgroup v-if="servicosDoPrestador.length" label="Serviços que o prestador atende">
          <option v-for="s in servicosDoPrestador" :key="`p-${s.idservico}`" :value="s.idservico">
            {{ s.nome }}
          </option>
        </optgroup>
        <optgroup v-for="c in categorias" :key="c.idcategoria" :label="c.nome">
          <option
            v-for="s in c.servicos.filter((s) => !idsDoPrestador.has(s.idservico))"
            :key="s.idservico"
            :value="s.idservico">
            {{ s.nome }}
          </option>
        </optgroup>
      </select>
    </label>

    <label class="flex flex-col gap-1 md:col-span-2">
      <span class="mono-sm">O que vai ser feito</span>
      <textarea
        v-model="descricao"
        required
        rows="3"
        maxlength="2000"
        placeholder="Ex.: trocar duas tomadas da cozinha, com material."
        class="resize-y rounded-lg border borda-campo bg-bg px-2.5 py-2 font-sans text-sm outline-none"></textarea>
    </label>

    <label class="flex flex-col gap-1">
      <span class="mono-sm">Onde</span>
      <input
        v-model="local"
        maxlength="255"
        placeholder="Bairro ou endereço"
        class="h-10 rounded-lg border borda-campo bg-bg px-2.5 text-sm outline-none" />
    </label>
    <label class="flex flex-col gap-1">
      <span class="mono-sm">Quando (previsão)</span>
      <input
        v-model="dataPrevista"
        type="date"
        class="h-10 rounded-lg border borda-campo bg-bg px-2.5 text-sm outline-none" />
    </label>

    <label class="flex flex-col gap-1">
      <span class="mono-sm">Valor estimado (R$)</span>
      <input
        v-model.number="valorEstimado"
        type="number"
        min="0"
        step="0.01"
        placeholder="Orçamento ou budget"
        class="h-10 rounded-lg border borda-campo bg-bg px-2.5 text-sm outline-none" />
    </label>

    <div class="flex items-end justify-end gap-2">
      <button type="button" class="h-10 px-3 text-[13px] text-ink-soft underline" @click="emit('cancelar')">
        Voltar
      </button>
      <button
        type="submit"
        :disabled="enviando"
        class="h-10 rounded-lg bg-gold px-4 text-sm font-semibold text-ink hover:opacity-90 disabled:opacity-60">
        {{ enviando ? 'Enviando…' : atual ? 'Salvar nova versão' : 'Enviar proposta' }}
      </button>
    </div>
  </form>
</template>
