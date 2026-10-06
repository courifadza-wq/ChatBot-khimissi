<script setup>
import { useI18n } from '../i18n'

const { t } = useI18n()

const usps = [
  {
    titleKey: 'usp1_t',
    textKey: 'usp1_p',
    icon: '<path d="M12 2l2.4 6.5L21 10l-5 4.4 1.5 7.1L12 18l-5.5 3.5L8 14.4 3 10l6.6-1.5z"/>',
  },
  {
    titleKey: 'usp2_t',
    textKey: 'usp2_p',
    icon: '<path d="M3 7h11v9H3zM14 10h4l3 3v3h-7z"/><circle cx="7" cy="18" r="1.6"/><circle cx="17.5" cy="18" r="1.6"/>',
  },
  {
    titleKey: 'usp3_t',
    textKey: 'usp3_p',
    icon: '<rect x="2" y="6" width="20" height="13" rx="2"/><path d="M2 10h20M6 15h4"/>',
  },
  {
    titleKey: 'usp4_t',
    textKey: 'usp4_p',
    icon: '<path d="M4 4v6h6M20 20v-6h-6"/><path d="M20 10a8 8 0 00-14.6-4.6M4 14a8 8 0 0014.6 4.6"/>',
  },
]
</script>

<template>
  <section class="section" id="apropos">
    <div class="container">
      <div class="section-head" v-reveal>
        <div class="eyebrow"><span class="line"></span><span>{{ t('usp_eyebrow') }}</span></div>
        <h2>{{ t('usp_title') }}</h2>
        <p class="lead">{{ t('usp_lead') }}</p>
      </div>

      <div class="usp-grid" v-reveal="'stagger'">
        <div class="usp-card" v-for="usp in usps" :key="usp.titleKey">
          <div class="usp-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" v-html="usp.icon"></svg>
          </div>
          <h3>{{ t(usp.titleKey) }}</h3>
          <p>{{ t(usp.textKey) }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
