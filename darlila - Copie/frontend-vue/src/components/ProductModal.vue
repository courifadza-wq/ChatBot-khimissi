<script setup>
import { computed, ref, watch } from 'vue'
import { useUiStore } from '../stores/ui'
import { useCartStore } from '../stores/cart'
import { useShopStore } from '../stores/shop'
import { useI18n, formatPrice } from '../i18n'
import { waLink, singleItemMessage } from '../utils/whatsapp'
import { hasPromo, unitPriceFor } from '../utils/pricing'

const { t, pick, locale } = useI18n()
const ui = useUiStore()
const cart = useCartStore()
const shop = useShopStore()

const qty = ref(1)
// Copie locale pour laisser jouer la transition de fermeture
const current = ref(null)
let hideTimer = null

watch(
  () => ui.activeProduct,
  (product) => {
    clearTimeout(hideTimer)
    if (product) {
      qty.value = 1
      current.value = product
    } else {
      hideTimer = setTimeout(() => (current.value = null), 450)
    }
  }
)

const isOpen = computed(() => ui.activeProduct !== null)

const promo = computed(() => hasPromo(current.value))
const promoApplied = computed(
  () => promo.value && qty.value >= current.value.promo_quantity
)
const effectiveUnit = computed(() =>
  current.value ? unitPriceFor(current.value, qty.value) : 0
)

const waHref = computed(() => {
  if (!current.value) return '#'
  const name = pick(current.value, 'name')
  return waLink(shop.whatsappNumber, singleItemMessage(name, effectiveUnit.value, qty.value, locale.value))
})

function addCurrentToCart() {
  if (!current.value) return
  cart.add(current.value.id, qty.value)
  ui.closeProduct()
  ui.openCart()
}

// Bloque le scroll de la page quand la modale est ouverte
// (sans déverrouiller si le panier vient de s'ouvrir)
watch(isOpen, (open) => {
  if (open) {
    document.body.style.overflow = 'hidden'
  } else if (!ui.cartOpen) {
    document.body.style.overflow = ''
  }
})
</script>

<template>
  <div class="overlay" :class="{ active: isOpen }" @click="ui.closeProduct()"></div>

  <div class="modal-panel" :class="{ active: isOpen }" role="dialog" aria-modal="true">
    <button class="modal-close" type="button" @click="ui.closeProduct()" aria-label="Fermer">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6L6 18"/></svg>
    </button>

    <template v-if="current">
      <img class="pm-img" :src="current.image" :alt="pick(current, 'name')">

      <div class="pm-body">
        <h3>{{ pick(current, 'name') }}</h3>
        <div class="pm-price">
          <template v-if="promoApplied">
            <span class="price-struck">{{ formatPrice(current.price, locale) }}</span>
            <span class="price-discounted">{{ formatPrice(effectiveUnit, locale) }}</span>
          </template>
          <template v-else>{{ formatPrice(current.price, locale) }}</template>
        </div>
        <p class="pm-promo" v-if="promo">
          {{ t('promo_hint', { quantity: current.promo_quantity, percent: current.promo_percent }) }}
        </p>
        <p class="pm-desc">{{ pick(current, 'description') }}</p>

        <div class="pm-qty">
          <span>{{ t('pm_qty') }}</span>
          <div class="qty-stepper">
            <button type="button" @click="qty = Math.max(1, qty - 1)">−</button>
            <span>{{ qty }}</span>
            <button type="button" @click="qty = Math.min(99, qty + 1)">+</button>
          </div>
        </div>

        <div class="pm-actions">
          <button
            class="btn btn-outline"
            style="border-color: rgba(23,21,18,.2); color: var(--indigo-deep);"
            type="button"
            @click="addCurrentToCart"
          >
            {{ t('pm_add') }}
          </button>

          <a class="btn btn-wa-solid" :href="waHref" target="_blank" rel="noopener">
            <svg viewBox="0 0 24 24" fill="currentColor" style="width:16px;height:16px;"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.87 9.87 0 0012.04 2zm5.79 14.02c-.24.68-1.4 1.32-1.93 1.4-.5.08-1.12.11-1.81-.11-.42-.13-.95-.31-1.64-.6-2.9-1.25-4.79-4.17-4.94-4.36-.14-.2-1.18-1.57-1.18-3 0-1.42.75-2.12 1.01-2.41.27-.29.58-.36.78-.36.19 0 .39 0 .55.01.18.01.42-.07.65.5.24.58.82 2 .89 2.14.07.15.12.32.02.51-.09.2-.14.32-.28.49-.14.17-.29.38-.42.51-.14.14-.28.29-.12.57.16.28.72 1.19 1.55 1.93 1.06.95 1.96 1.24 2.24 1.38.28.14.44.12.61-.07.16-.19.7-.82.89-1.1.19-.28.37-.23.62-.14.25.09 1.6.75 1.87.89.28.14.46.21.53.32.07.12.07.68-.17 1.36z"/></svg>
            <span>{{ t('pm_order') }}</span>
          </a>
        </div>
      </div>
    </template>
  </div>
</template>
