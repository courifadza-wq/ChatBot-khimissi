<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAdminStore } from '../stores/admin'

/**
 * Réglages de la boutique — tout est modifiable ici, sans toucher au code.
 * Le vendeur peut changer : WhatsApp, adresse, horaires, téléphone, e-mail, etc.
 */
const router = useRouter()
const admin = useAdminStore()

const loading = ref(true)
const saving = ref(false)

const form = reactive({
  whatsapp_number: '',
  seller_email: '',
  shop_name_fr: '',
  shop_name_ar: '',
  shop_address_fr: '',
  shop_address_ar: '',
  shop_hours_fr: '',
  shop_hours_ar: '',
  shop_phone_display: '',
  shop_email: '',
  hero_image: '',
  maps_query: '',
  whatsapp_group_url: '',
  instagram_url: '',
  facebook_url: '',
  tiktok_url: '',
})

const sections = [
  {
    title: '📞 Contact & WhatsApp',
    icon: 'M22 16.9v3a2 2 0 01-2.2 2 19.8 19.8 0 01-8.6-3.1 19.5 19.5 0 01-6-6A19.8 19.8 0 012.1 4.2 2 2 0 014.1 2h3a2 2 0 012 1.7c.1.9.3 1.8.6 2.7a2 2 0 01-.5 2.1L8 9.7a16 16 0 006 6l1.2-1.2a2 2 0 012.1-.5c.9.3 1.8.5 2.7.6a2 2 0 011.7 2z',
    fields: [
      { key: 'whatsapp_number', label: 'Numéro WhatsApp (format international sans +)', placeholder: 'ex. 213554698746', type: 'text' },
      { key: 'shop_phone_display', label: 'Téléphone affiché (avec espaces)', placeholder: 'ex. +213 554 69 87 46', type: 'text' },
      { key: 'whatsapp_group_url', label: 'Lien du groupe WhatsApp', placeholder: 'https://chat.whatsapp.com/...', type: 'url' },
      { key: 'shop_email', label: 'E-mail de la boutique', placeholder: 'contact@khemicishop.com', type: 'email' },
      { key: 'seller_email', label: 'E-mail qui reçoit les notifications de commande', placeholder: 'commandes@khemicishop.com', type: 'email' },
    ],
  },
  {
    title: '📍 Adresse & Localisation',
    icon: 'M12 21s7-6.5 7-12a7 7 0 10-14 0c0 5.5 7 12 7 12z',
    fields: [
      { key: 'shop_name_fr', label: 'Nom de la boutique (français)', placeholder: 'ex. Planet Kids — Boudouaou', type: 'text' },
      { key: 'shop_name_ar', label: 'اسم المتجر (عربي)', placeholder: 'ex. بلانيت كيدز — بودواو', type: 'text', rtl: true },
      { key: 'shop_address_fr', label: 'Adresse (français)', placeholder: 'ex. Rue des Frères Aoudia, Boudouaou, Boumerdès', type: 'text' },
      { key: 'shop_address_ar', label: 'العنوان (عربي)', placeholder: 'ex. شارع الإخوة عودية، بودواو، بومرداس', type: 'text', rtl: true },
      { key: 'maps_query', label: 'Recherche Google Maps (adresse à afficher sur la carte)', placeholder: 'ex. Rue des Frères Aoudia, Boudouaou, Boumerdès, Algérie', type: 'text' },
    ],
  },
  {
    title: '🕐 Horaires d\'ouverture',
    icon: 'M12 7v5l3.2 2',
    fields: [
      { key: 'shop_hours_fr', label: 'Horaires (français)', placeholder: 'ex. Tous les jours : 09h à 21h · Vendredi : 14h30 à 21h', type: 'text' },
      { key: 'shop_hours_ar', label: 'أوقات العمل (عربي)', placeholder: 'ex. كل الأيام: 9 صباحاً إلى 9 مساءً · الجمعة: 2:30 إلى 9 مساءً', type: 'text', rtl: true },
    ],
  },
  {
    title: '📱 Réseaux sociaux',
    icon: 'M18 2h-3a5 5 0 00-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 011-1h3z',
    fields: [
      { key: 'instagram_url', label: 'Lien Instagram', placeholder: 'https://www.instagram.com/planetekids_', type: 'url' },
      { key: 'facebook_url', label: 'Lien Facebook', placeholder: 'https://www.facebook.com/share/19YwPnT6jg/', type: 'url' },
      { key: 'tiktok_url', label: 'Lien TikTok', placeholder: 'https://www.tiktok.com/@planetkids_', type: 'url' },
    ],
  },
  {
    title: '🖼️ Apparence',
    icon: 'M21 19V5a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z',
    fields: [
      { key: 'hero_image', label: 'Image du hero (URL)', placeholder: 'https://... (laisser vide pour l\'image par défaut)', type: 'url' },
    ],
  },
]

async function load() {
  loading.value = true
  try {
    const settings = await api.adminSettings()
    Object.keys(form).forEach((key) => {
      form[key] = settings[key] || ''
    })
  } catch (error) {
    admin.handleApiError(error, router)
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function save() {
  if (saving.value) return
  saving.value = true

  try {
    // ne pas envoyer les valeurs vides
    const payload = {}
    Object.entries(form).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        payload[key] = value
      }
    })

    await api.adminUpdateSettings(payload)
    admin.notify('Réglages sauvegardés ! La boutique est mise à jour.')
  } catch (error) {
    admin.notify(error.message || 'Erreur lors de la sauvegarde.', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <div class="admin-page-head">
      <div>
        <h2>Réglages</h2>
        <p class="admin-muted">Configurez toute votre boutique ici — WhatsApp, adresse, horaires, e-mails. Aucun code à modifier.</p>
      </div>
      <button class="btn btn-gold" type="button" :disabled="saving || loading" @click="save">
        {{ saving ? 'Sauvegarde…' : '💾 Sauvegarder' }}
      </button>
    </div>

    <!-- Chargement -->
    <div class="admin-cards" v-if="loading">
      <div class="skel-card admin-skel" v-for="i in 3" :key="i">
        <div class="skel-line skel"></div><div class="skel-line skel short"></div>
      </div>
    </div>

    <!-- Sections -->
    <div v-else>
      <div class="settings-section" v-for="section in sections" :key="section.title">
        <h3 class="settings-section-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" v-html="'<path d=\'' + section.icon + '\'/>'"></svg>
          {{ section.title }}
        </h3>

        <div class="admin-form-grid">
          <div class="field" v-for="field in section.fields" :key="field.key">
            <label :for="'set_' + field.key">{{ field.label }}</label>
            <input
              v-if="field.type !== 'textarea'"
              :id="'set_' + field.key"
              v-model="form[field.key]"
              :type="field.type || 'text'"
              :placeholder="field.placeholder"
              :dir="field.rtl ? 'rtl' : 'ltr'"
              class="settings-input"
            >
          </div>
        </div>
      </div>

      <!-- Aperçu live -->
      <div class="settings-preview">
        <h4>📊 Aperçu (ce que verra le client)</h4>
        <div class="preview-grid">
          <div class="preview-item">
            <small>Nom affiché</small>
            <strong>{{ form.shop_name_fr || 'Planet Kids' }}</strong>
          </div>
          <div class="preview-item">
            <small>Adresse</small>
            <strong>{{ form.shop_address_fr || 'Non définie' }}</strong>
          </div>
          <div class="preview-item">
            <small>Horaires</small>
            <strong>{{ form.shop_hours_fr || 'Non définis' }}</strong>
          </div>
          <div class="preview-item">
            <small>Téléphone</small>
            <strong>{{ form.shop_phone_display || 'Non défini' }}</strong>
          </div>
          <div class="preview-item">
            <small>WhatsApp commandes</small>
            <strong>+{{ form.whatsapp_number || '…' }}</strong>
          </div>
        </div>
      </div>

      <div class="checkout-actions" style="margin-top: 20px;">
        <button class="btn btn-gold" type="button" :disabled="saving" @click="save">
          {{ saving ? 'Sauvegarde…' : '💾 Sauvegarder les réglages' }}
        </button>
      </div>
    </div>
  </div>
</template>
