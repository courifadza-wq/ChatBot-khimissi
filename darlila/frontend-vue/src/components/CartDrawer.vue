<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useUiStore } from '../stores/ui'
import { useCartStore } from '../stores/cart'
import { useShopStore } from '../stores/shop'
import { useI18n, formatPrice } from '../i18n'
import { unitPriceFor } from '../utils/pricing'
import { api } from '../api/client'
import { WILAYAS } from '../utils/wilayas'

const { t, pick, locale } = useI18n()
const ui = useUiStore()
const cart = useCartStore()
const shop = useShopStore()

/** étape courante : 'cart' | 'form' | 'success' */
const step = ref('cart')
const sending = ref(false)
const serverError = ref('')
const errors = ref({})
const success = ref(null)

const form = reactive({
  customer_name: '',
  customer_phone: '',
  wilaya: '',
  notes: '',
})

// Réinitialise l'étape à chaque ouverture du tiroir
watch(
  () => ui.cartOpen,
  (open) => {
    if (open) {
      step.value = 'cart'
      serverError.value = ''
      errors.value = {}
      document.body.style.overflow = 'hidden'
      // Hydrate les articles dont le produit n'est pas encore connu
      // (catalogue paginé : l'article peut ne pas être sur la page courante)
      cart.hydrate()
    } else if (!ui.activeProductSlug) {
      document.body.style.overflow = ''
    }
  }
)

const isOpen = computed(() => ui.cartOpen)

/** Résumé du contenu d'un lot, ex. « 2× Jasmin + 1× Oud ». */
function bundleContents(item) {
  const parts = (item.product.contents || []).map((line) => {
    const name = locale.value === 'ar' ? line.product.name_ar : line.product.name_fr
    return `${line.quantity}× ${name}`
  })

  return parts.join(' + ')
}

function startCheckout() {
  if (cart.count === 0) return
  serverError.value = ''
  errors.value = {}
  step.value = 'form'
}

/** Validation côté client (Laravel revalide tout côté serveur). */
function validate() {
  const next = {}
  if (form.customer_name.trim().length < 2) next.customer_name = [t('field_required')]
  if (!/^[0-9+\s().-]{9,20}$/.test(form.customer_phone.trim())) next.customer_phone = [t('field_required')]
  if (!form.wilaya) next.wilaya = [t('field_required')]
  errors.value = next
  return Object.keys(next).length === 0
}

async function submitOrder() {
  if (!validate() || sending.value) return

  sending.value = true
  serverError.value = ''

  try {
    // 1) Enregistrement de la commande dans Laravel (prix recalculés côté serveur)
    const data = await api.createOrder({
      customer_name: form.customer_name.trim(),
      customer_phone: form.customer_phone.trim(),
      wilaya: form.wilaya,
      notes: form.notes.trim() || null,
      lang: locale.value,
      items: cart.toOrderPayload().items,
    })

    success.value = data
    cart.clear()
    step.value = 'success'

    // 2) Ouverture de WhatsApp avec le récapitulatif généré par l'API
    //    (peut être bloqué par le navigateur : un bouton de secours est affiché)
    if (data.whatsapp_url) {
      window.open(data.whatsapp_url, '_blank', 'noopener')
    }
  } catch (error) {
    if (error.errors) {
      errors.value = error.errors
      serverError.value = t('form_error')
    } else if (error.status === 0) {
      serverError.value = t('error_title')
    } else {
      serverError.value = error.message
    }
  } finally {
    sending.value = false
  }
}

function finish() {
  step.value = 'cart'
  success.value = null
  ui.closeCart()
}
</script>

<template>
  <div class="overlay" :class="{ active: isOpen }" @click="ui.closeCart()"></div>

  <aside class="cart-drawer" :class="{ active: isOpen }" role="dialog" aria-modal="true">
    <div class="cart-head">
      <h3>{{ t('cart_title') }}</h3>
      <button class="modal-close" style="position: static" type="button" @click="ui.closeCart()" aria-label="Fermer">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </button>
    </div>

    <!-- ============ ÉTAPE 1 : PANIER ============ -->
    <template v-if="step === 'cart'">
      <div class="cart-items">
        <p class="cart-empty" v-if="cart.detailedItems.length === 0">{{ t('cart_empty') }}</p>

        <div class="cart-item" v-for="item in cart.detailedItems" :key="item.key">
          <img :src="item.product.image" :alt="pick(item.product, 'name')">
          <div class="cart-item-info">
            <h4>
              {{ pick(item.product, 'name') }}
              <span class="ci-bundle-tag" v-if="item.product.isBundle">{{ t('bundle_tag') }}</span>
            </h4>

            <!-- Prix unitaire : barré si promo appliquée à cette quantité -->
            <div class="ci-price">
              <template v-if="!item.product.isBundle && unitPriceFor(item.product, item.qty) < item.product.price">
                <span class="price-struck">{{ formatPrice(item.product.price, locale) }}</span>
                <span class="price-discounted">{{ formatPrice(unitPriceFor(item.product, item.qty), locale) }}</span>
              </template>
              <template v-else>{{ formatPrice(item.product.price, locale) }}</template>
            </div>

            <!-- Composition du lot -->
            <p class="ci-contents" v-if="item.product.isBundle">
              {{ bundleContents(item) }}
            </p>

            <div class="ci-row">
              <div class="ci-qty">
                <button type="button" @click="cart.changeQty(item.type, item.id, -1)">−</button>
                <span>{{ item.qty }}</span>
                <button type="button" @click="cart.changeQty(item.type, item.id, 1)">+</button>
              </div>
              <button class="ci-remove" type="button" @click="cart.remove(item.type, item.id)">{{ t('cart_remove') }}</button>
            </div>
          </div>
        </div>

        <div class="cart-recommendations" v-if="cart.recommendations.length">
          <h4>{{ t('cart_reco') }}</h4>
          <div class="reco-list">
            <div class="reco-card" v-for="product in cart.recommendations" :key="product.id">
              <img :src="product.image" :alt="pick(product, 'name')">
              <div>
                <strong>{{ pick(product, 'name') }}</strong>
                <small>{{ formatPrice(product.price, locale) }}</small>
              </div>
              <button type="button" :aria-label="t('cart_reco_add')" @click="cart.add(product.id, 1)">+</button>
            </div>
          </div>
        </div>
      </div>

      <div class="cart-footer">
        <div class="cart-total">
          <span>{{ t('cart_total') }}</span>
          <span>
            <span class="price-struck" v-if="cart.hasDiscounts">{{ formatPrice(cart.regularTotal, locale) }}</span>
            <strong>{{ formatPrice(cart.total, locale) }}</strong>
            <em class="cart-savings" v-if="cart.hasDiscounts">{{ t('savings', { amount: formatPrice(cart.regularTotal - cart.total, locale) }) }}</em>
          </span>
        </div>
        <button class="btn btn-wa-solid" type="button" :disabled="cart.count === 0" @click="startCheckout">
          <svg viewBox="0 0 24 24" fill="currentColor" style="width:16px;height:16px;"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.87 9.87 0 0012.04 2zm5.79 14.02c-.24.68-1.4 1.32-1.93 1.4-.5.08-1.12.11-1.81-.11-.42-.13-.95-.31-1.64-.6-2.9-1.25-4.79-4.17-4.94-4.36-.14-.2-1.18-1.57-1.18-3 0-1.42.75-2.12 1.01-2.41.27-.29.58-.36.78-.36.19 0 .39 0 .55.01.18.01.42-.07.65.5.24.58.82 2 .89 2.14.07.15.12.32.02.51-.09.2-.14.32-.28.49-.14.17-.29.38-.42.51-.14.14-.28.29-.12.57.16.28.72 1.19 1.55 1.93 1.06.95 1.96 1.24 2.24 1.38.28.14.44.12.61-.07.16-.19.7-.82.89-1.1.19-.28.37-.23.62-.14.25.09 1.6.75 1.87.89.28.14.46.21.53.32.07.12.07.68-.17 1.36z"/></svg>
          <span>{{ t('cart_order') }}</span>
        </button>
      </div>
    </template>

    <!-- ============ ÉTAPE 2 : COORDONNÉES ============ -->
    <div class="checkout-panel" v-else-if="step === 'form'">
      <h4>{{ t('checkout_title') }}</h4>
      <p class="checkout-intro">{{ t('checkout_intro') }}</p>

      <div class="field" :class="{ invalid: errors.customer_name }">
        <label for="ckName">{{ t('checkout_name') }}</label>
        <input id="ckName" v-model.trim="form.customer_name" type="text" autocomplete="name">
        <p class="field-error" v-if="errors.customer_name">{{ errors.customer_name[0] }}</p>
      </div>

      <div class="field" :class="{ invalid: errors.customer_phone }">
        <label for="ckPhone">{{ t('checkout_phone') }}</label>
        <input id="ckPhone" v-model.trim="form.customer_phone" type="tel" autocomplete="tel" placeholder="05 55 00 00 00">
        <p class="field-error" v-if="errors.customer_phone">{{ errors.customer_phone[0] }}</p>
      </div>

      <div class="field" :class="{ invalid: errors.wilaya }">
        <label for="ckWilaya">{{ t('checkout_wilaya') }}</label>
        <select id="ckWilaya" v-model="form.wilaya">
          <option value="" disabled>—</option>
          <option v-for="wilaya in WILAYAS" :key="wilaya" :value="wilaya">{{ wilaya }}</option>
        </select>
        <p class="field-error" v-if="errors.wilaya">{{ errors.wilaya[0] }}</p>
      </div>

      <div class="field">
        <label for="ckNotes">{{ t('checkout_notes') }}</label>
        <textarea id="ckNotes" v-model.trim="form.notes" rows="2"></textarea>
      </div>

      <div class="checkout-summary">
        <div class="cart-total">
          <span>{{ t('cart_total') }}</span>
          <span>{{ formatPrice(cart.total, locale) }}</span>
        </div>
      </div>

      <p class="form-error" v-if="serverError">{{ serverError }}</p>

      <div class="checkout-actions">
        <button class="btn btn-outline-dark" type="button" @click="step = 'cart'">← {{ t('back') }}</button>
        <button class="btn btn-wa-solid" type="button" :disabled="sending" @click="submitOrder">
          {{ sending ? t('checkout_sending') : t('checkout_submit') }}
        </button>
      </div>
    </div>

    <!-- ============ ÉTAPE 3 : CONFIRMATION ============ -->
    <div class="checkout-success" v-else-if="success">
      <div class="success-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M20 6L9 17l-5-5"/></svg>
      </div>
      <h4>{{ t('checkout_success_title') }}</h4>
      <p class="success-ref">{{ t('checkout_success_ref') }} : <strong>{{ success.reference }}</strong></p>
      <p class="success-msg">{{ t('checkout_success_msg') }}</p>

      <a class="btn btn-wa-solid" :href="success.whatsapp_url" target="_blank" rel="noopener">
        <svg viewBox="0 0 24 24" fill="currentColor" style="width:16px;height:16px;"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.87 9.87 0 0012.04 2zm5.79 14.02c-.24.68-1.4 1.32-1.93 1.4-.5.08-1.12.11-1.81-.11-.42-.13-.95-.31-1.64-.6-2.9-1.25-4.79-4.17-4.94-4.36-.14-.2-1.18-1.57-1.18-3 0-1.42.75-2.12 1.01-2.41.27-.29.58-.36.78-.36.19 0 .39 0 .55.01.18.01.42-.07.65.5.24.58.82 2 .89 2.14.07.15.12.32.02.51-.09.2-.14.32-.28.49-.14.17-.29.38-.42.51-.14.14-.28.29-.12.57.16.28.72 1.19 1.55 1.93 1.06.95 1.96 1.24 2.24 1.38.28.14.44.12.61-.07.16-.19.7-.82.89-1.1.19-.28.37-.23.62-.14.25.09 1.6.75 1.87.89.28.14.46.21.53.32.07.12.07.68-.17 1.36z"/></svg>
        <span>{{ t('cta_btn') }}</span>
      </a>

      <button class="btn btn-outline-dark" type="button" @click="finish">{{ t('checkout_back') }}</button>
    </div>
  </aside>
</template>
