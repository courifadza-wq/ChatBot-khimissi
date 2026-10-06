<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAdminStore } from '../stores/admin'
import { formatPrice } from '../i18n'

const router = useRouter()
const admin = useAdminStore()

const orders = ref([])
const loading = ref(true)
const expandedId = ref(null)
const updatingStatus = ref(null)

const STATUS_FLOW = [
  { value: 'nouvelle', label: 'Nouvelle' },
  { value: 'confirmee', label: 'Confirmée' },
  { value: 'expediee', label: 'Expédiée' },
  { value: 'livree', label: 'Livrée' },
  { value: 'annulee', label: 'Annulée' },
]

const statusFilter = ref('')

const filtered = computed(() => {
  if (!statusFilter.value) return orders.value
  return orders.value.filter((order) => order.status === statusFilter.value)
})

/** Statistiques calculées à partir des commandes chargées. */
const stats = computed(() => {
  const total = orders.value.length
  const revenue = orders.value
    .filter((o) => o.status !== 'annulee')
    .reduce((sum, order) => sum + order.total, 0)
  const pending = orders.value.filter((o) => o.status === 'nouvelle').length
  const items = orders.value.reduce((sum, o) => sum + (o.items?.length || 0), 0)
  return { total, revenue, pending, items }
})

async function load() {
  loading.value = true
  try {
    orders.value = await api.adminOrders()
  } catch (error) {
    admin.handleApiError(error, router)
  } finally {
    loading.value = false
  }
}
onMounted(load)

function toggleExpand(order) {
  expandedId.value = expandedId.value === order.id ? null : order.id
}

async function changeStatus(order, event) {
  const status = event.target.value
  const previous = order.status
  updatingStatus.value = order.id
  try {
    const updated = await api.adminUpdateOrderStatus(order.id, status)
    const index = orders.value.findIndex((o) => o.id === updated.id)
    if (index !== -1) orders.value[index] = updated
    admin.notify(`Commande ${updated.reference} → ${statusLabel(status)}.`)
  } catch (error) {
    order.status = previous
    event.target.value = previous
    admin.handleApiError(error, router)
  } finally {
    updatingStatus.value = null
  }
}

function statusLabel(value) {
  return STATUS_FLOW.find((s) => s.value === value)?.label || value
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

/* ---------- Export CSV (comptabilité) — suit le filtre de statut ---------- */
const exporting = ref(false)

async function exportCsv() {
  if (exporting.value) return
  exporting.value = true

  try {
    const csv = await api.adminExportOrders(statusFilter.value ? { status: statusFilter.value } : {})
    const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `darlila-commandes-${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    // laisse le temps au navigateur de démarrer le téléchargement
    setTimeout(() => URL.revokeObjectURL(url), 4000)
    admin.notify(`Export CSV téléchargé (${orders.value.length} commande·s).`)
  } catch (error) {
    admin.handleApiError(error, router)
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <div>
    <div class="admin-page-head">
      <div>
        <h2>Commandes</h2>
        <p class="admin-muted">Suivi des commandes passées sur la boutique</p>
      </div>
      <button class="btn btn-outline-dark" type="button" :disabled="exporting" @click="exportCsv">
        {{ exporting ? 'Export…' : '↓ Exporter CSV (comptabilité)' }}
      </button>
    </div>

    <!-- Statistiques -->
    <div class="admin-stats">
      <div class="admin-stat">
        <span class="admin-stat-value">{{ stats.total }}</span>
        <span class="admin-stat-label">commandes</span>
      </div>
      <div class="admin-stat">
        <span class="admin-stat-value">{{ stats.items }}</span>
        <span class="admin-stat-label">articles vendus</span>
      </div>
      <div class="admin-stat">
        <span class="admin-stat-value">{{ formatPrice(stats.revenue) }}</span>
        <span class="admin-stat-label">chiffre d'affaires</span>
      </div>
      <div class="admin-stat warn">
        <span class="admin-stat-value">{{ stats.pending }}</span>
        <span class="admin-stat-label">en attente</span>
      </div>
    </div>

    <!-- Filtre statut -->
    <div class="admin-toolbar">
      <div class="filter-chips">
        <button
          class="chip chip-sm"
          :class="{ active: statusFilter === '' }"
          type="button"
          @click="statusFilter = ''"
        >Toutes</button>
        <button
          v-for="status in STATUS_FLOW"
          :key="status.value"
          class="chip chip-sm"
          :class="{ active: statusFilter === status.value }"
          type="button"
          @click="statusFilter = status.value"
        >{{ status.label }}</button>
      </div>
    </div>

    <!-- Chargement -->
    <div class="admin-cards" v-if="loading">
      <div class="skel-card admin-skel" v-for="i in 4" :key="i">
        <div class="skel-line skel"></div><div class="skel-line skel short"></div>
      </div>
    </div>

    <!-- Liste -->
    <div class="admin-table-wrap" v-else>
      <table class="admin-table">
        <thead>
          <tr>
            <th>Référence</th>
            <th>Client</th>
            <th>Wilaya</th>
            <th class="ta-center">Articles</th>
            <th class="ta-right">Total</th>
            <th>Statut</th>
            <th class="ta-right">Détails</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="order in filtered" :key="order.id">
            <tr class="admin-order-row" @click="toggleExpand(order)">
              <td>
                <strong class="admin-ref">{{ order.reference }}</strong>
                <small class="admin-muted d-block">{{ formatDate(order.created_at) }}</small>
              </td>
              <td>
                {{ order.customer_name }}
                <small class="admin-muted d-block">{{ order.customer_phone }}</small>
              </td>
              <td>{{ order.wilaya }}</td>
              <td class="ta-center">{{ order.items?.length || 0 }}</td>
              <td class="ta-right admin-price">{{ formatPrice(order.total) }}</td>
              <td @click.stop>
                <select
                  class="admin-status-select"
                  :class="'status-' + order.status"
                  :value="order.status"
                  :disabled="updatingStatus === order.id"
                  @change="changeStatus(order, $event)"
                >
                  <option v-for="status in STATUS_FLOW" :key="status.value" :value="status.value">
                    {{ status.label }}
                  </option>
                </select>
              </td>
              <td class="ta-right">
                <span class="admin-expand">{{ expandedId === order.id ? '▲' : '▼' }}</span>
              </td>
            </tr>

            <!-- Détail dépliable -->
            <tr class="admin-order-detail" v-if="expandedId === order.id">
              <td colspan="7">
                <div class="admin-order-detail-grid">
                  <div>
                    <h4>Articles commandés</h4>
                    <table class="admin-table inner">
                      <thead>
                        <tr><th>Produit</th><th class="ta-center">Qté</th><th class="ta-right">P.U.</th><th class="ta-right">Total</th></tr>
                      </thead>
                      <tbody>
                        <tr v-for="item in order.items" :key="item.id">
                          <td>{{ item.product_name }}</td>
                          <td class="ta-center">{{ item.quantity }}</td>
                          <td class="ta-right">{{ formatPrice(item.unit_price) }}</td>
                          <td class="ta-right">{{ formatPrice(item.line_total) }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="admin-order-info">
                    <h4>Informations</h4>
                    <p v-if="order.notes"><strong>Note :</strong> {{ order.notes }}</p>
                    <p><strong>Téléphone :</strong> {{ order.customer_phone }}</p>
                    <p class="admin-muted">Commande enregistrée le {{ formatDate(order.created_at) }} — paiement à la livraison.</p>
                  </div>
                </div>
              </td>
            </tr>
          </template>

          <tr v-if="filtered.length === 0">
            <td colspan="7" class="admin-empty">Aucune commande pour ce statut.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
