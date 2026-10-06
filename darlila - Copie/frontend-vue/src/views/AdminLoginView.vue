<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAdminStore } from '../stores/admin'
import { useI18n } from '../i18n'

const router = useRouter()
const route = useRoute()
const admin = useAdminStore()

const form = reactive({ email: 'admin@planetkids.dz', password: '' })
const errors = ref({})
const { t } = useI18n()
const submitting = ref(false)

async function submit() {
  if (submitting.value) return
  submitting.value = true
  errors.value = {}
  try {
    await admin.login(form.email.trim(), form.password)
    admin.notify('Bienvenue ! Connexion réussie.')
    router.push(route.query.redirect || { name: 'admin-products' })
  } catch (error) {
    errors.value = error.errors || { email: [error.message || 'Connexion impossible.'] }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="admin-login-page">
    <div class="zellige-divider dark" style="position:absolute;top:0;left:0;"></div>

    <form class="admin-login-card" @submit.prevent="submit">
      <a href="#accueil" class="logo-pill admin-login-logo-pill">
        <img src="/logo-planet-kids.png" alt="Planet Kids">
      </a>
      <p class="admin-login-sub">Espace d'administration — {{ t('brand_tagline') }}</p>

      <div class="field" :class="{ invalid: errors.email }">
        <label for="loginEmail">Adresse e-mail</label>
        <input id="loginEmail" v-model.trim="form.email" type="email" autocomplete="username" required>
        <p class="field-error" v-if="errors.email">{{ errors.email[0] }}</p>
      </div>

      <div class="field" :class="{ invalid: errors.password }">
        <label for="loginPassword">Mot de passe</label>
        <input id="loginPassword" v-model="form.password" type="password" autocomplete="current-password" required>
        <p class="field-error" v-if="errors.password">{{ errors.password[0] }}</p>
      </div>

      <button class="btn btn-gold admin-login-btn" type="submit" :disabled="admin.loggingIn">
        {{ admin.loggingIn ? 'Connexion…' : 'Se connecter' }}
      </button>

      <router-link class="admin-login-back" to="/">← Retour à la boutique</router-link>
    </form>
  </div>
</template>
