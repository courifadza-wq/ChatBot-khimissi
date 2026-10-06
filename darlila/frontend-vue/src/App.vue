<script setup>
/**
 * Coquille de l'application : le routeur choisit entre
 *  - la boutique publique (HomeView)
 *  - l'espace d'administration (/admin…)
 */
import { RouterView } from 'vue-router'
</script>

<template>
  <RouterView />
</template>
