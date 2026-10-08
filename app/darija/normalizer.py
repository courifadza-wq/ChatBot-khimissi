"""
Darija spelling normalizer.
Loads darija_variants.json at startup and provides normalize_darija()
which corrects common spelling variations BEFORE the NLP classifier runs.

Example: "bghit seroual azreq" → "bghit serwal azreq"
"""

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

_VARIANTS: dict[str, str] = {}

def _load():
    """Load variant->base mapping from JSON (runs once at import)."""
    global _VARIANTS
    json_path = Path(__file__).resolve().parent.parent.parent / "data" / "darija_variants.json"
    if not json_path.exists():
        log.warning("darija_variants.json not found at %s", json_path)
        return
    with open(json_path, "r", encoding="utf-8") as f:
        _VARIANTS = json.load(f)
    log.info("Darija normalizer loaded: %d variants", len(_VARIANTS))

_load()


def normalize_darija(text: str) -> str:
    """
    Normalize darija spelling variants in user input.
    Replaces each word with its canonical base form if found in the dictionary.
    
    - Does NOT change Arabic script words (only Latin/Arabizi)
    - Does NOT affect words already in canonical form
    - O(n) per word lookup (dict-based, very fast)
    """
    if not _VARIANTS or not text:
        return text
    
    words = text.split()
    result = []
    changed = False
    
    for word in words:
        low = word.lower().strip()
        base = _VARIANTS.get(low)
        if base and base != low:
            result.append(base)
            changed = True
        else:
            result.append(word)
    
    if changed:
        normalized = " ".join(result)
        log.debug("Darija normalized: %r → %r", text, normalized)
        return normalized
    
    return text
