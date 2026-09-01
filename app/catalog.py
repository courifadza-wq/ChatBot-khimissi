# ============================================================
#  Chargement du catalogue produits (products.yaml)
# ============================================================
from functools import lru_cache

import yaml

from .config import settings


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
def get_products() -> list[dict]:
    return load_catalog()["products"]


@lru_cache()
def get_payment() -> list[str]:
    return load_catalog()["payment"]


def find_product(keyword: str) -> dict | None:
    """Retourne le produit le plus proche d'un mot-clé (fr + arabe + derja)."""
    kw = keyword.lower().strip()
    if not kw:
        return None
    # 1) correspondance exacte / dans le nom ou la catégorie
    for p in get_products():
        if kw in p["name"].lower() or kw in p["category"].lower():
            return p
    # 2) correspondance via les alias (fr / arabe / derja)
    for p in get_products():
        for a in p.get("aliases", []):
            if kw == a.lower() or a.lower() in kw or kw in a.lower():
                return p
    # 3) mots contenus l'un dans l'autre (nom + alias)
    for p in get_products():
        name = p["name"].lower()
        tokens = kw.split()
        if any(w in name for w in tokens) or any(w in kw for w in name.split()):
            return p
        for a in p.get("aliases", []):
            if any(w in a.lower() for w in tokens) or any(w in kw for w in a.lower().split()):
                return p
    return None


def format_catalog() -> str:
    """Liste lisible des produits pour envoyer sur WhatsApp."""
    lines = [f"🛍️ *{get_store()['name']}* — Catalogue :", ""]
    for p in get_products():
        lines.append(f"• *{p['name']}* — {p['price']} DZD")
        lines.append(f"  {p['description']}")
    lines.append("")
    lines.append("Pour commander, dis-moi *je veux commander* 📦")
    return "\n".join(lines)
