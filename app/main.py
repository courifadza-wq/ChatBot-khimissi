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


@app.get("/privacy")
async def privacy_policy():
    from fastapi.responses import HTMLResponse
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Politique de confidentialité — Planète Kids</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto;
           padding: 0 20px; color: #333; line-height: 1.7; }
    h1 { color: #2c7be5; border-bottom: 2px solid #2c7be5; padding-bottom: 10px; }
    h2 { color: #444; margin-top: 30px; }
    p  { margin: 10px 0; }
    a  { color: #2c7be5; }
    .footer { margin-top: 50px; font-size: 0.85em; color: #888; }
  </style>
</head>
<body>
  <h1>🛍️ Planète Kids — Politique de Confidentialité</h1>
  <p><strong>Date de mise à jour :</strong> Octobre 2026</p>

  <h2>1. Présentation</h2>
  <p>Planète Kids exploite un assistant WhatsApp automatisé pour faciliter les commandes et
     répondre aux questions de nos clients. Cette politique décrit comment nous collectons,
     utilisons et protégeons vos données personnelles.</p>

  <h2>2. Données collectées</h2>
  <p>Dans le cadre de l'utilisation de notre chatbot WhatsApp, nous pouvons collecter :</p>
  <ul>
    <li>Votre numéro de téléphone WhatsApp</li>
    <li>Votre prénom et nom (fournis lors d'une commande)</li>
    <li>Votre adresse de livraison</li>
    <li>L'historique de vos commandes</li>
    <li>Vos préférences de paiement</li>
  </ul>

  <h2>3. Utilisation des données</h2>
  <p>Les données collectées sont utilisées exclusivement pour :</p>
  <ul>
    <li>Traiter et livrer vos commandes</li>
    <li>Vous envoyer des confirmations et mises à jour</li>
    <li>Améliorer notre service client</li>
    <li>Mémoriser vos préférences pour des échanges futurs plus rapides</li>
  </ul>

  <h2>4. Partage des données</h2>
  <p>Nous ne vendons, ne louons et ne partageons pas vos données personnelles avec des tiers,
     sauf obligation légale ou nécessité pour la livraison (transporteur).</p>

  <h2>5. Conservation des données</h2>
  <p>Vos données sont conservées dans notre base de données sécurisée tant que vous êtes
     client actif. Vous pouvez demander la suppression à tout moment.</p>

  <h2>6. Vos droits</h2>
  <p>Conformément à la réglementation applicable, vous disposez des droits suivants :</p>
  <ul>
    <li>Droit d'accès à vos données</li>
    <li>Droit de rectification</li>
    <li>Droit à l'effacement ("droit à l'oubli")</li>
    <li>Droit d'opposition au traitement</li>
  </ul>
  <p>Pour exercer ces droits, contactez-nous via WhatsApp ou en écrivant à notre page Facebook.</p>

  <h2>7. Sécurité</h2>
  <p>Vos données sont stockées sur des serveurs sécurisés et protégées par des mesures
     techniques appropriées contre tout accès non autorisé.</p>

  <h2>8. Contact</h2>
  <p>Pour toute question concernant cette politique :<br>
     📱 WhatsApp : disponible via notre page Facebook Planète Kids<br>
     🌐 Facebook : <a href="https://www.facebook.com/planetekids" target="_blank">Planète Kids</a>
  </p>

  <div class="footer">
    <p>© 2026 Planète Kids — Tous droits réservés.</p>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html)


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

    # 0) Pré-détection recherche produit (avant NLP pour éviter les faux intents)
    from .catalog import parse_search_query, format_search_results, get_categories
    from .database import search_products, count_products
    _PRODUCT_KEYWORDS = {
        "robe", "veste", "pantalon", "chaussure", "chaussures", "sandale",
        "chaussette", "body", "pyjama", "pull", "manteau", "gilet", "combinaison",
        "salopette", "jogging", "ensemble", "tenue", "short", "jean",
        "sucette", "biberon", "tetine", "tétine", "couche", "couette",
        "couverture", "bavoir", "bavette", "cuillere", "cuillère", "baignoire",
        "jouet", "peluche", "doudou", "hochet", "tricycle", "vélo",
        "savon", "creme", "crème", "shampoing", "lotion", "lingette",
        "coffret", "cadeau", "kit",
    }
    # Mots qui indiquent clairement un intent catalogue/commande → NE PAS intercepter
    _EXCLUDE_TRIGGERS = {"catalogue", "commander", "commande", "livraison", "paiement",
                         "prix", "responsable", "bonjour", "merci", "aide"}
    _txt_lower = text.lower()
    _has_product_kw = any(kw in _txt_lower for kw in _PRODUCT_KEYWORDS)
    _has_age = any(p in _txt_lower for p in ["mois", " ans", "bébé", "bebe", "nourrisson"])
    _has_price_filter = any(p in _txt_lower for p in ["moins de", "plus de", "max", "budget", "dzd"])
    _has_exclude = any(w in _txt_lower for w in _EXCLUDE_TRIGGERS)

    if (_has_product_kw or _has_age or _has_price_filter) and not _has_exclude and not _in_order_session(phone):
        params = parse_search_query(text)
        results = search_products(
            keyword=params.get("keyword", ""),
            max_price=params.get("max_price", 0),
            min_price=params.get("min_price", 0),
            age_hint=params.get("age_hint", ""),
            limit=5,
        )
        response = format_search_results(results, query=params.get("keyword", text))
        send_text_message(phone, response)
        logger.info("Recherche produit directe pour : %s", text)
        return {"status": "ok"}

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
        # ── Fallback intelligent : tenter une recherche produit ──────
        from .catalog import parse_search_query, format_search_results
        from .database import search_products, count_products
        if count_products() > 0:
            params = parse_search_query(text)
            kw = params.get("keyword", "")
            # Ignorer les mots trop courts (non, oui, ok…) pour éviter les faux positifs
            if kw and max((len(w) for w in kw.split()), default=0) < 4:
                kw = ""
            if kw or params.get("age_hint") or params.get("max_price"):


                results = search_products(
                    keyword=params.get("keyword", ""),
                    max_price=params.get("max_price", 0),
                    min_price=params.get("min_price", 0),
                    age_hint=params.get("age_hint", ""),
                    limit=5,
                )
                if results:
                    response = format_search_results(results, query=params.get("keyword", text))
                else:
                    response = (
                        f"😕 Aucun résultat pour *\"{text}\"*.\n\n"
                        "Essayez avec d'autres mots, ou tapez *catalogue* pour voir les catégories disponibles."
                    )
            else:
                response = (
                    "Désolé, je n'ai pas bien compris 😅.\n"
                    "Vous pouvez me demander : les *produits*, les *prix*, la *livraison*, "
                    "le *paiement*, ou simplement *je veux commander*.\n"
                    "Ou demandez à parler à un *responsable*."
                )
        else:
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
    from .database import load_order_session
    from .order import ST_NEW
    data = load_order_session(phone)
    return data is not None and data.get("state", ST_NEW) != ST_NEW


def _current_order(phone: str):
    from .order import get_session
    return get_session(phone)["order"]
