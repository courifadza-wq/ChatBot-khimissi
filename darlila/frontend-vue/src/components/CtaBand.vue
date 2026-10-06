<script setup>
import { computed } from 'vue'
import { useShopStore } from '../stores/shop'
import { useI18n } from '../i18n'
import { waLink, genericMessage } from '../utils/whatsapp'

const { t, locale } = useI18n()
const shop = useShopStore()

const waHref = 'https://chat.whatsapp.com/KJLlKQ6cbQe8GGFmy7UhL6'
</script>

<template>
  <section class="cta-band" id="contact">
    <div class="zellige-divider dark" style="position:absolute;top:0;left:0;"></div>

    <h2>{{ t('cta_title') }}</h2>
    <p>{{ t('cta_p') }}</p>

    <a class="btn btn-gold cta-wa-btn" style="margin: 0 auto" :href="waHref" target="_blank" rel="noopener">
      <svg viewBox="0 0 24 24" fill="currentColor" style="width:17px;height:17px;"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.87 9.87 0 0012.04 2zm5.79 14.02c-.24.68-1.4 1.32-1.93 1.4-.5.08-1.12.11-1.81-.11-.42-.13-.95-.31-1.64-.6-2.9-1.25-4.79-4.17-4.94-4.36-.14-.2-1.18-1.57-1.18-3 0-1.42.75-2.12 1.01-2.41.27-.29.58-.36.78-.36.19 0 .39 0 .55.01.18.01.42-.07.65.5.24.58.82 2 .89 2.14.07.15.12.32.02.51-.09.2-.14.32-.28.49-.14.17-.29.38-.42.51-.14.14-.28.29-.12.57.16.28.72 1.19 1.55 1.93 1.06.95 1.96 1.24 2.24 1.38.28.14.44.12.61-.07.16-.19.7-.82.89-1.1.19-.28.37-.23.62-.14.25.09 1.6.75 1.87.89.28.14.46.21.53.32.07.12.07.68-.17 1.36z"/></svg>
      <span>{{ t('cta_btn') }}</span>
    </a>
  </section>
</template>
