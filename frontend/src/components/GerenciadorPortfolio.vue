<script setup lang="ts">
// Portfólio na área do prestador: enviar, legendar, remover e reordenar
// (arrastando ou pelos botões ◀ ▶, que também servem no celular e no teclado).
import { computed, ref } from 'vue'
import { ErroApi, urlArquivo } from '../api/client'
import { LIMITE_PORTFOLIO, prestadorApi, type ItemPortfolio } from '../api/prestador'

const itens = defineModel<ItemPortfolio[]>({ required: true })

const enviando = ref(0)
const erros = ref<string[]>([])
const legendas = ref<Record<number, string>>({})
const arrastando = ref<number | null>(null)

const cabemMais = computed(() => itens.value.length + enviando.value < LIMITE_PORTFOLIO)

function textoDoErro(e: unknown): string {
  return e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
}

function legendaDe(item: ItemPortfolio): string {
  return legendas.value[item.idprestadorportfolio] ?? item.legenda ?? ''
}

async function enviar(evento: Event) {
  const campo = evento.target as HTMLInputElement
  const arquivos = Array.from(campo.files ?? [])
  campo.value = ''
  erros.value = []

  const vagas = LIMITE_PORTFOLIO - itens.value.length
  if (arquivos.length > vagas) {
    erros.value.push(
      `Cabem só mais ${vagas} ${vagas === 1 ? 'imagem' : 'imagens'}; as demais foram ignoradas.`,
    )
  }

  // Uma por vez, para manter a ordem de escolha e não estourar o limite.
  for (const arquivo of arquivos.slice(0, Math.max(vagas, 0))) {
    enviando.value++
    try {
      const item = await prestadorApi.adicionarAoPortfolio(arquivo)
      itens.value = [...itens.value, item]
    } catch (e) {
      erros.value.push(`${arquivo.name}: ${textoDoErro(e)}`)
    } finally {
      enviando.value--
    }
  }
}

async function salvarLegenda(item: ItemPortfolio) {
  const texto = legendaDe(item).trim()
  if (texto === (item.legenda ?? '')) return
  try {
    const atualizado = await prestadorApi.editarLegenda(item.idprestadorportfolio, texto || null)
    itens.value = itens.value.map((i) =>
      i.idprestadorportfolio === atualizado.idprestadorportfolio ? atualizado : i,
    )
    delete legendas.value[item.idprestadorportfolio]
  } catch (e) {
    erros.value = [textoDoErro(e)]
  }
}

async function remover(item: ItemPortfolio) {
  if (!confirm('Remover esta imagem do portfólio?')) return
  try {
    await prestadorApi.removerDoPortfolio(item.idprestadorportfolio)
    itens.value = itens.value
      .filter((i) => i.idprestadorportfolio !== item.idprestadorportfolio)
      .map((i, posicao) => ({ ...i, ordem: posicao }))
  } catch (e) {
    erros.value = [textoDoErro(e)]
  }
}

async function aplicarOrdem(novaOrdem: ItemPortfolio[]) {
  const anterior = itens.value
  itens.value = novaOrdem // otimista: a grade muda na hora
  try {
    itens.value = await prestadorApi.reordenarPortfolio(
      novaOrdem.map((i) => i.idprestadorportfolio),
    )
  } catch (e) {
    itens.value = anterior
    erros.value = [textoDoErro(e)]
  }
}

function mover(indice: number, deslocamento: -1 | 1) {
  const destino = indice + deslocamento
  if (destino < 0 || destino >= itens.value.length) return
  const lista = [...itens.value]
  const [item] = lista.splice(indice, 1)
  lista.splice(destino, 0, item)
  aplicarOrdem(lista)
}

function soltarSobre(indiceDestino: number) {
  const origem = itens.value.findIndex((i) => i.idprestadorportfolio === arrastando.value)
  arrastando.value = null
  if (origem < 0 || origem === indiceDestino) return
  const lista = [...itens.value]
  const [item] = lista.splice(origem, 1)
  lista.splice(indiceDestino, 0, item)
  aplicarOrdem(lista)
}
</script>

<template>
  <div>
    <div class="mb-3 text-[12px] text-muted">
      {{ itens.length }} / {{ LIMITE_PORTFOLIO }} imagens · JPG, PNG ou WebP, até 5 MB cada
    </div>

    <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <figure
        v-for="(item, indice) in itens"
        :key="item.idprestadorportfolio"
        draggable="true"
        :class="['group rounded-xl border border-rule bg-surface p-2 transition-opacity',
          arrastando === item.idprestadorportfolio ? 'opacity-40' : '']"
        @dragstart="arrastando = item.idprestadorportfolio"
        @dragend="arrastando = null"
        @dragover.prevent
        @drop.prevent="soltarSobre(indice)">
        <div class="relative aspect-square overflow-hidden rounded-lg bg-ph">
          <img
            :src="urlArquivo(item.imagem_url) ?? ''"
            :alt="item.legenda ?? `Imagem ${indice + 1} do portfólio`"
            class="h-full w-full cursor-grab object-cover"
            draggable="false" />
          <button
            type="button"
            aria-label="Remover imagem"
            class="absolute right-1.5 top-1.5 flex h-6 w-6 items-center justify-center rounded-full bg-black/55 text-xs text-white"
            @click="remover(item)">
            ×
          </button>
        </div>
        <input
          :value="legendaDe(item)"
          maxlength="255"
          placeholder="Legenda (opcional)"
          class="mt-2 h-9 w-full rounded-md border border-rule-soft bg-bg px-2 text-[12px]"
          @input="legendas[item.idprestadorportfolio] = ($event.target as HTMLInputElement).value"
          @blur="salvarLegenda(item)"
          @keydown.enter="($event.target as HTMLInputElement).blur()" />
        <div class="mt-1.5 flex items-center justify-between text-[12px] text-muted">
          <button
            type="button"
            :disabled="indice === 0"
            aria-label="Mover para a esquerda"
            class="rounded px-2 py-0.5 hover:bg-bg disabled:opacity-30"
            @click="mover(indice, -1)">
            ◀
          </button>
          <span>{{ indice + 1 }}º</span>
          <button
            type="button"
            :disabled="indice === itens.length - 1"
            aria-label="Mover para a direita"
            class="rounded px-2 py-0.5 hover:bg-bg disabled:opacity-30"
            @click="mover(indice, 1)">
            ▶
          </button>
        </div>
      </figure>

      <div
        v-for="n in enviando"
        :key="`enviando-${n}`"
        class="flex aspect-square items-center justify-center rounded-xl border border-rule bg-bg text-[13px] text-muted">
        Enviando…
      </div>

      <label
        v-if="cabemMais"
        class="flex aspect-square cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-rule bg-bg text-[13px] font-semibold text-muted hover:border-ink hover:text-ink">
        <i class="fa fa-plus mb-1"></i>
        Adicionar
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          class="sr-only"
          @change="enviar" />
      </label>
    </div>

    <ul v-if="erros.length" class="mt-3 space-y-1 text-[12px] text-red-700">
      <li v-for="(e, i) in erros" :key="i">{{ e }}</li>
    </ul>
  </div>
</template>
