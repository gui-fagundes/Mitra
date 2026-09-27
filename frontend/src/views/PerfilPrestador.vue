<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import PublicNav from '../components/PublicNav.vue'
import StarRating from '../components/StarRating.vue'
import CategoryChip from '../components/CategoryChip.vue'
import Tabs from '../components/Tabs.vue'

const router = useRouter()

type Aba = 'sobre' | 'portfolio' | 'avaliacoes'
const aba = ref<Aba>('sobre')

const abas = [
  { id: 'sobre' as const, label: 'Sobre' },
  { id: 'portfolio' as const, label: 'Portfólio' },
  { id: 'avaliacoes' as const, label: 'Avaliações (27)' },
]

const prestador = {
  nome: '[Nome do prestador]',
  cidade: 'Rio Grande, RS',
  atendeHa: '2 anos',
  nota: 4.9,
  avaliacoes: 27,
  servicosConcluidos: 48,
  respostaMedia: '~4h',
  categorias: ['Eletroeletrônicos', 'Construção / manutenção'],
  cnpj: true,
  bio: '[Bio do prestador — 2 a 4 parágrafos descrevendo experiência, tipos de serviço e diferencial. Preenchido no cadastro; editável pelo próprio prestador na área logada.]',
  ultimaAtividade: 'hoje',
  portfolioCount: 9,
}

const avaliacoes = [
  {
    autor: '[Cliente A.]',
    nota: 5,
    quando: 'há 2 semanas · instalação elétrica',
    texto: '"Chegou no horário, resolveu rápido e explicou tudo. Recomendo."',
  },
  {
    autor: '[Cliente B.]',
    nota: 4,
    quando: 'há 1 mês · conserto de eletrodoméstico',
    texto: '"Bom trabalho, só demorou um pouco para responder inicialmente."',
    resposta: '"Obrigado pelo retorno! Vou ajustar minha rotina de mensagens."',
  },
]

function iniciarContato() {
  router.push({ name: 'mensagens' })
}
</script>

<template>
  <div class="min-h-screen bg-bg pb-24 md:pb-0">
    <div class="hidden md:block">
      <PublicNav />
      <div class="px-16 py-4 text-[13px] text-muted">
        <router-link to="/buscar" class="text-ink-soft">Eletricistas em Rio Grande</router-link>
        <span class="mx-2">›</span>
        <span>{{ prestador.nome }}</span>
      </div>
    </div>

    <div class="flex items-center justify-between border-b border-rule-soft bg-surface px-5 py-3.5 md:hidden">
      <button aria-label="Voltar" class="flex h-9 w-9 items-center justify-center rounded-lg border border-rule" @click="router.back()">
        <i class="fa fa-arrow-left"></i>
      </button>
      <div class="flex gap-2">
        <button aria-label="Compartilhar" class="flex h-9 w-9 items-center justify-center rounded-lg border border-rule">
          <i class="fa fa-share-alt"></i>
        </button>
        <button aria-label="Mais" class="flex h-9 w-9 items-center justify-center rounded-lg border border-rule">
          <i class="fa fa-ellipsis-h"></i>
        </button>
      </div>
    </div>

    <div class="grid gap-8 px-0 md:grid-cols-[1fr_360px] md:gap-12 md:px-16 md:pb-10">
      <div>
        <div class="border-b border-rule-soft bg-surface px-5 py-6 md:rounded-2xl md:border md:border-rule md:p-8">
          <div class="flex items-start gap-4 md:gap-7">
            <div class="ph h-[88px] w-[88px] shrink-0 rounded-2xl md:h-[140px] md:w-[140px]"></div>
            <div class="min-w-0 flex-1">
              <div class="flex items-start justify-between gap-3">
                <div>
                  <h1 class="mb-1 text-[22px] font-semibold tracking-[-0.01em] md:text-[30px] md:tracking-[-0.02em]">
                    {{ prestador.nome }}
                  </h1>
                  <div class="text-[13px] text-muted md:text-sm">
                    {{ prestador.cidade }}<span class="hidden md:inline"> · atende há {{ prestador.atendeHa }}</span>
                  </div>
                </div>
                <div class="hidden gap-2 md:flex">
                  <button aria-label="Compartilhar" class="flex h-9 w-9 items-center justify-center rounded-lg border border-rule bg-transparent">
                    <i class="fa fa-share-alt"></i>
                  </button>
                  <button aria-label="Salvar" class="flex h-9 w-9 items-center justify-center rounded-lg border border-rule bg-transparent">
                    <i class="fa fa-heart-o"></i>
                  </button>
                </div>
              </div>

              <div class="mt-4 hidden items-center gap-6 border-y border-rule-soft py-4 md:flex">
                <div>
                  <div class="flex items-center gap-1.5">
                    <StarRating :value="prestador.nota" size="md" />
                    <span class="text-base font-semibold">
                      {{ prestador.nota.toFixed(1).replace('.', ',') }}
                    </span>
                  </div>
                  <div class="mono-sm">{{ prestador.avaliacoes }} avaliações</div>
                </div>
                <span class="h-8 w-px bg-rule-soft"></span>
                <div>
                  <div class="num text-[22px] font-semibold">{{ prestador.servicosConcluidos }}</div>
                  <div class="mono-sm">Serviços concluídos</div>
                </div>
                <span class="h-8 w-px bg-rule-soft"></span>
                <div>
                  <div class="num text-[22px] font-semibold">{{ prestador.respostaMedia }}</div>
                  <div class="mono-sm">Resposta média</div>
                </div>
              </div>

              <div class="mt-2 flex items-center gap-1.5 md:hidden">
                <StarRating :value="prestador.nota" size="md" />
                <span class="text-[13px] font-semibold">
                  {{ prestador.nota.toFixed(1).replace('.', ',') }}
                </span>
                <span class="text-xs text-muted">· {{ prestador.avaliacoes }} avaliações</span>
              </div>

              <div class="mt-3.5 flex flex-wrap gap-1.5">
                <CategoryChip v-for="c in prestador.categorias" :key="c">{{ c }}</CategoryChip>
                <CategoryChip v-if="prestador.cnpj" tone="gold">CNPJ validado ✓</CategoryChip>
              </div>
            </div>
          </div>

          <div class="mt-4 md:hidden">
            <button class="h-[50px] w-full rounded-xl bg-gold text-[15px] font-semibold text-ink hover:opacity-90" @click="iniciarContato">
              Iniciar contato
            </button>
            <div class="mt-2 text-center text-xs text-muted">
              A conversa fica registrada no Mitra
            </div>
          </div>
        </div>

        <div class="mt-4 md:mt-8">
          <Tabs v-model="aba" :items="abas" size="md" />
        </div>

        <div class="space-y-8 px-5 py-6 md:px-0 md:py-8">
          <template v-if="aba === 'sobre'">
            <section>
              <div class="mono mb-2">Apresentação</div>
              <p class="max-w-[60ch] text-[14px] leading-[1.6] text-ink-soft md:text-[15px]">
                {{ prestador.bio }}
              </p>
            </section>

            <section>
              <div class="mb-3 flex items-baseline justify-between">
                <div class="mono">Portfólio · {{ prestador.portfolioCount }} imagens</div>
                <button class="text-[13px] text-ink-soft underline underline-offset-[3px]" @click="aba = 'portfolio'">
                  Ver galeria
                </button>
              </div>
              <div class="grid grid-cols-3 gap-1.5 md:grid-cols-4 md:gap-2">
                <div v-for="i in 5" :key="i" class="ph aspect-square rounded-lg md:rounded-xl"></div>
                <div class="relative aspect-square overflow-hidden rounded-lg md:rounded-xl">
                  <div class="ph absolute inset-0"></div>
                  <div class="absolute inset-0 flex items-center justify-center bg-black/40 text-base font-semibold text-white">
                    +{{ prestador.portfolioCount - 5 }}
                  </div>
                </div>
              </div>
            </section>

            <section>
              <div class="mb-3 flex items-baseline justify-between">
                <div class="mono">Últimas avaliações</div>
                <button class="text-[13px] text-ink-soft underline underline-offset-[3px]" @click="aba = 'avaliacoes'">
                  Ver todas
                </button>
              </div>
              <div class="grid gap-3 md:grid-cols-2">
                <article v-for="(a, i) in avaliacoes" :key="i" class="rounded-xl border border-rule bg-surface p-4 md:p-5">
                  <div class="mb-1.5 flex items-baseline justify-between">
                    <div class="text-[13px] font-semibold md:text-sm">{{ a.autor }}</div>
                    <StarRating :value="a.nota" />
                  </div>
                  <p class="text-[13px] leading-[1.55] text-ink-soft md:text-sm">{{ a.texto }}</p>
                  <div class="mt-2.5 text-[11px] text-muted">{{ a.quando }}</div>
                  <div v-if="a.resposta" class="mt-3 border-t border-dashed border-rule-soft pt-3 text-[13px] text-ink-soft">
                    <div class="mono-sm mb-1">Resposta do prestador</div>
                    {{ a.resposta }}
                  </div>
                </article>
              </div>
            </section>
          </template>

          <template v-else-if="aba === 'portfolio'">
            <section>
              <div class="mono mb-3">{{ prestador.portfolioCount }} imagens</div>
              <div class="grid grid-cols-3 gap-2 md:grid-cols-4">
                <div v-for="i in prestador.portfolioCount" :key="i" class="ph aspect-square rounded-xl"></div>
              </div>
            </section>
          </template>

          <template v-else>
            <section>
              <div class="mono mb-3">Todas as {{ prestador.avaliacoes }} avaliações</div>
              <div class="grid gap-3 md:grid-cols-2">
                <article v-for="(a, i) in avaliacoes" :key="i" class="rounded-xl border border-rule bg-surface p-4 md:p-5">
                  <div class="mb-1.5 flex items-baseline justify-between">
                    <div class="text-[13px] font-semibold md:text-sm">{{ a.autor }}</div>
                    <StarRating :value="a.nota" />
                  </div>
                  <p class="text-[13px] leading-[1.55] text-ink-soft md:text-sm">{{ a.texto }}</p>
                  <div class="mt-2.5 text-[11px] text-muted">{{ a.quando }}</div>
                </article>
              </div>
            </section>
          </template>
        </div>
      </div>

      <aside class="sticky top-6 hidden self-start rounded-2xl border border-rule bg-surface p-6 md:block">
        <div class="mb-3">
          <div class="mono mb-2">Entrar em contato</div>
          <div class="text-[13px] leading-[1.5] text-ink-soft">
            A conversa acontece dentro do Mitra e fica registrada para viabilizar a avaliação depois.
          </div>
        </div>
        <button class="h-13 w-full rounded-xl bg-gold py-3.5 text-[15px] font-semibold text-ink hover:opacity-90" @click="iniciarContato">
          Iniciar contato
        </button>

        <div class="my-4 h-px bg-rule-soft"></div>

        <ul class="space-y-2.5 text-[13px]">
          <li class="flex justify-between"><span class="text-muted">Cidade</span><span>{{ prestador.cidade }}</span></li>
          <li class="flex justify-between"><span class="text-muted">Resposta média</span><span>{{ prestador.respostaMedia }}</span></li>
          <li class="flex justify-between"><span class="text-muted">CNPJ</span><span class="text-gold-ink">Validado ✓</span></li>
          <li class="flex justify-between"><span class="text-muted">Última atividade</span><span>{{ prestador.ultimaAtividade }}</span></li>
        </ul>

        <div class="my-4 h-px bg-rule-soft"></div>
        <a href="#" class="text-[12px] text-muted underline underline-offset-[3px]">Reportar perfil</a>
      </aside>
    </div>

    <div class="fixed inset-x-0 bottom-0 border-t border-rule bg-surface px-5 py-3 md:hidden">
      <button class="h-12 w-full rounded-lg bg-gold text-[15px] font-semibold text-ink hover:opacity-90" @click="iniciarContato">
        Iniciar contato
      </button>
    </div>
  </div>
</template>
