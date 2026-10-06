<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useShopStore } from '../stores/shop'
import { useI18n } from '../i18n'
import { waLink, genericMessage } from '../utils/whatsapp'

const { t, locale } = useI18n()
const shop = useShopStore()

const FALLBACK_HERO = 'https://arsenaldza-coif.github.io/boutique1/assets/hero-professional.jpg'
const heroImage = computed(() => shop.settings.hero_image || FALLBACK_HERO)
const waHref = 'https://chat.whatsapp.com/KJLlKQ6cbQe8GGFmy7UhL6'

/* ------------------------------------------------------------------ */
/* Diaporama du hero : image + jusqu'à 6 vidéos                        */
/*                                                                     */
/* Déposez vos vidéos dans `frontend-vue/public/` :                    */
/*   hero-video.mp4, hero2-video.mp4, hero3-video.mp4,                 */
/*   hero4-video.mp4, hero5-video.mp4, hero6-video.mp4                 */
/* Elles sont détectées automatiquement (requête HEAD) et intégrées    */
/* au diaporama. Répondez-vous comme l'image en 7 s puis les vidéos.   */
/*                                                                     */
/* Responsive : les vidéos utilisent object-fit:cover pour remplir    */
/* l'écran (desktop, tablette et mobile) sans déformation.            */
/* ------------------------------------------------------------------ */

const VIDEO_SOURCES = [
  '/hero-video.mp4',
  '/hero2-video.mp4',
  '/hero3-video.mp4',
  '/hero4-video.mp4',
  '/hero5-video.mp4',
  '/hero6-video.mp4',
]
const SLIDE_DURATION = 7000 // ms par slide

const videoSlides = ref([]) // vidéos détectées
const videoEls = ref([]) // éléments <video> correspondants
const activeIndex = ref(0) // 0 = image, 1..n = vidéos
let slideshowTimer = null

onMounted(async () => {
  // Détecte les vidéos disponibles dans /public (requête HEAD)
  const found = []
  for (const url of VIDEO_SOURCES) {
    try {
      const response = await fetch(url, { method: 'HEAD' })
      if (response.ok) found.push(url)
    } catch {
      /* fichier absent : slide ignorée */
    }
  }

  if (found.length > 0) {
    videoSlides.value = found
    startSlideshow()
  }
})

function startSlideshow() {
  const total = 1 + videoSlides.value.length
  slideshowTimer = setInterval(() => {
    activeIndex.value = (activeIndex.value + 1) % total
  }, SLIDE_DURATION)
}

// Lecture/pause des vidéos selon la slide active
watch(activeIndex, (index) => {
  videoEls.value.forEach((video, videoIndex) => {
    if (!video) return

    if (videoIndex === index - 1) {
      video.currentTime = 0
      video.play().catch(() => {})
    } else {
      video.pause()
    }
  })
})

onBeforeUnmount(() => clearInterval(slideshowTimer))

/* Parallaxe douce au scroll (désactivée si l'utilisateur préfère réduire les animations) */
const heroBg = ref(null)
let ticking = false

const onScroll = () => {
  if (ticking) return
  ticking = true
  window.requestAnimationFrame(() => {
    const y = window.scrollY
    if (y < window.innerHeight * 1.2 && heroBg.value) {
      heroBg.value.style.transform = `translateY(${y * 0.35}px)`
    }
    ticking = false
  })
}

onMounted(() => {
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    window.addEventListener('scroll', onScroll, { passive: true })
  }
})
onBeforeUnmount(() => window.removeEventListener('scroll', onScroll))
</script>

<template>
  <section class="hero" id="accueil">
    <div ref="heroBg" class="hero-bg" aria-label="Présentation Planet Kids">
      <!-- Slide 1 : image (toujours présente) -->
      <img
        class="hero-slide"
        :class="{ active: activeIndex === 0 }"
        :src="heroImage"
        :alt="t('hero_image_alt')"
      >

      <!-- Slides suivantes : vidéos (si présentes dans /public) -->
      <video
        v-for="(video, videoIndex) in videoSlides"
        :key="video"
        :ref="(el) => (videoEls[videoIndex] = el)"
        class="hero-slide"
        :class="{ active: activeIndex === videoIndex + 1 }"
        :src="video"
        muted
        playsinline
        preload="metadata"
      ></video>

      <!-- Indicateurs de slides (points) -->
      <div class="hero-dots" v-if="videoSlides.length > 0">
        <span
          v-for="(video, i) in videoSlides"
          :key="i"
          :class="{ active: activeIndex === i + 1 }"
        ></span>
      </div>
    </div>

    <div class="hero-content">
      <div class="hero-eyebrow">
        <span class="line"></span>
        <span>{{ t('hero_eyebrow') }}</span>
        <span class="line"></span>
      </div>

      <h1>{{ t('hero_title') }}</h1>
      <p>{{ t('hero_sub') }}</p>

      <div class="hero-ctas">
        <a class="btn btn-gold" :href="waHref" target="_blank" rel="noopener">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.87 9.87 0 0012.04 2zm5.79 14.02c-.24.68-1.4 1.32-1.93 1.4-.5.08-1.12.11-1.81-.11-.42-.13-.95-.31-1.64-.6-2.9-1.25-4.79-4.17-4.94-4.36-.14-.2-1.18-1.57-1.18-3 0-1.42.75-2.12 1.01-2.41.27-.29.58-.36.78-.36.19 0 .39 0 .55.01.18.01.42-.07.65.5.24.58.82 2 .89 2.14.07.15.12.32.02.51-.09.2-.14.32-.28.49-.14.17-.29.38-.42.51-.14.14-.28.29-.12.57.16.28.72 1.19 1.55 1.93 1.06.95 1.96 1.24 2.24 1.38.28.14.44.12.61-.07.16-.19.7-.82.89-1.1.19-.28.37-.23.62-.14.25.09 1.6.75 1.87.89.28.14.46.21.53.32.07.12.07.68-.17 1.36z"/></svg>
          <span>{{ t('hero_cta1') }}</span>
        </a>
        <a href="#boutique" class="btn btn-outline">{{ t('hero_cta2') }}</a>
      </div>
    </div>

    <div class="scroll-cue">
      <span>{{ t('scroll') }}</span>
      <span class="stick"></span>
    </div>
  </section>
</template>
