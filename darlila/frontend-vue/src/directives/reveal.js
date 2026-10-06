/**
 * Directive v-reveal : animation d'apparition au scroll
 * (portage de l'IntersectionObserver du site d'origine).
 *
 *   <div v-reveal>            → .reveal
 *   <div v-reveal="'stagger'">→ .reveal-stagger (enfants décalés)
 */
export const reveal = {
  mounted(el, binding) {
    const stagger = binding.value === 'stagger'
    el.classList.add(stagger ? 'reveal-stagger' : 'reveal')

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            el.classList.add('in')
            observer.unobserve(el)
          }
        })
      },
      { threshold: 0.15, rootMargin: '0px 0px -60px 0px' }
    )

    observer.observe(el)
    el._revealObserver = observer
  },

  unmounted(el) {
    el._revealObserver?.disconnect()
  },
}
