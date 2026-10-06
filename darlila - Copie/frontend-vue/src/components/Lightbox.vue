<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useShopStore } from '../stores/shop'
import { useUiStore } from '../stores/ui'
import { useI18n } from '../i18n'

const { pick } = useI18n()
const shop = useShopStore()
const ui = useUiStore()

const isOpen = computed(() => ui.lightboxIndex !== null)
const current = computed(() =>
  ui.lightboxIndex !== null ? shop.gallery[ui.lightboxIndex] : null
)

function showDelta(delta) {
  if (ui.lightboxIndex === null || shop.gallery.length === 0) return
  const total = shop.gallery.length
  ui.lightboxIndex = (ui.lightboxIndex + delta + total) % total
}

// Navigation clavier (flèches, en tenant compte du sens RTL)
const onKeydown = (event) => {
  if (!isOpen.value) return
  const rtl = document.documentElement.dir === 'rtl'
  if (event.key === 'ArrowRight') showDelta(rtl ? -1 : 1)
  if (event.key === 'ArrowLeft') showDelta(rtl ? 1 : -1)
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div class="lightbox" :class="{ active: isOpen }" @click.self="ui.closeLightbox()">
    <button class="lightbox-close" type="button" @click="ui.closeLightbox()" aria-label="Fermer">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6L6 18"/></svg>
    </button>

    <button class="lightbox-nav lightbox-prev" type="button" @click="showDelta(-1)" aria-label="Précédent">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
    </button>

    <img v-if="current" :src="current.image" :alt="pick(current, 'alt')">

    <button class="lightbox-nav lightbox-next" type="button" @click="showDelta(1)" aria-label="Suivant">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
    </button>
  </div>
</template>
