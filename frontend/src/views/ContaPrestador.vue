<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../api/auth'
import { useAuthStore } from '../stores/auth'
import PublicNav from '../components/PublicNav.vue'
import CategoryChip from '../components/CategoryChip.vue'

const router = useRouter()
const auth = useAuthStore()

type Aba = 'contratacoes' | 'vitrine' | 'portfolio' | 'dados'
const aba = ref<Aba>('vitrine')

// KPIs mockados
const kpis = [
  { label: 'Reputação · 27 avaliações', valor: '★ 4,9' },
  { label: 'Contratações em andamento', valor: '3' },
  { label: 'Resposta média', valor: '~4h' },
  { label: 'Serviços concluídos (total)', valor: '48' },
]

// Vitrine — form data
const nomePublico = ref('[Seu nome]')
const cidade = ref('Rio Grande, RS')
const bio = ref('[Bio do prestador — 2 a 4 parágrafos descrevendo experiência, tipos de serviço e diferencial.]')
const disponibilidade = ref('Seg a Sáb · 8h–18h')
const precoMin = ref('R$ 80')
const precoMax = ref('R$ 150')

async function sair() {
  try {
    await authApi.logout()
  } finally {
    auth.clearUser()
    router.push('/login')
  }
}
</script>

<template>
  <div class="min-h-screen bg-bg">
    <div class="hidden md:block"><PublicNav /></div>

    <div class="flex items-center justify-between border-b border-rule-soft bg-surface px-5 py-3.5 md:hidden">
      <div class="text-[15px] font-semibold">Mitra</div>
      <div class="flex items-center gap-3">
        <router-link to="/mensagens" aria-label="Mensagens" class="relative">
          <i class="fa fa-envelope-o text-lg"></i>
          <span class="absolute -top-1 -right-2 flex h-4 w-4 items-center justify-center rounded-full bg-gold text-[10px] font-semibold text-ink">2</span>
        </router-link>
        <button class="text-[13px] text-ink-soft" @click="sair">Sair</button>
      </div>
    </div>

    <!-- Chip "área do prestador" no desktop -->
    <div class="hidden items-center gap-3 border-b border-rule-soft bg-surface px-16 py-3 md:flex">
      <span class="mono-sm rounded-full bg-surface-2 px-2.5 py-1 text-ink-soft">
        Área do prestador
      </span>
    </div>

    <!-- Header prestador (mobile) -->
    <div class="flex items-center gap-3.5 border-b border-rule-soft bg-surface px-5 py-4 md:hidden">
      <div class="ph h-14 w-14 shrink-0 rounded-xl"></div>
      <div class="min-w-0 flex-1">
        <div class="text-[15px] font-semibold">[Seu nome]</div>
        <div class="mt-0.5 flex items-center gap-1.5 text-xs text-muted">
          <span class="text-gold">★</span> 4,9 · 27 avaliações
        </div>
      </div>
    </div>

    <!-- KPIs (desktop) -->
    <div class="hidden grid-cols-4 gap-3.5 px-16 pt-6 md:grid">
      <div v-for="k in kpis" :key="k.label" class="rounded-xl border border-rule bg-surface p-4">
        <div class="num flex items-center gap-1.5 text-[22px] font-semibold">
          <span v-if="k.valor.startsWith('★')" class="text-gold">★</span>
          {{ k.valor.replace('★ ', '') }}
        </div>
        <div class="mono-sm mt-0.5">{{ k.label }}</div>
      </div>
    </div>

    <div class="md:grid md:grid-cols-[240px_1fr] md:gap-8 md:px-16 md:py-6">
      <!-- Sidebar desktop -->
      <aside class="hidden self-start rounded-xl border border-rule bg-surface p-3 md:block">
        <div class="mono-sm mb-2 px-3.5">Sua área</div>
        <nav class="flex flex-col gap-0.5">
          <button
            v-for="item in [
              { id: 'contratacoes', label: 'Contratações', badge: '3' },
              { id: 'vitrine', label: 'Vitrine (perfil público)' },
              { id: 'portfolio', label: 'Portfólio', badge: '6' },
              { id: 'dados', label: 'Dados da conta' },
            ]"
            :key="item.id"
            :class="['flex items-center justify-between rounded-lg px-3.5 py-2.5 text-left text-sm',
              aba === (item.id as Aba)
                ? 'bg-ink font-medium text-white'
                : 'text-ink-soft hover:bg-bg']"
            @click="aba = item.id as Aba">
            <span>{{ item.label }}</span>
            <span
              v-if="item.badge"
              :class="['rounded-full px-1.5 py-0.5 text-[11px]',
                aba === (item.id as Aba) ? 'bg-white/15 text-white' : 'bg-surface-2 text-ink-soft']">
              {{ item.badge }}
            </span>
          </button>
        </nav>
        <div class="mt-3 border-t border-rule-soft pt-3 px-3.5">
          <button class="text-[13px] text-ink-soft underline" @click="sair">Sair</button>
        </div>
      </aside>

      <!-- Abas mobile -->
      <div class="flex gap-1 overflow-x-auto border-b border-rule bg-surface px-5 pt-3 md:hidden">
        <button
          v-for="a in [
            { id: 'contratacoes', label: 'Contratações' },
            { id: 'vitrine', label: 'Vitrine' },
            { id: 'portfolio', label: 'Portfólio' },
            { id: 'dados', label: 'Dados' },
          ]"
          :key="a.id"
          :style="aba === (a.id as Aba) ? 'bottom:-1px' : ''"
          :class="['relative -mb-px whitespace-nowrap rounded-t-lg border border-b-0 px-3 py-[7px] text-[13px]',
            aba === (a.id as Aba)
              ? 'border-rule bg-surface font-semibold text-ink'
              : 'border-transparent text-muted']"
          @click="aba = a.id as Aba">
          {{ a.label }}
        </button>
      </div>

      <!-- Conteúdo -->
      <main class="p-5 md:p-0">
        <!-- VITRINE -->
        <template v-if="aba === 'vitrine'">
          <div class="mb-5 flex flex-col gap-1 md:mb-6">
            <h1 class="text-xl font-semibold tracking-[-0.01em] md:text-2xl md:tracking-[-0.02em]">
              Sua vitrine pública
            </h1>
            <div class="text-[13px] text-muted">
              É o que aparece quando alguém encontra você numa busca.
            </div>
          </div>

          <div class="mb-4 rounded-lg bg-surface-2 px-3 py-2.5 text-[12px] leading-[1.5] text-ink-soft md:hidden">
            É isto que aparece no seu perfil público quando alguém encontra você numa busca.
          </div>

          <section class="rounded-2xl border border-rule bg-surface p-5 md:p-7">
            <div class="grid gap-4 md:grid-cols-2">
              <label class="col-span-full flex flex-col gap-1.5">
                <span class="mono-sm">Nome público</span>
                <input v-model="nomePublico" class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
              </label>

              <label class="col-span-full flex flex-col gap-1.5">
                <span class="mono-sm">Bio (aparece no topo do perfil)</span>
                <textarea v-model="bio" rows="4" class="rounded-lg border border-rule bg-bg px-3 py-2.5 text-sm resize-y font-sans"></textarea>
                <div class="text-right text-[11px] text-muted">{{ bio.length }} / 400 caracteres</div>
              </label>

              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">Cidade</span>
                <select v-model="cidade" class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm">
                  <option>Rio Grande, RS</option>
                </select>
              </label>
              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">Disponibilidade</span>
                <select v-model="disponibilidade" class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm">
                  <option>Seg a Sáb · 8h–18h</option>
                  <option>Somente à tarde</option>
                  <option>Sob consulta</option>
                </select>
              </label>

              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">Faixa de preço · mínimo</span>
                <input v-model="precoMin" class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
              </label>
              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">Faixa de preço · máximo</span>
                <input v-model="precoMax" class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
              </label>

              <div class="col-span-full">
                <div class="mono-sm mb-2">
                  Categorias que você atende
                  <span class="ml-1 font-normal normal-case tracking-normal text-muted"> · até 3</span>
                </div>
                <div class="flex flex-wrap gap-1.5">
                  <span class="rounded-full border border-ink bg-ink px-3 py-1 text-[13px] text-white">
                    Eletroeletrônicos ×
                  </span>
                  <span class="rounded-full border border-ink bg-ink px-3 py-1 text-[13px] text-white">
                    Construção / manutenção ×
                  </span>
                  <button class="rounded-full border border-rule bg-surface px-3 py-1 text-[13px] text-ink-soft">
                    + adicionar categoria
                  </button>
                </div>
              </div>
            </div>
          </section>

          <section class="mt-6 rounded-2xl border border-rule bg-surface p-5 md:p-7">
            <div class="mb-3 flex items-baseline justify-between">
              <div>
                <div class="text-base font-semibold">Portfólio</div>
                <div class="mt-0.5 text-[12px] text-muted">6 imagens · arraste para reordenar</div>
              </div>
              <button class="text-[13px] text-ink underline underline-offset-[3px]" @click="aba = 'portfolio'">
                Abrir aba Portfólio
              </button>
            </div>
            <div class="grid grid-cols-3 gap-2 md:grid-cols-6">
              <div v-for="i in 5" :key="i" class="relative aspect-square overflow-hidden rounded-lg">
                <div class="ph absolute inset-0"></div>
                <button
                  aria-label="Remover"
                  class="absolute right-1.5 top-1.5 flex h-5.5 w-5.5 items-center justify-center rounded-full bg-black/55 text-xs text-white">
                  ×
                </button>
              </div>
              <button class="flex aspect-square flex-col items-center justify-center rounded-lg border-2 border-dashed border-rule bg-bg text-[13px] font-semibold text-muted">
                <i class="fa fa-plus mb-1"></i>
                Adicionar
              </button>
            </div>
          </section>

          <section class="mt-6 flex items-center gap-4 rounded-2xl border border-rule bg-surface p-5 md:p-6">
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gold-soft text-2xl font-semibold text-gold-ink">
              <i class="fa fa-check"></i>
            </div>
            <div class="min-w-0 flex-1">
              <div class="text-[15px] font-semibold">Selo CNPJ validado · ativo</div>
              <div class="mt-0.5 text-[13px] text-muted">
                CNPJ 12.***.***/0001-45 · aparece como badge dourado no seu perfil público.
              </div>
            </div>
            <a href="#" class="hidden rounded-lg border border-rule px-3.5 py-2 text-[13px] text-ink-soft md:inline-block">
              Trocar CNPJ
            </a>
          </section>

          <div class="mt-6 flex justify-end gap-2.5">
            <button class="h-11 rounded-lg border border-rule px-5 text-sm text-ink-soft">
              Descartar alterações
            </button>
            <button class="h-11 rounded-lg bg-gold px-6 text-sm font-semibold text-ink hover:opacity-90">
              Salvar alterações
            </button>
          </div>
        </template>

        <!-- Outras abas: placeholders — a serem detalhadas com dados reais -->
        <template v-else-if="aba === 'contratacoes'">
          <div class="mb-5">
            <h1 class="text-xl font-semibold md:text-2xl">Contratações recebidas</h1>
            <div class="mt-0.5 text-[13px] text-muted">
              Serviços que outros contrataram via Mitra com você.
            </div>
          </div>
          <div class="rounded-2xl border border-dashed border-rule bg-surface p-8 text-center">
            <div class="mono mb-2">Preencher quando houver dados da API</div>
            <p class="text-[13px] text-muted">
              Mesma estrutura da lista de Contratações do cliente — mudam os CTAs
              (o prestador "Confirma serviço", "Cancela", "Responde avaliação").
            </p>
          </div>
        </template>

        <template v-else-if="aba === 'portfolio'">
          <div class="mb-5">
            <h1 class="text-xl font-semibold md:text-2xl">Portfólio</h1>
            <div class="mt-0.5 text-[13px] text-muted">
              Suas fotos de trabalho — arraste para reordenar.
            </div>
          </div>
          <div class="grid grid-cols-3 gap-2 md:grid-cols-6">
            <div v-for="i in 6" :key="i" class="ph aspect-square rounded-xl"></div>
            <button class="flex aspect-square flex-col items-center justify-center rounded-xl border-2 border-dashed border-rule bg-bg text-[13px] font-semibold text-muted">
              <i class="fa fa-plus mb-1"></i> Adicionar
            </button>
          </div>
        </template>

        <template v-else>
          <div class="mb-5">
            <h1 class="text-xl font-semibold md:text-2xl">Dados da conta</h1>
            <div class="mt-0.5 text-[13px] text-muted">
              Informações privadas de identificação e CNPJ.
            </div>
          </div>

          <div class="rounded-2xl border border-rule bg-surface p-6">
            <div class="grid gap-4 md:grid-cols-2">
              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">Nome</span>
                <input :value="auth.user?.nome ?? '[Seu nome]'" class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
              </label>
              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">E-mail</span>
                <input :value="auth.user?.email ?? 'voce@exemplo.com'" class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
              </label>
              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">CNPJ</span>
                <input value="12.345.678/0001-45" class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
              </label>
              <label class="flex flex-col gap-1.5">
                <span class="mono-sm">Telefone</span>
                <input value="(53) 99999-9999" class="h-11 rounded-lg border border-rule bg-bg px-3 text-sm" />
              </label>
            </div>

            <div class="mt-5 flex flex-col items-start justify-between gap-3 border-t border-dashed border-rule-soft pt-4 md:flex-row md:items-center">
              <a href="#" class="text-[13px] text-ink-soft underline">
                Exportar meus dados · LGPD
              </a>
              <button class="rounded-lg bg-ink px-4 py-2.5 text-sm font-semibold text-white">
                Salvar alterações
              </button>
            </div>
          </div>
        </template>
      </main>
    </div>
  </div>
</template>
