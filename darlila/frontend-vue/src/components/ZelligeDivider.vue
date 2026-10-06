<script setup>
defineProps({
  /** 'light' (motifs argile) ou 'dark' (motifs or). */
  theme: { type: String, default: 'light' },
})
</script>

<template>
  <div class="zellige-divider" :class="theme" aria-hidden="true"></div>
</template>
