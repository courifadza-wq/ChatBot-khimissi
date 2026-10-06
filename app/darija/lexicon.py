"""Lexique darija — ajouter à la main des mots/expressions dans la mémoire du bot.

Adapté pour le bot Planète Kids (mono-client, sans tenants).

Deux modes
----------
  mode = "produit"    le mot désigne un article   ->  « rda3a » = produit_biberon
                      le générateur darija fabrique toutes les tournures
                      (prix, dispo, stock, commande…) autour du mot.
  mode = "intention"  l'expression est une question générale ->  « fin rakom » = location
                      on décline l'expression elle-même (orthographes arabizi,
                      translittération arabe, politesse, bruit clavier).

Stockage : data/lexicon.yaml
Rechargé au démarrage dans app/main.py.
"""
from __future__ import annotations

import logging
import random
import re
import threading
import time
import unicodedata
from pathlib import Path

import yaml

from . import engine as darija
from ..nlp import classifier, normalize

log = logging.getLogger("lexicon")
_lock = threading.RLock()

MAX_ENTRIES = int(__import__("os").getenv("MAX_LEXICON_ENTRIES", "800"))

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


# ---------------------------------------------------------------------------
#  Adaptateurs — notre nlp.py a une API différente du générateur
# ---------------------------------------------------------------------------
class _PredictResult:
    """Enveloppe le retour string de classifier.predict() en objet riche."""
    __slots__ = ("intent", "confidence", "method", "alternatives")

    def __init__(self, intent: str, confidence: float = 0.0,
                 method: str = "rules", alternatives=None):
        self.intent      = intent
        self.confidence  = confidence
        self.method      = method
        self.alternatives = alternatives or []


def _predict(text: str) -> _PredictResult:
    """Appelle classifier.predict() et retourne un _PredictResult."""
    intent = classifier.predict(text) if text else "fallback"
    # Essaie d'obtenir la confiance depuis le ML (optionnel)
    confidence, alts = 0.0, []
    try:
        if classifier._clf is not None and classifier._vectorizer is not None:
            import numpy as np
            vec   = classifier._vectorizer.transform([normalize(text)])
            proba = classifier._clf.predict_proba(vec)[0]
            idx   = int(proba.argmax())
            confidence = float(proba[idx])
            classes = classifier._clf.classes_
            alts = [(classes[i], float(proba[i]))
                    for i in proba.argsort()[::-1][1:4] if proba[i] > 0.05]
    except Exception:
        pass
    return _PredictResult(intent, confidence, "ml" if confidence > 0 else "rules", alts)


def _train() -> None:
    """Reconstruit les règles et réentraîne le ML."""
    try:
        classifier._build_patterns()
        classifier._train_ml()
        log.info("📖 Classifieur ré-entraîné : %d patterns", len(classifier._patterns))
    except Exception as exc:
        log.warning("Ré-entraînement partiel : %s", exc)


def _stats() -> dict:
    """Résumé du classifieur compatible avec notre nlp.py."""
    n_pats = len(classifier._patterns)
    return {"intents": len(classifier.intents), "patterns": n_pats}



def lexicon_file() -> Path:
    return DATA_DIR / "lexicon.yaml"


# ---------------------------------------------------------------------------
#  Libellés français des intentions
# ---------------------------------------------------------------------------
LABELS = {
    "greeting": "Salutation", "goodbye": "Au revoir", "thanks": "Remerciement",
    "affirm": "Oui / d'accord", "deny": "Non", "bot_challenge": "Es-tu un robot ?",
    "help_menu": "Menu d'aide", "products": "Quels produits ?",
    "prices": "Prix", "discount": "Promotion / remise",
    "order_start": "Passer commande", "cancel_order": "Annuler la commande",
    "payment": "Paiement", "delivery": "Livraison",
    "track_order": "Suivi de colis", "warranty": "Garantie",
    "location": "Adresse du magasin", "hours": "Horaires",
    "availability": "Disponibilité", "fallback": "Incompris",
}

KIND_LABELS = {
    "price": "Prix", "availability": "Disponibilité", "info": "Infos",
    "stock": "Stock", "order": "Commande", "photo": "Photo", "promo": "Promotion",
    "size": "Taille", "color": "Couleur", "delivery": "Livraison",
    "payment": "Paiement", "reserve": "Réservation",
}
DEFAULT_KINDS = ("price", "availability", "info", "stock", "order", "photo", "promo")


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def entry_id(word: str, target: str) -> str:
    base = normalize(word) or _slug(word) or "mot"
    return f"{base}@{target}"


# ---------------------------------------------------------------------------
#  Cibles disponibles
# ---------------------------------------------------------------------------
def targets() -> dict:
    prods, gen = [], []
    for intent in sorted(classifier.intents):
        conf = classifier.intents[intent]
        n = len(conf.get("patterns", [])) if isinstance(conf, dict) else len(conf or [])
        if intent.startswith("produit_"):
            prods.append({"intent": intent, "label": intent.replace("produit_", "").replace("_", " ").title(),
                          "patterns": n})
        else:
            gen.append({"intent": intent, "label": LABELS.get(intent, intent), "patterns": n})
    return {
        "produits": prods,
        "intentions": gen,
        "familles_darija": [{"id": k, "label": KIND_LABELS.get(k, k)} for k in darija.KINDS],
        "registres": list(darija.REGISTERS),
    }


# ---------------------------------------------------------------------------
#  Fabrication des formulations
# ---------------------------------------------------------------------------
def _split_word(word: str, word_ar: str = "") -> tuple[str, str]:
    word, word_ar = (word or "").strip(), (word_ar or "").strip()
    if darija.has_arabic(word) and not darija.has_arabic(word_ar):
        word, word_ar = word_ar, word
    return word, word_ar


def phrase_variants(phrase: str, level: int = 2, translit: bool = True,
                    seed: int = 1337) -> list[str]:
    """Décline UNE expression : orthographes, écriture arabe/latine, politesse, bruit."""
    rnd = random.Random(f"{seed}:{phrase}")
    cfg = darija.LEVELS.get(level, darija.LEVELS[2])
    out, seen = [], set()

    def push(p: str) -> None:
        p = re.sub(r"\s+", " ", p or "").strip()
        n = darija.norm(p)
        if n and len(n) >= 2 and n not in seen:
            seen.add(n)
            out.append(p)

    base = re.sub(r"\s+", " ", (phrase or "").strip())
    if not base:
        return []
    is_ar = darija.has_arabic(base)
    push(base)

    forms = [base]
    if not is_ar:
        words = base.split()
        nmax = 3 if level >= 3 else (2 if level == 2 else 1)
        for i, w in enumerate(words):
            if len(w) < 3:
                continue
            for sp in darija.arabizi_spellings(w, limit=nmax + 1)[1:nmax + 1]:
                v = " ".join(words[:i] + [sp] + words[i + 1:])
                push(v)
                forms.append(v)
        if translit:
            ar = darija.to_arabic(base)
            if ar and ar != base:
                push(ar)
                forms.append(ar)
    elif translit:
        lat = darija.to_arabizi(base)
        if lat and lat != base:
            push(lat)
            forms.append(lat)

    if level >= 2:
        for f in forms[: 6 if level == 2 else 20]:
            r = "ar" if darija.has_arabic(f) else "arabizi"
            pres = [p for p in darija.PREFIX[r] if p][: 2 if level == 2 else 5]
            sufs = [s for s in (darija.POLITE_SUFFIX[r] + darija.SUFFIX[r]) if s][: 3 if level == 2 else 9]
            for p in pres:
                push(f"{p}{f}")
            for s in sufs:
                push(f"{f}{s}")
            if level >= 3:
                for p in pres[:2]:
                    for s in sufs[:3]:
                        push(f"{p}{f}{s}")

    if cfg["noise"] > 0:
        for f in forms[: 8 if level >= 3 else 3]:
            for _ in range(2 if level >= 3 else 1):
                push(darija.noisy(f, rnd))
    return out


def build(word: str, word_ar: str = "", mode: str = "produit", target: str = "",
          kinds: list[str] | tuple[str, ...] = DEFAULT_KINDS, level: int = 2,
          registers: list[str] | tuple[str, ...] = darija.REGISTERS,
          extra: list[str] | None = None, cap: int | None = None) -> list[str]:
    """Fabrique la liste des formulations à injecter dans le modèle."""
    word, word_ar = _split_word(word, word_ar)
    pats: list[str] = []
    if mode == "produit":
        pats = darija.generate(word, word_ar,
                               kinds=[k for k in (kinds or DEFAULT_KINDS) if k in darija.C]
                               or list(DEFAULT_KINDS),
                               registers=list(registers or darija.REGISTERS),
                               level=level, cap=cap, include_bare=True)
    else:
        for w in (word, word_ar):
            if w:
                pats += phrase_variants(w, level=level)
    for x in (extra or []):
        x = (x or "").strip()
        if x:
            pats.append(x)
    seen, uniq = set(), []
    for p in pats:
        n = darija.norm(p)
        if n and n not in seen:
            seen.add(n)
            uniq.append(p)
    return uniq


def preview(word: str, word_ar: str = "", mode: str = "produit", target: str = "",
            kinds=DEFAULT_KINDS, level: int = 2, registers=darija.REGISTERS,
            extra=None, sample: int = 60) -> dict:
    """Aperçu AVANT enregistrement."""
    pats = build(word, word_ar, mode, target, kinds, level, registers, extra)
    word_l, word_a = _split_word(word, word_ar)
    pools = darija.keyword_pools(word_l, word_a, level) if mode == "produit" else ([], [])
    probe = (word_a or word_l or "").strip()
    before = {}
    if probe:
        r = _predict(probe)
        before = {"intent": r.intent, "confidence": round(r.confidence, 2), "method": r.method}
    by_script = {"latin": [p for p in pats if not darija.has_arabic(p)],
                 "arabe": [p for p in pats if darija.has_arabic(p)]}
    return {
        "mot": word_l, "mot_ar": word_a, "mode": mode, "cible": target, "niveau": level,
        "total": len(pats),
        "latin": len(by_script["latin"]), "arabe": len(by_script["arabe"]),
        "variantes_mot": {"latin": pools[0], "arabe": pools[1]},
        "avant": before, "fiche": {},
        "exemples": {"latin": by_script["latin"][:sample // 2],
                     "arabe": by_script["arabe"][:sample // 2]},
        "tous": pats,
    }


# ---------------------------------------------------------------------------
#  Persistance
# ---------------------------------------------------------------------------
def _load() -> dict:
    f = lexicon_file()
    if f.exists():
        try:
            return yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except Exception as exc:                                  # noqa: BLE001
            log.error("lexicon.yaml illisible : %s", exc)
    return {}


def _save(data: dict) -> None:
    f = lexicon_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=4096),
                 encoding="utf-8")


def _inject(entry: dict) -> int:
    """Injecte les patterns d'une entrée dans le modèle en mémoire.
    Structure nlp.py: intents[name] = {"patterns": [...], ...}
    """
    target = entry.get("target") or ""
    pats = entry.get("patterns") or []
    if not target or not pats:
        return 0
    if target not in classifier.intents:
        classifier.intents[target] = {"patterns": []}
    conf = classifier.intents[target]
    if isinstance(conf, dict):
        cur = conf.setdefault("patterns", [])
    else:
        cur = conf  # fallback si structure plate
    have = set(cur)
    add = [p for p in pats if p not in have]
    cur.extend(add)
    return len(add)


# ---------------------------------------------------------------------------
#  API publique
# ---------------------------------------------------------------------------
def add(word: str, word_ar: str = "", mode: str = "produit", target: str = "",
        kinds=DEFAULT_KINDS, level: int = 2, registers=darija.REGISTERS,
        extra=None, note: str = "", retrain: bool = True,
        author: str = "lexique", fr_keyword: str = "") -> dict:
    """Ajoute un mot/une expression dans la mémoire du bot."""
    word_l, word_a = _split_word(word, word_ar)
    if not (word_l or word_a):
        raise ValueError("mot vide")
    if target in ("", "__new__", "nouveau") and mode == "produit":
        racine = word_l or darija.to_arabizi(word_a) or ""
        if not _slug(racine):
            raise ValueError("impossible de créer une famille : donnez le mot en lettres latines")
        target = f"produit_{_slug(racine)[:34]}"
    if not target:
        raise ValueError("aucune cible choisie")

    pats = build(word_l, word_a, mode, target, kinds, level, registers, extra)
    if not pats:
        raise ValueError("aucune formulation générée")

    with _lock:
        data = _load()
        if len(data) >= MAX_ENTRIES and entry_id(word_l or word_a, target) not in data:
            raise ValueError(f"lexique plein ({MAX_ENTRIES} entrées)")
        eid = entry_id(word_l or word_a, target)
        entry = {
            "word": word_l, "word_ar": word_a, "mode": mode, "target": target,
            "kinds": list(kinds or DEFAULT_KINDS) if mode == "produit" else [],
            "registers": list(registers or darija.REGISTERS) if mode == "produit" else [],
            "level": level, "note": note, "extra": list(extra or []),
            "fr_keyword": (fr_keyword or "").strip(),
            "patterns": pats, "at": time.strftime("%Y-%m-%d %H:%M"), "by": author,
        }
        data[eid] = entry
        _save(data)
        added = _inject(entry)
        if retrain:
            _train()
        log.info("📖 Lexique : « %s » -> %s (%d formulations, +%d nouvelles)",
                 word_l or word_a, target, len(pats), added)
        after = _predict(word_a or word_l)
        return {
            "ok": True, "id": eid, "mot": word_l, "mot_ar": word_a, "cible": target,
            "formulations": len(pats), "ajoutees": added,
            "entrees": len(data),
            "modele": _stats(),
            "apres": {"intent": after.intent, "confidence": round(after.confidence, 2),
                      "method": after.method},
        }


def delete(eid: str, retrain: bool = True) -> dict:
    """Retire une entrée et reconstruit le modèle proprement."""
    with _lock:
        data = _load()
        if eid not in data:
            return {"ok": False, "raison": "entrée inconnue"}
        removed = data.pop(eid)
        _save(data)
        # Recharge depuis intents.yaml + réinjecte le lexique restant
        from ..nlp import reload_classifier
        reload_classifier()
        apply_all()
        if retrain:
            _train()
        log.info("📖 Lexique : suppression de « %s »", removed.get("word") or eid)
        return {"ok": True, "supprime": eid, "entrees": len(data),
                "modele": _stats()}


def apply_all() -> dict:
    """Réinjecte tout le lexique dans le modèle en mémoire (sans ré-entraîner)."""
    data = _load()
    total = 0
    for e in data.values():
        total += _inject(e)
    if data:
        log.info("📖 Lexique restauré : %d entrée(s), %d formulations", len(data), total)
    return {"entries": len(data), "patterns": total}


def restore() -> dict:
    """Réinjecte le lexique PUIS ré-entraîne (utilisé au démarrage)."""
    res = apply_all()
    if res["entries"]:
        _train()
    return res


def entries(q: str = "", target: str = "", limit: int = 500) -> list[dict]:
    data = _load()
    out = []
    nq = normalize(q) if q else ""
    for eid, e in data.items():
        if target and e.get("target") != target:
            continue
        if nq and nq not in normalize(f"{e.get('word','')} {e.get('word_ar','')} {e.get('target','')}"):
            continue
        out.append({
            "id": eid, "word": e.get("word", ""), "word_ar": e.get("word_ar", ""),
            "mode": e.get("mode", "produit"), "target": e.get("target", ""),
            "label": LABELS.get(e.get("target", ""), e.get("target", "")),
            "level": e.get("level", 2), "kinds": e.get("kinds", []),
            "note": e.get("note", ""), "fr_keyword": e.get("fr_keyword", ""),
            "at": e.get("at", ""),
            "patterns": len(e.get("patterns") or []),
            "exemples": (e.get("patterns") or [])[:6],
        })
    out.sort(key=lambda x: x["at"], reverse=True)
    return out[:limit]


def state() -> dict:
    data = _load()
    pats = sum(len(e.get("patterns") or []) for e in data.values())
    par_cible: dict[str, int] = {}
    for e in data.values():
        par_cible[e.get("target", "?")] = par_cible.get(e.get("target", "?"), 0) + 1
    return {
        "entrees": len(data), "formulations": pats, "max": MAX_ENTRIES,
        "fichier": str(lexicon_file()),
        "par_cible": dict(sorted(par_cible.items(), key=lambda x: -x[1])[:15]),
        "modele": _stats(),
        "gabarits_darija": darija.stats()["gabarits_total"],
    }


def test(text: str) -> dict:
    """Teste une phrase client : intention détectée + infos."""
    r = _predict(text)
    try:
        from ..responses import reply_for
        from ..normalize import detect_lang
        reply = reply_for(r.intent, message=text, client=None, lang=detect_lang(text))
    except Exception as exc:                                      # noqa: BLE001
        reply = f"(réponse indisponible : {exc})"
    return {"texte": text, "intent": r.intent, "confidence": round(r.confidence, 3),
            "method": r.method,
            "label": LABELS.get(r.intent, r.intent),
            "alternatives": [{"intent": a, "score": round(s, 3)} for a, s in (r.alternatives or [])][:3],
            "reply": reply}


def export_yaml() -> str:
    return yaml.safe_dump(_load(), allow_unicode=True, sort_keys=False, width=4096)


def import_entries(rows: list[dict], retrain: bool = True) -> dict:
    """Import en lot : [{word, word_ar, mode, target, level}, …]"""
    ok, errs = 0, []
    for r in rows:
        try:
            add(r.get("word", ""), r.get("word_ar", ""), r.get("mode") or "produit",
                r.get("target", ""), r.get("kinds") or DEFAULT_KINDS,
                int(r.get("level") or 2), darija.REGISTERS, None,
                r.get("note", ""), retrain=False, author="import")
            ok += 1
        except Exception as exc:                                  # noqa: BLE001
            errs.append({"ligne": r, "erreur": str(exc)})
    if ok and retrain:
        _train()
    return {"ajoutes": ok, "erreurs": errs[:20], "modele": _stats()}

