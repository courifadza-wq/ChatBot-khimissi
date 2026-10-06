<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAdminStore } from '../stores/admin'
import { useI18n, formatPrice } from '../i18n'

/**
 * Gestion des lots (bundles) : plusieurs produits regroupés à prix réduit.
 * La boutique affiche le prix cumulé barré + le prix du lot.
 */
const router = useRouter()
const admin = useAdminStore()
const { pick, locale } = useI18n()

const bundles = ref([])
const loading = ref(true)
const saving = ref(false)

/* ---------- Barre de recherche de la liste (serveur, debouncée) ---------- */
const search = ref('')

function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => load(), 350)
}

/* ---------- Formulaire ---------- */
const formOpen = ref(false)
const editingBundle = ref(null)
const selectedIds = ref(new Set())
const bulkDeleting = ref(false)
const errors = ref({})

const form = reactive({
  name_fr: '',
  name_ar: '',
  description_fr: '',
  description_ar: '',
  price: null,
  image: '',
  is_active: true,
  is_featured: false,
  items: [], // [{ product_id, quantity, product }]
})

/* ---------- Sélecteur de produits (recherche serveur) ---------- */
const productSearch = ref('')
const searchResults = ref([])
const searching = ref(false)
let searchTimer = null

function onProductSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(searchProducts, 350)
}

async function searchProducts() {
  const term = productSearch.value.trim()
  if (term.length < 2) {
    searchResults.value = []
    return
  }

  searching.value = true
  try {
    const { items } = await api.adminProducts({ search: term, per_page: 8 })
    // retire ceux déjà sélectionnés
    const selected = new Set(form.items.map((item) => item.product_id))
    searchResults.value = items.filter((product) => !selected.has(product.id))
  } catch (error) {
    admin.handleApiError(error, router)
  } finally {
    searching.value = false
  }
}

function addProductToBundle(product) {
  if (form.items.some((item) => item.product_id === product.id)) return

  form.items.push({ product_id: product.id, quantity: 1, product })
  productSearch.value = ''
  searchResults.value = []
}

function removeItem(index) {
  form.items.splice(index, 1)
}

/* ---------- Total cumulé du lot en cours ---------- */
const regularTotal = computed(() =>
  form.items.reduce(
    (sum, item) => sum + (Number(item.product.price) || 0) * (Number(item.quantity) || 1),
    0
  )
)

const savings = computed(() => Math.max(0, regularTotal.value - Number(form.price || 0)))

/* ---------- Chargement ---------- */
async function load() {
  loading.value = true
  try {
    bundles.value = await api.adminBundles(search.value.trim() ? { search: search.value.trim() } : {})
  } catch (error) {
    admin.handleApiError(error, router)
  } finally {
    loading.value = false
  }
}
onMounted(load)

/* ---------- CRUD ---------- */
function toggleSelect(id) {
  if (selectedIds.value.has(id)) selectedIds.value.delete(id)
  else selectedIds.value.add(id)
}

const allSelected = computed(() =>
  bundles.value.length > 0 && bundles.value.every((b) => selectedIds.value.has(b.id))
)

function toggleSelectAll() {
  if (allSelected.value) selectedIds.value.clear()
  else bundles.value.forEach((b) => selectedIds.value.add(b.id))
}

async function bulkDelete() {
  const count = selectedIds.value.size
  if (count === 0) return
  if (!window.confirm(`Supprimer définitivement ${count} lot(s) sélectionné(s) ?`)) return

  bulkDeleting.value = true
  try {
    const result = await api.adminBulkDeleteBundles([...selectedIds.value])
    admin.notify(`${result.deleted} lot(s) supprimé(s).`)
    selectedIds.value.clear()
    load()
  } catch (error) {
    admin.handleApiError(error, router)
  } finally {
    bulkDeleting.value = false
  }
}

function openCreate() {
  editingBundle.value = null
  Object.assign(form, {
    name_fr: '', name_ar: '', description_fr: '', description_ar: '',
    price: null, image: '', is_active: true, is_featured: false, items: [],
  })
  errors.value = {}
  formOpen.value = true
}

function openEdit(bundle) {
  editingBundle.value = bundle
  Object.assign(form, {
    name_fr: bundle.name_fr,
    name_ar: bundle.name_ar,
    description_fr: bundle.description_fr || '',
    description_ar: bundle.description_ar || '',
    price: bundle.price,
    image: bundle.image && !bundle.image.includes('/storage') ? bundle.image : '',
    is_active: bundle.is_active,
    is_featured: bundle.is_featured,
    items: (bundle.items || []).map((item) => ({
      product_id: item.product.id,
      quantity: item.quantity,
      product: item.product,
    })),
  })
  errors.value = {}
  formOpen.value = true
}

function buildPayload() {
  return {
    name_fr: form.name_fr.trim(),
    name_ar: form.name_ar.trim(),
    description_fr: form.description_fr.trim() || null,
    description_ar: form.description_ar.trim() || null,
    price: Number(form.price),
    image: form.image.trim() || null,
    is_active: form.is_active,
    is_featured: form.is_featured,
    items: form.items.map((item) => ({
      product_id: item.product_id,
      quantity: Number(item.quantity) || 1,
    })),
  }
}

async function submit() {
  if (saving.value) return
  saving.value = true
  errors.value = {}

  try {
    const payload = buildPayload()
    const saved = editingBundle.value
      ? await api.adminUpdateBundle(editingBundle.value.id, payload)
      : await api.adminCreateBundle(payload)

    admin.notify(`Lot « ${saved.name_fr} » ${editingBundle.value ? 'mis à jour' : 'créé'}.`)
    formOpen.value = false
    load()
  } catch (error) {
    if (error.errors) {
      errors.value = error.errors
      admin.notify('Le formulaire contient des erreurs.', 'error')
    } else {
      admin.notify(error.message || 'Enregistrement impossible.', 'error')
    }
  } finally {
    saving.value = false
  }
}

/** Bascule « en vedette » : le lot s'affiche en tête de la boutique. */
async function toggleFeatured(bundle) {
  const previous = bundle.is_featured
  bundle.is_featured = !previous // optimiste

  try {
    const updated = await api.adminUpdateBundle(bundle.id, { is_featured: !previous })
    const index = bundles.value.findIndex((b) => b.id === updated.id)
    if (index !== -1) bundles.value[index] = updated
  } catch (error) {
    bundle.is_featured = previous // rollback
    admin.handleApiError(error, router)
  }
}

async function confirmDelete(bundle) {
  if (!window.confirm(`Supprimer le lot « ${bundle.name_fr} » ?`)) return
  try {
    await api.adminDeleteBundle(bundle.id)
    admin.notify(`Lot « ${bundle.name_fr} » supprimé.`)
    load()
  } catch (error) {
    admin.handleApiError(error, router)
  }
}

function contentsOf(bundle) {
  return (bundle.items || [])
    .map((item) => `${item.quantity}× ${item.product.name_fr}`)
    .join(' + ')
}
</script>

<template>
  <div>
    <div class="admin-page-head">
      <div>
        <h2>Lots</h2>
        <p class="admin-muted">Regroupez plusieurs produits à un prix réduit — la boutique affiche le prix cumulé barré.</p>
      </div>
      <button class="btn btn-gold" type="button" @click="openCreate">+ Nouveau lot</button>
    </div>

    <!-- Barre de recherche -->
    <div class="admin-toolbar admin-toolbar-split">
      <div class="search-box admin-search">
        <input
          v-model="search"
          type="search"
          placeholder="Rechercher un lot (nom, slug)…"
          @input="onSearchInput"
        >
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
      </div>
      <p class="admin-muted" v-if="!loading">{{ bundles.length }} lot(s)</p>
    </div>

    <!-- Chargement -->
    <div class="admin-cards" v-if="loading">
      <div class="skel-card admin-skel" v-for="i in 3" :key="i">
        <div class="skel-line skel"></div><div class="skel-line skel short"></div>
      </div>
    </div>

    <!-- Liste -->
    <div class="admin-table-wrap" v-else>
      <table class="admin-table">
        <thead>
          <tr>
            <th class="ta-center" style="width:40px;">
              <input type="checkbox" :checked="allSelected" @change="toggleSelectAll"
                style="width:16px;height:16px;cursor:pointer;accent-color:var(--gold);">
            </th>
            <th>Lot</th>
            <th>Composition</th>
            <th class="ta-right">Valeur cumulée</th>
            <th class="ta-right">Prix du lot</th>
            <th class="ta-right">Économie</th>
            <th class="ta-center" title="Affiché en tête de la section Nos lots">★</th>
            <th class="ta-center">Actif</th>
            <th class="ta-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="bundle in bundles" :key="bundle.id" :class="{ 'row-selected': selectedIds.has(bundle.id) }">
            <td class="ta-center">
              <input type="checkbox" :checked="selectedIds.has(bundle.id)" @change="toggleSelect(bundle.id)"
                style="width:16px;height:16px;cursor:pointer;accent-color:var(--gold);">
            </td>
            <td>
              <div class="admin-product-cell">
                <img :src="bundle.image" :alt="bundle.name_fr">
                <div>
                  <strong>{{ bundle.name_fr }}</strong>
                  <small>{{ bundle.name_ar }}</small>
                </div>
              </div>
            </td>
            <td class="admin-contents">{{ contentsOf(bundle) }}</td>
            <td class="ta-right"><span class="price-struck">{{ formatPrice(bundle.regular_total) }}</span></td>
            <td class="ta-right admin-price">{{ formatPrice(bundle.price) }}</td>
            <td class="ta-right admin-savings">-{{ formatPrice(bundle.savings) }} ({{ bundle.savings_percent }}%)</td>
            <td class="ta-center">
              <button
                class="admin-switch"
                :class="{ on: bundle.is_featured }"
                type="button"
                aria-label="En vedette"
                title="En vedette : affiché en premier dans la boutique"
                @click="toggleFeatured(bundle)"
              >★</button>
            </td>
            <td class="ta-center">{{ bundle.is_active ? '✓' : '—' }}</td>
            <td class="ta-right">
              <button class="admin-action" type="button" @click="openEdit(bundle)">Modifier</button>
              <button class="admin-action danger" type="button" @click="confirmDelete(bundle)">Supprimer</button>
            </td>
          </tr>
          <tr v-if="bundles.length === 0">
            <td colspan="9" class="admin-empty">Aucun lot pour l'instant — créez-en un pour booster vos ventes.</td>
          </tr>
        </tbody>
      </table>
      <!-- Barre d'actions en masse -->
      <div class="bulk-bar" v-if="selectedIds.size > 0">
        <span>{{ selectedIds.size }} sélectionné(s)</span>
        <button class="admin-action danger" type="button" :disabled="bulkDeleting" @click="bulkDelete">
          {{ bulkDeleting ? 'Suppression…' : '🗑 Supprimer la sélection' }}
        </button>
        <button class="admin-action" type="button" @click="selectedIds.clear()">Annuler</button>
      </div>
    </div>

    <!-- Formulaire création / édition -->
    <div class="overlay active" v-if="formOpen" @click.self="formOpen = false"></div>
    <div class="modal-panel active admin-form-panel" v-if="formOpen" role="dialog" aria-modal="true">
      <button class="modal-close" type="button" @click="formOpen = false" aria-label="Fermer">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </button>

      <div class="admin-form-head">
        <h3>{{ editingBundle ? 'Modifier le lot' : 'Nouveau lot' }}</h3>
      </div>

      <form class="admin-form" @submit.prevent="submit">
        <div class="admin-form-grid">
          <div class="field" :class="{ invalid: errors.name_fr }">
            <label for="bfNameFr">Nom du lot (français) *</label>
            <input id="bfNameFr" v-model="form.name_fr" type="text" required>
            <p class="field-error" v-if="errors.name_fr">{{ errors.name_fr[0] }}</p>
          </div>
          <div class="field" :class="{ invalid: errors.name_ar }">
            <label for="bfNameAr">الاسم (عربي) *</label>
            <input id="bfNameAr" v-model="form.name_ar" type="text" dir="rtl" required>
            <p class="field-error" v-if="errors.name_ar">{{ errors.name_ar[0] }}</p>
          </div>
        </div>

        <div class="admin-form-grid">
          <div class="field" :class="{ invalid: errors.price }">
            <label for="bfPrice">Prix du lot (DA) *</label>
            <input id="bfPrice" v-model.number="form.price" type="number" min="0" step="1" required>
            <p class="field-error" v-if="errors.price">{{ errors.price[0] }}</p>
          </div>
          <div class="field">
            <label for="bfImage">Image (URL, facultatif)</label>
            <input id="bfImage" v-model="form.image" type="url" placeholder="vide → image du premier article">
          </div>
        </div>

        <!-- Sélecteur de produits -->
        <div class="field">
          <label>Composition du lot *</label>
          <div class="search-box admin-search" style="min-width:0;">
            <input
              v-model="productSearch"
              type="search"
              placeholder="Rechercher un produit à ajouter (2 caractères minimum)…"
              @input="onProductSearch"
            >
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
          </div>

          <!-- Résultats de recherche -->
          <div class="bundle-search-results" v-if="searchResults.length">
            <button
              type="button"
              class="bundle-result"
              v-for="product in searchResults"
              :key="product.id"
              @click="addProductToBundle(product)"
            >
              <img :src="product.image" :alt="product.name_fr">
              <span>{{ product.name_fr }}</span>
              <small>{{ formatPrice(product.price) }}</small>
              <b>+</b>
            </button>
          </div>

          <!-- Articles sélectionnés -->
          <div class="bundle-selected" v-if="form.items.length">
            <div class="bundle-selected-row" v-for="(item, index) in form.items" :key="item.product_id">
              <img :src="item.product.image" :alt="item.product.name_fr">
              <span class="bundle-selected-name">{{ item.product.name_fr }}</span>
              <div class="qty-stepper" style="border-color:rgba(23,21,18,.15);">
                <button type="button" @click="item.quantity = Math.max(1, item.quantity - 1)">−</button>
                <span style="color:var(--indigo-deep);">{{ item.quantity }}</span>
                <button type="button" @click="item.quantity = Math.min(99, item.quantity + 1)">+</button>
              </div>
              <small class="admin-muted">{{ formatPrice(item.product.price * item.quantity) }}</small>
              <button class="admin-action danger" type="button" @click="removeItem(index)">✕</button>
            </div>
          </div>
          <p class="field-error" v-if="errors.items">{{ errors.items[0] }}</p>
        </div>

        <!-- Récapitulatif du prix -->
        <div class="checkout-summary" v-if="form.items.length">
          <div class="cart-total">
            <span>Valeur cumulée</span>
            <span><span class="price-struck">{{ formatPrice(regularTotal) }}</span></span>
          </div>
          <div class="cart-total" style="margin-top:6px;">
            <span><strong>Prix du lot</strong></span>
            <span><strong style="color:var(--clay);">{{ formatPrice(form.price || 0) }}</strong></span>
          </div>
          <p class="admin-muted" style="margin-top:6px;" v-if="savings > 0">
            → le client économise {{ formatPrice(savings) }}
            ({{ regularTotal > 0 ? Math.round(savings / regularTotal * 100) : 0 }} %)
          </p>
        </div>

        <div class="admin-checkboxes">
          <label class="admin-check">
            <input v-model="form.is_active" type="checkbox">
            <span>Lot visible dans la boutique</span>
          </label>
          <label class="admin-check">
            <input v-model="form.is_featured" type="checkbox">
            <span>★ En vedette (affiché en premier)</span>
          </label>
        </div>

        <div class="checkout-actions">
          <button class="btn btn-outline-dark" type="button" @click="formOpen = false">Annuler</button>
          <button class="btn btn-gold" type="submit" :disabled="saving">
            {{ saving ? 'Enregistrement…' : (editingBundle ? 'Enregistrer' : 'Créer le lot') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
