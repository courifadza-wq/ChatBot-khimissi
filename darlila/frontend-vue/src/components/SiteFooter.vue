<script setup>
import { computed } from 'vue'
import { useShopStore } from '../stores/shop'
import { useI18n } from '../i18n'
import { waLink, genericMessage } from '../utils/whatsapp'

const { t, locale } = useI18n()
const shop = useShopStore()

const mapsUrl = 'https://www.google.com/maps/place/Plan%C3%A8te+kids/@36.7265418,3.4099902,17z/data=!3m1!4b1!4m6!3m5!1s0x128e5d36f87bb7c1:0x1de62d4fac009f6a!8m2!3d36.7265418!4d3.4099902!16s%2Fg%2F11rn00r0lk'
const whatsappGroupUrl = 'https://chat.whatsapp.com/KJLlKQ6cbQe8GGFmy7UhL6'
const whatsappNumberRaw = '+213554698746'

const waHref = 'https://chat.whatsapp.com/KJLlKQ6cbQe8GGFmy7UhL6'

// unused computed kept for compatibility
const _waHrefOld = computed(() => waLink(shop.whatsappNumber, genericMessage(locale.value)))

const navLinks = [
  { href: '#accueil', key: 'nav_home' },
  { href: '#boutique', key: 'nav_shop' },
  { href: '#galerie', key: 'nav_gallery' },
  { href: '#localisation', key: 'foot_loc' },
]
</script>

<template>
  <footer>
    <div class="container">
      <div class="footer-grid">
        <div>
          <div class="footer-logo">
            <a href="#accueil" class="logo-pill"><img src="/logo-planet-kids.png" :alt="t('brand')"></a>
            <p class="footer-tagline">{{ t('brand_tagline') }}</p>
          </div>
          <p style="max-width: 280px; opacity: .75">{{ t('foot_desc') }}</p>

          <div class="social-row">
            <a :href="shop.settings.instagram_url || 'https://www.instagram.com/planetekids_'" target="_blank" rel="noopener" aria-label="Instagram" title="Instagram">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.3" cy="6.7" r="1"/></svg>
            </a>
            <a :href="shop.settings.facebook_url || 'https://www.facebook.com/share/19YwPnT6jg/'" target="_blank" rel="noopener" aria-label="Facebook" title="Facebook">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M14 9h3V6h-3a4 4 0 00-4 4v2H7v3h3v6h3v-6h3l1-3h-4v-2a1 1 0 011-1z"/></svg>
            </a>
            <a :href="shop.settings.tiktok_url || 'https://www.tiktok.com/@planetkids_'" target="_blank" rel="noopener" aria-label="TikTok" title="TikTok">
              <svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 11-2.31-2.83v-3.5a6.37 6.37 0 106.37 6.37V8.61a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1.61 0z"/></svg>
            </a>
            <a :href="waHref" target="_blank" rel="noopener" aria-label="WhatsApp" title="WhatsApp">
              <svg viewBox="0 0 24 24" fill="currentColor" style="width:16px;height:16px;"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.87 9.87 0 0012.04 2zm5.79 14.02c-.24.68-1.4 1.32-1.93 1.4-.5.08-1.12.11-1.81-.11-.42-.13-.95-.31-1.64-.6-2.9-1.25-4.79-4.17-4.94-4.36-.14-.2-1.18-1.57-1.18-3 0-1.42.75-2.12 1.01-2.41.27-.29.58-.36.78-.36.19 0 .39 0 .55.01.18.01.42-.07.65.5.24.58.82 2 .89 2.14.07.15.12.32.02.51-.09.2-.14.32-.28.49-.14.17-.29.38-.42.51-.14.14-.28.29-.12.57.16.28.72 1.19 1.55 1.93 1.06.95 1.96 1.24 2.24 1.38.28.14.44.12.61-.07.16-.19.7-.82.89-1.1.19-.28.37-.23.62-.14.25.09 1.6.75 1.87.89.28.14.46.21.53.32.07.12.07.68-.17 1.36z"/></svg>
            </a>
          </div>
        </div>

        <div class="footer-col">
          <h4>{{ t('foot_nav') }}</h4>
          <a v-for="link in navLinks" :key="link.key" :href="link.href">{{ t(link.key) }}</a>
        </div>

        <div class="footer-col">
          <h4>{{ t('foot_contact') }}</h4>

          <a :href="mapsUrl" target="_blank" rel="noopener" class="footer-info-link">
            <span class="footer-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 21s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12z"/><circle cx="12" cy="9" r="2.4"/></svg>
            </span>
            <span>{{ shop.settings.shop_address_fr || 'Rue des Frères Aoudia, Boudouaou, Boumerdès' }}</span>
          </a>

          <a :href="'tel:' + (shop.settings.shop_phone_display || '+213554698746').replace(/\s/g, '')" class="footer-info-link">
            <span class="footer-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M22 16.9v3a2 2 0 01-2.2 2 19.8 19.8 0 01-8.6-3.1 19.5 19.5 0 01-6-6A19.8 19.8 0 012.1 4.2 2 2 0 014.1 2h3a2 2 0 012 1.7c.1.9.3 1.8.6 2.7a2 2 0 01-.5 2.1L8 9.7a16 16 0 006 6l1.2-1.2a2 2 0 012.1-.5c.9.3 1.8.5 2.7.6a2 2 0 011.7 2z"/></svg>
            </span>
            <span>{{ shop.settings.shop_phone_display || '+213 554 69 87 46' }}</span>
          </a>

          <a :href="whatsappGroupUrl" target="_blank" rel="noopener" class="footer-info-link wa">
            <span class="footer-icon">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91c0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21h.01c5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01A9.87 9.87 0 0012.04 2zm5.79 14.02c-.24.68-1.4 1.32-1.93 1.4-.5.08-1.12.11-1.81-.11-.42-.13-.95-.31-1.64-.6-2.9-1.25-4.79-4.17-4.94-4.36-.14-.2-1.18-1.57-1.18-3 0-1.42.75-2.12 1.01-2.41.27-.29.58-.36.78-.36.19 0 .39 0 .55.01.18.01.42-.07.65.5.24.58.82 2 .89 2.14.07.15.12.32.02.51-.09.2-.14.32-.28.49-.14.17-.29.38-.42.51-.14.14-.28.29-.12.57.16.28.72 1.19 1.55 1.93 1.06.95 1.96 1.24 2.24 1.38.28.14.44.12.61-.07.16-.19.7-.82.89-1.1.19-.28.37-.23.62-.14.25.09 1.6.75 1.87.89.28.14.46.21.53.32.07.12.07.68-.17 1.36z"/></svg>
            </span>
            <span>{{ t('foot_whatsapp_group') }}</span>
          </a>

          <a :href="'mailto:' + (shop.settings.shop_email || 'contact@khemicishop.com')" class="footer-info-link">
            <span class="footer-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M2 7l10 6 10-6"/></svg>
            </span>
            <span>{{ shop.settings.shop_email || 'contact@khemicishop.com' }}</span>
          </a>
        </div>
      </div>

      <div class="footer-bottom">
        <span>{{ t('foot_rights') }}</span>
        <span>{{ t('foot_made') }}</span>
      </div>
    </div>
  </footer>
</template>
