<script setup>
import { useShopStore } from '../stores/shop'
import { useI18n } from '../i18n'

const { t, pick } = useI18n()
const shop = useShopStore()
</script>

<template>
  <section class="section tight testimonials" id="avis">
    <div class="container">
      <div class="section-head center" v-reveal>
        <div class="eyebrow" style="justify-content: center">
          <span class="line"></span><span>{{ t('test_eyebrow') }}</span><span class="line"></span>
        </div>
        <h2>{{ t('test_title') }}</h2>
      </div>

      <div class="t-grid" v-reveal="'stagger'">
        <div class="t-card" v-for="review in shop.reviews" :key="review.id">
          <div class="t-stars">★{{ '★'.repeat(Math.max(0, review.rating - 1)) }}</div>
          <p>{{ pick(review, 'content') }}</p>
          <div class="t-name">
            <div class="t-avatar">{{ review.author_name.charAt(0) }}</div>
            <div>
              <strong>{{ review.author_name }}</strong>
              <span>{{ pick(review, 'city') }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
