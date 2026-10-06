<script setup>
import { computed } from 'vue'
import { useShopStore } from '../stores/shop'
import { useI18n } from '../i18n'
import { waLink, genericMessage } from '../utils/whatsapp'

const { t, pick, locale } = useI18n()
const shop = useShopStore()

const mapsEmbedUrl = 'https://www.google.com/maps?q=Plan%C3%A8te+kids+Boudouaou+Boumerd%C3%A8s&output=embed'
const mapsLinkUrl = 'https://www.google.com/maps/place/Plan%C3%A8te+kids/@36.7265418,3.4099902,17z/data=!3m1!4b1!4m6!3m5!1s0x128e5d36f87bb7c1:0x1de62d4fac009f6a!8m2!3d36.7265418!4d3.4099902!16s%2Fg%2F11rn00r0lk'
const whatsappGroupUrl = 'https://chat.whatsapp.com/KJLlKQ6cbQe8GGFmy7UhL6'

const waHref = 'https://chat.whatsapp.com/KJLlKQ6cbQe8GGFmy7UhL6'
</script>

<template>
  <section class="section" id="localisation">
    <div class="container">
      <div class="section-head" v-reveal>
        <div class="eyebrow"><span class="line"></span><span>{{ t('loc_eyebrow') }}</span></div>
        <h2>{{ t('loc_title') }}</h2>
      </div>

      <div class="loc-wrap" v-reveal>
        <div class="loc-info">
          <h3>Planet Kids — Boudouaou</h3>

          <div class="loc-row">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 21s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12z"/><circle cx="12" cy="9" r="2.4"/></svg>
            <p>
              <strong>{{ t('loc_addr_l') }}</strong>
              <span>Rue des Frères Aoudia, Boudouaou, Boumerdès</span>
            </p>
          </div>

          <div class="loc-row">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.2 2"/></svg>
            <p>
              <strong>{{ t('loc_hours_l') }}</strong>
              <span>Tous les jours : 09h à 21h<br>Vendredi : 14h30 à 21h</span>
            </p>
          </div>

          <div class="loc-row">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M22 16.9v3a2 2 0 01-2.2 2 19.8 19.8 0 01-8.6-3.1 19.5 19.5 0 01-6-6A19.8 19.8 0 012.1 4.2 2 2 0 014.1 2h3a2 2 0 012 1.7c.1.9.3 1.8.6 2.7a2 2 0 01-.5 2.1L8 9.7a16 16 0 006 6l1.2-1.2a2 2 0 012.1-.5c.9.3 1.8.5 2.7.6a2 2 0 011.7 2z"/></svg>
            <p>
              <strong>{{ t('loc_phone_l') }}</strong>
              <span><a :href="'tel:+213554698746'" style="color:inherit;text-decoration:underline;">+213 554 69 87 46</a></span>
            </p>
          </div>

          <a class="btn btn-gold" style="align-self: flex-start" :href="waHref" target="_blank" rel="noopener">
            <svg viewBox="0 0 24 24" fill="currentColor" style="width:16px;height:16px;"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.87 9.87 0 0012.04 2zm5.79 14.02c-.24.68-1.4 1.32-1.93 1.4-.5.08-1.12.11-1.81-.11-.42-.13-.95-.31-1.64-.6-2.9-1.25-4.79-4.17-4.94-4.36-.14-.2-1.18-1.57-1.18-3 0-1.42.75-2.12 1.01-2.41.27-.29.58-.36.78-.36.19 0 .39 0 .55.01.18.01.42-.07.65.5.24.58.82 2 .89 2.14.07.15.12.32.02.51-.09.2-.14.32-.28.49-.14.17-.29.38-.42.51-.14.14-.28.29-.12.57.16.28.72 1.19 1.55 1.93 1.06.95 1.96 1.24 2.24 1.38.28.14.44.12.61-.07.16-.19.7-.82.89-1.1.19-.28.37-.23.62-.14.25.09 1.6.75 1.87.89.28.14.46.21.53.32.07.12.07.68-.17 1.36z"/></svg>
            <span>{{ t('loc_cta') }}</span>
          </a>

          <a class="loc-wa-group" :href="whatsappGroupUrl" target="_blank" rel="noopener">
            📲 {{ t('foot_whatsapp_group') }}
          </a>
        </div>

        <iframe
          class="map-frame"
          loading="lazy"
          allowfullscreen
          referrerpolicy="no-referrer-when-downgrade"
          :src="mapsEmbedUrl"
        ></iframe>
      </div>
    </div>
  </section>
</template>
