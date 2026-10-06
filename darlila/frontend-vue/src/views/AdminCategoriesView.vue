<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAdminStore } from '../stores/admin'
import { useI18n } from '../i18n'

/**
 * Gestion des catégories et SOUS-catégories : création, renommage
 * (FR/AR), description, ordre d'affichage, catégorie parent — avec
 * protection anti-suppression si des produits y sont rattachés ou
 * si elle possède des sous-catégories.
 */
const router = useRouter()
const admin = useAdminStore()
const { pick } = useI18n()

const categories = ref([])
const loading = ref(true)
const saving = ref(false)

const formOpen = ref(false)
const editingCategory = ref(null)
const errors = ref({})

const form = reactive({
  parent_id: null,
  name_fr: '',
  name_ar: '',
  description_fr: '',
  description_ar: '',
  position: null,
})

/** Catégories principales (pouvant servir de parent). */
const mainCategories = computed(() => {
  const list = Array.isArray(categories.value) ? categories.value : []
  return list.filter((c) => !c.parent_id)
})

/**
 * Arbre d'affichage : chaque catégorie principale suivie de ses
 * sous-catégories, triées par ordre d'affichage.
 */
const tree = computed(() => {
  const list = Array.isArray(categories.value) ? categories.value : []
  const mains = [...list.filter((c) => !c.parent_id)]
    .sort((a, b) => (a.position ?? 0) - (b.position ?? 0) || a.id - b.id)

  return mains.map((main) => {
    const children = list
      .filter((c) => c.parent_id === main.id)
      .sort((a, b) => (a.position ?? 0) - (b.position ?? 0) || a.id - b.id)

    // Nombre total de produits : directs + ceux des sous-catégories.
    const total = (main.products_count ?? 0)
      + children.reduce((sum, child) => sum + (child.products_count ?? 0), 0)

    return { main, children, total }
  })
})

/** Sous-catégories « orphelines » (parent supprimé en base, sécurité). */
const orphanSubs = computed(() => {
  const list = Array.isArray(categories.value) ? categories.value : []
  const ids = new Set(list.map((c) => c.id))
  return list.filter((c) => c.parent_id && !ids.has(c.parent_id))
})

async function load() {
  loading.value = true
  try {
    const res = await api.adminCategories()
    categories.value = Array.isArray(res) ? res : (res?.data ?? [])
  } catch (error) {
    admin.handleApiError(error, router)
  } finally {
    loading.value = false
  }
}
onMounted(load)

function nextPosition() {
  return (mainCategories.value.length + 1) * 10
}

const subCategoriesToAdd = ref([])

function addSubCategoryField() {
  subCategoriesToAdd.value.push({ name_fr: '', name_ar: '' })
}

function removeSubCategoryField(index) {
  subCategoriesToAdd.value.splice(index, 1)
}

function openCreate() {
  editingCategory.value = null
  Object.assign(form, {
    parent_id: null,
    name_fr: '', name_ar: '', description_fr: '', description_ar: '',
    position: nextPosition(),
  })
  subCategoriesToAdd.value = []
  errors.value = {}
  formOpen.value = true
}

function openEdit(category) {
  editingCategory.value = category
  Object.assign(form, {
    parent_id: category.parent_id,
    name_fr: category.name_fr,
    name_ar: category.name_ar,
    description_fr: category.description_fr || '',
    description_ar: category.description_ar || '',
    position: category.position,
  })
  subCategoriesToAdd.value = []
  errors.value = {}
  formOpen.value = true
}

/** Créer directement une sous-catégorie depuis une ligne parent. */
function openCreateSub(parent) {
  openCreate()
  form.parent_id = parent.id
  const subs = categories.value.filter((c) => c.parent_id === parent.id)
  form.position = Math.max(...subs.map((c) => c.position ?? 0), 0) + 10
}

async function submit() {
  if (saving.value) return
  saving.value = true
  errors.value = {}

  try {
    const payload = {
      parent_id: form.parent_id || null,
      name_fr: form.name_fr.trim(),
      name_ar: form.name_ar.trim(),
      description_fr: form.description_fr.trim() || null,
      description_ar: form.description_ar.trim() || null,
      position: Number(form.position) || null,
    }

    const saved = editingCategory.value
      ? await api.adminUpdateCategory(editingCategory.value.id, payload)
      : await api.adminCreateCategory(payload)

    // Si des sous-catégories ont été saisies lors de la création d'une catégorie principale :
    if (!editingCategory.value && !form.parent_id && subCategoriesToAdd.value.length > 0) {
      let createdSubsCount = 0
      for (const [idx, sub] of subCategoriesToAdd.value.entries()) {
        if (sub.name_fr.trim() && sub.name_ar.trim()) {
          await api.adminCreateCategory({
            parent_id: saved.id,
            name_fr: sub.name_fr.trim(),
            name_ar: sub.name_ar.trim(),
            position: (saved.position || 10) + (idx + 1) * 10,
          })
          createdSubsCount++
        }
      }
      admin.notify(`Catégorie « ${saved.name_fr} » créée avec ${createdSubsCount} sous-catégorie(s).`)
    } else {
      admin.notify(`Catégorie « ${saved.name_fr} » ${editingCategory.value ? 'mise à jour' : 'créée'}.`)
    }

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

async function confirmDelete(category) {
  if (!window.confirm(`Supprimer la catégorie « ${category.name_fr} » ?`)) return

  try {
    await api.adminDeleteCategory(category.id)
    admin.notify(`Catégorie « ${category.name_fr} » supprimée.`)
    load()
  } catch (error) {
    // 422 : produits ou sous-catégories rattachés → message du serveur
    admin.notify(error.message || 'Suppression impossible.', 'error')
  }
}
</script>

<template>
  <div>
    <div class="admin-page-head">
      <div>
        <h2>Catégories</h2>
        <p class="admin-muted">
          {{ mainCategories.length }} catégorie(s) principale(s) et
          {{ categories.length - mainCategories.length }} sous-catégorie(s) — organisent
          la boutique et les filtres. Une catégorie utilisée par des produits ne peut pas
          être supprimée.
        </p>
      </div>
      <button class="btn btn-gold" type="button" @click="openCreate">+ Nouvelle catégorie</button>
    </div>

    <!-- Chargement -->
    <div class="admin-cards" v-if="loading">
      <div class="skel-card admin-skel" v-for="i in 4" :key="i">
        <div class="skel-line skel"></div><div class="skel-line skel short"></div>
      </div>
    </div>

    <!-- Tableau hiérarchique -->
    <div class="admin-table-wrap" v-else>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Catégorie</th>
            <th>Slug</th>
            <th class="ta-center">Produits</th>
            <th class="ta-center">Ordre</th>
            <th class="ta-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="{ main, children, total } in tree" :key="main.id">
            <!-- Catégorie principale -->
            <tr class="cat-row-main">
              <td>
                <div class="admin-product-cell">
                  <div>
                    <strong>{{ main.name_fr }}</strong>
                    <small>{{ main.name_ar }}</small>
                    <small v-if="main.description_fr" class="admin-slug">{{ main.description_fr.slice(0, 50) }}</small>
                  </div>
                </div>
              </td>
              <td><code class="admin-slug">{{ main.slug }}</code></td>
              <td class="ta-center">
                <span class="admin-count-badge">{{ total }}</span>
              </td>
              <td class="ta-center">{{ main.position }}</td>
              <td class="ta-right">
                <button class="admin-action" type="button" @click="openCreateSub(main)">+ Sous-catégorie</button>
                <button class="admin-action" type="button" @click="openEdit(main)">Modifier</button>
                <button class="admin-action danger" type="button" @click="confirmDelete(main)">Supprimer</button>
              </td>
            </tr>
            <!-- Sous-catégories -->
            <tr v-for="sub in children" :key="sub.id" class="cat-row-sub">
              <td>
                <div class="admin-product-cell cat-sub-cell">
                  <span class="cat-sub-arrow" aria-hidden="true">↳</span>
                  <div>
                    <strong>{{ sub.name_fr }}</strong>
                    <small>{{ sub.name_ar }}</small>
                    <small v-if="sub.description_fr" class="admin-slug">{{ sub.description_fr.slice(0, 50) }}</small>
                  </div>
                </div>
              </td>
              <td><code class="admin-slug">{{ sub.slug }}</code></td>
              <td class="ta-center">
                <span class="admin-count-badge">{{ sub.products_count ?? 0 }}</span>
              </td>
              <td class="ta-center">{{ sub.position }}</td>
              <td class="ta-right">
                <button class="admin-action" type="button" @click="openEdit(sub)">Modifier</button>
                <button class="admin-action danger" type="button" @click="confirmDelete(sub)">Supprimer</button>
              </td>
            </tr>
          </template>

          <!-- Sécurité : sous-catégories orphelines -->
          <tr v-for="sub in orphanSubs" :key="sub.id" class="cat-row-sub">
            <td>
              <div class="admin-product-cell cat-sub-cell">
                <span class="cat-sub-arrow" aria-hidden="true">↳</span>
                <div>
                  <strong>{{ sub.name_fr }}</strong>
                  <small>{{ sub.name_ar }}</small>
                </div>
              </div>
            </td>
            <td><code class="admin-slug">{{ sub.slug }}</code></td>
            <td class="ta-center">
              <span class="admin-count-badge">{{ sub.products_count ?? 0 }}</span>
            </td>
            <td class="ta-center">{{ sub.position }}</td>
            <td class="ta-right">
              <button class="admin-action" type="button" @click="openEdit(sub)">Modifier</button>
              <button class="admin-action danger" type="button" @click="confirmDelete(sub)">Supprimer</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Formulaire -->
    <div class="overlay active" v-if="formOpen" @click.self="formOpen = false"></div>
    <div class="modal-panel active admin-form-panel" v-if="formOpen" role="dialog" aria-modal="true" style="max-width: 640px;">
      <button class="modal-close" type="button" @click="formOpen = false" aria-label="Fermer">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </button>

      <div class="admin-form-head">
        <h3>{{ editingCategory ? 'Modifier la catégorie' : 'Nouvelle catégorie' }}</h3>
      </div>

      <form class="admin-form" @submit.prevent="submit">
        <div class="field" :class="{ invalid: errors.parent_id }">
          <label for="cfParent">Catégorie parent</label>
          <select id="cfParent" v-model="form.parent_id">
            <option :value="null">Aucune — catégorie principale</option>
            <option v-for="main in mainCategories" :key="main.id" :value="main.id">
              {{ main.name_fr }}
            </option>
          </select>
          <p class="field-error" v-if="errors.parent_id">{{ errors.parent_id[0] }}</p>
          <p class="admin-muted" style="margin-top: 4px;">
            Choisissez une catégorie parent pour créer une <strong>sous-catégorie</strong>
            (ex. « Chaussures » dans « Chaussures &amp; Accessoires »).
          </p>
        </div>

        <div class="admin-form-grid">
          <div class="field" :class="{ invalid: errors.name_fr }">
            <label for="cfNameFr">Nom (français) *</label>
            <input id="cfNameFr" v-model="form.name_fr" type="text" required>
            <p class="field-error" v-if="errors.name_fr">{{ errors.name_fr[0] }}</p>
          </div>
          <div class="field" :class="{ invalid: errors.name_ar }">
            <label for="cfNameAr">الاسم (عربي) *</label>
            <input id="cfNameAr" v-model="form.name_ar" type="text" dir="rtl" required>
            <p class="field-error" v-if="errors.name_ar">{{ errors.name_ar[0] }}</p>
          </div>
        </div>

        <div class="admin-form-grid">
          <div class="field">
            <label for="cfDescFr">Description (français)</label>
            <textarea id="cfDescFr" v-model="form.description_fr" rows="2"></textarea>
          </div>
          <div class="field">
            <label for="cfDescAr">الوصف (عربي)</label>
            <textarea id="cfDescAr" v-model="form.description_ar" rows="2" dir="rtl"></textarea>
          </div>
        </div>

        <!-- Sous-catégories à créer en même temps (uniquement pour nouvelle catégorie principale) -->
        <div v-if="!form.parent_id && !editingCategory" class="subcategories-builder" style="margin: 16px 0; padding: 14px; background: rgba(45, 53, 144, 0.03); border-radius: 8px; border: 1px dashed rgba(45, 53, 144, 0.2);">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
            <strong style="font-size: 13px;">Sous-catégories (optionnel)</strong>
            <button class="btn btn-sm btn-outline-dark" type="button" @click="addSubCategoryField" style="padding: 4px 10px; font-size: 12px;">+ Ajouter une sous-catégorie</button>
          </div>
          <p class="admin-muted" style="margin-bottom: 10px; font-size: 12px;" v-if="subCategoriesToAdd.length === 0">
            Ajoutez directement des sous-catégories rattachées à cette catégorie mère.
          </p>
          <div v-for="(sub, idx) in subCategoriesToAdd" :key="idx" style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px;">
            <input v-model="sub.name_fr" type="text" placeholder="Nom FR (ex. Chaussures)" required style="flex: 1; padding: 6px 10px; font-size: 13px;">
            <input v-model="sub.name_ar" type="text" placeholder="الاسم بالعربية" dir="rtl" required style="flex: 1; padding: 6px 10px; font-size: 13px;">
            <button class="admin-action danger" type="button" @click="removeSubCategoryField(idx)" title="Supprimer" style="padding: 6px 10px;">✕</button>
          </div>
        </div>

        <div class="field" :class="{ invalid: errors.position }">
          <label for="cfPosition">Ordre d'affichage (petit = en premier)</label>
          <input id="cfPosition" v-model.number="form.position" type="number" min="0" max="9999">
          <p class="field-error" v-if="errors.position">{{ errors.position[0] }}</p>
        </div>

        <p class="admin-muted">
          Le slug (URL) est généré automatiquement à partir du nom français.
        </p>

        <div class="checkout-actions">
          <button class="btn btn-outline-dark" type="button" @click="formOpen = false">Annuler</button>
          <button class="btn btn-gold" type="submit" :disabled="saving">
            {{ saving ? 'Enregistrement…' : (editingCategory ? 'Enregistrer' : 'Créer la catégorie') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.cat-row-main td {
  background: rgba(45, 53, 144, 0.045);
  border-top: 2px solid rgba(45, 53, 144, 0.14);
}
.cat-row-sub td {
  background: rgba(234, 47, 144, 0.025);
}
.cat-sub-cell {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding-inline-start: 14px;
}
.cat-sub-arrow {
  color: var(--gold, #ea2f90);
  font-weight: 700;
  line-height: 1.5;
}
</style>
