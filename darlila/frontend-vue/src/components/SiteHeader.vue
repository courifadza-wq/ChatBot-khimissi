<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useUiStore } from '../stores/ui'
import { useCartStore } from '../stores/cart'
import { useShopStore } from '../stores/shop'
import { useI18n } from '../i18n'
import { waLink, genericMessage } from '../utils/whatsapp'

const { t, locale, setLocale } = useI18n()
const ui = useUiStore()
const cart = useCartStore()
const shop = useShopStore()

const scrolled = ref(false)
const onScroll = () => {
  scrolled.value = window.scrollY > 60
}
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))

const links = [
  { href: '#accueil', key: 'nav_home' },
  { href: '#apropos', key: 'nav_about' },
  { href: '#boutique', key: 'nav_shop' },
  { href: '#galerie', key: 'nav_gallery' },
  { href: '#avis', key: 'nav_reviews' },
  { href: '#contact', key: 'nav_contact' },
]

const waHref = 'https://chat.whatsapp.com/KJLlKQ6cbQe8GGFmy7UhL6'
</script>

<template>
  <header id="siteHeader" :class="{ scrolled }">
    <div class="container nav-wrap">
      <a href="#accueil" class="logo-pill" :aria-label="t('brand')">
        <img src="/logo-planet-kids.png" :alt="t('brand')">
      </a>

      <nav class="links" :class="{ open: ui.burgerOpen }" @click="ui.burgerOpen = false">
        <a v-for="link in links" :key="link.key" :href="link.href" @click="ui.burgerOpen = false">
          {{ t(link.key) }}
        </a>
      </nav>

      <div class="header-actions">
        <div class="lang-toggle">
          <button id="btnFr" :class="{ active: locale === 'fr' }" type="button" @click="setLocale('fr')">FR</button>
          <button id="btnAr" :class="{ active: locale === 'ar' }" type="button" @click="setLocale('ar')">AR</button>
        </div>

        <a class="header-wa" :href="waHref" target="_blank" rel="noopener">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.87 9.87 0 0012.04 2zm5.79 14.02c-.24.68-1.4 1.32-1.93 1.4-.5.08-1.12.11-1.81-.11-.42-.13-.95-.31-1.64-.6-2.9-1.25-4.79-4.17-4.94-4.36-.14-.2-1.18-1.57-1.18-3 0-1.42.75-2.12 1.01-2.41.27-.29.58-.36.78-.36.19 0 .39 0 .55.01.18.01.42-.07.65.5.24.58.82 2 .89 2.14.07.15.12.32.02.51-.09.2-.14.32-.28.49-.14.17-.29.38-.42.51-.14.14-.28.29-.12.57.16.28.72 1.19 1.55 1.93 1.06.95 1.96 1.24 2.24 1.38.28.14.44.12.61-.07.16-.19.7-.82.89-1.1.19-.28.37-.23.62-.14.25.09 1.6.75 1.87.89.28.14.46.21.53.32.07.12.07.68-.17 1.36z"/></svg>
          <span>{{ t('header_wa') }}</span>
        </a>

        <button class="cart-icon-btn" type="button" aria-label="Panier" @click="ui.openCart()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 3h2l2.6 12.4a2 2 0 002 1.6h8a2 2 0 002-1.6L21 7H6"/><circle cx="9.5" cy="20.5" r="1.4"/><circle cx="17.5" cy="20.5" r="1.4"/></svg>
          <span class="cart-count" v-show="cart.count > 0">{{ cart.count }}</span>
        </button>

        <button class="burger" :class="{ open: ui.burgerOpen }" type="button" aria-label="Menu" @click="ui.burgerOpen = !ui.burgerOpen">
          <span></span><span></span><span></span>
        </button>
      </div>
    </div>
  </header>
</template>
