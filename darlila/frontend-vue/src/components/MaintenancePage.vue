<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useShopStore } from '../stores/shop'
import { useI18n } from '../i18n'
import { api } from '../api/client'
import { waLink, genericMessage } from '../utils/whatsapp'

/**
 * Page d'attente affichée quand l'API répond 503 (mode maintenance).
 * Elle vérifie automatiquement toutes les 20 secondes si la boutique
 * est revenue, et se recharge le cas échéant.
 */
const { t, locale } = useI18n()
const shop = useShopStore()

const COUNTDOWN_FROM = 20
const countdown = ref(COUNTDOWN_FROM)
const checking = ref(false)
let tickTimer = null
let pollTimer = null

const waHref = 'https://chat.whatsapp.com/KJLlKQ6cbQe8GGFmy7UhL6'

async function checkNow() {
  if (checking.value) return
  checking.value = true

  try {
    await api.settings()
    window.location.reload() // la boutique est de retour 🎉
  } catch {
    countdown.value = COUNTDOWN_FROM
  } finally {
    checking.value = false
  }
}

onMounted(() => {
  tickTimer = setInterval(() => {
    if (countdown.value > 0) {
      countdown.value -= 1
    }
    if (countdown.value === 0) checkNow()
  }, 1000)

  pollTimer = setInterval(checkNow, 20000)
})

onUnmounted(() => {
  clearInterval(tickTimer)
  clearInterval(pollTimer)
})
</script>

<template>
  <section class="maintenance-page" :dir="locale === 'ar' ? 'rtl' : 'ltr'">
    <div class="zellige-divider dark" style="position:absolute;top:0;left:0;"></div>

    <div class="maintenance-card">
      <svg class="maintenance-star" viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="1.4">
        <path d="M50 4 L61 39 L96 50 L61 61 L50 96 L39 61 L4 50 L39 39 Z"/>
        <path d="M50 22 L57 43 L78 50 L57 57 L50 78 L43 57 L22 50 L43 43 Z" opacity=".7"/>
        <circle cx="50" cy="50" r="4" fill="currentColor" stroke="none"/>
      </svg>

      <a href="#accueil" class="logo-pill maintenance-logo-pill">
        <img src="/logo-planet-kids.png" :alt="t('brand')">
      </a>
      <p class="maintenance-tagline">{{ t('brand_tagline') }}</p>

      <h1>{{ t('maintenance_title') }}</h1>
      <p class="maintenance-msg">{{ t('maintenance_msg') }}</p>

      <div class="maintenance-countdown">
        <span v-if="checking">{{ t('maintenance_checking') }}</span>
        <template v-else>
          {{ t('maintenance_next_check') }} <strong>{{ countdown }}</strong> {{ t('maintenance_seconds') }}
        </template>
      </div>

      <div class="maintenance-actions">
        <button class="btn btn-outline" type="button" :disabled="checking" @click="checkNow">
          {{ t('maintenance_retry') }}
        </button>

        <a class="btn btn-gold" :href="waHref" target="_blank" rel="noopener">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.87 9.87 0 0012.04 2zm5.79 14.02c-.24.68-1.4 1.32-1.93 1.4-.5.08-1.12.11-1.81-.11-.42-.13-.95-.31-1.64-.6-2.9-1.25-4.79-4.17-4.94-4.36-.14-.2-1.18-1.57-1.18-3 0-1.42.75-2.12 1.01-2.41.27-.29.58-.36.78-.36.19 0 .39 0 .55.01.18.01.42-.07.65.5.24.58.82 2 .89 2.14.07.15.12.32.02.51-.09.2-.14.32-.28.49-.14.17-.29.38-.42.51-.14.14-.28.29-.12.57.16.28.72 1.19 1.55 1.93 1.06.95 1.96 1.24 2.24 1.38.28.14.44.12.61-.07.16-.19.7-.82.89-1.1.19-.28.37-.23.62-.14.25.09 1.6.75 1.87.89.28.14.46.21.53.32.07.12.07.68-.17 1.36z"/></svg>
          <span>{{ t('maintenance_wa') }}</span>
        </a>
      </div>

      <router-link class="maintenance-admin-link" to="/admin">
        {{ t('maintenance_admin') }}
      </router-link>
    </div>
  </section>
</template>
