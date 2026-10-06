/**
 * Règles de prix partagées : promotions « achetez N → -X % »
 * et calculs de lots. Miroir exact de Product::unitPriceFor() côté Laravel.
 */

/** Le produit a-t-il une promotion quantité active ? */
export function hasPromo(product) {
  return Boolean(
    product
      && product.promo_quantity >= 2
      && product.promo_percent >= 1
      && product.promo_percent <= 99
  )
}

/** Prix unitaire réel pour une quantité donnée (promo appliquée au seuil). */
export function unitPriceFor(product, quantity = 1) {
  if (!hasPromo(product) || quantity < product.promo_quantity) {
    return product.price
  }

  return Math.round((product.price * (100 - product.promo_percent)) / 100)
}

/** Total d'une ligne (produit avec promo). */
export function lineTotalFor(product, quantity) {
  return unitPriceFor(product, quantity) * quantity
}
