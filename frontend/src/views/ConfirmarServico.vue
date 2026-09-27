<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import PublicNav from '../components/PublicNav.vue'

const route = useRoute()
const router = useRouter()

const servicoId = route.params.id

// Mock — trocar por chamada à API na fase seguinte
const servico = {
  id: servicoId,
  prestador: '[Nome do prestador]',
  categoria: 'Eletroeletrônicos',
  descricao: 'Instalação elétrica',
  cidade: 'Rio Grande, RS',
  contatoIniciado: '14/09/2026',
  dataCombinada: '18/09/2026',
  valor: 'R$ 240,00',
  origem: 'Busca no Mitra',
  prestadorConfirmou: true,
  prestadorConfirmadoEm: 'ontem, 18:20',
  clienteConfirmou: false,
}

// Ciclo — passos completos até agora
const ciclo = [
  { label: 'Contato iniciado · 14/09', estado: 'done' as const },
  { label: 'Em conversa · 14–17/09', estado: 'done' as const },
  { label: 'Prestador confirmou · 19/09', estado: 'done' as const },
  { label: 'Sua confirmação (agora)', estado: 'now' as const },
  { label: 'Avaliação pública liberada', estado: 'pending' as const },
]

function confirmar() {
  // Onda 2 mock: só volta para a área do cliente.
  router.push({ name: 'conta-cliente' })
}
</script>

<template>
  <div class="min-h-screen bg-bg">
    <div class="hidden md:block"><PublicNav /></div>

    <!-- Header mobile -->
    <div class="flex items-center justify-between border-b border-rule-soft bg-surface px-5 py-3.5 md:hidden">
      <button
        aria-label="Voltar"
        class="flex h-9 w-9 items-center justify-center rounded-lg border border-rule bg-surface"
        @click="router.back()">
        <i class="fa fa-arrow-left"></i>
      </button>
      <div class="text-sm font-semibold">Confirmação de serviço</div>
      <div class="w-9"></div>
    </div>

    <!-- Breadcrumb desktop -->
    <div class="hidden px-16 py-4 text-[13px] text-muted md:block">
      <router-link to="/conta/cliente" class="text-ink-soft">
        Suas contratações
      </router-link>
      <span class="mx-2">›</span>
      <span>Serviço #{{ servico.id }} · Confirmação</span>
    </div>

    <!-- Grid principal -->
    <div class="grid gap-6 px-5 pb-32 md:grid-cols-[1fr_380px] md:gap-10 md:px-16 md:pb-10">
      <!-- Coluna principal -->
      <div class="space-y-6">
        <!-- Cabeçalho -->
        <div>
          <div class="mono-sm mb-2">Serviço #{{ servico.id }} · via Mitra</div>
          <h1 class="mb-2 text-[22px] font-semibold tracking-[-0.01em] md:text-[30px] md:tracking-[-0.02em]">
            Confirmar que o serviço foi realizado
          </h1>
          <p class="max-w-[60ch] text-[13px] leading-[1.5] text-ink-soft md:text-[15px]">
            Cliente e prestador precisam confirmar independentemente. Quando os
            dois lados marcarem a conclusão, a avaliação pública fica
            disponível para ambos.
          </p>
        </div>

        <!-- Resumo do serviço -->
        <section class="rounded-2xl border border-rule bg-surface p-5 md:p-6">
          <div class="mono mb-3">Resumo do serviço</div>
          <div class="grid gap-y-0 md:grid-cols-2 md:gap-x-8">
            <div class="flex justify-between border-b border-rule-soft py-3 text-sm">
              <span class="text-muted">Prestador</span><span>{{ servico.prestador }}</span>
            </div>
            <div class="flex justify-between border-b border-rule-soft py-3 text-sm">
              <span class="text-muted">Categoria</span><span>{{ servico.categoria }}</span>
            </div>
            <div class="flex justify-between border-b border-rule-soft py-3 text-sm">
              <span class="text-muted">Serviço combinado</span><span>{{ servico.descricao }}</span>
            </div>
            <div class="flex justify-between border-b border-rule-soft py-3 text-sm">
              <span class="text-muted">Cidade</span><span>{{ servico.cidade }}</span>
            </div>
            <div class="flex justify-between border-b border-rule-soft py-3 text-sm">
              <span class="text-muted">Contato iniciado</span><span>{{ servico.contatoIniciado }}</span>
            </div>
            <div class="flex justify-between border-b border-rule-soft py-3 text-sm">
              <span class="text-muted">Data combinada</span><span>{{ servico.dataCombinada }}</span>
            </div>
            <div class="flex justify-between py-3 text-sm">
              <span class="text-muted">Valor combinado</span>
              <span><strong>{{ servico.valor }}</strong></span>
            </div>
            <div class="flex justify-between py-3 text-sm">
              <span class="text-muted">Origem</span><span>{{ servico.origem }}</span>
            </div>
          </div>
        </section>

        <!-- Estado bilateral -->
        <section>
          <div class="mono mb-3">Estado da confirmação bilateral</div>
          <div class="grid gap-3.5 md:grid-cols-2">
            <div class="flex items-center gap-3.5 rounded-xl border border-rule bg-surface p-4 md:p-5">
              <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-good-soft text-lg font-semibold text-good">
                <i class="fa fa-check"></i>
              </div>
              <div class="min-w-0 flex-1">
                <div class="text-sm font-semibold">{{ servico.prestador }}</div>
                <div class="mt-0.5 text-xs text-good">
                  Confirmou · {{ servico.prestadorConfirmadoEm }}
                </div>
              </div>
            </div>
            <div class="flex items-center gap-3.5 rounded-xl border border-dashed border-gold bg-surface p-4 md:p-5">
              <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gold-soft text-lg font-semibold text-gold-ink">
                …
              </div>
              <div class="min-w-0 flex-1">
                <div class="text-sm font-semibold">Você (cliente)</div>
                <div class="mt-0.5 text-xs text-gold-ink">Ainda não confirmou</div>
              </div>
            </div>
          </div>
        </section>

        <!-- Bloco de ação (desktop) -->
        <section class="hidden items-center justify-between gap-5 rounded-2xl border border-rule bg-surface p-6 md:flex">
          <div class="max-w-[52ch]">
            <div class="mb-1 text-[15px] font-semibold">
              Ao confirmar você diz que o serviço combinado foi realizado.
            </div>
            <div class="text-[13px] leading-[1.5] text-muted">
              Depois da sua confirmação a avaliação pública fica aberta por 14
              dias, para os dois lados.
            </div>
          </div>
          <button
            class="h-12 shrink-0 rounded-xl bg-gold px-6 text-[15px] font-semibold text-ink hover:opacity-90"
            @click="confirmar">
            Confirmar conclusão
          </button>
        </section>

        <!-- Mensagem no mobile -->
        <div class="md:hidden rounded-lg bg-surface-2 p-3.5 text-xs leading-[1.5] text-ink-soft">
          Ao confirmar você diz que o serviço combinado foi realizado. Isso
          destrava a avaliação pública para ambos os lados e encerra o ciclo
          dentro do Mitra.
        </div>
      </div>

      <!-- Sidebar direita: ciclo (desktop) -->
      <aside class="hidden self-start rounded-2xl border border-rule bg-surface p-6 md:block">
        <div class="mono mb-4">Ciclo do serviço</div>
        <div class="flex flex-col gap-3.5">
          <div
            v-for="(passo, i) in ciclo"
            :key="i"
            class="flex items-center gap-3">
            <span
              :class="['flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold',
                passo.estado === 'done' ? 'bg-good-soft text-good'
                : passo.estado === 'now' ? 'bg-gold text-ink'
                : 'bg-surface-2 text-muted']">
              {{ passo.estado === 'done' ? '✓' : i + 1 }}
            </span>
            <span
              :class="['text-[13px]',
                passo.estado === 'done' ? 'text-good'
                : passo.estado === 'now' ? 'font-semibold text-ink'
                : 'text-muted']">
              {{ passo.label }}
            </span>
          </div>
        </div>

        <div class="my-4 h-px bg-rule-soft"></div>

        <div>
          <div class="mono-sm mb-1">Conversa relacionada</div>
          <router-link :to="{ name: 'mensagens' }" class="text-[13px] text-ink underline">
            Abrir chat com {{ servico.prestador }}
          </router-link>
        </div>
      </aside>
    </div>

    <!-- Ação fixa mobile -->
    <div class="fixed inset-x-0 bottom-0 border-t border-rule bg-surface px-5 py-3 md:hidden">
      <button
        class="h-[52px] w-full rounded-xl bg-gold text-[15px] font-semibold text-ink hover:opacity-90"
        @click="confirmar">
        Confirmar conclusão do serviço
      </button>
    </div>
  </div>
</template>
