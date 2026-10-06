import { defineStore } from 'pinia'
import { api } from '../api/client'

/**
 * Store « boutique » : catalogue paginé côté serveur (conçu pour 1000+
 * produits), catégories, avis, galerie et réglages.
 *
 * La recherche et le filtre par catégorie sont exécutés par l'API :
 * le navigateur ne charge que la page courante (24 produits) et
 * « Charger plus » accumule les pages suivantes.
 */
export const useShopStore = defineStore('shop', {
  state: () => ({
    products: [], // produits de la page courante (ou accumulés via « Charger plus »)
    pagination: null, // { total, current_page, last_page, per_page } ou null

    categories: [],
    reviews: [],
    gallery: [],
    bundles: [], // lots actifs (avec composition et économies)
    settings: {},

    loading: false,
    loadingMore: false,
    loaded: false,
    error: null,
    /** true quand l'API répond 503 (mode maintenance) → page d'attente */
    maintenance: false,

    filters: {
      category: 'all', // slug de catégorie principale ou 'all'
      subcategory: 'all', // slug de sous-catégorie ou 'all'
      search: '',
    },
  }),

  getters: {
    /** Produits affichés (filtrage serveur — plus de filtrage client). */
    filteredProducts(state) {
      return state.products
    },

    /**
     * Catégories PRINCIPALES uniquement (celles des puces du haut),
     * triées par ordre d'affichage.
     */
    mainCategories(state) {
      const cats = Array.isArray(state.categories) ? state.categories : []
      return cats
        .filter((c) => !c.parent_id)
        .sort((a, b) => (a.position ?? 0) - (b.position ?? 0) || a.id - b.id)
    },

    /** Catégorie principale actuellement sélectionnée (ou null). */
    activeMain(state) {
      const cats = Array.isArray(state.categories) ? state.categories : []
      return state.filters.category === 'all'
        ? null
        : cats.find((c) => c.slug === state.filters.category && !c.parent_id) || null
    },

    /** Sous-catégories de la catégorie principale active (puces secondaires). */
    activeChildren(state) {
      const cats = Array.isArray(state.categories) ? state.categories : []
      const main = cats.find((c) => c.slug === state.filters.category && !c.parent_id)
      return main
        ? cats
            .filter((c) => c.parent_id === main.id)
            .sort((a, b) => (a.position ?? 0) - (b.position ?? 0) || a.id - b.id)
        : []
    },

    /**
     * Nombre de produits affiché sur une puce : pour une catégorie
     * principale, on additionne ses produits directs et ceux de ses
     * sous-catégories (le filtre serveur les inclut aussi).
     */
    categoryCount(state) {
      return (category) => {
        if (!category) return 0
        let total = category.products_count ?? 0
        const cats = Array.isArray(state.categories) ? state.categories : []
        if (!category.parent_id) {
          for (const child of cats) {
            if (child.parent_id === category.id) total += child.products_count ?? 0
          }
        }
        return total
      }
    },

    /** Nombre total de produits correspondant aux filtres (toutes pages). */
    totalProducts(state) {
      return state.pagination?.total ?? state.products.length
    },

    /** Vrai s'il reste des pages à charger. */
    hasMorePages(state) {
      return state.pagination ? state.pagination.current_page < state.pagination.last_page : false
    },

    whatsappNumber(state) {
      return state.settings.whatsapp_number || '213554698746'
    },

    mapsEmbedUrl(state) {
      const query = state.settings.maps_query || 'Alger Centre, Alger, Algérie'
      return `https://www.google.com/maps?q=${encodeURIComponent(query)}&output=embed`
    },
  },

  actions: {
    /**
     * Chargement initial : réglages, catégories, avis, galerie +
     * première page de produits.
     */
    async fetchAll() {
      if (this.loading) return
      this.loading = true
      this.error = null

      try {
        const [settings, categories, reviews, gallery, bundles, products] = await Promise.all([
          api.settings(),
          api.categories(),
          api.reviews(),
          api.gallery(),
          api.bundles(),
          this.fetchProducts({ quiet: true }),
        ])

        this.settings = settings || {}
        this.categories = categories || []
        this.reviews = reviews || []
        this.gallery = gallery || []
        this.bundles = bundles || []
        this.loaded = true
        this.maintenance = false
        void products
      } catch (error) {
        if (error?.status === 503) {
          this.maintenance = true
          this.error = null
        } else {
          this.error = error
        }
      } finally {
        this.loading = false
      }
    },

    /**
     * Charge une page de produits depuis l'API (filtres + recherche serveur).
     * append: true → ajoute à la liste (bouton « Charger plus »).
     */
    async fetchProducts({ append = false, quiet = false } = {}) {
      if (append && this.loadingMore) return
      if (append) this.loadingMore = true

      const page = append ? (this.pagination?.current_page ?? 0) + 1 : 1

      // Sous-catégorie sélectionnée → filtre précis ; sinon catégorie
      // principale (l'API inclut automatiquement ses sous-catégories).
      let category = ''
      if (this.filters.subcategory !== 'all') {
        category = this.filters.subcategory
      } else if (this.filters.category !== 'all') {
        category = this.filters.category
      }

      try {
        const { items, meta } = await api.products({
          category,
          search: this.filters.search,
          page,
          per_page: 24,
        })

        this.products = append ? [...this.products, ...items] : items
        this.pagination = meta
        if (!quiet) this.maintenance = false
        return items
      } catch (error) {
        if (error?.status === 503) {
          this.maintenance = true
          this.error = null
        } else if (!quiet) {
          this.error = error
        }
        throw error
      } finally {
        this.loadingMore = false
      }
    },

    /** Bouton « Charger plus » : page suivante. */
    async loadMore() {
      if (!this.hasMorePages) return
      try {
        await this.fetchProducts({ append: true })
      } catch {
        /* erreur déjà exposée via le store */
      }
    },

    /** Sélection d'une catégorie principale (réinitialise la sous-catégorie). */
    setCategory(slug) {
      this.filters.category = slug
      this.filters.subcategory = 'all'
      this.fetchProducts().catch(() => {})
    },

    /** Sélection d'une sous-catégorie de la catégorie principale active. */
    setSubcategory(slug) {
      this.filters.subcategory = slug
      this.fetchProducts().catch(() => {})
    },

    setSearch(term) {
      this.filters.search = term
      this.fetchProducts().catch(() => {})
    },
  },
})
