/**
 * Client HTTP minimaliste (fetch, sans dépendance) pour l'API Laravel.
 *
 * - Toutes les réponses Laravel sont au format { "data": ... } (Resources),
 *   ce client « déplie » automatiquement le champ data.
 * - Gère le token Sanctum de l'espace admin (Authorization: Bearer …).
 * - En cas d'erreur HTTP, lève une Error enrichie de :
 *     error.status  : code HTTP
 *     error.errors  : erreurs de validation Laravel { champ: [messages] }
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
const TOKEN_KEY = 'darlila_admin_token'

let authToken = localStorage.getItem(TOKEN_KEY)

export function setAuthToken(token) {
  authToken = token || null
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export function getAuthToken() {
  return authToken
}

function toQuery(params = {}) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, value)
  })
  const query = search.toString()
  return query ? `?${query}` : ''
}

async function request(path, options = {}) {
  const headers = { Accept: 'application/json' }

  // Pour un FormData (téléversement d'image), le navigateur fixe lui-même
  // le Content-Type avec la frontière multipart.
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`
  }

  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, { headers, ...options })
  } catch {
    throw Object.assign(new Error('Network error: API injoignable'), { status: 0 })
  }

  const body = await response.json().catch(() => null)

  if (!response.ok) {
    const error = new Error(body?.message || `Erreur HTTP ${response.status}`)
    error.status = response.status
    error.errors = body?.errors ?? null
    error.maintenance = response.status === 503 && body?.maintenance !== false
    throw error
  }

  return body?.data ?? body
}

/**
 * Comme request(), mais conserve la pagination Laravel :
 * renvoie { items, meta: { total, current_page, last_page, per_page } }.
 * Si la réponse n'est pas paginée (meta absente), meta = null.
 */
async function requestPaginated(path, options = {}) {
  const headers = { Accept: 'application/json' }
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json'
  if (authToken) headers.Authorization = `Bearer ${authToken}`

  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, { headers, ...options })
  } catch {
    throw Object.assign(new Error('Network error: API injoignable'), { status: 0 })
  }

  const body = await response.json().catch(() => null)

  if (!response.ok) {
    const error = new Error(body?.message || `Erreur HTTP ${response.status}`)
    error.status = response.status
    error.errors = body?.errors ?? null
    error.maintenance = response.status === 503 && body?.maintenance !== false
    throw error
  }

  return {
    items: body?.data ?? [],
    meta: body?.meta ?? null,
  }
}

export const api = {
  /* ---------- Public ---------- */
  settings: () => request('/settings'),
  categories: () => request('/categories'),
  /** Produits paginés côté serveur → { items, meta } (gros catalogues). */
  products: (params = {}) => requestPaginated(`/products${toQuery(params)}`),
  /** Sélection de produits par identifiants (hydratation du panier). */
  productsByIds: (ids) => request(`/products${toQuery({ ids: ids.join(',') })}`),
  product: (slug) => request(`/products/${encodeURIComponent(slug)}`),
  reviews: () => request('/reviews'),
  gallery: () => request('/gallery'),
  /** Lots actifs (avec composition, prix cumulé et économies). */
  bundles: () => request('/bundles'),
  createOrder: (payload) =>
    request('/orders', { method: 'POST', body: JSON.stringify(payload) }),

  /* ---------- Authentification (Sanctum) ---------- */
  login: (email, password) =>
    request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  me: () => request('/auth/me'),
  logout: () => request('/auth/logout', { method: 'POST' }),

  /* ---------- Administration ---------- */
  adminConfig: () => request('/admin/config'),
  adminSettings: () => request('/admin/settings'),
  adminUpdateSettings: (payload) =>
    request('/admin/settings', { method: 'PUT', body: JSON.stringify(payload) }),

  adminChangePassword: (currentPassword, newPassword, confirmation) =>
    request('/admin/change-password', {
      method: 'POST',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
        new_password_confirmation: confirmation,
      }),
    }),
  adminCategories: () => request('/admin/categories'),
  adminCreateCategory: (payload) =>
    request('/admin/categories', { method: 'POST', body: JSON.stringify(payload) }),
  adminUpdateCategory: (id, payload) =>
    request(`/admin/categories/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  adminDeleteCategory: (id) => request(`/admin/categories/${id}`, { method: 'DELETE' }),
  adminBundles: (params = {}) => request(`/admin/bundles${toQuery(params)}`),
  adminCreateBundle: (payload) =>
    request('/admin/bundles', { method: 'POST', body: JSON.stringify(payload) }),
  adminUpdateBundle: (id, payload) =>
    request(`/admin/bundles/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  adminDeleteBundle: (id) => request(`/admin/bundles/${id}`, { method: 'DELETE' }),
  adminBulkDeleteBundles: (ids) =>
    request('/admin/bundles/bulk-delete', { method: 'POST', body: JSON.stringify({ ids }) }),
  adminProducts: (params = {}) => requestPaginated(`/admin/products${toQuery(params)}`),
  adminImportProducts: (formData) =>
    request('/admin/products/import', { method: 'POST', body: formData }),
  /** Télécharge le CSV du catalogue (avec le token) → texte CSV. */
  adminExportProducts: async () => {
    const response = await fetch(`${BASE_URL}/admin/products/export`, {
      headers: { Accept: 'text/csv', ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}) },
    })
    if (!response.ok) {
      throw Object.assign(new Error(`Erreur HTTP ${response.status}`), { status: response.status })
    }
    return response.text()
  },

  /** Télécharge le CSV des commandes (comptabilité) → texte CSV. */
  adminExportOrders: async (params = {}) => {
    const response = await fetch(`${BASE_URL}/admin/orders/export${toQuery(params)}`, {
      headers: { Accept: 'text/csv', ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}) },
    })
    if (!response.ok) {
      throw Object.assign(new Error(`Erreur HTTP ${response.status}`), { status: response.status })
    }
    return response.text()
  },
  adminCreateProduct: (payload) =>
    payload instanceof FormData
      ? request('/admin/products', { method: 'POST', body: payload })
      : request('/admin/products', { method: 'POST', body: JSON.stringify(payload) }),
  adminUpdateProduct: (id, payload) =>
    payload instanceof FormData
      ? request(`/admin/products/${id}`, { method: 'POST', body: withMethodSpoof(payload, 'PUT') })
      : request(`/admin/products/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  adminDeleteProduct: (id) => request(`/admin/products/${id}`, { method: 'DELETE' }),
  adminBulkDeleteProducts: (ids) =>
    request('/admin/products/bulk-delete', { method: 'POST', body: JSON.stringify({ ids }) }),

  adminOrders: (params = {}) => request(`/admin/orders${toQuery(params)}`),
  adminUpdateOrderStatus: (id, status) =>
    request(`/admin/orders/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
}

/**
 * Laravel ne lit pas PUT sur un corps multipart : on utilise la
 * substitution de méthode HTML (_method=PUT) sur un POST.
 */
function withMethodSpoof(formData, method) {
  formData.append('_method', method)
  return formData
}
