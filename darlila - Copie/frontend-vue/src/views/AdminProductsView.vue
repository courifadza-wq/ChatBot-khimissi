<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAdminStore } from '../stores/admin'
import { useI18n, formatPrice } from '../i18n'
import AdminProductForm from '../components/admin/AdminProductForm.vue'

/** Parseur CSV côté client (guillemets, séparateur ; ou ,). */
function parseCsvText(text) {
  const lines = text.replace(/^\uFEFF/, '').split(/\r\n|\r|\n/).filter((l) => l.trim() !== '')
  if (lines.length < 1) return []
  const separator = (lines[0].split(';').length >= lines[0].split(',').length) ? ';' : ','
  const splitLine = (line) => {
    const cells = []
    let current = ''
    let inQuotes = false
    for (let i = 0; i < line.length; i++) {
      const ch = line[i]
      if (inQuotes) {
        if (ch === '"') {
          if (line[i + 1] === '"') { current += '"'; i++ } else { inQuotes = false }
        } else { current += ch }
      } else if (ch === '"') { inQuotes = true }
      else if (ch === separator) { cells.push(current); current = '' }
      else { current += ch }
    }
    cells.push(current)
    return cells
  }
  const header = splitLine(lines[0]).map((c) => c.trim().toLowerCase().replace(/[\s-]+/g, '_').replace(/[^a-z0-9_]/g, ''))
  return lines.slice(1).map((line) => {
    const cells = splitLine(line)
    const row = {}
    header.forEach((key, index) => { if (key) row[key] = cells[index] ?? '' })
    return row
  })
}

/** Convertit un fichier .xlsx en texte CSV (« ; ») via SheetJS (import dynamique). */
async function xlsxToCsv(file) {
  const XLSX = await import('xlsx')
  const workbook = XLSX.read(await file.arrayBuffer(), { type: 'array' })
  const sheet = workbook.Sheets[workbook.SheetNames[0]]
  if (!sheet) throw new Error('Le fichier Excel est vide.')
  return XLSX.utils.sheet_to_csv(sheet, { FS: ';', blankrows: false })
}

/** Convertit un texte CSV en classeur .xlsx et déclenche le téléchargement. */
async function downloadCsvAsXlsx(csvText, filename) {
  const XLSX = await import('xlsx')
  const rows = parseCsvText(csvText)
  const sheet = XLSX.utils.json_to_sheet(rows)
  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, sheet, 'Produits')
  XLSX.writeFile(workbook, filename)
}

const router = useRouter()
const admin = useAdminStore()
const { pick, locale } = useI18n()

const PER_PAGE = 20

const products = ref([])
const categories = ref([])
const pagination = ref(null) // { total, current_page, last_page }
const loading = ref(true)
const saving = ref(false)

const formOpen = ref(false)
const editingProduct = ref(null)
const selectedIds = ref(new Set())
const bulkDeleting = ref(false) // null = création
const deleting = ref(null)

/* ---------- Recherche serveur (debounce) ---------- */
const search = ref('')
let searchTimer = null
function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    load()
  }, 350)
}

/* ---------- Pagination ---------- */
const page = ref(1)
const totalPages = computed(() => pagination.value?.last_page ?? 1)
const totalProducts = computed(() => pagination.value?.total ?? products.value.length)
const paginationPages = computed(() => {
  const last = totalPages.value
  const current = page.value
  const pages = []
  const push = (p) => !pages.includes(p) && p >= 1 && p <= last && pages.push(p)
  push(1)
  for (let p = current - 1; p <= current + 1; p++) push(p)
  push(last)
  return pages.sort((a, b) => a - b)
})

function goTo(nextPage) {
  if (nextPage < 1 || nextPage > totalPages.value || nextPage === page.value) return
  page.value = nextPage
  load()
}

async function load() {
  loading.value = true
  try {
    const { items, meta } = await api.adminProducts({
      search: search.value,
      page: page.value,
      per_page: PER_PAGE,
    })
    products.value = items
    pagination.value = meta
    if (meta && page.value > meta.last_page) {
      page.value = meta.last_page
    }
  } catch (error) {
    admin.handleApiError(error, router)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    categories.value = await api.adminCategories()
  } catch (error) {
    admin.handleApiError(error, router)
  }
  load()
})

function toggleSelect(id) {
  if (selectedIds.value.has(id)) selectedIds.value.delete(id)
  else selectedIds.value.add(id)
}

const allSelected = computed(() =>
  products.value.length > 0 && products.value.every((p) => selectedIds.value.has(p.id))
)

function toggleSelectAll() {
  if (allSelected.value) selectedIds.value.clear()
  else products.value.forEach((p) => selectedIds.value.add(p.id))
}

async function bulkDelete() {
  const count = selectedIds.value.size
  if (count === 0) return
  if (!window.confirm(`Supprimer définitivement ${count} produit(s) sélectionné(s) ?`)) return

  bulkDeleting.value = true
  try {
    const result = await api.adminBulkDeleteProducts([...selectedIds.value])
    admin.notify(`${result.deleted} produit(s) supprimé(s).`)
    selectedIds.value.clear()
    load()
  } catch (error) {
    admin.handleApiError(error, router)
  } finally {
    bulkDeleting.value = false
  }
}

function openCreate() {
  editingProduct.value = null
  formOpen.value = true
}

function openEdit(product) {
  editingProduct.value = product
  formOpen.value = true
}

function onSaved(product) {
  formOpen.value = false
  // recharge la page courante pour refléter l'ordre/les filtres
  load()
  admin.notify(
    products.value.some((p) => p.id === product.id)
      ? `Produit « ${product.name_fr} » mis à jour.`
      : `Produit « ${product.name_fr} » créé.`
  )
}

/** Bascule rapide (actif / en vedette) depuis la liste. */
async function toggleFlag(product, field) {
  const previous = product[field]
  product[field] = !previous // optimiste

  try {
    const updated = await api.adminUpdateProduct(product.id, { [field]: !previous })
    const index = products.value.findIndex((p) => p.id === updated.id)
    if (index !== -1) products.value[index] = updated
  } catch (error) {
    product[field] = previous // rollback
    admin.handleApiError(error, router)
  }
}

async function confirmDelete(product) {
  if (!window.confirm(`Supprimer définitivement « ${product.name_fr} » ?`)) return
  deleting.value = product.id
  try {
    await api.adminDeleteProduct(product.id)
    admin.notify(`Produit « ${product.name_fr} » supprimé.`)
    load()
  } catch (error) {
    admin.handleApiError(error, router)
  } finally {
    deleting.value = null
  }
}

/** Copie le lien direct du produit dans la boutique. */
async function copyProductLink(product) {
  const url = `${window.location.origin}/produit/${product.slug}`
  try {
    await navigator.clipboard.writeText(url)
    admin.notify(`Lien copié : ${url}`)
  } catch {
    window.prompt('Copiez le lien du produit :', url)
  }
}

function categoryName(product) {
  return product.category ? pick(product.category, 'name') : '—'
}

/* ---------- Export CSV + Excel ---------- */
const exporting = ref(false)

async function exportExcel() {
  if (exporting.value) return
  exporting.value = true
  try {
    const csv = await api.adminExportProducts()
    await downloadCsvAsXlsx(csv, 'darlila-produits.xlsx')
    admin.notify(`Export Excel téléchargé (${totalProducts.value} produits).`)
  } catch (error) {
    admin.handleApiError(error, router)
  } finally {
    exporting.value = false
  }
}

async function exportCsv() {
  if (exporting.value) return
  exporting.value = true
  try {
    const csv = await api.adminExportProducts()
    const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'darlila-produits.csv'
    link.click()
    // laisse le temps au navigateur de démarrer le téléchargement
    setTimeout(() => URL.revokeObjectURL(url), 4000)
    admin.notify(`Export CSV téléchargé (${totalProducts.value} produits).`)
  } catch (error) {
    admin.handleApiError(error, router)
  } finally {
    exporting.value = false
  }
}

/* ---------- Import CSV ---------- */
const importOpen = ref(false)
const importState = reactive({
  file: null,
  running: false,
  result: null, // { created, updated, errors, rows }
})

function openImport() {
  importState.file = null
  importState.result = null
  importOpen.value = true
}

function onImportFileChange(event) {
  importState.file = event.target.files?.[0] || null
  importState.result = null
}

/**
 * Fichier prêt à envoyer : un .xlsx est d'abord converti en CSV
 * dans le navigateur (SheetJS) — le backend n'a rien à installer.
 */
async function importFileForUpload() {
  const file = importState.file
  if (!file) return null

  if (/\.xlsx?$/i.test(file.name)) {
    const csvText = await xlsxToCsv(file)
    return new File([csvText], 'import-converti.csv', { type: 'text/csv' })
  }

  return file
}

async function submitImport() {
  if (!importState.file || importState.running) return
  importState.running = true

  try {
    const formData = new FormData()
    formData.append('file', await importFileForUpload())
    importState.result = await api.adminImportProducts(formData)
    admin.notify(
      `Import terminé : ${importState.result.created} créé(s), ${importState.result.updated} mis à jour.`
    )
    page.value = 1
    load()
  } catch (error) {
    admin.handleApiError(error, router)
  } finally {
    importState.running = false
  }
}
</script>

<template>
  <div>
    <div class="admin-page-head">
      <div>
        <h2>Produits</h2>
        <p class="admin-muted">{{ totalProducts.toLocaleString('fr-FR') }} produit·s au catalogue</p>
        <p class="admin-legend">
          ★ <strong>En vedette</strong> = affiché en tête de la boutique (avant les autres produits) —
          à utiliser pour vos meilleures ventes et promotions.
        </p>
      </div>
      <div class="admin-head-actions">
        <button class="btn btn-outline-dark" type="button" :disabled="exporting" @click="exportCsv">
          {{ exporting ? 'Export…' : '↓ CSV' }}
        </button>
        <button class="btn btn-outline-dark" type="button" :disabled="exporting" @click="exportExcel">
          {{ exporting ? 'Export…' : '↓ Excel (.xlsx)' }}
        </button>
        <button class="btn btn-outline-dark" type="button" @click="openImport">↑ Importer Excel / CSV</button>
        <button class="btn btn-gold" type="button" @click="openCreate">+ Nouveau produit</button>
      </div>
    </div>

    <div class="admin-toolbar admin-toolbar-split">
      <div class="search-box admin-search">
        <input
          v-model="search"
          type="search"
          placeholder="Rechercher (nom, slug)…"
          @input="onSearchInput"
        >
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
      </div>
      <p class="admin-muted" v-if="pagination">
        Page {{ pagination.current_page }} / {{ pagination.last_page }} —
        {{ pagination.total.toLocaleString('fr-FR') }} résultat·s
      </p>
    </div>

    <!-- Chargement -->
    <div class="admin-cards" v-if="loading">
      <div class="skel-card admin-skel" v-for="i in 6" :key="i">
        <div class="skel-line skel"></div><div class="skel-line skel short"></div>
      </div>
    </div>

    <!-- Tableau -->
    <div class="admin-table-wrap" v-else>
      <table class="admin-table">
        <thead>
          <tr>
            <th class="ta-center" style="width:40px;">
              <input
                type="checkbox"
                :checked="allSelected"
                @change="toggleSelectAll"
                style="width:16px;height:16px;cursor:pointer;accent-color:var(--gold);"
              >
            </th>
            <th>Produit</th>
            <th>Catégorie</th>
            <th class="ta-right">Prix</th>
            <th class="ta-center">En vedette</th>
            <th class="ta-center">Actif</th>
            <th class="ta-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in products" :key="product.id" :class="{ 'row-selected': selectedIds.has(product.id) }">
            <td class="ta-center">
              <input
                type="checkbox"
                :checked="selectedIds.has(product.id)"
                @change="toggleSelect(product.id)"
                style="width:16px;height:16px;cursor:pointer;accent-color:var(--gold);"
              >
            </td>
            <td>
              <div class="admin-product-cell">
                <img :src="product.image" :alt="product.name_fr">
                <div>
                  <strong>{{ product.name_fr }}</strong>
                  <small>{{ product.name_ar }}</small>
                  <small class="admin-slug">/{{ product.slug }}</small>
                </div>
              </div>
            </td>
            <td>{{ categoryName(product) }}</td>
            <td class="ta-right admin-price">{{ formatPrice(product.price, locale) }}</td>
            <td class="ta-center">
              <button
                class="admin-switch"
                :class="{ on: product.is_featured }"
                type="button"
                aria-label="En vedette"
                @click="toggleFlag(product, 'is_featured')"
              >★</button>
            </td>
            <td class="ta-center">
              <button
                class="admin-switch"
                :class="{ on: product.is_active }"
                type="button"
                aria-label="Actif"
                @click="toggleFlag(product, 'is_active')"
              ></button>
            </td>
            <td class="ta-right">
              <button class="admin-action" type="button" title="Lien direct vers ce produit dans la boutique" @click="copyProductLink(product)">🔗 Lien</button>
              <button class="admin-action" type="button" @click="openEdit(product)">Modifier</button>
              <button
                class="admin-action danger"
                type="button"
                :disabled="deleting === product.id"
                @click="confirmDelete(product)"
              >Supprimer</button>
            </td>
          </tr>
          <tr v-if="products.length === 0">
            <td colspan="7" class="admin-empty">Aucun produit ne correspond à la recherche.</td>
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

      <!-- Pagination -->
      <div class="admin-pagination" v-if="totalPages > 1">
        <button
          class="admin-page-btn"
          type="button"
          :disabled="page <= 1"
          @click="goTo(page - 1)"
        >← Précédent</button>

        <button
          v-for="p in paginationPages"
          :key="p"
          class="admin-page-btn"
          :class="{ active: p === page }"
          type="button"
          @click="goTo(p)"
        >{{ p }}</button>

        <button
          class="admin-page-btn"
          type="button"
          :disabled="page >= totalPages"
          @click="goTo(page + 1)"
        >Suivant →</button>
      </div>
    </div>

    <!-- Formulaire création / édition -->
    <AdminProductForm
      v-if="formOpen"
      :product="editingProduct"
      :categories="categories"
      @close="formOpen = false"
      @saved="onSaved"
    />

    <!-- Modal import CSV -->
    <div class="overlay active" v-if="importOpen" @click.self="importOpen = false"></div>
    <div class="modal-panel active admin-form-panel" v-if="importOpen" role="dialog" aria-modal="true">
      <button class="modal-close" type="button" @click="importOpen = false" aria-label="Fermer">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </button>

      <div class="admin-form-head">
        <h3>Importer des produits (Excel ou CSV)</h3>
      </div>

      <div class="admin-form">
        <div class="box">
          <p class="admin-muted">
            Colonnes reconnues : <code>category</code> (slug ou nom), <code>name_fr</code>*,
            <code>name_ar</code>*, <code>description_fr</code>, <code>description_ar</code>,
            <code>price</code>*, <code>image</code> (URL), <code>slug</code>,
            <code>is_active</code>, <code>is_featured</code>.<br>
            CSV (<code>;</code> ou <code>,</code>) ou Excel <code>.xlsx</code> — un produit existant (même slug) est
            <strong>mis à jour</strong>, sinon créé. Astuce : exportez d'abord le CSV pour
            obtenir un modèle prêt à remplir.
          </p>
        </div>

        <div class="field">
          <label for="importFile">Fichier CSV ou Excel (.xlsx)</label>
          <input id="importFile" type="file" accept=".csv,.xlsx,text/csv,text/plain" @change="onImportFileChange">
        </div>

        <div class="checkout-actions">
          <button class="btn btn-outline-dark" type="button" @click="importOpen = false">Fermer</button>
          <button
            class="btn btn-gold"
            type="button"
            :disabled="!importState.file || importState.running"
            @click="submitImport"
          >
            {{ importState.running ? 'Import en cours…' : 'Importer' }}
          </button>
        </div>

        <!-- Résultat -->
        <div v-if="importState.result" class="import-result">
          <p>
            <strong>{{ importState.result.created }}</strong> créé(s) ·
            <strong>{{ importState.result.updated }}</strong> mis à jour ·
            <strong>{{ importState.result.errors.length }}</strong> erreur(s)
            <span class="admin-muted">(sur {{ importState.result.rows }} lignes)</span>
          </p>
          <div class="import-errors" v-if="importState.result.errors.length">
            <p v-for="error in importState.result.errors" :key="error">{{ error }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
