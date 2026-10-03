# ============================================================
#  Point d'entrée FastAPI : webhook WhatsApp entrant
#  GET  -> vérification Meta
#  POST -> réception des messages
# ============================================================
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from .config import settings
from .whatsapp import verify_webhook, send_text_message
from .nlp import classifier
from .responses import reply_for
from .order import process, reset_session, build_email_body, Order
from .email_sender import send_order_email
from .database import init_db, get_client, touch_client, upsert_client, save_order
from .human_handover import is_active, handle_owner_command

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")


# -----------------------------------------------------------
# Initialisation de la base de données au démarrage
# -----------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Initialisation de la mémoire long-terme (SQLite)…")
        init_db()
        logger.info("Base de données prête.")
    except Exception as e:
        logger.error("Erreur init DB (mode dégradé sans mémoire) : %s", e)
    yield
    logger.info("Arrêt du serveur.")


app = FastAPI(title="Bot WhatsApp — Ventes & Commandes", lifespan=lifespan)


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
    return {"status": "ok", "nl_mode": settings.NL_MODE}


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

    logger.info("Message de %s : %s", phone, text)

    # ── Commandes du propriétaire (on / off / état) ──────────────────
    owner_phone = settings.OWNER_PHONE.replace("+", "").replace(" ", "")
    if phone == owner_phone:
        owner_reply = handle_owner_command(text)
        if owner_reply:
            send_text_message(phone, owner_reply)
            return {"status": "ok"}
        # Si ce n'est pas une commande → le propriétaire peut tester le bot normalement

    # ── Bot désactivé → ignorer les messages des clients ────────────
    if not is_active() and phone != owner_phone:
        logger.info("Bot OFF — message de %s ignoré", phone)
        return {"status": "bot_off"}


    # Charger le profil client (mémoire long-terme)
    try:
        client_profile = get_client(phone)
        if client_profile:
            touch_client(phone)
    except Exception as e:
        logger.warning("Erreur lecture profil client : %s", e)
        client_profile = None

    # 1) Détecter l'intention
    intent = classifier.predict(text)
    logger.info("Intention détectée : %s", intent)

    # 2) Machine à états de commande (priorité si déjà en cours ou intent commande)
    if intent == "order_start" or _in_order_session(phone):
        reply = process(phone, text, intent)
        if reply == "CONFIRMED":
            order: Order = _current_order(phone)
            send_order_email(order)

            # ── Mémoire long-terme : sauvegarder client + commande ──
            try:
                upsert_client(order.phone, order.name, order.address, order.payment)
                save_order(order.phone, order.name, order.address,
                           order.items, order.total, order.payment)
                logger.info("Commande sauvegardée en base pour %s", order.phone)
            except Exception as e:
                logger.error("Erreur sauvegarde mémoire : %s", e)

            # Message de confirmation personnalisé (client fidèle vs nouveau)
            is_returning = client_profile and client_profile.get("order_count", 0) > 0
            if is_returning:
                confirmation_msg = (
                    f"✅ *Commande confirmée, merci {order.name} !* 🙏\n"
                    f"_(Commande n°{client_profile['order_count'] + 1} chez nous — on vous connaît bien 😊)_\n\n"
                    "Notre équipe vous contactera pour la livraison."
                )
            else:
                confirmation_msg = (
                    "✅ *Commande confirmée et enregistrée !*\n"
                    "Notre équipe vous contactera pour la livraison.\nMerci de votre confiance 🙏"
                )
            send_text_message(phone, confirmation_msg)
            reset_session(phone)
            return {"status": "ok"}
        if reply:
            send_text_message(phone, reply)
            return {"status": "ok"}

    # 3) Sinon réponse normale selon l'intention (avec profil client)
    response = reply_for(intent, message=text, client=client_profile)
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
