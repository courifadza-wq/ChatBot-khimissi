"""Paquet darija — moteur de génération NLP pour le bot Planète Kids.

app/darija/
    engine.py    moteur  : 351 gabarits, translittération, variantes  (sans état, stdlib pure)
    lexicon.py   mémoire : stockage, injection dans le modèle NLP    (data/lexicon.yaml)
    api.py       routes  : /lexique + /api/lexicon/*
    page.html    interface web admin (autonome, sans dépendance externe)

Usage :
    from .darija import generate, norm, to_arabic, to_arabizi
    from .darija.api import router
"""
from __future__ import annotations

from .engine import (                                          # noqa: F401
    AR2LAT, AR_PREFIXES, C, KINDS, LAT2AR_DIGRAPHS, LEVELS, POLITE_SUFFIX,
    PREFIX, REGISTERS, SUFFIX, SWAPS_BIDIR, SWAPS_ONEWAY, TYPO_NEIGHBORS,
    arabizi_spellings, generate, generate_for_product, has_arabic, keyword_pools,
    keyword_variants, noisy, norm, preview, stats, to_arabic, to_arabizi,
)

__all__ = [
    "generate", "generate_for_product", "keyword_pools", "keyword_variants",
    "arabizi_spellings", "to_arabic", "to_arabizi", "norm", "has_arabic",
    "noisy", "preview", "stats",
    "C", "KINDS", "REGISTERS", "LEVELS", "PREFIX", "POLITE_SUFFIX", "SUFFIX",
    "AR2LAT", "AR_PREFIXES", "LAT2AR_DIGRAPHS", "SWAPS_BIDIR", "SWAPS_ONEWAY",
    "TYPO_NEIGHBORS", "lexicon", "engine",
]


def __getattr__(name):
    """Import paresseux : darija.lexicon / darija.api chargés seulement à la demande."""
    if name in ("lexicon", "api", "engine"):
        import importlib
        return importlib.import_module(f".{name}", __name__)
    raise AttributeError(name)
