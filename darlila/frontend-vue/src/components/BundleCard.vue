<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n, formatPrice } from '../i18n'

/**
 * Carte d'un lot — carrousel automatique présentant CHAQUE produit
 * du lot en détail : image plein cadre, nom, description courte,
 * quantité dans le lot et prix unitaire, sur une superposition
 * élégante (dégradé indigo, accents or).
 *
 * Comportements PRO : défilement auto (barre de progression or),
 * pause au survol, flèches, points de navigation, compteur 1/3.
 */
const props = defineProps({
  bundle: { type: Object, required: true },
})

const emit = defineEmits(['add'])

const { t, pick, locale } = useI18n()

/* ---------- Slides : détail de chaque produit du lot ---------- */
const AUTOPLAY_MS = 4000

const slides = computed(() =>
  (props.bundle.items || [])
    .filter((line) => line.product)
    .map((line) => {
      const product = line.product

      return {
        image: product.image,
        name: locale.value === 'ar' ? product.name_ar : product.name_fr,
        description: locale.value === 'ar' ? product.description_ar : product.description_fr,
        quantity: line.quantity,
        unitPrice: product.price,
      }
    })
)

const index = ref(0)
let timer = null
let paused = false

function next() {
  if (slides.value.length < 2) return
  index.value = (index.value + 1) % slides.value.length
  restart()
}

function prev() {
  if (slides.value.length < 2) return
  index.value = (index.value - 1 + slides.value.length) % slides.value.length
  restart()
}

function goTo(slideIndex) {
  index.value = slideIndex
  restart()
}

function start() {
  clearInterval(timer)
  if (slides.value.length > 1 && !paused) {
    timer = setInterval(() => {
      index.value = (index.value + 1) % slides.value.length
    }, AUTOPLAY_MS)
  }
}

function restart() {
  clearInterval(timer)
  start()
}

function pause() {
  paused = true
  clearInterval(timer)
}

function resume() {
  paused = false
  start()
}

onMounted(start)
onBeforeUnmount(() => clearInterval(timer))

/* ---------- Libellés ---------- */
const nameLabel = computed(() => pick(props.bundle, 'name'))

function contentsOf(bundle) {
  const parts = (bundle.items || []).map((line) => {
    const name = locale.value === 'ar' ? line.product.name_ar : line.product.name_fr
    return `${line.quantity}× ${name}`
  })

  return parts.join(' + ')
}
</script>

<template>
  <article class="bundle-card">
    <div class="bundle-media">
      <!-- Carrousel : un produit détaillé par slide -->
      <div
        class="bundle-carousel"
        @mouseenter="slides.length > 1 && pause()"
        @mouseleave="slides.length > 1 && resume()"
      >
        <div
          class="bundle-carousel-track"
          :style="{ transform: `translateX(-${index * 100}%)` }"
        >
          <div class="bundle-slide" v-for="(slide, i) in slides" :key="i">
            <img :src="slide.image" :alt="slide.name" loading="lazy">

            <!-- Détail du produit (superposition élégante) -->
            <div class="bundle-slide-info">
              <span class="bundle-slide-counter">{{ i + 1 }} / {{ slides.length }}</span>
              <h4 class="bundle-slide-name">{{ slide.name }}</h4>
              <p class="bundle-slide-desc">{{ slide.description }}</p>
              <div class="bundle-slide-meta">
                <span class="bundle-slide-qty">×{{ slide.quantity }}</span>
                <span class="bundle-slide-price">{{ formatPrice(slide.unitPrice, locale) }}</span>
                <span class="bundle-slide-unit">{{ t('unit_price') }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Flèches (au survol) -->
        <button
          v-if="slides.length > 1"
          class="carousel-arrow carousel-prev"
          type="button"
          :aria-label="t('carousel_prev')"
          @click="prev"
        >‹</button>
        <button
          v-if="slides.length > 1"
          class="carousel-arrow carousel-next"
          type="button"
          :aria-label="t('carousel_next')"
          @click="next"
        >›</button>

        <!-- Points + barre de progression du défilement auto -->
        <div class="carousel-nav" v-if="slides.length > 1">
          <div class="carousel-dots">
            <button
              v-for="(slide, i) in slides"
              :key="i"
              type="button"
              :class="{ active: i === index }"
              :aria-label="`Produit ${i + 1}`"
              @click="goTo(i)"
            ></button>
          </div>
          <div class="carousel-progress">
            <span :key="index" :style="{ animationDuration: `${AUTOPLAY_MS}ms` }"></span>
          </div>
        </div>
      </div>

      <span class="bundle-featured-badge" v-if="bundle.is_featured" :title="t('bundle_featured')">★</span>
      <span class="bundle-savings-badge">-{{ bundle.savings_percent }}%</span>
    </div>

    <div class="bundle-body">
      <h3>{{ nameLabel }}</h3>
      <p class="bundle-contents">{{ contentsOf(bundle) }}</p>

      <div class="bundle-prices">
        <span class="price-struck">{{ formatPrice(bundle.regular_total, locale) }}</span>
        <span class="bundle-price">{{ formatPrice(bundle.price, locale) }}</span>
        <span class="bundle-economy">{{ t('savings', { amount: formatPrice(bundle.savings, locale) }) }}</span>
      </div>

      <button class="btn btn-gold bundle-add" type="button" @click="emit('add', bundle)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 3h2l2.6 12.4a2 2 0 002 1.6h8a2 2 0 002-1.6L21 7H6"/><circle cx="9.5" cy="20.5" r="1.4"/><circle cx="17.5" cy="20.5" r="1.4"/></svg>
        <span>{{ t('bundle_add') }}</span>
      </button>
    </div>
  </article>
</template>
