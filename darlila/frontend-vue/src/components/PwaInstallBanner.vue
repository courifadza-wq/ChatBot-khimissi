<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from '../i18n'

/**
 * Invite d'installation élégante (PWA) :
 *
 *  • Android / Chrome/Edge : l'événement `beforeinstallprompt` est capté,
 *    la bannière propose « Installer » → dialogue natif du navigateur.
 *  • iPhone / Safari : pas d'événement — la bannière affiche la marche à
 *    suivre (Partager → Sur l'écran d'accueil).
 *  • Déjà installée (mode standalone) : jamais affichée.
 *  • Refus mémorisé 7 jours (localStorage).
 */
const { t, locale } = useI18n()

const DISMISS_KEY = 'darlila_pwa_dismissed_until'

const deferredPrompt = ref(null)
const dismissed = ref(false)
const ready = ref(false)

const isStandalone = computed(() =>
  window.matchMedia('(display-mode: standalone)').matches
  || window.navigator.standalone === true
)

const isIos = computed(
  () => /iphone|ipad|ipod/i.test(window.navigator.userAgent)
    && !/crios|fxios|edgios/i.test(window.navigator.userAgent) // pas Chrome/Firefox sur iOS
)

const showAndroid = computed(() => deferredPrompt.value !== null)
const showIosHint = computed(() => isIos.value)
const visible = computed(
  () => ready.value && !dismissed.value && !isStandalone.value && (showAndroid.value || showIosHint.value)
)

function onBeforeInstallPrompt(event) {
  event.preventDefault()
  deferredPrompt.value = event
}

async function install() {
  const prompt = deferredPrompt.value
  if (!prompt) return

  prompt.prompt()
  const choice = await prompt.userChoice

  if (choice.outcome === 'accepted') {
    deferredPrompt.value = null
  }
}

function dismiss(days = 7) {
  dismissed.value = true
  localStorage.setItem(DISMISS_KEY, String(Date.now() + days * 86400000))
}

onMounted(() => {
  const until = Number(localStorage.getItem(DISMISS_KEY) || 0)
  dismissed.value = Date.now() < until

  window.addEventListener('beforeinstallprompt', onBeforeInstallPrompt)
  window.addEventListener('appinstalled', () => (deferredPrompt.value = null))

  // petit délai pour ne pas perturber l'entrée sur la page
  setTimeout(() => (ready.value = true), 2500)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeinstallprompt', onBeforeInstallPrompt)
})
</script>

<template>
  <transition name="pwa-banner">
    <aside class="pwa-banner" v-if="visible" :dir="locale === 'ar' ? 'rtl' : 'ltr'">
      <img src="/pwa-192x192.png" alt="Planet Kids" class="pwa-banner-icon">

      <div class="pwa-banner-text">
        <strong>{{ t('pwa_title') }}</strong>
        <span v-if="showAndroid">{{ t('pwa_text') }}</span>
        <span v-else>{{ t('pwa_text_ios') }}</span>
      </div>

      <button
        v-if="showAndroid"
        class="btn btn-gold pwa-banner-btn"
        type="button"
        @click="install"
      >
        {{ t('pwa_install') }}
      </button>

      <button class="pwa-banner-close" type="button" :aria-label="t('pwa_close')" @click="dismiss()">
        ✕
      </button>
    </aside>
  </transition>
</template>
