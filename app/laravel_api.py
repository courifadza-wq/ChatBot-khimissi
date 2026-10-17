# ============================================================
#  laravel_api.py — Pont vers l'API Laravel (api.khemicishop.com)
#  Le bot appelle l'API en temps réel pour trouver les produits.
#  Si l'API est indisponible, il retombe sur le SQLite local.
# ============================================================
import logging
import os
from functools import lru_cache
from typing import Optional

import httpx

logger = logging.getLogger("laravel_api")

# URL de l'API Laravel — variable d'environnement ou valeur par défaut
LARAVEL_API_URL = os.getenv("LARAVEL_API_URL", "https://api.khemicishop.com/api")
# Timeout en secondes (court pour ne pas bloquer le bot)
API_TIMEOUT = float(os.getenv("LARAVEL_API_TIMEOUT", "4.0"))


def _normalize(text: str) -> str:
    """Supprime accents et met en majuscules pour comparaison."""
    import unicodedata
    return "".join(
        c for c in unicodedata.normalize("NFD", text.upper())
        if unicodedata.category(c) != "Mn"
    )


def search_products_laravel(
    keyword: str = "",
    category: str = "",
    max_price: float = 0,
    min_price: float = 0,
    limit: int = 5,
) -> list[dict]:
    """
    Cherche des produits via l'API Laravel en temps réel.
    Retourne une liste de dicts normalisés (même format que SQLite local).
    Retourne [] en cas d'erreur réseau ou timeout.
    """
    if not LARAVEL_API_URL:
        return []

    params: dict = {"limit": limit}
    if keyword:
        params["search"] = keyword
    if category:
        params["category"] = category
    if max_price > 0:
        params["max_price"] = max_price
    if min_price > 0:
        params["min_price"] = min_price

    try:
        headers = {"Accept": "application/json"}
        with httpx.Client(timeout=API_TIMEOUT, verify=False, follow_redirects=True) as client:
            resp = client.get(f"{LARAVEL_API_URL}/products", params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            # Laravel retourne {"data": [...], "meta": {...}} (paginé)
            items = data.get("data", data) if isinstance(data, dict) else data

            results = []
            for p in items[:limit]:
                # Ignorer les produits inactifs
                if not p.get("is_active", True):
                    continue
                results.append({
                    "id":             p.get("id", 0),
                    "designation":    p.get("name_fr") or p.get("name") or p.get("designation", ""),
                    "designation_ar": p.get("name_ar", ""),
                    "reference":      p.get("reference") or p.get("slug") or str(p.get("id", "")),
                    "stock":          1,   # actif dans Laravel = considéré en stock
                    "price":          float(p.get("price", 0)),
                    "category":       _get_category_name(p),
                    "age_range":      p.get("age_range", ""),
                    "image_url":      _get_first_image(p),
                    "source":         "laravel",
                })

            logger.info("Laravel API : %d produits trouvés pour '%s'", len(results), keyword)
            return results

    except httpx.TimeoutException:
        logger.warning("Laravel API timeout (%.1fs) pour keyword='%s'", API_TIMEOUT, keyword)
        return []
    except httpx.HTTPStatusError as e:
        logger.warning("Laravel API HTTP %s pour keyword='%s'", e.response.status_code, keyword)
        return []
    except Exception as e:
        logger.warning("Laravel API erreur : %s", e)
        return []


def get_categories_laravel() -> list[str]:
    """
    Récupère la liste des catégories depuis Laravel.
    Retourne [] en cas d'erreur.
    """
    try:
        headers = {"Accept": "application/json"}
        with httpx.Client(timeout=API_TIMEOUT, verify=False, follow_redirects=True) as client:
            resp = client.get(f"{LARAVEL_API_URL}/categories", headers=headers)
            resp.raise_for_status()
            data = resp.json()
            items = data if isinstance(data, list) else data.get("data", [])
            return [
                c.get("name_fr") or c.get("name") or c.get("slug", "")
                for c in items
                if c.get("name_fr") or c.get("name")
            ]
    except Exception as e:
        logger.warning("Laravel API categories erreur : %s", e)
        return []


def count_products_laravel() -> int:
    """Compte les produits actifs dans Laravel."""
    try:
        headers = {"Accept": "application/json"}
        with httpx.Client(timeout=API_TIMEOUT, verify=False, follow_redirects=True) as client:
            resp = client.get(f"{LARAVEL_API_URL}/products", params={"limit": 1}, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            # Cherche un champ total/count dans la réponse paginée
            if isinstance(data, dict):
                return (
                    data.get("total")
                    or data.get("count")
                    or data.get("meta", {}).get("total", 0)
                    or len(data.get("data", []))
                )
            return len(data) if isinstance(data, list) else 0
    except Exception:
        return 0



# ── Helpers internes ──────────────────────────────────────────────────────────

def _get_category_name(product: dict) -> str:
    """Extrait le nom de catégorie depuis un objet produit Laravel."""
    cat = product.get("category")
    if isinstance(cat, dict):
        return cat.get("name_fr") or cat.get("name") or cat.get("slug", "")
    if isinstance(cat, str):
        return cat
    # Essayer category_parent
    parent = product.get("category_parent")
    if isinstance(parent, dict):
        return parent.get("name_fr") or parent.get("name", "")
    return ""


def _get_first_image(product: dict) -> str:
    """Extrait la première URL d'image depuis un objet produit Laravel."""
    # Format tableau d'images
    images = product.get("images")
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, dict):
            return first.get("url") or first.get("path", "")
        if isinstance(first, str):
            return first

    # Format URL directe
    url = product.get("image_url") or product.get("image") or product.get("thumbnail", "")
    if isinstance(url, str) and url:
        # Peut contenir plusieurs URLs séparées par |
        return url.split("|")[0].strip()

    return ""
