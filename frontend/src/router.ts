import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Login from './views/Login.vue'
import Register from './views/Register.vue'
import { useAuthStore } from './stores/auth'

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
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLogged) return { name: 'login' }
  if (to.meta.guestOnly && auth.isLogged) return { name: 'home' }
})

export default router
