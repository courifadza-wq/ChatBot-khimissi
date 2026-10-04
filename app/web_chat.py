"""
web_chat.py — Logique bot pour le widget web (sans WhatsApp API).
Réutilise NLP, recherche, commandes et email existants.
"""
import logging
import re as _re

logger = logging.getLogger("web_chat")


def get_bot_reply(session_id: str, text: str) -> str:
    """Retourne la réponse du bot pour un message web."""
    from .nlp import classifier
    from .responses import reply_for
    from .order import process, reset_session
    from .email_sender import send_order_email
    from .database import get_client, touch_client, upsert_client, save_order

    text = text.strip()
    if not text:
        return "Bonjour ! Comment puis-je vous aider ? 😊"

    # ── Détection langue ─────────────────────────────────────────────
    arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    lang = "ar" if arabic_chars / max(len(text), 1) > 0.25 else "fr"

    # ── Profil client ────────────────────────────────────────────────
    try:
        client_profile = get_client(session_id)
        if client_profile:
            touch_client(session_id)
    except Exception:
        client_profile = None

    # ── AR_MENU (même que WhatsApp) ──────────────────────────────────
    _AR_MENU = {
        "السلام عليكم": "greeting", "سلام": "greeting", "مرحبا": "greeting",
        "صباح الخير": "greeting", "مساء الخير": "greeting",
        "أهلا": "greeting", "اهلا": "greeting", "هلا": "greeting",
        "مع السلامة": "goodbye", "باي": "goodbye",
        "شكرا": "thanks", "شكراً": "thanks", "مرسي": "thanks",
        "يعطيك الصحة": "thanks", "بارك الله فيك": "thanks",
        "الكتالوج": "products", "كتالوج": "products",
        "الأسعار": "products", "الاسعار": "products", "اسعار": "products",
        "الكتالوج / الأسعار": "products", "الكتالوج / الاسعار": "products",
        "الكتالوج/الاسعار": "products", "الكتالوج/ الاسعار": "products",
        "التوصيل": "delivery", "توصيل": "delivery",
        "الدفع": "payment", "دفع": "payment", "طريقة الدفع": "payment",
        "تطلب": "order_start", "اطلب": "order_start", "طلب": "order_start",
        "مساعدة": "help",
    }
    _AR_KEYWORDS = [
        (["كتالوج", "اسعار", "أسعار", "الكتالوج"], "products"),
        (["توصيل", "توصيلة"], "delivery"),
        (["الدفع", "طريقة دفع"], "payment"),
        (["اطلب", "تطلب", "بغيت نطلب"], "order_start"),
    ]

    _txt_norm = _re.sub(r"\s*/\s*", "/", _re.sub(r"\s+", " ", text))
    _forced_intent = _AR_MENU.get(text) or _AR_MENU.get(_txt_norm)
    if not _forced_intent and lang == "ar":
        for _kws, _intent in _AR_KEYWORDS:
            if any(kw in text for kw in _kws):
                _forced_intent = _intent
                break

    if _forced_intent:
        resp = reply_for(_forced_intent, message=text, client=client_profile, lang=lang)
        if resp:
            return resp
        if _forced_intent == "order_start":
            r = process(session_id, text, "order_start")
            if r and r != "CONFIRMED":
                return r

    # ── Pré-détection produit ────────────────────────────────────────
    from .catalog import parse_search_query, format_search_results, get_categories
    from .database import search_products, count_products

    _PRODUCT_KW = {
        "robe", "veste", "pantalon", "chaussure", "chaussures", "sandale",
        "chaussette", "body", "pyjama", "pull", "manteau", "gilet",
        "salopette", "jogging", "ensemble", "tenue", "short", "jean",
        "sucette", "biberon", "tetine", "tétine", "couche", "couette",
        "couverture", "bavoir", "bavette", "jouet", "peluche", "doudou",
        "hochet", "tricycle", "savon", "creme", "crème", "shampoing",
        "lotion", "lingette", "coffret", "cadeau", "kit", "ballerine",
        "basket", "بيبرون", "لباس", "حذاء", "جوارب", "حفاض", "لعبة",
    }
    _EXCLUDE = {
        "catalogue", "commander", "commande", "livraison", "paiement",
        "bonjour", "merci", "aide",
        "الكتالوج", "كتالوج", "الاسعار", "طلب", "توصيل",
    }
    _tl = text.lower()
    _has_kw = any(kw in _tl for kw in _PRODUCT_KW)
    _has_age = any(p in _tl for p in ["mois", " ans", "bébé", "bebe"])
    _has_price = any(p in _tl for p in ["moins de", "plus de", "max", "budget"])
    _has_excl = any(w in _tl for w in _EXCLUDE)

    if (_has_kw or _has_age or _has_price) and not _has_excl and not _in_session(session_id):
        from .catalog import smart_search
        return smart_search(text)

    # ── Détection catégorie ──────────────────────────────────────────
    if not _in_session(session_id) and not _has_excl:
        _CAT_ALIASES = {
            "ملابس": "Vêtements", "vetements": "Vêtements",
            "حذاء": "Chaussures", "chaussure": "Chaussures & Chaussettes",
            "جوارب": "Chaussures & Chaussettes",
            "العاب": "Jouets & Éveil", "jouet": "Jouets & Éveil",
            "نظافة": "Hygiène & Soin", "hygiene": "Hygiène & Soin",
            "هدايا": "Coffrets & Cadeaux", "cadeau": "Coffrets & Cadeaux",
            "حفاضات": "Linge & Couches", "couche": "Linge & Couches",
            "رضاعة": "Alimentation bébé", "biberon": "Alimentation bébé",
            "عربية": "Puériculture",
        }
        matched_cat = None
        for cat in get_categories():
            if cat.lower() in _tl or _tl in cat.lower():
                matched_cat = cat
                break
        if not matched_cat:
            for alias, cat in _CAT_ALIASES.items():
                if alias in _tl:
                    matched_cat = cat
                    break
        if matched_cat:
            results = search_products(category=matched_cat, limit=5)
            return format_search_results(results, query=matched_cat)

    # ── NLP ──────────────────────────────────────────────────────────
    intent = classifier.predict(text)

    # ── Détection par mots-clés (complète le NLP) ────────────────────
    _KEYWORD_INTENT: dict[str, tuple[str, ...]] = {
        "hours": (
            "fermeture", "fermé", "ferme", "ouverture", "ouvert", "ouvre",
            "horaire", "horaires", "heure", "heures", "schedule",
            "مواعيد", "وقت الفتح", "مغلق", "مفتوح", "ساعات",
        ),
        "location": (
            "localisation", "adresse", "emplacement", "situé", "où êtes",
            "ou etes", "magasin", "boutique", "trouver", "venir",
            "عنوان", "اين", "وين", "محل", "متجر", "لوكاليزاسيون",
        ),
        "delivery": (
            "livraison", "livrer", "livreur", "wilaya", "wilayas", "délai",
            "frais", "transport", "expédition",
            "توصيل", "يوصل", "ديليفري", "ولاية",
        ),
        "payment": (
            "paiement", "payer", "règlement", "virement", "ccp", "baridimob",
            "دفع", "فلوس", "تسديد", "بريدي موب",
        ),
        "discount": (
            "promo", "promotion", "réduction", "solde", "remise", "offre",
            "تخفيض", "برومو", "سولد",
        ),
        "warranty": (
            "garantie", "retour", "échange", "remboursement", "défaut",
            "ضمان", "ترجيع", "تبديل",
        ),
    }
    if not _in_session(session_id):
        for _kw_intent, _kws in _KEYWORD_INTENT.items():
            if any(kw in _tl or kw in text for kw in _kws):
                _kw_reply = reply_for(_kw_intent, message=text, client=client_profile, lang=lang)
                if _kw_reply:
                    return _kw_reply

    # ── NLP ──────────────────────────────────────────────────────────
    # ── Flux commande ─────────────────────────────────────────────────
    if intent == "order_start" or _in_session(session_id):
        _BAILOUT = {
            "bonjour", "bonsoir", "salut", "salam", "hi", "hello",
            "stop", "annuler", "quitter", "cancel", "menu",
            "aide", "help", "retour", "accueil",
            "catalogue", "livraison", "paiement", "prix",
            # Arabe / Darija
            "سلام", "مرحبا", "اهلا", "هلا", "السلام عليكم", "سلام عليكم",
            "صباح الخير", "مساء الخير", "مع السلامة", "باي", "خلاص",
        }
        _is_bailout = (
            text.strip().lower() in _BAILOUT
            or text.strip() in _BAILOUT
            or intent in ("greeting", "goodbye", "cancel_order")
            or _forced_intent in ("greeting", "goodbye")  # salutation arabe détectée
        )
        if _is_bailout and _in_session(session_id):
            reset_session(session_id)
            return reply_for("greeting", message=text, client=client_profile, lang=lang) or "Comment puis-je vous aider ?"

        reply = process(session_id, text, intent)
        if reply == "CONFIRMED":
            order = _get_order(session_id)
            send_order_email(order)
            try:
                upsert_client(session_id, order.name, order.address, order.payment)
                save_order(session_id, order.name, order.address,
                           order.items, order.total, order.payment)
            except Exception as e:
                logger.error("Erreur sauvegarde commande web : %s", e)
            reset_session(session_id)
            return (
                "✅ *Commande confirmée et enregistrée !*\n"
                "Notre équipe vous contactera pour la livraison.\n"
                "Merci de votre confiance 🙏"
            )
        if reply:
            return reply

    # ── Réponse standard ─────────────────────────────────────────────
    response = reply_for(intent, message=text, client=client_profile, lang=lang)
    if response:
        return response

    # ── Fallback recherche ───────────────────────────────────────────
    if count_products() > 0:
        params = parse_search_query(text)
        kw = params.get("keyword", "")
        if kw and max((len(w) for w in kw.split()), default=0) < 4:
            kw = ""
        if kw or params.get("age_hint") or params.get("max_price"):
            results = search_products(keyword=kw, limit=5)
            if results:
                return format_search_results(results, query=kw or text)
            return (
                f"😕 Aucun résultat pour *\"{text}\"*.\n\n"
                "Essayez d'autres mots, ou tapez *catalogue* pour voir les catégories."
            )

    return (
        "Désolé, je n'ai pas bien compris 😅.\n"
        "Demandez-moi : *produits*, *prix*, *livraison*, *paiement*, ou *je veux commander*."
    )


def _in_session(session_id: str) -> bool:
    from .database import load_order_session
    from .order import ST_NEW
    data = load_order_session(session_id)
    return data is not None and data.get("state", ST_NEW) != ST_NEW


def _get_order(session_id: str):
    from .order import get_session
    return get_session(session_id)["order"]
