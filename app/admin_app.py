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


# ----------------------------------------------------------
# API Mémoire long-terme (lecture seule pour l'admin)
# ----------------------------------------------------------
@app.get("/api/clients")
async def list_clients(limit: int = 50):
    """Retourne la liste des clients connus (triés par dernière commande)."""
    try:
        from .database import _get_conn
        with _get_conn() as conn:
            rows = conn.execute(
                """SELECT phone, name, address, preferred_payment,
                          order_count, first_seen, last_seen
                   FROM clients
                   ORDER BY last_seen DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
            return {"clients": [dict(r) for r in rows], "total": len(rows)}
    except Exception as e:
        return {"error": str(e), "clients": []}


@app.get("/api/clients/{phone}/orders")
async def client_orders(phone: str):
    """Retourne l'historique des commandes d'un client."""
    try:
        from .database import get_client, get_client_orders
        client = get_client(phone)
        if not client:
            return {"error": "Client introuvable", "orders": []}
        orders = get_client_orders(phone, limit=20)
        return {"client": client, "orders": orders}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/stats")
async def stats():
    """Statistiques globales : nombre de clients, commandes, CA total."""
    try:
        from .database import _get_conn
        with _get_conn() as conn:
            nb_clients = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
            nb_orders  = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            ca_total   = conn.execute("SELECT COALESCE(SUM(total), 0) FROM orders").fetchone()[0]
            top_clients = conn.execute(
                """SELECT name, phone, order_count
                   FROM clients ORDER BY order_count DESC LIMIT 5"""
            ).fetchall()
        return {
            "total_clients":  nb_clients,
            "total_orders":   nb_orders,
            "ca_total_dzd":   ca_total,
            "top_clients":    [dict(r) for r in top_clients],
        }
    except Exception as e:
        return {"error": str(e)}
