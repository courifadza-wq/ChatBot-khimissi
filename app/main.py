# ============================================================
#  Point d'entrée FastAPI : webhook WhatsApp entrant
#  GET  -> vérification Meta
#  POST -> réception des messages
# ============================================================
import logging

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from .config import settings
from .whatsapp import verify_webhook, send_text_message
from .nlp import classifier
from .responses import reply_for
from .order import process, reset_session, build_email_body, Order
from .email_sender import send_order_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(title="Bot WhatsApp — Ventes & Commandes")


@app.get("/webhook", response_class=PlainTextResponse)
async def webhook_verify(
    hub_mode: str = Query(default="", alias="hub.mode"),
    hub_verify_token: str = Query(default="", alias="hub.verify_token"),
    hub_challenge: str = Query(default="", alias="hub.challenge"),
):
    challenge = verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    if challenge is not None:
        return str(challenge)
    return JSONResponse(status_code=403, content={"error": "Invalid verification token"})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
async def webhook_receive(request: Request):
    data = await request.json()

    # Meta envoie toujours une liste "entry" même pour les confirmations
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        # On ignore les messages de statut (read, delivered)
        if "messages" not in value:
            return {"status": "ignored"}
        message = value["messages"][0]
        if message.get("type") != "text":
            send_text_message(message["from"], "Je gère uniquement les messages texte pour l'instant 😊")
            return {"status": "ok"}
    except (KeyError, IndexError):
        return {"status": "ignored"}

    phone = message["from"]
    text = message["text"]["body"]
    message_id = message["id"]

    logger.info("Message de %s : %s", phone, text)

    # 1) Détecter l'intention
    intent = classifier.predict(text)
    logger.info("Intention détectée : %s", intent)

    # 2) Machine à états de commande (priorité si déjà en cours ou intent commande)
    if intent == "order_start" or _in_order_session(phone):
        reply = process(phone, text, intent)
        if reply == "CONFIRMED":
            order: Order = _current_order(phone)
            ok = send_order_email(order)
            send_text_message(
                phone,
                "✅ *Commande confirmée et enregistrée !*\n"
                "Notre équipe vous contactera pour la livraison.\nMerci de votre confiance 🙏"
            )
            reset_session(phone)
            return {"status": "ok"}
        if reply:
            send_text_message(phone, reply)
            return {"status": "ok"}

    # 3) Sinon réponse normale selon l'intention
    response = reply_for(intent, message=text)
    if response is None:
        # Fallback intelligent : on ne reste jamais muet
        response = (
            "Désolé, je n'ai pas bien compris 😅.\n"
            "Vous pouvez me demander : les *produits*, les *prix*, la *livraison*, "
            "le *paiement*, ou simplement *je veux commander*.\n"
            "Ou demandez à parler à un *responsable*."
        )
    send_text_message(phone, response)
    return {"status": "ok"}


# ------------------------------------------------------------------
# Helpers pour retrouver la session en cours (ordre)
# ------------------------------------------------------------------
def _in_order_session(phone: str) -> bool:
    from .order import _sessions
    return phone in _sessions


def _current_order(phone: str):
    from .order import _sessions
    return _sessions[phone]["order"]
