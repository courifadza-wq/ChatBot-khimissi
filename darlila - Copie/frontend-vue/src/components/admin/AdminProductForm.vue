<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../../api/client'
import { useAdminStore } from '../../stores/admin'

const props = defineProps({
  /** Produit à éditer, ou null pour une création. */
  product: { type: Object, default: null },
  categories: { type: Array, required: true },
})

const emit = defineEmits(['close', 'saved'])

const admin = useAdminStore()
const isEdit = computed(() => Boolean(props.product))

const safeCategories = computed(() => Array.isArray(props.categories) ? props.categories : [])

/** Catégories principales (parent_id = null) */
const mainCategories = computed(() => {
  return [...safeCategories.value.filter((c) => !c.parent_id)]
    .sort((a, b) => (a.position ?? 0) - (b.position ?? 0) || a.id - b.id)
})

/** Où les images seront stockées : Bunny CDN ou serveur local. */
const imageDriver = ref('local')
/** Conversion WebP disponible (GD + Intervention Image côté Laravel). */
const webpEnabled = ref(false)

onMounted(async () => {
  try {
    const config = await api.adminConfig()
    imageDriver.value = config.image_driver || 'local'
    webpEnabled.value = Boolean(config.webp)
  } catch {
    /* information indicative uniquement */
  }
})

const form = reactive({
  category_id: props.product?.category_id ?? safeCategories.value[0]?.id ?? null,
  name_fr: props.product?.name_fr ?? '',
  name_ar: props.product?.name_ar ?? '',
  description_fr: props.product?.description_fr ?? '',
  description_ar: props.product?.description_ar ?? '',
  price: props.product?.price ?? null,
  slug: props.product?.slug ?? '',
  is_featured: props.product?.is_featured ?? false,
  is_active: props.product?.is_active ?? true,
  promo_quantity: props.product?.promo_quantity ?? null,
  promo_percent: props.product?.promo_percent ?? null,
})

const mainCategoryId = ref(null)
const subCategoryId = ref(null)

// Initialisation selon le produit ou la 1ère catégorie
const initialCatId = props.product?.category_id ?? safeCategories.value[0]?.id ?? null
const initialCat = safeCategories.value.find((c) => c.id === initialCatId)

if (initialCat) {
  if (initialCat.parent_id) {
    mainCategoryId.value = initialCat.parent_id
    subCategoryId.value = initialCat.id
  } else {
    mainCategoryId.value = initialCat.id
    subCategoryId.value = null
  }
} else if (mainCategories.value.length > 0) {
  mainCategoryId.value = mainCategories.value[0].id
  subCategoryId.value = null
}

/** Sous-catégories associées à la catégorie principale sélectionnée */
const availableSubCategories = computed(() => {
  if (!mainCategoryId.value) return []
  return safeCategories.value
    .filter((c) => c.parent_id === mainCategoryId.value)
    .sort((a, b) => (a.position ?? 0) - (b.position ?? 0) || a.id - b.id)
})

// Mettre à jour form.category_id en fonction de la sélection
watch([mainCategoryId, subCategoryId], () => {
  form.category_id = subCategoryId.value || mainCategoryId.value
}, { immediate: true })

// Réinitialiser la sous-catégorie si la catégorie principale change
watch(mainCategoryId, (newMainId) => {
  const currentSub = safeCategories.value.find((c) => c.id === subCategoryId.value)
  if (currentSub && currentSub.parent_id !== newMainId) {
    subCategoryId.value = null
  }
})

/**
 * Sous-catégorie « orpheline » actuellement sélectionnée (son parent
 * n'existe plus) : on la garde sélectionnable dans la liste.
 */
const orphanCurrent = computed(() => {
  const current = safeCategories.value.find((c) => c.id === form.category_id)
  if (!current || !current.parent_id) return null
  const parentExists = safeCategories.value.some((c) => c.id === current.parent_id)
  return parentExists ? null : current
})

/* ---------- Image : URL ou fichier ---------- */
const imageMode = ref(isEdit.value ? 'keep' : 'url') // 'keep' | 'url' | 'file'
const imageUrl = ref(isEdit.value ? '' : '')
const imageFile = ref(null)
const imagePreview = ref(isEdit.value ? props.product.image : '')

watch(imageMode, (mode) => {
  imageFile.value = null
  imageUrl.value = ''
  imagePreview.value = mode === 'keep' ? props.product?.image : ''
})

function onFileChange(event) {
  const file = event.target.files?.[0] || null
  imageFile.value = file
  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => (imagePreview.value = e.target.result)
    reader.readAsDataURL(file)
  } else {
    imagePreview.value = ''
  }
}

/* ---------- Slug auto ---------- */
const slugTouched = ref(isEdit.value)
function autoSlug() {
  if (slugTouched.value) return
  form.slug = form.name_fr
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/[\s-]+/g, '-')
}

/* ---------- Soumission ---------- */
const errors = ref({})
const submitting = ref(false)

function buildPayload() {
  const payload = {
    category_id: form.category_id,
    name_fr: form.name_fr.trim(),
    name_ar: form.name_ar.trim(),
    description_fr: form.description_fr.trim() || null,
    description_ar: form.description_ar.trim() || null,
    price: Number(form.price),
    slug: form.slug.trim() || null,
    is_featured: form.is_featured,
    is_active: form.is_active,
    promo_quantity: form.promo_quantity || null,
    promo_percent: form.promo_percent || null,
  }

  // Fichier sélectionné → multipart/form-data
  if (imageMode.value === 'file' && imageFile.value) {
    const formData = new FormData()
    Object.entries(payload).forEach(([key, value]) => {
      if (value !== null && value !== undefined) formData.append(key, value)
    })
    formData.append('image', imageFile.value)
    return formData
  }

  if (imageMode.value === 'url' && imageUrl.value.trim()) {
    payload.image_url = imageUrl.value.trim()
  }

  return payload
}

async function submit() {
  if (submitting.value) return
  submitting.value = true
  errors.value = {}
  try {
    const payload = buildPayload()
    const saved = isEdit.value
      ? await api.adminUpdateProduct(props.product.id, payload)
      : await api.adminCreateProduct(payload)
    emit('saved', saved)
  } catch (error) {
    if (error.errors) {
      errors.value = error.errors
      admin.notify('Le formulaire contient des erreurs.', 'error')
    } else {
      admin.notify(error.message || 'Enregistrement impossible.', 'error')
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="overlay active" @click.self="emit('close')"></div>

  <div class="modal-panel active admin-form-panel" role="dialog" aria-modal="true">
    <button class="modal-close" type="button" @click="emit('close')" aria-label="Fermer">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6L6 18"/></svg>
    </button>

    <div class="admin-form-head">
      <h3>{{ isEdit ? 'Modifier le produit' : 'Nouveau produit' }}</h3>
      <p v-if="isEdit" class="admin-slug">/{{ form.slug }}</p>
    </div>

    <form class="admin-form" @submit.prevent="submit">
      <div class="admin-form-grid">
        <div class="field" :class="{ invalid: errors.name_fr }">
          <label for="pfNameFr">Nom (français) *</label>
          <input id="pfNameFr" v-model="form.name_fr" type="text" @input="autoSlug" required>
          <p class="field-error" v-if="errors.name_fr">{{ errors.name_fr[0] }}</p>
        </div>

        <div class="field" :class="{ invalid: errors.name_ar }">
          <label for="pfNameAr">الاسم (عربي) *</label>
          <input id="pfNameAr" v-model="form.name_ar" type="text" dir="rtl" required>
          <p class="field-error" v-if="errors.name_ar">{{ errors.name_ar[0] }}</p>
        </div>

        <div class="field" :class="{ invalid: errors.category_id }">
          <label for="pfMainCategory">Catégorie principale *</label>
          <select id="pfMainCategory" v-model="mainCategoryId" required>
            <option v-for="main in mainCategories" :key="main.id" :value="main.id">
              {{ main.name_fr }} ({{ main.name_ar }})
            </option>
          </select>
        </div>

        <div class="field">
          <label for="pfSubCategory">Sous-catégorie</label>
          <select
            id="pfSubCategory"
            v-model="subCategoryId"
            :disabled="availableSubCategories.length === 0"
          >
            <option :value="null">
              {{ availableSubCategories.length > 0 ? '— Aucune (Générale) —' : '— Pas de sous-catégorie —' }}
            </option>
            <option v-for="sub in availableSubCategories" :key="sub.id" :value="sub.id">
              {{ sub.name_fr }} ({{ sub.name_ar }})
            </option>
            <option
              v-if="orphanCurrent"
              :value="orphanCurrent.id"
            >{{ orphanCurrent.name_fr }} (sans parent)</option>
          </select>
          <p class="field-error" v-if="errors.category_id">{{ errors.category_id[0] }}</p>
        </div>

        <div class="field" :class="{ invalid: errors.price }">
          <label for="pfPrice">Prix (DA) *</label>
          <input id="pfPrice" v-model.number="form.price" type="number" min="0" step="1" required>
          <p class="field-error" v-if="errors.price">{{ errors.price[0] }}</p>
        </div>

        <div class="field" :class="{ invalid: errors.description_fr }">
          <label for="pfDescFr">Description (français)</label>
          <textarea id="pfDescFr" v-model="form.description_fr" rows="3"></textarea>
          <p class="field-error" v-if="errors.description_fr">{{ errors.description_fr[0] }}</p>
        </div>

        <div class="field" :class="{ invalid: errors.description_ar }">
          <label for="pfDescAr">الوصف (عربي)</label>
          <textarea id="pfDescAr" v-model="form.description_ar" rows="3" dir="rtl"></textarea>
          <p class="field-error" v-if="errors.description_ar">{{ errors.description_ar[0] }}</p>
        </div>
      </div>

      <!-- Image -->
      <div class="field admin-image-field" :class="{ invalid: errors.image || errors.image_url }">
        <label>Image</label>
        <div class="admin-image-modes">
          <button
            v-for="mode in isEdit ? ['keep', 'url', 'file'] : ['url', 'file']"
            :key="mode"
            class="chip chip-sm"
            :class="{ active: imageMode === mode }"
            type="button"
            @click="imageMode = mode"
          >
            {{ mode === 'keep' ? 'Conserver' : mode === 'url' ? 'URL' : 'Fichier' }}
          </button>
        </div>

        <div class="admin-image-row">
          <div class="admin-image-preview">
            <img v-if="imagePreview" :src="imagePreview" alt="Aperçu">
            <span v-else>—</span>
          </div>

          <div class="admin-image-input">
            <template v-if="imageMode === 'url'">
              <input v-model="imageUrl" type="url" placeholder="https://…/photo.jpg">
            </template>
            <template v-else-if="imageMode === 'file'">
              <input type="file" accept="image/jpeg,image/png,image/webp" @change="onFileChange">
              <small class="admin-muted">
                {{ imageDriver === 'bunny'
                  ? 'Stocké sur Bunny CDN (diffusion mondiale) —'
                  : 'Stocké sur le serveur (/storage) —' }}
                JPG, PNG ou WebP, 2 Mo max{{ webpEnabled ? ' — convertie en WebP optimisé automatiquement' : '' }}.
              </small>
            </template>
            <template v-else>
              <p class="admin-muted">L'image actuelle est conservée.</p>
            </template>
          </div>
        </div>
        <p class="field-error" v-if="errors.image">{{ errors.image[0] }}</p>
        <p class="field-error" v-if="errors.image_url">{{ errors.image_url[0] }}</p>
      </div>

      <!-- Promotion « achetez N → -X % » -->
      <div class="admin-form-grid">
        <div class="field" :class="{ invalid: errors.promo_quantity }">
          <label for="pfPromoQty">Promo : quantité déclencheuse</label>
          <input id="pfPromoQty" v-model.number="form.promo_quantity" type="number" min="2" max="99" placeholder="ex. 2 (vide = pas de promo)">
          <p class="field-error" v-if="errors.promo_quantity">{{ errors.promo_quantity[0] }}</p>
        </div>
        <div class="field" :class="{ invalid: errors.promo_percent }">
          <label for="pfPromoPct">Promo : réduction (%)</label>
          <input id="pfPromoPct" v-model.number="form.promo_percent" type="number" min="1" max="99" placeholder="ex. 15 (vide = pas de promo)">
          <p class="field-error" v-if="errors.promo_percent">{{ errors.promo_percent[0] }}</p>
        </div>
      </div>
      <p class="admin-muted" style="margin: -6px 0 12px;">
        Laissez les deux champs vides pour désactiver la promo. Exemple : 2 et 15 = « -15 % dès 2 achetés »,
        remise appliquée automatiquement dans la boutique, le panier et la commande.
      </p>

      <div class="admin-form-grid">
        <div class="field" :class="{ invalid: errors.slug }">
          <label for="pfSlug">Slug (URL)</label>
          <input id="pfSlug" v-model="form.slug" type="text" placeholder="auto depuis le nom" @input="slugTouched = true">
          <p class="field-error" v-if="errors.slug">{{ errors.slug[0] }}</p>
        </div>

        <div class="admin-checkboxes">
          <label class="admin-check">
            <input v-model="form.is_featured" type="checkbox">
            <span>Produit en vedette</span>
          </label>
          <label class="admin-check">
            <input v-model="form.is_active" type="checkbox">
            <span>Visible dans la boutique</span>
          </label>
        </div>
      </div>

      <div class="checkout-actions">
        <button class="btn btn-outline-dark" type="button" @click="emit('close')">Annuler</button>
        <button class="btn btn-gold" type="submit" :disabled="submitting">
          {{ submitting ? 'Enregistrement…' : (isEdit ? 'Enregistrer les modifications' : 'Créer le produit') }}
        </button>
      </div>
    </form>
  </div>
</template>
