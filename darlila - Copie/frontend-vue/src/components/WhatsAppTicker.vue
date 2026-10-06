<script setup>
import { computed } from 'vue'
import { useShopStore } from '../stores/shop'
import { useI18n } from '../i18n'
import { waLink, genericMessage } from '../utils/whatsapp'

const { t, locale } = useI18n()
const shop = useShopStore()

const href = 'https://chat.whatsapp.com/KJLlKQ6cbQe8GGFmy7UhL6'
</script>

<template>
  <a class="whatsapp-ticker" :href="href" target="_blank" rel="noopener" aria-label="WhatsApp">
    <div class="ticker-track">
      <span v-for="i in 4" :key="i">{{ t('wa_ticker') }}</span>
    </div>
  </a>
</template>
