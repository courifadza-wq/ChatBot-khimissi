# ============================================================
#  Contrôle on/off du bot par le propriétaire
#  Le propriétaire envoie "on" ou "off" via WhatsApp
#  L'état est persisté en SQLite (survit aux redémarrages)
# ============================================================

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger("handover")

_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "bot_memory.db"


def _get_state() -> bool:
    """Lit l'état bot depuis SQLite. Défaut : actif (True)."""
    try:
        conn = sqlite3.connect(_DB_PATH)
        row = conn.execute(
            "SELECT value FROM bot_settings WHERE key='bot_active'"
        ).fetchone()
        conn.close()
        if row is None:
            return True
        return row[0] == "1"
    except Exception:
        return True  # En cas d'erreur → bot actif par défaut


def _set_state(active: bool) -> None:
    """Sauvegarde l'état bot dans SQLite."""
    try:
        conn = sqlite3.connect(_DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bot_settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.execute(
            "INSERT OR REPLACE INTO bot_settings (key, value) VALUES ('bot_active', ?)",
            ("1" if active else "0",)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("Erreur sauvegarde état bot : %s", e)


def is_active() -> bool:
    """Retourne True si le bot est actif."""
    return _get_state()


def turn_off() -> None:
    """Désactiver le bot — il ne répond plus aux clients."""
    _set_state(False)
    logger.info("🔴 Bot désactivé par le propriétaire")


def turn_on() -> None:
    """Activer le bot — il reprend les réponses automatiques."""
    _set_state(True)
    logger.info("🟢 Bot activé par le propriétaire")


def handle_owner_command(text: str) -> str | None:
    """
    Traite les commandes du propriétaire.
    Retourne le message de réponse, ou None si c'est un message normal.

    Commandes :
      on   → active le bot
      off  → désactive le bot
      état → voir l'état actuel
    """
    cmd = text.strip().lower()

    if cmd == "off":
        turn_off()
        return (
            "🔴 *Bot désactivé.*\n"
            "Le bot ne répond plus aux clients.\n"
            "Tu peux répondre manuellement.\n\n"
            "Envoie *on* pour le réactiver."
        )

    if cmd == "on":
        turn_on()
        return (
            "🟢 *Bot activé.*\n"
            "Le bot répond à nouveau automatiquement à tous les clients."
        )

    if cmd in ("état", "etat", "status"):
        active = is_active()
        if active:
            return "🟢 *Bot actif* — il répond automatiquement aux clients.\nEnvoie *off* pour le désactiver."
        else:
            return "🔴 *Bot désactivé* — tu réponds manuellement.\nEnvoie *on* pour le réactiver."

    return None  # Pas une commande → message normal au bot
