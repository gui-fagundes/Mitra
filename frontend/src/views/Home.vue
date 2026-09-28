<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { taxonomiaApi, type Categoria } from '../api/taxonomia'
import PublicNav from '../components/PublicNav.vue'

const router = useRouter()

const query = ref('')
const cidade = ref('Rio Grande, RS')

function buscar() {
  router.push({
    name: 'buscar',
    query: { q: query.value || undefined, cidade: cidade.value },
  })
}

const categorias = ref<Categoria[]>([])

function resumo(categoria: Categoria): string {
  return categoria.servicos.map((s) => s.nome).join(', ')
}

onMounted(async () => {
  try {
    categorias.value = await taxonomiaApi.listarCategorias()
  } catch {
    // Sem a API, a seção de categorias fica vazia; a busca continua funcionando.
  }
})

const populares = ['Eletricista', 'Adestramento', 'Aula particular', 'Personal trainer']
</script>

<template>
  <div class="min-h-screen bg-bg">
    <PublicNav />

    <!-- =========================================================
         Hero: título + subtítulo + busca principal + prova/como
         ========================================================= -->
    <section class="px-5 py-8 md:px-16 md:py-14">
      <div class="grid gap-10 md:grid-cols-[1.1fr_1fr] md:items-center md:gap-16">
        <!-- Coluna esquerda -->
        <div>
          <div class="mono mb-3 md:mb-4">
            Marketplace de serviços · piloto em Rio Grande
          </div>
          <h1
            class="mb-3 text-[32px] font-semibold leading-[1.06] tracking-[-0.02em] md:mb-4 md:text-[60px] md:leading-[1.02] md:tracking-[-0.025em]"
          >
            Encontre quem faz bem<br />o que faz.
          </h1>
          <p
            class="mb-6 max-w-[52ch] text-[15px] leading-[1.5] text-ink-soft md:mb-8 md:text-lg"
          >
            Ranking por reputação e proximidade. Sem posições vendidas.
            Sem cadastro para pesquisar.
          </p>

          <!-- Busca ---------------------------------------------- -->
          <form
            class="rounded-2xl border border-rule bg-surface p-2 md:grid md:grid-cols-[1.4fr_1fr_auto] md:gap-2"
            @submit.prevent="buscar"
          >
            <!-- Mobile: empilhado -->
            <label
              class="mb-2 flex items-center gap-2.5 rounded-lg border border-rule bg-bg px-3 py-2.5 md:mb-0 md:border-0 md:border-r md:border-rule-soft md:bg-transparent md:px-3.5 md:py-2.5"
            >
              <i class="fa fa-search shrink-0 text-muted"></i>
              <div class="min-w-0 flex-1">
                <div class="mono-sm hidden md:block">O que</div>
                <input
                  v-model="query"
                  type="text"
                  placeholder="Eletricista, aula de violão…"
                  class="w-full border-0 bg-transparent text-[15px] outline-none placeholder:text-muted"
                />
              </div>
            </label>

            <label
              class="mb-2 flex items-center gap-2.5 rounded-lg border border-rule bg-bg px-3 py-2.5 md:mb-0 md:border-0 md:bg-transparent md:px-3.5 md:py-2.5"
            >
              <i class="fa fa-map-marker shrink-0 text-muted"></i>
              <div class="min-w-0 flex-1">
                <div class="mono-sm hidden md:block">Cidade</div>
                <select
                  v-model="cidade"
                  class="w-full appearance-none border-0 bg-transparent text-[15px] outline-none"
                >
                  <option>Rio Grande, RS</option>
                </select>
              </div>
            </label>

            <button
              type="submit"
              class="flex h-12 w-full items-center justify-center gap-2 rounded-lg bg-gold px-6 text-[15px] font-semibold text-ink transition-opacity hover:opacity-90 md:h-auto md:w-auto"
            >
              <i class="fa fa-search"></i>
              Buscar
            </button>
          </form>

          <!-- Populares --------------------------------------------- -->
          <div class="mt-5 flex flex-wrap items-center gap-2 md:mt-6">
            <span class="mono mr-1">Populares:</span>
            <router-link
              v-for="p in populares"
              :key="p"
              :to="{ name: 'buscar', query: { q: p } }"
              class="rounded-full border border-rule bg-surface px-3.5 py-1.5 text-[13px] font-medium"
            >
              {{ p }}
            </router-link>
          </div>
        </div>

        <!-- Coluna direita: Como funciona ------------------------ -->
        <aside
          id="como-funciona"
          class="rounded-2xl border border-rule bg-surface p-6 md:p-8"
        >
          <div class="mono mb-4">Como funciona</div>
          <ol class="flex flex-col gap-4 md:gap-5">
            <li v-for="(step, i) in [
              {
                t: 'Busque sem cadastro',
                d: 'Pesquise por categoria e cidade e compare prestadores lado a lado.',
              },
              {
                t: 'Converse pelo Mitra',
                d: 'O primeiro contato acontece por aqui, com histórico registrado.',
              },
              {
                t: 'Confirme e avalie',
                d: 'Cliente e prestador confirmam o serviço concluído; a avaliação vem em seguida.',
              },
            ]" :key="i" class="grid grid-cols-[36px_1fr] items-start gap-4">
              <span
                class="num flex h-[30px] w-[30px] items-center justify-center rounded-full bg-ink text-[13px] font-semibold text-white"
              >
                {{ i + 1 }}
              </span>
              <div>
                <div class="text-base font-semibold">{{ step.t }}</div>
                <div class="mt-0.5 text-[13px] leading-[1.5] text-ink-soft">
                  {{ step.d }}
                </div>
              </div>
            </li>
          </ol>
        </aside>
      </div>
    </section>

    <!-- =========================================================
         Categorias
         ========================================================= -->
    <section class="px-5 pb-10 md:px-16 md:pb-16">
      <div class="mb-4 flex items-baseline justify-between md:mb-5">
        <div class="mono">Categorias</div>
        <router-link
          to="/buscar"
          class="text-[13px] font-medium text-ink-soft underline-offset-[3px] hover:underline"
        >
          Ver todas
        </router-link>
      </div>
      <div class="grid grid-cols-2 gap-3 md:grid-cols-5 md:gap-4">
        <router-link
          v-for="(cat, i) in categorias"
          :key="cat.slug"
          :to="{ name: 'buscar', query: { categoria: cat.slug } }"
          :class="[
            'block rounded-2xl border border-rule bg-surface p-4 md:p-5',
            i === categorias.length - 1 ? 'col-span-2 md:col-span-1' : '',
          ]"
        >
          <div
            class="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-gold-soft text-gold-ink md:mb-3.5"
          >
            <i :class="['fa text-lg', cat.icone]"></i>
          </div>
          <div class="text-base font-semibold">{{ cat.nome }}</div>
          <div class="mt-1 text-[12px] text-muted">{{ resumo(cat) }}</div>
        </router-link>
      </div>
    </section>

    <!-- CTA prestador (mobile ganha caixinha discreta) -->
    <section class="px-5 pb-10 md:px-16 md:pb-16">
      <router-link
        to="/register"
        class="flex items-center justify-between gap-3 rounded-xl border border-dashed border-rule bg-transparent px-4 py-3.5"
      >
        <div>
          <div class="text-sm font-semibold">Presta serviço?</div>
          <div class="mt-0.5 text-[12px] text-muted">
            Crie sua vitrine em minutos.
          </div>
        </div>
        <span class="text-[13px] font-medium underline underline-offset-[3px]">
          Cadastrar
        </span>
      </router-link>
    </section>
  </div>
</template>
