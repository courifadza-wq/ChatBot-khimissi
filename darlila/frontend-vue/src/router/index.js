import { createRouter, createWebHistory } from 'vue-router'
import { useAdminStore } from '../stores/admin'

import HomeView from '../views/HomeView.vue'
import AdminLoginView from '../views/AdminLoginView.vue'
import AdminLayout from '../components/admin/AdminLayout.vue'
import AdminProductsView from '../views/AdminProductsView.vue'
import AdminCategoriesView from '../views/AdminCategoriesView.vue'
import AdminBundlesView from '../views/AdminBundlesView.vue'
import AdminSettingsView from '../views/AdminSettingsView.vue'
import AdminOrdersView from '../views/AdminOrdersView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
  {
    // Lien direct vers un produit (partage / action « lien » de l'admin)
    path: '/produit/:slug',
    name: 'product-link',
    component: HomeView,
  },
    {
      path: '/admin/login',
      name: 'admin-login',
      component: AdminLoginView,
      meta: { guest: true },
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: { name: 'admin-products' } },
        { path: 'products', name: 'admin-products', component: AdminProductsView },
        { path: 'categories', name: 'admin-categories', component: AdminCategoriesView },
        { path: 'lots', name: 'admin-bundles', component: AdminBundlesView },
        { path: 'reglages', name: 'admin-settings', component: AdminSettingsView },
        { path: 'orders', name: 'admin-orders', component: AdminOrdersView },
      ],
    },
    // toute route inconnue → boutique
    { path: '/:pathMatch(.*)*', redirect: { name: 'home' } },
  ],
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
})

/**
 * Garde de navigation : les routes /admin exigent une session valide.
 * Si un token existe mais n'a pas encore été vérifié, on appelle /auth/me :
 * token expiré/révoqué → retour à la page de connexion.
 */
router.beforeEach(async (to) => {
  const admin = useAdminStore()

  if (to.meta.requiresAuth) {
    if (!admin.isAuthenticated) {
      return { name: 'admin-login', query: { redirect: to.fullPath } }
    }
    if (!admin.user) {
      const valid = await admin.verifySession()
      if (!valid) {
        return { name: 'admin-login', query: { redirect: to.fullPath } }
      }
    }
  }

  if (to.meta.guest && admin.isAuthenticated) {
    return { name: 'admin-products' }
  }
})

export default router
