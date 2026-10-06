# ============================================================
#  API Journal des messages — /api/journal/*
# ============================================================
from fastapi import APIRouter, Query
from ..console import require_console
from fastapi import Depends

router = APIRouter(tags=["journal"])


@router.get("/api/journal")
def list_journal(
    q: str = "",
    intent: str = "",
    fallback_only: bool = False,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    _=Depends(require_console),
):
    from ..database import get_journal
    return get_journal(q=q, intent=intent, fallback_only=fallback_only,
                       page=page, per_page=per_page)


@router.get("/api/journal/stats")
def journal_stats(_=Depends(require_console)):
    from ..database import get_journal_stats
    return get_journal_stats()


@router.post("/api/journal/cleanup")
def journal_cleanup(days: int = 30, _=Depends(require_console)):
    from ..database import cleanup_journal
    deleted = cleanup_journal(days)
    return {"ok": True, "deleted": deleted, "days": days}
