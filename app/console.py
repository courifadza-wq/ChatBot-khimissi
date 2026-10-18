"""Auth admin simple pour Planète Kids — token depuis variable d'environnement.

Usage dans les routes FastAPI :
    from .console import require_console
    @router.get("/route")
    async def ma_route(_: bool = Depends(require_console)):
        ...

Configurer ADMIN_TOKEN dans les variables d'environnement Coolify.
Si ADMIN_TOKEN est vide → accès libre (développement local).
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, Header, HTTPException, Query

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")


async def require_console(
    x_admin_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
) -> bool:
    """Vérifie le token admin. Retourne True si authentifié.

    Accepte le token depuis :
      - Header X-Admin-Token: <token>
      - Header Authorization: Bearer <token>  (proxy PHP lexicon-api.php)
      - Query param ?token=<token>
    """
    if not ADMIN_TOKEN:
        return True  # Pas de token configuré → accès libre (dev local)

    # Extraire le token selon la source
    bearer = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization[7:].strip()

    t = (x_admin_token or bearer or token or "").strip()
    if t != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Token admin requis — ?token=VOTRE_TOKEN")
    return True
