# ============================================================
#  Catalogue produits — Laravel API (temps réel) + SQLite fallback
# ============================================================
from functools import lru_cache

import yaml

from .config import settings
from .database import search_products, count_products, get_categories, fuzzy_keyword
from .laravel_api import (
    search_products_laravel,
    get_categories_laravel,
    count_products_laravel,
)


# ── Données statiques depuis products.yaml ───────────────────────────────────

@lru_cache()
def load_catalog() -> dict:
    with open(settings.PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache()
def get_store() -> dict:
    return load_catalog()["store"]


@lru_cache()
def get_delivery() -> dict:
    return load_catalog()["delivery"]


@lru_cache()
def get_payment() -> list[str]:
    return load_catalog()["payment"]


# ── Recherche intelligente dans SQLite ───────────────────────────────────────

def find_product(keyword: str) -> dict | None:
    """
    Retourne le premier produit correspondant au mot-clé.
    Stratégie : Laravel API d'abord → SQLite local en fallback.
    """
    # 1. Essai via Laravel (produits toujours à jour)
    results = search_products_laravel(keyword=keyword, limit=1)
    if results:
        return results[0]

    # 2. Fallback SQLite local (mode strict puis souple)
    results = search_products(keyword=keyword, limit=1, strict=True)
    if not results:
        results = search_products(keyword=keyword, limit=1, strict=False)
    return results[0] if results else None


def format_catalog() -> str:
    """Affiche les catégories disponibles + nombre de produits (depuis Laravel)."""
    store = get_store()

    # Catégories et total depuis Laravel en priorité
    categories = get_categories_laravel() or get_categories()
    total = count_products_laravel() or count_products()

    lines = [f"🛍️ *{store['name']}*", ""]

    if categories:
        lines.append("📂 *Catégories disponibles :*")
        for cat in categories:
            lines.append(f"• {cat}")
        lines.append("")
        lines.append("💬 Précisez votre recherche, par exemple :")
        lines.append("  _\"robe 6 mois\"_, _\"moins de 2000 DZD\"_, _\"chaussures enfant\"_")
    else:
        lines.append("Catalogue en cours de chargement... Réessayez dans un instant.")

    return "\n".join(lines)


def format_search_results(results: list[dict], query: str = "", corrected: str = "") -> str:
    """Formate une liste de produits pour affichage WhatsApp."""
    if not results:
        return (
            f"😕 Aucun produit trouvé pour *\"{query}\"*.\n\n"
            "Essayez avec d'autres mots-clés ou demandez le *catalogue* pour voir les catégories."
        )

    # En-tête : signaler si on a corrigé la recherche
    if corrected:
        header = (
            f"🔍 *Résultats pour \"{corrected.capitalize()}\"*\n"
            f"_(recherche approchée de \"{query}\")_\n"
        )
    else:
        header = f"🔍 *Résultats{f' pour \"{query}\"' if query else ''} :*\n"

    lines = [header]

    for p in results:
        name = p["designation"]
        if len(name) > 45:
            name = name[:42] + "..."
        age = f" ({p['age_range']})" if p.get("age_range") else ""
        lines.append(f"• *{name}*{age}")
        lines.append(f"  💰 {int(p['price'])} DZD  |  Réf: {p['reference']}")

    lines.append("")
    lines.append("🛒 Pour commander, dites *je veux commander* en précisant la référence.")
    return "\n".join(lines)


def smart_search_with_products(keyword: str, max_price: float = 0, min_price: float = 0,
                               age_hint: str = "", category: str = "", limit: int = 5) -> tuple[str, list[dict]]:
    """
    Recherche intelligente : Laravel API → SQLite fallback → fuzzy SQLite.
    Retourne (message_texte, liste_produits).
    """
    # ── 1. Laravel API (produits en temps réel) ──────────────────────────────
    results = search_products_laravel(
        keyword=keyword, category=category,
        max_price=max_price, min_price=min_price, limit=limit,
    )
    if results:
        return format_search_results(results, query=keyword), results

    # ── 2. SQLite local (fallback si Laravel indisponible) ───────────────────
    results = search_products(
        keyword=keyword, max_price=max_price, min_price=min_price,
        age_hint=age_hint, category=category, limit=limit,
    )
    if results:
        return format_search_results(results, query=keyword), results

    # ── 3. Fuzzy search sur SQLite (correction orthographique) ───────────────
    if keyword:
        corrected = fuzzy_keyword(keyword)
        if corrected:
            results = search_products(
                keyword=corrected, max_price=max_price, min_price=min_price,
                age_hint=age_hint, category=category, limit=limit,
            )
            if results:
                return format_search_results(results, query=keyword, corrected=corrected), results

    return format_search_results([], query=keyword), []

def smart_search(keyword: str, max_price: float = 0, min_price: float = 0,
                 age_hint: str = "", category: str = "", limit: int = 5) -> str:
    """Version originale retournant uniquement le texte (pour compatibilité)."""
    return smart_search_with_products(keyword, max_price, min_price, age_hint, category, limit)[0]


def parse_search_query(message: str) -> dict:
    """
    Extrait les critères de recherche depuis le message du client.
    Retourne un dict avec keyword, max_price, min_price, age_hint.
    """
    import re
    msg = message.lower().strip()
    params: dict = {"keyword": "", "max_price": 0, "min_price": 0, "age_hint": ""}

    # Prix maximum : "moins de 2000", "max 1500", "pas plus de 3000"
    m = re.search(r"(?:moins de|max|maximum|pas plus de)\s*(\d+)", msg)
    if m:
        params["max_price"] = float(m.group(1))

    # Prix minimum : "plus de 1000", "min 500", "au moins 2000"
    m = re.search(r"(?:plus de|min|minimum|au moins)\s*(\d+)", msg)
    if m:
        params["min_price"] = float(m.group(1))

    # Tranche d'âge : "6 mois", "2 ans", "bébé", "nouveau-né"
    m = re.search(r"(\d+)\s*(?:mois|ans?)", msg)
    if m:
        params["age_hint"] = m.group(0)

    if re.search(r"bébé|bebe|nourrisson", msg):
        params["age_hint"] = params["age_hint"] or "bébé"

    if re.search(r"nouveau[- ]?né|newborn", msg):
        params["age_hint"] = "0"

    # Mot-clé : retirer les mots de prix/âge pour garder le nom du produit
    keyword = re.sub(r"(?:moins de|plus de|max|min|au moins|pas plus de)\s*\d+\s*(?:dzd|da)?", "", msg)
    keyword = re.sub(r"\d+\s*(?:mois|ans?)", "", keyword)
    keyword = re.sub(r"\b(?:bébé|bebe|nouveau[- ]?né|enfant|fille|garçon)\b", "", keyword)
    keyword = re.sub(r"\b(?:cherche|veux|voudrais|montres?[- ]?moi|je|un|une|des|le|la|les|du|de)\b", "", keyword)
    keyword = re.sub(r"\s+", " ", keyword).strip()
    # Normaliser les pluriels français : ballerines → ballerine, sandales → sandale
    keyword = re.sub(r"\b(\w{4,})es\b", r"\1e", keyword)   # ballerines → ballerine
    keyword = re.sub(r"\b(\w{4,})s\b", r"\1", keyword)     # pantalons → pantalon
    params["keyword"] = keyword

    return params


# Alias pour compatibilité avec responses.py
def get_products() -> list[dict]:
    """Retourne quelques produits depuis la DB (pour compatibilité)."""
    return search_products(limit=5)
