<script setup>
import { onMounted, ref } from 'vue'
import { useShopStore } from '../stores/shop'
import { useI18n } from '../i18n'
import ProductCard from './ProductCard.vue'

const { t, pick } = useI18n()
const shop = useShopStore()

// Recherche : debounce 350 ms → une seule requête serveur à l'arrêt de la frappe
const searchInput = ref('')
let debounceTimer = null

onMounted(() => {
  searchInput.value = shop.filters.search
})

function onSearchInput() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    shop.setSearch(searchInput.value)
  }, 350)
}
</script>

<template>
  <section class="section services" id="boutique">
    <div class="container">
      <div class="section-head" v-reveal>
        <div class="eyebrow"><span class="line"></span><span>{{ t('serv_eyebrow') }}</span></div>
        <h2>{{ t('serv_title') }}</h2>
        <p class="lead">{{ t('serv_lead') }}</p>
      </div>

      <!-- Barre de filtres : puces de catégories + recherche serveur -->
      <div class="shop-toolbar" v-if="shop.loaded">
        <div class="filter-chips" role="group" aria-label="Catégories">
          <button
            class="chip"
            :class="{ active: shop.filters.category === 'all' }"
            type="button"
            @click="shop.setCategory('all')"
          >
            {{ t('filter_all') }}
          </button>
          <button
            v-for="category in shop.mainCategories"
            :key="category.slug"
            class="chip"
            :class="{ active: shop.filters.category === category.slug }"
            type="button"
            @click="shop.setCategory(category.slug)"
          >
            {{ pick(category, 'name') }}
          </button>
        </div>

        <div class="search-box">
          <input
            v-model="searchInput"
            type="search"
            :placeholder="t('search_placeholder')"
            aria-label="Recherche"
            @input="onSearchInput"
          >
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
        </div>
      </div>

      <!-- Sous-catégories de la catégorie principale active -->
      <div
        class="filter-subbar"
        v-if="shop.loaded && shop.activeMain && shop.activeChildren.length > 0"
        v-reveal
      >
        <span class="subbar-label">{{ pick(shop.activeMain, 'name') }}&nbsp;:</span>
        <div class="filter-chips" role="group" :aria-label="t('subcategory_aria')">
          <button
            class="chip chip-sub"
            :class="{ active: shop.filters.subcategory === 'all' }"
            type="button"
            @click="shop.setSubcategory('all')"
          >
            {{ t('filter_all') }}
          </button>
          <button
            v-for="sub in shop.activeChildren"
            :key="sub.slug"
            class="chip chip-sub"
            :class="{ active: shop.filters.subcategory === sub.slug }"
            type="button"
            @click="shop.setSubcategory(sub.slug)"
          >
            {{ pick(sub, 'name') }}
          </button>
        </div>
      </div>

      <!-- Compteur de résultats (toutes pages) -->
      <p class="shop-count" v-if="shop.loaded">
        {{ t('products_found', { count: shop.totalProducts.toLocaleString() }) }}
      </p>

      <!-- Chargement : squelettes -->
      <div class="services-grid" v-if="shop.loading" aria-busy="true">
        <div class="skel-card" v-for="i in 8" :key="i">
          <div class="skel-media skel"></div>
          <div class="skel-body">
            <div class="skel-line skel"></div>
            <div class="skel-line skel short"></div>
          </div>
        </div>
      </div>

      <!-- Erreur réseau -->
      <div class="shop-error" v-else-if="shop.error">
        <p>{{ t('error_title') }}</p>
        <button class="btn btn-gold" type="button" @click="shop.fetchAll()">{{ t('error_retry') }}</button>
      </div>

      <!-- Aucun résultat -->
      <div class="shop-empty" v-else-if="shop.loaded && shop.products.length === 0">
        {{ t('search_no_results') }}
      </div>

      <!-- Grille produits -->
      <div class="services-grid" v-else v-reveal="'stagger'">
        <ProductCard v-for="product in shop.products" :key="product.id" :product="product" />
      </div>

      <!-- Charger plus (pagination serveur) -->
      <div class="shop-loadmore" v-if="shop.hasMorePages && !shop.loading">
        <button class="btn btn-outline shop-loadmore-btn" type="button" :disabled="shop.loadingMore" @click="shop.loadMore()">
          <span v-if="shop.loadingMore">{{ t('loading') }}</span>
          <span v-else>{{ t('load_more') }}</span>
        </button>
        <p class="shop-count-hint">
          {{ shop.products.length.toLocaleString() }} / {{ shop.totalProducts.toLocaleString() }}
        </p>
      </div>
    </div>
  </section>
</template>
