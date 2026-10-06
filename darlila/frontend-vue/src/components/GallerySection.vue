<script setup>
import { useShopStore } from '../stores/shop'
import { useUiStore } from '../stores/ui'
import { useI18n } from '../i18n'

const { t, pick } = useI18n()
const shop = useShopStore()
const ui = useUiStore()
</script>

<template>
  <section class="section" id="galerie">
    <div class="container">
      <div class="section-head" v-reveal>
        <div class="eyebrow"><span class="line"></span><span>{{ t('gal_eyebrow') }}</span></div>
        <h2>{{ t('gal_title') }}</h2>
        <p class="lead">{{ t('gal_lead') }}</p>
      </div>

      <div class="gallery-grid" v-reveal="'stagger'">
        <div
          class="g-item"
          v-for="(image, index) in shop.gallery"
          :key="image.id"
          @click="ui.openLightbox(index)"
        >
          <img :src="image.image" :alt="pick(image, 'alt')" loading="lazy">
        </div>
      </div>
    </div>
  </section>
</template>
