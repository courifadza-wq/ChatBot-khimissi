import { defineStore } from 'pinia'
import { api, setAuthToken } from '../api/client'

/**
 * Store « administration » : session Sanctum (token + utilisateur),
 * notifications toast et gestion centralisée des erreurs 401.
 */
export const useAdminStore = defineStore('admin', {
  state: () => ({
    token: localStorage.getItem('darlila_admin_token') || null,
    user: null,
    loggingIn: false,
    toast: null, // { message, type: 'success' | 'error' }
    toastTimer: null,
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },

  actions: {
    /**
     * Connexion : stocke le token Sanctum et l'utilisateur.
     * Lève l'erreur (avec .errors) en cas d'identifiants invalides.
     */
    async login(email, password) {
      this.loggingIn = true
      try {
        const data = await api.login(email, password)
        if (!data || !data.token) {
          throw new Error('Réponse invalide du serveur (token manquant).')
        }
        this.token = data.token
        this.user = data.user
        setAuthToken(data.token)
        return true
      } finally {
        this.loggingIn = false
      }
    },

    /**
     * Vérifie la session courante (GET /api/auth/me).
     * Retourne false et purge la session si le token est invalide.
     */
    async verifySession() {
      if (!this.token) return false
      try {
        this.user = await api.me()
        return true
      } catch {
        this.clearSession()
        return false
      }
    },

    async logout() {
      try {
        await api.logout()
      } catch {
        // token déjà révoqué/expiré : on ignore
      }
      this.clearSession()
    },

    clearSession() {
      this.token = null
      this.user = null
      setAuthToken(null)
    },

    /**
     * Gestion centralisée des erreurs d'appel API dans l'admin.
     * 401 → session expirée (déconnexion + redirection).
     */
    handleApiError(error, router) {
      if (error?.status === 401) {
        this.clearSession()
        this.notify('Session expirée, veuillez vous reconnecter.', 'error')
        if (router) router.push({ name: 'admin-login' })
        return
      }
      this.notify(error?.message || 'Une erreur est survenue.', 'error')
    },

    /** Petit toast en bas à droite (rendu par AdminLayout). */
    notify(message, type = 'success') {
      clearTimeout(this.toastTimer)
      this.toast = { message, type }
      this.toastTimer = setTimeout(() => (this.toast = null), 3200)
    },
  },
})
