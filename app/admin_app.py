# ============================================================
#  Interface d'ADMIN locale — alimenter le bot en intentions
#
#  Lancer localement :  uvicorn app.admin_app:app --port 8080
#  Puis ouvrir :        http://localhost:8080
#
#  Fonctions :
#   - Ajouter / modifier / supprimer des intentions (fr, arabe, derja)
#   - Modifier le catalogue produits + alias
#   - Re-entraîner le classifieur immédiatement
#   - Tester une phrase -> intention détectée
#
#  ATTENTION : à utiliser en LOCAL uniquement (pas exposé publiquement).
# ============================================================
from __future__ import annotations

from pathlib import Path
from copy import deepcopy

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from .config import settings

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="Admin Bot WhatsApp")

INTENTS_FILE = settings.INTENTS_FILE
PRODUCTS_FILE = settings.PRODUCTS_FILE
HTML_FILE = BASE_DIR / "admin" / "editor.html"


# ----------------------------------------------------------
# Helpers YAML (sûrs, préservent l'ordre)
# ----------------------------------------------------------
def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save_yaml(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=100)
    return True


def _classifier():
    from . import nlp
    return nlp.classifier


# ----------------------------------------------------------
# Pages
# ----------------------------------------------------------
@app.get("/")
async def index():
    if not HTML_FILE.exists():
        raise HTTPException(500, "editor.html introuvable")
    return FileResponse(HTML_FILE)


# ----------------------------------------------------------
# API Intentions
# ----------------------------------------------------------
@app.get("/api/intents")
async def get_intents():
    data = _load_yaml(INTENTS_FILE)
    intents = data.get("intents", {})
    # compte les exemples par langue (approx : mots arabes / latins)
    result = []
    for name, conf in intents.items():
        patterns = conf.get("patterns", [])
        nb_ar = sum(1 for p in patterns if any("\u0600" <= c <= "\u06FF" for c in p))
        result.append({
            "name": name,
            "patterns": patterns,
            "count": len(patterns),
            "arabic": nb_ar,
        })
    return {"intents": result}


@app.post("/api/intents")
async def save_intents(payload: dict):
    """payload = {"intents": [{"name": "x", "patterns": [...]}, ...]}"""
    intents_in = payload.get("intents", [])
    ordered = {}
    for it in intents_in:
        name = it.get("name", "").strip()
        if not name:
            continue
        patterns = [p.strip() for p in it.get("patterns", []) if p.strip()]
        ordered[name] = {"patterns": patterns}
    data = _load_yaml(INTENTS_FILE)
    data["intents"] = ordered
    _save_yaml(INTENTS_FILE, data)
    # re-entraîne le classifieur
    from .nlp import reload_classifier
    clf = reload_classifier()
    return {"ok": True, "saved": len(ordered), "trained": True}


@app.post("/api/predict")
async def predict(payload: dict):
    text = payload.get("text", "")
    intent = _classifier().predict(text)
    return {"intent": intent}


# ----------------------------------------------------------
# API Produits (catalogue)
# ----------------------------------------------------------
@app.get("/api/products")
async def get_products():
    data = _load_yaml(PRODUCTS_FILE)
    return {
        "store": data.get("store", {}),
        "delivery": data.get("delivery", {}),
        "products": data.get("products", []),
        "payment": data.get("payment", []),
    }


@app.post("/api/products")
async def save_products(payload: dict):
    data = deepcopy(payload)
    _save_yaml(PRODUCTS_FILE, data)
    from .catalog import load_catalog
    load_catalog.cache_clear()
    return {"ok": True}


# ----------------------------------------------------------
# Santé
# ----------------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok", "nl_mode": settings.NL_MODE}
