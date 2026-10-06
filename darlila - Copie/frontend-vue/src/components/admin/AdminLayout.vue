<script setup>
/**
 * Layout de l'espace d'administration : barre latérale + zone de contenu
 * (les pages Produits / Commandes s'y rendent via <RouterView>).
 */
import { useRouter } from 'vue-router'
import { useAdminStore } from '../../stores/admin'
import { useI18n } from '../../i18n'

import { ref } from 'vue'
import { api } from '../../api/client'

const router = useRouter()
const admin = useAdminStore()
const { t } = useI18n()

/* ---------- Sidebar rétractable ---------- */
const sidebarCollapsed = ref(localStorage.getItem('pk_sidebar_collapsed') === '1')

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('pk_sidebar_collapsed', sidebarCollapsed.value ? '1' : '0')
}

/* ---------- Changement de mot de passe ---------- */
const passwordOpen = ref(false)
const passwordForm = ref({ current: '', next: '', confirm: '' })
const passwordError = ref('')
const passwordSaving = ref(false)

function openPasswordModal() {
  passwordForm.value = { current: '', next: '', confirm: '' }
  passwordError.value = ''
  passwordOpen.value = true
}

async function submitPassword() {
  if (passwordSaving.value) return
  passwordSaving.value = true
  passwordError.value = ''

  try {
    await api.adminChangePassword(
      passwordForm.value.current,
      passwordForm.value.next,
      passwordForm.value.confirm
    )
    admin.notify('Mot de passe changé avec succès !')
    passwordOpen.value = false
  } catch (error) {
    if (error.errors) {
      const first = Object.values(error.errors)[0]
      passwordError.value = first ? first[0] : 'Erreur de validation.'
    } else {
      passwordError.value = error.message || 'Erreur inconnue.'
    }
  } finally {
    passwordSaving.value = false
  }
}

const nav = [
  { name: 'admin-products', label: 'Produits', icon: 'M21 8l-9-5-9 5v8l9 5 9-5V8zM3.3 8.2L12 13l8.7-4.8M12 13v9' },
  { name: 'admin-categories', label: 'Catégories', icon: 'M4 6h16M4 12h10M4 18h7' },
  { name: 'admin-bundles', label: 'Lots', icon: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4' },
  { name: 'admin-orders', label: 'Commandes', icon: 'M3 3h2l2.6 12.4a2 2 0 002 1.6h8a2 2 0 002-1.6L21 7H6' },
  { name: 'admin-settings', label: 'Réglages', icon: 'M12 15a3 3 0 100-6 3 3 0 000 6z' },
]

async function logout() {
  await admin.logout()
  router.push({ name: 'admin-login' })
}
</script>

<template>
  <div class="admin-shell" :class="{ collapsed: sidebarCollapsed }">
    <aside class="admin-sidebar">
      <router-link to="/admin" class="admin-logo">
        <span class="logo-pill admin-logo-pill"><img src="/logo-planet-kids.png" :alt="t('brand')"></span>
        <em>admin</em>
      </router-link>

      <nav class="admin-nav">
        <router-link
          v-for="item in nav"
          :key="item.name"
          :to="{ name: item.name }"
          class="admin-nav-link"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path :d="item.icon"/></svg>
          <span class="sidebar-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <button class="sidebar-toggle" type="button" @click="toggleSidebar" :aria-label="sidebarCollapsed ? 'Ouvrir le menu' : 'Réduire le menu'">
        <svg v-if="!sidebarCollapsed" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
      </button>

      <div class="admin-sidebar-footer">
        <router-link to="/" class="admin-nav-link muted">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          <span class="sidebar-label">Retour au site</span>
        </router-link>
        <button class="admin-nav-link muted" type="button" @click="logout">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/></svg>
          <span class="sidebar-label">Déconnexion</span>
        </button>
      </div>
    </aside>

    <div class="admin-main">
      <header class="admin-topbar">
        <div class="admin-topbar-title">
          <slot name="title" />
        </div>
        <button class="admin-action" type="button" @click="openPasswordModal" title="Changer le mot de passe">
          🔑
        </button>

        <div class="admin-topbar-user" v-if="admin.user">
          <div class="admin-avatar">{{ admin.user.name.charAt(0) }}</div>
          <div>
            <strong>{{ admin.user.name }}</strong>
            <span>{{ admin.user.email }}</span>
          </div>
        </div>
      </header>

      <main class="admin-content">
        <RouterView />
      </main>
    </div>

    <!-- Modal : changement de mot de passe -->
    <div class="overlay active" v-if="passwordOpen" @click.self="passwordOpen = false"></div>
    <div class="modal-panel active" v-if="passwordOpen" style="max-width: 420px;" role="dialog" aria-modal="true">
      <button class="modal-close" type="button" @click="passwordOpen = false" aria-label="Fermer">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </button>
      <div class="admin-form-head"><h3>🔑 Changer le mot de passe</h3></div>
      <form class="admin-form" @submit.prevent="submitPassword">
        <div class="field">
          <label for="pwdCurrent">Mot de passe actuel *</label>
          <input id="pwdCurrent" v-model="passwordForm.current" type="password" required>
        </div>
        <div class="field">
          <label for="pwdNext">Nouveau mot de passe * (min. 8 caractères)</label>
          <input id="pwdNext" v-model="passwordForm.next" type="password" required minlength="8">
        </div>
        <div class="field">
          <label for="pwdConfirm">Confirmer le nouveau mot de passe *</label>
          <input id="pwdConfirm" v-model="passwordForm.confirm" type="password" required>
        </div>
        <p class="field-error" v-if="passwordError">{{ passwordError }}</p>
        <div class="checkout-actions">
          <button class="btn btn-outline-dark" type="button" @click="passwordOpen = false">Annuler</button>
          <button class="btn btn-gold" type="submit" :disabled="passwordSaving">
            {{ passwordSaving ? 'Enregistrement…' : 'Changer' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Toast global -->
    <transition name="toast">
      <div class="admin-toast" :class="admin.toast?.type" v-if="admin.toast">
        {{ admin.toast.message }}
      </div>
    </transition>
  </div>
</template>
