<script setup>
import { computed, ref } from 'vue'
import { useUiStore } from '../stores/ui'
import { useCartStore } from '../stores/cart'
import { useI18n, formatPrice } from '../i18n'
import { hasPromo } from '../utils/pricing'

const props = defineProps({
  product: { type: Object, required: true },
})

const promo = computed(() => hasPromo(props.product))

const { t, pick, locale } = useI18n()
const ui = useUiStore()
const cart = useCartStore()

const justAdded = ref(false)

function quickAdd() {
  cart.add(props.product.id, 1)
  justAdded.value = true
  setTimeout(() => (justAdded.value = false), 900)
}
</script>

<template>
  <div class="product-card">
    <div class="product-media" @click="ui.openProduct(product)">
      <img :src="product.image" :alt="pick(product, 'name')" loading="lazy">
      <span class="product-badge">{{ pick(product.category, 'name') }}</span>
      <span class="promo-badge" v-if="promo">-{{ product.promo_percent }}%</span>
    </div>

    <div class="product-body">
      <h3 style="cursor: pointer" @click="ui.openProduct(product)">
        {{ pick(product, 'name') }}
      </h3>

      <div class="product-price">
        {{ formatPrice(product.price, locale) }}
        <small class="promo-hint" v-if="promo">−{{ product.promo_percent }}% ×{{ product.promo_quantity }}</small>
      </div>

      <div class="product-actions">
        <button class="btn-detail" type="button" @click="ui.openProduct(product)">
          {{ t('prod_detail') }}
        </button>
        <button
          class="btn-cart-add"
          :class="{ added: justAdded }"
          type="button"
          :aria-label="t('prod_add')"
          @click="quickAdd"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 3h2l2.6 12.4a2 2 0 002 1.6h8a2 2 0 002-1.6L21 7H6"/><circle cx="9.5" cy="20.5" r="1.4"/><circle cx="17.5" cy="20.5" r="1.4"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>
