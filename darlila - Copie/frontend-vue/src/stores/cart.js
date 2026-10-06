import { defineStore } from 'pinia'
import { api } from '../api/client'
import { useShopStore } from './shop'
import { unitPriceFor } from '../utils/pricing'

const STORAGE_KEY = 'darlila_cart_v1'

function loadCart() {
  try {
    const raw = JSON.parse(localStorage.getItem(STORAGE_KEY))
    if (!Array.isArray(raw)) return []
    // Lignes { id, qty, type } — type 'product' par défaut (compat ancien panier)
    return raw
      .filter((item) => item && Number.isInteger(item.id) && Number.isInteger(item.qty) && item.qty > 0)
      .map((item) => ({
        id: item.id,
        qty: Math.min(item.qty, 99),
        type: item.type === 'bundle' ? 'bundle' : 'product',
      }))
  } catch {
    return []
  }
}

/**
 * Store « panier » : lignes { id, qty, type: 'product' | 'bundle' },
 * persistées dans localStorage.
 *
 * - Les produits appliquent la promo « -X % dès N achetés » (prix recalculés
 *   côté serveur à la commande — miroir dans utils/pricing.js).
 * - Les lots (bundles) utilisent le prix du lot ; les données viennent du
 *   store boutique (GET /api/bundles).
 * - Les produits sont hydratés à la demande via GET /api/products?ids=…
 *   (catalogue paginé 1000+ : l'article n'est pas forcément en page courante).
 */
export const useCartStore = defineStore('cart', {
  state: () => ({
    items: loadCart(),
    catalog: {}, // id → produit (hydratation à la demande)
  }),

  getters: {
    count: (state) => state.items.reduce((sum, item) => sum + item.qty, 0),

    /** Identifiants de produits pas encore hydratés. */
    missingProductIds(state) {
      return state.items
        .filter((item) => item.type === 'product' && !state.catalog[item.id])
        .map((item) => item.id)
    },

    /** Lignes enrichies (produit hydraté ou lot résolu depuis la boutique). */
    detailedItems(state) {
      const shop = useShopStore()

      return state.items
        .map((item) => {
          if (item.type === 'bundle') {
            const bundle = shop.bundles.find((b) => b.id === item.id)
            if (!bundle) return null

            // Représentation « pseudo-produit » du lot pour l'affichage
            return {
              ...item,
              key: `bundle-${item.id}`,
              product: {
                id: `bundle-${bundle.id}`,
                bundle_id: bundle.id,
                name_fr: bundle.name_fr,
                name_ar: bundle.name_ar,
                price: bundle.price,
                image: bundle.image,
                isBundle: true,
                contents: bundle.items,
                regular_total: bundle.regular_total,
                savings: bundle.savings,
              },
            }
          }

          const product = state.catalog[item.id] || null

          return product ? { ...item, key: `product-${item.id}`, product } : null
        })
        .filter(Boolean)
    },

    /** Total réel : promos produits + prix des lots. */
    total() {
      return this.detailedItems.reduce((sum, item) => {
        const unit = item.product.isBundle
          ? item.product.price
          : unitPriceFor(item.product, item.qty)

        return sum + unit * item.qty
      }, 0)
    },

    /** Total sans aucune remise (pour afficher l'économie réalisée). */
    regularTotal() {
      return this.detailedItems.reduce((sum, item) => {
        const unit = item.product.isBundle
          ? item.product.regular_total
          : item.product.price

        return sum + unit * item.qty
      }, 0)
    },

    /** Vrai si le panier contient au moins une remise (promo ou lot). */
    hasDiscounts() {
      return this.regularTotal > this.total
    },

    /**
     * Recommandations : jusqu'à 4 produits des catégories présentes
     * dans le panier (hors lots), non encore ajoutés.
     */
    recommendations() {
      const shop = useShopStore()
      const pool = [...Object.values(this.catalog), ...shop.products]
      const seen = new Set()
      const products = pool.filter((p) => (seen.has(p.id) ? false : (seen.add(p.id), true)))

      const inCart = new Set(
        this.items.filter((item) => item.type === 'product').map((item) => item.id)
      )
      const categories = new Set(
        this.detailedItems
          .filter((item) => !item.product.isBundle)
          .map((item) => item.product.category?.slug)
          .filter(Boolean)
      )

      return products
        .filter(
          (product) => categories.has(product.category?.slug) && !inCart.has(product.id)
        )
        .slice(0, 4)
    },
  },

  actions: {
    persist() {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.items))
    },

    /**
     * Hydrate les produits manquants du panier depuis l'API
     * (les lots sont résolus via le store boutique).
     */
    async hydrate() {
      const missing = this.missingProductIds
      if (missing.length === 0) return

      try {
        const products = await api.productsByIds(missing)
        products.forEach((product) => {
          this.catalog[product.id] = product
        })
      } catch {
        /* réseau indisponible : les lignes non hydratées sont ignorées */
      }
    },

    add(productId, quantity = 1) {
      this.addItem('product', productId, quantity)
    },

    addBundle(bundleId, quantity = 1) {
      this.addItem('bundle', bundleId, quantity)
    },

    addItem(type, id, quantity = 1) {
      const existing = this.items.find((item) => item.type === type && item.id === id)
      if (existing) {
        existing.qty = Math.min(existing.qty + quantity, 99)
      } else {
        this.items.push({ id, qty: quantity, type })
      }
      this.persist()

      if (type === 'product') {
        this.hydrate()
      }
    },

    remove(type, id) {
      this.items = this.items.filter((item) => !(item.type === type && item.id === id))
      this.persist()
    },

    changeQty(type, id, delta) {
      const item = this.items.find((line) => line.type === type && line.id === id)
      if (!item) return

      item.qty += delta

      if (item.qty <= 0) {
        this.remove(type, id)
        return
      }
      this.persist()
    },

    clear() {
      this.items = []
      this.persist()
    },

    /** Payload pour POST /api/orders (produits + lots). */
    toOrderPayload() {
      return {
        items: this.items.map((item) =>
          item.type === 'bundle'
            ? { bundle_id: item.id, quantity: item.qty }
            : { product_id: item.id, quantity: item.qty }
        ),
      }
    },
  },
})
