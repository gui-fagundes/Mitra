import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Login from './views/Login.vue'
import Register from './views/Register.vue'
import { useSessaoStore } from './stores/sessao'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // Rotas públicas — não exigem login (RF-BS-01: busca sem cadastro)
    { path: '/', name: 'home', component: Home },
    {
      path: '/buscar',
      name: 'buscar',
      component: () => import('./views/Buscar.vue'),
    },
    {
      path: '/prestador/:id',
      name: 'prestador',
      component: () => import('./views/PerfilPrestador.vue'),
    },

    // Auth
    { path: '/login', name: 'login', component: Login, meta: { guestOnly: true } },
    { path: '/register', name: 'register', component: Register, meta: { guestOnly: true } },
    {
      path: '/esqueci-senha',
      name: 'esqueci-senha',
      component: () => import('./views/EsqueciSenha.vue'),
      meta: { guestOnly: true },
    },
    {
      // Sem guestOnly: o link do e-mail precisa abrir mesmo com alguém logado no navegador.
      path: '/redefinir-senha',
      name: 'redefinir-senha',
      component: () => import('./views/RedefinirSenha.vue'),
    },

    // Área logada
    {
      path: '/conta/cliente',
      name: 'conta-cliente',
      component: () => import('./views/ContaCliente.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/conta/prestador',
      name: 'conta-prestador',
      component: () => import('./views/ContaPrestador.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/mensagens',
      name: 'mensagens',
      component: () => import('./views/Mensagens.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/mensagens/:id',
      name: 'mensagem',
      component: () => import('./views/Mensagens.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/servico/:id/confirmar',
      name: 'confirmar-servico',
      component: () => import('./views/ConfirmarServico.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to) => {
  const sessao = useSessaoStore()
  // Depois de entrar, volta para onde a pessoa queria ir (ver Login.vue).
  if (to.meta.requiresAuth && !sessao.logado) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && sessao.logado) return { name: 'home' }
})

export default router
