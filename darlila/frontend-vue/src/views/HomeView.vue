<script setup>
import { onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'
import { useShopStore } from '../stores/shop'
import { useUiStore } from '../stores/ui'

import WhatsAppTicker from '../components/WhatsAppTicker.vue'
import SiteHeader from '../components/SiteHeader.vue'
import HeroSection from '../components/HeroSection.vue'
import UspSection from '../components/UspSection.vue'
import ZelligeDivider from '../components/ZelligeDivider.vue'
import ShopSection from '../components/ShopSection.vue'
import BundlesSection from '../components/BundlesSection.vue'
import GallerySection from '../components/GallerySection.vue'
import ReviewsSection from '../components/ReviewsSection.vue'
import LocationSection from '../components/LocationSection.vue'
import CtaBand from '../components/CtaBand.vue'
import SiteFooter from '../components/SiteFooter.vue'
import ChatBotWidget from '../components/ChatBotWidget.vue'
import ProductModal from '../components/ProductModal.vue'
import CartDrawer from '../components/CartDrawer.vue'
import Lightbox from '../components/Lightbox.vue'
import MaintenancePage from '../components/MaintenancePage.vue'
import PwaInstallBanner from '../components/PwaInstallBanner.vue'

const shop = useShopStore()
const ui = useUiStore()
const route = useRoute()

// Chargement initial du catalogue depuis l'API Laravel
onMounted(() => {
  shop.fetchAll()
  openProductFromRoute()
})

// Lien direct /produit/{slug} : charge le produit puis ouvre sa modale
async function openProductFromRoute() {
  const slug = route.params.slug
  if (!slug) return

  try {
    const product = await api.product(slug)
    if (product) ui.openProduct(product)
  } catch {
    /* produit introuvable → la boutique s'affiche normalement */
  }
}

watch(
  () => route.params.slug,
  () => openProductFromRoute()
)

// Échap : ferme la visionneuse, la modale produit ou le panier (comme l'original)
const onKeydown = (event) => {
  if (event.key !== 'Escape') return
  if (ui.lightboxIndex !== null) ui.closeLightbox()
  else if (ui.activeProduct) ui.closeProduct()
  else if (ui.cartOpen) ui.closeCart()
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <!-- Mode maintenance : page d'attente plein écran -->
  <MaintenancePage v-if="shop.maintenance" />

  <template v-else>
    <WhatsAppTicker />
    <SiteHeader />

    <main>
      <HeroSection />
      <UspSection />
      <ZelligeDivider theme="light" />
      <ShopSection />
      <BundlesSection />
      <ZelligeDivider theme="dark" />
      <GallerySection />
      <ReviewsSection />
      <LocationSection />
      <CtaBand />
    </main>

    <SiteFooter />
    <ChatBotWidget />

    <!-- Surcouches globales -->
    <PwaInstallBanner />
    <ProductModal />
    <CartDrawer />
    <Lightbox />
  </template>
</template>
