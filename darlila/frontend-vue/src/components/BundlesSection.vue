<script setup>
import { useShopStore } from '../stores/shop'
import { useCartStore } from '../stores/cart'
import { useI18n } from '../i18n'
import BundleCard from './BundleCard.vue'

/**
 * Section « Nos lots » : bundles à prix réduit avec prix cumulé barré.
 * Chaque carte affiche un carrousel des images des produits du lot.
 */
const { t } = useI18n()
const shop = useShopStore()
const cart = useCartStore()

function addBundle(bundle) {
  cart.addBundle(bundle.id, 1)
  cart.hydrate()
}
</script>

<template>
  <section class="section bundles" id="lots" v-if="shop.bundles.length > 0">
    <div class="container">
      <div class="section-head" v-reveal>
        <div class="eyebrow"><span class="line"></span><span>{{ t('bundles_eyebrow') }}</span></div>
        <h2>{{ t('bundles_title') }}</h2>
        <p class="lead">{{ t('bundles_lead') }}</p>
      </div>

      <div class="bundles-grid" v-reveal="'stagger'">
        <BundleCard
          v-for="bundle in shop.bundles"
          :key="bundle.id"
          :bundle="bundle"
          @add="addBundle"
        />
      </div>
    </div>
  </section>
</template>
