"""Pipeline de normalisation multilingue — utilise le moteur darija (engine.py).

Remplace l'ancienne version basique.
Registres couverts : français, arabizi, darija arabe, arabe standard.
"""
from __future__ import annotations

import re
import unicodedata

# Import du moteur darija (stdlib pure, pas de dépendances externes)
from .darija.engine import norm as _darija_norm, to_arabic, to_arabizi, has_arabic


# ---------------------------------------------------------------------------
#  Arabizi étendu : vocabulaire darija courant mappé à sa forme normalisée
# ---------------------------------------------------------------------------
_ARABIZI_VOCAB: dict[str, str] = {
    # Horaires / fermeture
    "msakker": "مسكر", "msaker": "مسكر", "sakker": "سكر",
    "mftu7": "مفتوح", "mftuh": "مفتوح", "meftou7": "مفتوح",
    "sa3at": "ساعات", "saa3at": "ساعات", "wa9t": "وقت",
    "yefta7": "يفتح", "ysakker": "يسكر",
    # Disponibilité
    "kayen": "كاين", "kayna": "كاينة", "makaynch": "ماكاينش",
    "wach kayen": "واش كاين", "wach kayna": "واش كاينة",
    "3andkom": "عندكم", "3andi": "عندي", "3andak": "عندك",
    "wach 3andkom": "واش عندكم",
    # Prix
    "bchhal": "بشحال", "chhal": "شحال", "ch7al": "شحال",
    "bchhal yswa": "بشحال يسوى", "soumt": "سومة", "taman": "ثمن",
    # Commande / achat
    "bghit": "بغيت", "nhawas": "نحوس", "nahwas": "نحوس",
    "nchri": "نشري", "chri": "شري", "bghit nchri": "بغيت نشري",
    # Livraison
    "twassal": "توصّل", "twassalt": "توصلت", "livraison": "livraison",
    "bchhal twassal": "بشحال توصّل", "wach kayen livraison": "واش كاين ليفريزون",
    # Paiement
    "kifach nkhaless": "كيفاش نخلص", "khaless": "خلص",
    "baridi": "بريدي", "baridimob": "بريدي موب", "ccp": "ccp",
    # Adresse / localisation
    "win rakom": "وين راكم", "win nlaqa": "وين نلقى", "adresse": "عنوان",
    "boudouaou": "بودواو",
    # Salutations
    "salam": "سلام", "wach": "واش", "wesh": "واش",
    "ana": "أنا", "nta": "نتا", "ntia": "نتيا",
    # Retour
    "rjeâ": "رجع", "rja3": "رجع",
}


def normalize(text: str) -> str:
    """Normalise un message client : unicode, arabizi → arabe, nettoyage.

    Retourne la forme canonique utilisée pour la recherche NLP.
    Préserve l'arabe natif, convertit l'arabizi.
    """
    # Utilise la normalisation du moteur darija (NFKC + tashkeel + ortho arabe)
    return _darija_norm(text)


def normalize_for_search(text: str) -> str:
    """Version étendue : applique aussi la substitution du vocabulaire arabizi."""
    t = text.lower().strip()
    # Substitution vocabulaire arabizi connu
    for lat, ar in _ARABIZI_VOCAB.items():
        if lat in t:
            t = t.replace(lat, ar)
    return _darija_norm(t)


def detect_lang(text: str) -> str:
    """Détecte si le texte est principalement en arabe/darija (ar) ou en français (fr)."""
    arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    ratio = arabic_chars / max(len(text.strip()), 1)
    if ratio > 0.2:
        return "ar"
    # Arabizi : mots-clés courants
    arabizi_kw = {"bghit", "kayen", "3andkom", "wach", "chhal", "bchhal",
                  "nchri", "salam", "twassal", "msakker", "mftu7", "sa3at"}
    words = set(text.lower().split())
    if words & arabizi_kw:
        return "ar"
    return "fr"
