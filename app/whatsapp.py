# ============================================================
#  Client WhatsApp Cloud API (Meta Graph)
#  - Vérifie l'abonnement webhook (GET)
#  - Envoie des messages texte (POST)
# ============================================================
import logging

import httpx

from .config import settings

logger = logging.getLogger("whatsapp")

GRAPH_URL = "https://graph.facebook.com"
HEADERS = {
    "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
    "Content-Type": "application/json",
}


# -----------------------------------------------------------
# Vérification du webhook (Meta envoie un GET au premier setup)
# -----------------------------------------------------------
def verify_webhook(mode: str, token: str, challenge: str) -> int | None:
    """Renvoie le 'challenge' si le token correspond, sinon None."""
    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook vérifié avec succès.")
        return int(challenge)
    logger.warning("Échec de la vérification du webhook.")
    return None


# -----------------------------------------------------------
# Envoi d'un message texte
# -----------------------------------------------------------
def send_text_message(to_phone: str, text: str) -> bool:
    """Envoie un message texte au numéro WhatsApp 'to_phone' (format E.164)."""
    url = f"{GRAPH_URL}/{settings.GRAPH_API_VERSION}/{settings.WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }
    try:
        resp = httpx.post(url, headers=HEADERS, json=payload, timeout=15)
        if resp.status_code in (200, 201):
            logger.info("Message envoyé à %s", to_phone)
            return True
        logger.error("Erreur envoi message: %s %s", resp.status_code, resp.text)
        return False
    except httpx.HTTPError as e:
        logger.error("Erreur réseau WhatsApp: %s", e)
        return False


# -----------------------------------------------------------
# Marquer le message comme lu (bonne pratique UX)
# -----------------------------------------------------------
def mark_as_read(message_id: str, phone_number_id: str = None) -> bool:
    pid = phone_number_id or settings.WHATSAPP_PHONE_ID
    url = f"{GRAPH_URL}/{settings.GRAPH_API_VERSION}/{pid}/messages"
    payload = {"messaging_product": "whatsapp", "status": "read", "message_id": message_id}
    try:
        httpx.post(url, headers=HEADERS, json=payload, timeout=10)
        return True
    except httpx.HTTPError:
        return False
