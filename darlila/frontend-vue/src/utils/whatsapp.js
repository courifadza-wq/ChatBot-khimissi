import { formatPrice } from '../i18n'

/**
 * Construit un lien wa.me pré-rempli.
 */
export function waLink(number, message) {
  return `https://wa.me/${number}?text=${encodeURIComponent(message)}`
}

/**
 * Message générique (boutons « Commander » hors panier).
 */
export function genericMessage(locale) {
  return locale === 'ar'
    ? 'مرحباً بلانيت كيدز، أريد المزيد من المعلومات حول منتجاتكم.'
    : "Bonjour Planet Kids, je souhaite avoir plus d'informations sur vos produits."
}

/**
 * Message pour la commande directe d'un seul article (modale produit).
 */
export function singleItemMessage(productName, unitPrice, quantity, locale) {
  const total = unitPrice * quantity

  if (locale === 'ar') {
    return `مرحباً، أريد طلب: ${productName} × ${quantity} — ${formatPrice(total, locale)}`
  }

  return `Bonjour, je souhaite commander : ${productName} × ${quantity} — ${formatPrice(total, locale)}`
}

/**
 * Message de repli pour le panier (utilisé uniquement si l'enregistrement
 * de la commande via l'API échoue ; le message officiel est construit
 * côté Laravel dans OrderController::buildWhatsAppMessage).
 */
export function cartMessage(items, total, locale) {
  if (items.length === 0) return genericMessage(locale)

  const lines = items
    .map((item) => {
      const lineTotal = item.product.price * item.qty
      return `- ${locale === 'ar' ? item.product.name_ar : item.product.name_fr} × ${item.qty} = ${formatPrice(lineTotal, locale)}`
    })
    .join('\n')

  const intro = locale === 'ar' ? 'مرحباً، أريد طلب:' : 'Bonjour, je souhaite commander :'
  const totalLabel = locale === 'ar' ? 'المجموع' : 'Total'

  return `${intro}\n${lines}\n${totalLabel}: ${formatPrice(total, locale)}`
}
