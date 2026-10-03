# ============================================================
#  Contrôle on/off du bot par le propriétaire
#  Le propriétaire envoie "on" ou "off" via WhatsApp
# ============================================================

import logging

logger = logging.getLogger("handover")

# État global du bot (True = actif, False = désactivé)
_bot_active: bool = True


def is_active() -> bool:
    """Retourne True si le bot est actif."""
    return _bot_active


def turn_off() -> None:
    """Désactiver le bot — il ne répond plus aux clients."""
    global _bot_active
    _bot_active = False
    logger.info("🔴 Bot désactivé par le propriétaire")


def turn_on() -> None:
    """Activer le bot — il reprend les réponses automatiques."""
    global _bot_active
    _bot_active = True
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
        if _bot_active:
            return "🟢 *Bot actif* — il répond automatiquement aux clients.\nEnvoie *off* pour le désactiver."
        else:
            return "🔴 *Bot désactivé* — tu réponds manuellement.\nEnvoie *on* pour le réactiver."

    return None  # Pas une commande → message normal au bot
