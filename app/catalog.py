# ============================================================
#  Catalogue produits — lecture YAML (config store) + recherche SQLite
# ============================================================
from functools import lru_cache

import yaml

from .config import settings
from .database import search_products, count_products, get_categories


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
    """Retourne le premier produit correspondant au mot-clé (mode strict AND)."""
    # Mode strict : tous les mots doivent matcher → évite les faux positifs
    results = search_products(keyword=keyword, limit=1, strict=True)
    if not results:
        # Fallback : mode souple (OR) si strict ne trouve rien
        results = search_products(keyword=keyword, limit=1, strict=False)
    return results[0] if results else None


def format_catalog() -> str:
    """Affiche les catégories disponibles + nombre de produits."""
    store = get_store()
    categories = get_categories()
    total = count_products()

    lines = [f"🛍️ *{store['name']}* — Catalogue ({total} articles en stock)", ""]

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


def format_search_results(results: list[dict], query: str = "") -> str:
    """Formate une liste de produits pour affichage WhatsApp."""
    if not results:
        return (
            "😕 Aucun produit trouvé pour cette recherche.\n\n"
            "Essayez avec d'autres mots-clés ou demandez le *catalogue* pour voir les catégories."
        )

    header = f"🔍 *Résultats{f' pour \"{query}\"' if query else ''} :*\n"
    lines = [header]

    for p in results:
        name = p["designation"]
        # Tronquer si trop long
        if len(name) > 45:
            name = name[:42] + "..."
        age = f" ({p['age_range']})" if p.get("age_range") else ""
        lines.append(f"• *{name}*{age}")
        lines.append(f"  💰 {int(p['price'])} DZD  |  Réf: {p['reference']}")

    lines.append("")
    lines.append("🛒 Pour commander, dites *je veux commander* en précisant la référence.")
    return "\n".join(lines)


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
    keyword = re.sub(r"(?:bébé|bebe|nouveau[- ]?né|enfant|fille|garçon)", "", keyword)
    keyword = re.sub(r"(?:cherche|veux|voudrais|montres?[- ]?moi|je|un|une|des|le|la|les|du|de)", "", keyword)
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
