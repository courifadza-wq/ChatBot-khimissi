import { computed, reactive } from 'vue'
import { fr } from './fr'
import { ar } from './ar'

/**
 * Mini système i18n maison (léger, sans dépendance) :
 * - locale réactive partagée par toute l'application
 * - bascule document.documentElement.lang / .dir (RTL pour l'arabe)
 * - `pick()` sélectionne le champ localisé d'un objet venu de l'API
 *   (ex. pick(product, 'name') -> product.name_ar ou product.name_fr)
 */
const state = reactive({
  locale: localStorage.getItem('darlila_lang') || 'fr',
})

function applyDocument(locale) {
  document.documentElement.lang = locale
  document.documentElement.dir = locale === 'ar' ? 'rtl' : 'ltr'
}

export function initLocale() {
  applyDocument(state.locale)
}

export function useI18n() {
  const locale = computed(() => state.locale)
  const dir = computed(() => (state.locale === 'ar' ? 'rtl' : 'ltr'))
  const isRtl = computed(() => state.locale === 'ar')

  const messages = computed(() => (state.locale === 'ar' ? ar : fr))

  const t = (key, params = {}) => {
    let text = messages.value[key] ?? fr[key] ?? key
    Object.entries(params).forEach(([name, value]) => {
      text = text.split(`{${name}}`).join(String(value))
    })
    return text
  }

  const pick = (obj, field) => {
    if (!obj) return ''
    return obj[`${field}_${state.locale}`] ?? obj[`${field}_fr`] ?? ''
  }

  const setLocale = (locale) => {
    if (locale !== 'fr' && locale !== 'ar') return
    state.locale = locale
    localStorage.setItem('darlila_lang', locale)
    applyDocument(locale)
  }

  return { locale, dir, isRtl, t, pick, setLocale }
}

/**
 * Formate un prix en dinars : « 8 500 DA » (fr) / « ٨٬٥٠٠ دج » (ar).
 */
export function formatPrice(value, locale = state.locale) {
  const formatted = Number(value).toLocaleString(locale === 'ar' ? 'ar-DZ' : 'fr-DZ')
  return locale === 'ar' ? `${formatted} دج` : `${formatted} DA`
}
