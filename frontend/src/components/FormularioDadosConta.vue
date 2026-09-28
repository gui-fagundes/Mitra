<script setup lang="ts">
// Aba "Dados da conta" — comum às áreas do cliente e do prestador:
// foto (upload direto) + nome, cidade e telefone (PATCH /conta).
import { onMounted, ref, watch } from 'vue'
import { cidadeApi, rotuloCidade, type Cidade } from '../api/cidade'
import { ErroApi } from '../api/client'
import { contaApi, type Usuario } from '../api/conta'
import { useSessaoStore } from '../stores/sessao'
import FotoUsuario from './FotoUsuario.vue'

const sessao = useSessaoStore()

const cidades = ref<Cidade[]>([])
const nome = ref('')
const idcidade = ref<number | null>(null)
const telefone = ref('')
const salvando = ref(false)
const mensagem = ref<{ tipo: 'ok' | 'erro'; texto: string } | null>(null)
const enviandoFoto = ref(false)
const erroFoto = ref<string | null>(null)

function preencher(usuario: Usuario | null) {
  if (!usuario) return
  nome.value = usuario.nome
  idcidade.value = usuario.cidade?.idcidade ?? null
  telefone.value = usuario.telefone ?? ''
}

watch(() => sessao.usuario, preencher, { immediate: true })

function textoDoErro(e: unknown): string {
  return e instanceof ErroApi ? e.detalhe : 'Erro inesperado'
}

async function salvar() {
  mensagem.value = null
  salvando.value = true
  try {
    sessao.definirUsuario(
      await contaApi.atualizar({
        nome: nome.value,
        idcidade: idcidade.value,
        telefone: telefone.value || null,
      }),
    )
    mensagem.value = { tipo: 'ok', texto: 'Alterações salvas.' }
  } catch (e) {
    mensagem.value = { tipo: 'erro', texto: textoDoErro(e) }
  } finally {
    salvando.value = false
  }
}

async function enviarFoto(evento: Event) {
  const campo = evento.target as HTMLInputElement
  const arquivo = campo.files?.[0]
  campo.value = '' // permite escolher o mesmo arquivo de novo
  if (!arquivo) return

  erroFoto.value = null
  enviandoFoto.value = true
  try {
    sessao.definirUsuario(await contaApi.enviarFoto(arquivo))
  } catch (e) {
    erroFoto.value = textoDoErro(e)
  } finally {
    enviandoFoto.value = false
  }
}

async function removerFoto() {
  erroFoto.value = null
  try {
    sessao.definirUsuario(await contaApi.removerFoto())
  } catch (e) {
    erroFoto.value = textoDoErro(e)
  }
}

onMounted(async () => {
  try {
    cidades.value = await cidadeApi.listar()
  } catch {
    // Sem a lista, o select mostra só a cidade atual (se houver).
  }
})
</script>

<template>
  <div class="rounded-2xl border border-rule bg-surface p-6">
    <!-- Foto: upload direto, independente do "Salvar alterações" -->
    <div class="mb-5 flex items-center gap-4 border-b border-dashed border-rule-soft pb-5">
      <FotoUsuario
        :url="sessao.usuario?.foto_url"
        :nome="sessao.usuario?.nome"
        tamanho="h-16 w-16 text-xl" />
      <div class="flex flex-col gap-1.5">
        <div class="flex items-center gap-3">
          <label
            :class="['cursor-pointer rounded-lg border border-ink px-3 py-1.5 text-[13px] font-medium',
              enviandoFoto ? 'pointer-events-none opacity-60' : '']">
            {{ enviandoFoto ? 'Enviando…' : sessao.usuario?.foto_url ? 'Trocar foto' : 'Enviar foto' }}
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              class="sr-only"
              @change="enviarFoto" />
          </label>
          <button
            v-if="sessao.usuario?.foto_url"
            type="button"
            class="text-[13px] text-ink-soft underline underline-offset-[3px]"
            @click="removerFoto">
            Remover
          </button>
        </div>
        <span v-if="erroFoto" class="text-[12px] text-red-700">{{ erroFoto }}</span>
        <span v-else class="text-[12px] text-muted">JPG, PNG ou WebP, até 5 MB.</span>
      </div>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <label class="flex flex-col gap-1.5">
        <span class="mono-sm">Nome completo</span>
        <input v-model="nome" class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
      </label>
      <label class="flex flex-col gap-1.5">
        <span class="mono-sm">E-mail</span>
        <input
          :value="sessao.usuario?.email ?? ''"
          disabled
          title="A troca de e-mail ainda não está disponível."
          class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm text-muted" />
      </label>
      <label class="flex flex-col gap-1.5">
        <span class="mono-sm">Cidade</span>
        <select v-model="idcidade" class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm">
          <option :value="null">—</option>
          <option v-for="c in cidades" :key="c.idcidade" :value="c.idcidade">
            {{ rotuloCidade(c) }}
          </option>
        </select>
      </label>
      <label class="flex flex-col gap-1.5">
        <span class="mono-sm">Telefone</span>
        <input
          v-model="telefone"
          type="tel"
          placeholder="(53) 99999-9999"
          class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
      </label>
    </div>

    <slot />

    <div class="mt-5 flex flex-col items-start justify-between gap-3 border-t border-dashed border-rule-soft pt-4 md:flex-row md:items-center">
      <!-- Exportação LGPD ainda não implementada no backend (GET /conta/exportar). -->
      <a href="#" class="text-[13px] text-ink-soft underline">Exportar meus dados · LGPD</a>
      <div class="flex items-center gap-3">
        <span
          v-if="mensagem"
          :class="['text-[13px]', mensagem.tipo === 'ok' ? 'text-good' : 'text-red-700']">
          {{ mensagem.texto }}
        </span>
        <button
          :disabled="salvando"
          class="rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
          @click="salvar">
          {{ salvando ? 'Salvando…' : 'Salvar alterações' }}
        </button>
      </div>
    </div>
  </div>
</template>
