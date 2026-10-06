"""Routes de l'outil « Lexique darija » (page /lexique + API /api/lexicon/*).

Adapté pour Planète Kids — mono-client, pas de multi-tenant.
Protégé par ADMIN_TOKEN (variable d'environnement Coolify).
"""
from __future__ import annotations

import csv
import io
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse

from ..console import require_console

log = logging.getLogger("lexicon-api")
router = APIRouter()

PAGE = Path(__file__).resolve().parent / "page.html"


def _lex():
    from . import lexicon
    return lexicon


# ---------------------------------------------------------------------------
@router.get("/lexique")
async def lexique_page():
    if not PAGE.exists():
        raise HTTPException(404, "page.html introuvable")
    return FileResponse(PAGE, media_type="text/html")


@router.get("/api/lexicon/targets")
async def api_targets(_: bool = Depends(require_console)):
    return _lex().targets()


@router.get("/api/lexicon")
async def api_list(q: str = "", target: str = "",
                   _: bool = Depends(require_console)):
    lx = _lex()
    return {"entrees": lx.entries(q, target), "etat": lx.state()}


@router.get("/api/lexicon/state")
async def api_state(_: bool = Depends(require_console)):
    return _lex().state()


@router.post("/api/lexicon/preview")
async def api_preview(request: Request, _: bool = Depends(require_console)):
    b = await request.json()
    lx = _lex()
    return lx.preview(
        b.get("word", ""), b.get("word_ar", ""), b.get("mode", "produit"),
        b.get("target", ""), b.get("kinds") or lx.DEFAULT_KINDS,
        int(b.get("level") or 2),
        b.get("registers") or list(lx.darija.REGISTERS),
        b.get("extra") or [])


@router.post("/api/lexicon")
async def api_add(request: Request, _: bool = Depends(require_console)):
    b = await request.json()
    lx = _lex()
    try:
        return lx.add(
            b.get("word", ""), b.get("word_ar", ""), b.get("mode", "produit"),
            b.get("target", ""), b.get("kinds") or lx.DEFAULT_KINDS,
            int(b.get("level") or 2),
            b.get("registers") or list(lx.darija.REGISTERS),
            b.get("extra") or [], b.get("note", ""),
            fr_keyword=b.get("fr_keyword", ""))
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.delete("/api/lexicon")
async def api_delete(id: str = Query(...), _: bool = Depends(require_console)):
    res = _lex().delete(id)
    if not res.get("ok"):
        raise HTTPException(404, res.get("raison", "entrée inconnue"))
    return res


@router.post("/api/lexicon/test")
async def api_test(request: Request, _: bool = Depends(require_console)):
    b = await request.json()
    return _lex().test(b.get("text", "") or b.get("message", ""))


@router.post("/api/lexicon/import")
async def api_import(request: Request, _: bool = Depends(require_console)):
    """Import en lot. Corps : {"csv": "mot;mot_ar;cible\\n...", ...}"""
    b = await request.json()
    rows = b.get("rows")
    if not rows and b.get("csv"):
        txt = b["csv"].strip()
        dialect = ";" if txt.count(";") >= txt.count(",") else ","
        rows = []
        for r in csv.reader(io.StringIO(txt), delimiter=dialect):
            r = [c.strip() for c in r if c is not None]
            if not r or not r[0]:
                continue
            rows.append({"word": r[0],
                         "word_ar": r[1] if len(r) > 1 else "",
                         "target": r[2] if len(r) > 2 else b.get("target", ""),
                         "mode": (r[3] if len(r) > 3 else b.get("mode", "produit")) or "produit",
                         "level": int(r[4]) if len(r) > 4 and r[4].isdigit() else int(b.get("level") or 2)})
    if not rows:
        raise HTTPException(400, "rien à importer")
    return _lex().import_entries(rows)


@router.get("/api/lexicon/export.yaml")
async def api_export(_: bool = Depends(require_console)):
    return PlainTextResponse(_lex().export_yaml(), media_type="text/yaml; charset=utf-8")
