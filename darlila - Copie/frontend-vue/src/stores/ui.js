import { defineStore } from 'pinia'
import { useShopStore } from './shop'

/**
 * Store « interface » : état des surcouches (modale produit, panier,
 * visionneuse galerie, menu mobile).
 *
 * La modale produit référence l'objet produit directement (il peut venir
 * de la liste chargée OU d'un lien direct /produit/{slug}).
 */
export const useUiStore = defineStore('ui', {
  state: () => ({
    activeProduct: null,
    cartOpen: false,
    lightboxIndex: null,
    burgerOpen: false,
  }),

  actions: {
    openProduct(product) {
      this.activeProduct = product
    },

    closeProduct() {
      this.activeProduct = null
    },

    openCart() {
      this.cartOpen = true
    },

    closeCart() {
      this.cartOpen = false
    },

    openLightbox(index) {
      this.lightboxIndex = index
    },

    closeLightbox() {
      this.lightboxIndex = null
    },

    closeAll() {
      this.activeProduct = null
      this.cartOpen = false
      this.lightboxIndex = null
      this.burgerOpen = false
    },
  },
})
