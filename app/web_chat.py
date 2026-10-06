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
    from .database import get_client, touch_client, upsert_client, save_order, log_message

    text = text.strip()
    if not text:
        return "Bonjour ! Comment puis-je vous aider ? 😊"

    # ── Journal : helper pour logger + retourner ─────────────────────
    def _log(reply: str, intent: str = "unknown", confidence: float = 0.0,
             method: str = "direct") -> str:
        try:
            log_message(
                text=text, intent=intent, confidence=confidence, method=method,
                responded=bool(reply and "Aucun résultat" not in reply and "pas bien compris" not in reply),
                session_id=session_id, source="web",
            )
        except Exception:
            pass
        return reply


    # ── Normalisation (arabizi, diacritiques, élongations) ───────────
    from .normalize import normalize, detect_lang
    text_norm = normalize(text)   # version normalisée pour la comparaison
    lang = "ar" if detect_lang(text) in ("ar", "arabizi") else "fr"

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
    _tl = text_norm  # texte normalisé (arabizi converti, diacritiques supprimés)
    _has_kw = any(kw in _tl for kw in _PRODUCT_KW)
    _has_age = any(p in _tl for p in ["mois", " ans", "bébé", "bebe", "شهر", "سنه"])
    _has_price = any(p in _tl for p in ["moins de", "plus de", "max", "budget", "bchhal", "شحال"])
    _has_excl = any(w in _tl for w in _EXCLUDE)

    if (_has_kw or _has_age or _has_price) and not _has_excl and not _in_session(session_id):
        from .catalog import smart_search
        return _log(smart_search(text_norm), intent="product_search", confidence=1.0, method="keyword")


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
            return _log(format_search_results(results, query=matched_cat), intent="category_search", confidence=1.0, method="keyword")


    # ── NLP ──────────────────────────────────────────────────────────
    intent = classifier.predict(text)

    # ── Capturer la confiance NLP ────────────────────────────────────
    _nlp_conf = 0.0
    _nlp_method = "pattern"
    try:
        from .darija.lexicon import _predict
        _pr = _predict(text)
        _nlp_conf = _pr.confidence
        _nlp_method = _pr.method
    except Exception:
        pass

    # ── Détection par mots-clés (complète le NLP) ────────────────────
    _KEYWORD_INTENT: dict[str, tuple[str, ...]] = {
        "hours": (
            "fermeture", "fermé", "ferme", "ouverture", "ouvert", "ouvre",
            "horaire", "horaires", "heure", "heures", "schedule",
            # Arabe standard
            "مواعيد", "وقت الفتح", "مغلق", "مفتوح", "ساعات", "يفتح", "يسكر",
            # Darija (après normalisation arabizi)
            "مسكر", "مسكار", "مسكار", "يفتحو", "يسكرو", "مفتوح",
            # Arabizi direct (avant normalisation)
            "msakker", "msaker", "msakar", "mftu7", "meftou7", "meftuh",
            "sa3a", "sa3at", "waqt", "wa9t", "lyom",
        ),
        "location": (
            "localisation", "adresse", "emplacement", "situé", "où êtes",
            "ou etes", "magasin", "boutique", "trouver", "venir",
            "boudouaou", "boumerdes", "boumerdès",
            # Arabe
            "عنوان", "اين", "وين", "محل", "متجر", "لوكاليزاسيون",
            # Arabizi
            "wein", "fin lmahal", "fin lboutique",
        ),
        "delivery": (
            "livraison", "livrer", "livreur", "wilaya", "wilayas", "délai",
            "frais", "transport", "expédition",
            # Arabe / Darija
            "توصيل", "يوصل", "ديليفري", "ولاية", "يوصلو",
            # Arabizi
            "twassal", "tawsil", "wila9a",
        ),
        "payment": (
            "paiement", "payer", "règlement", "virement", "ccp", "baridimob",
            # Arabe / Darija
            "دفع", "فلوس", "تسديد", "بريدي موب", "دفعه",
            # Arabizi
            "flous", "dfou3", "d9ou3",
        ),
        "discount": (
            "promo", "promotion", "réduction", "solde", "remise", "offre",
            "تخفيض", "برومو", "سولد", "عروض",
        ),
        "warranty": (
            "garantie", "retour", "échange", "remboursement", "défaut",
            "ضمان", "ترجيع", "تبديل", "رجع",
        ),
    }
    if not _in_session(session_id):
        for _kw_intent, _kws in _KEYWORD_INTENT.items():
            # Vérifie dans le texte normalisé ET dans le texte original (arabizi brut)
            if any(kw in _tl or kw in text.lower() for kw in _kws):
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

    # ── Intent produit_* du lexique darija ─────────────────────────────
    if intent.startswith("produit_") and not _in_session(session_id):
        slug = intent.replace("produit_", "").replace("_", " ")

        # Mapping darija → mots-clés français pour la recherche catalogue
        _DARIJA_FR = {
            # Alimentation bébé
            "rda3a": "biberon", "reda3a": "biberon", "bibrou": "biberon",
            "biberou": "biberon", "biberon": "biberon",
            "sucette": "sucette", "tottota": "sucette", "totota": "sucette",
            "tetine": "tétine", "tetina": "tétine",
            # Vêtements
            "serwal": "pantalon", "sarwal": "pantalon", "sarwel": "pantalon",
            "serwel": "pantalon", "pantalon": "pantalon",
            "roba": "robe", "robe": "robe", "keswa": "robe",
            "tricou": "t-shirt", "trikou": "t-shirt", "tshirt": "t-shirt",
            "gilet": "gilet", "jilet": "gilet", "gileh": "gilet",
            "veste": "veste", "jaquette": "veste", "vest": "veste",
            "pyjama": "pyjama", "bijama": "pyjama",
            "body": "body", "bodi": "body",
            "bavette": "bavoir", "bavoir": "bavoir", "baveta": "bavoir",
            "kombinezon": "combinaison", "combinaison": "combinaison",
            "jogging": "jogging", "training": "jogging",
            "short": "short", "calecon": "short",
            "manteau": "manteau", "manto": "manteau", "kabbout": "manteau",
            "pull": "pull", "tricot": "pull",
            "chaussette": "chaussette", "jwareb": "chaussette", "chosette": "chaussette",
            "ensemble": "ensemble", "taqm": "ensemble",
            # Chaussures
            "sabbat": "chaussure", "chaussure": "chaussure", "hdiya": "chaussure",
            "sabat": "chaussure", "sbbat": "chaussure",
            "sandale": "sandale", "sandala": "sandale",
            "basket": "basket", "baskit": "basket",
            "ballerine": "ballerine", "balerina": "ballerine",
            # Puériculture
            "kerrousa": "poussette", "karroussa": "poussette", "poussette": "poussette",
            "kouchat": "couche", "couche": "couche", "kouchet": "couche",
            "bsiklit": "tricycle", "bsiklat": "tricycle", "tricycle": "tricycle",
            "baniou": "baignoire", "baignoire": "baignoire",
            "chaise": "chaise haute", "korsi": "chaise haute",
            # Jouets
            "7wija": "jouet", "la3ba": "jouet", "jouet": "jouet", "laba": "jouet",
            "doudou": "peluche", "peluche": "peluche",
            "hochet": "hochet",
            # Hygiène
            "saboun": "savon", "savon": "savon",
            "creme": "crème", "krem": "crème",
            "chompoing": "shampoing", "shampoing": "shampoing", "champo": "shampoing",
            "lingette": "lingette",
            # Cadeaux
            "dekkane": "coffret", "coffret": "coffret", "cadeau": "cadeau",
            "hdia": "cadeau", "hdiya": "cadeau",
            # Linge
            "couverture": "couverture", "ghta": "couverture",
            "couette": "couette",
        }
        fr_kw = _DARIJA_FR.get(slug.strip(), "")

        # ── Fallback dynamique : chercher le mot FR dans le lexique ───
        if not fr_kw:
            try:
                from .darija import lexicon as lex_mod
                lex_data = lex_mod._load()
                for e in lex_data.values():
                    if e.get("target") == intent:
                        # Chercher un mot français dans les patterns
                        for p in e.get("patterns", []):
                            p_low = p.lower().strip()
                            if p_low and p_low != slug and not any("\u0600" <= c <= "\u06FF" for c in p_low):
                                fr_kw = p_low
                                break
                        break
            except Exception:
                pass

        from .database import search_products

        # 1) Cherche avec le mot français mappé
        if fr_kw:
            result = smart_search(fr_kw)
            if result and "Aucun résultat" not in result:
                return _log(result, intent=intent, confidence=_nlp_conf, method=_nlp_method)

        # 2) Cherche avec le slug brut
        result = smart_search(slug)
        if result and "Aucun résultat" not in result:
            return _log(result, intent=intent, confidence=_nlp_conf, method=_nlp_method)

        # 3) Cherche le mot original dans le lexique
        try:
            from .darija import lexicon as lex_mod
            lex_data = lex_mod._load()
            for e in lex_data.values():
                if e.get("target") == intent:
                    for w in (e.get("word", ""), e.get("word_ar", "")):
                        if w and w != slug:
                            result = smart_search(w)
                            if result and "Aucun résultat" not in result:
                                return _log(result, intent=intent, confidence=_nlp_conf, method=_nlp_method)
                    break
        except Exception:
            pass

        # 4) Recherche directe dans la base
        results = search_products(keyword=fr_kw or slug, limit=5)
        if results:
            return _log(format_search_results(results, query=slug), intent=intent, confidence=_nlp_conf, method=_nlp_method)

        # Dernier fallback
        return _log(
            f"🔍 Vous cherchez *{slug}* ?\n"
            f"Je n'ai pas trouvé ce produit exact dans le catalogue.\n\n"
            f"Tapez *catalogue* pour voir toutes nos catégories, "
            f"ou décrivez le produit autrement 😊",
            intent=intent, confidence=_nlp_conf, method=_nlp_method
        )


    # ── Réponse standard ─────────────────────────────────────────────
    response = reply_for(intent, message=text, client=client_profile, lang=lang)
    if response:
        return _log(response, intent=intent, confidence=_nlp_conf, method=_nlp_method)

    # ── Fallback recherche ───────────────────────────────────────────
    if count_products() > 0:
        params = parse_search_query(text)
        kw = params.get("keyword", "")
        if kw and max((len(w) for w in kw.split()), default=0) < 4:
            kw = ""
        if kw or params.get("age_hint") or params.get("max_price"):
            results = search_products(keyword=kw, limit=5)
            if results:
                return _log(format_search_results(results, query=kw or text), intent=intent, confidence=_nlp_conf, method=_nlp_method)
            return _log(
                f"😕 Aucun résultat pour *\"{text}\"*.\n\n"
                "Essayez d'autres mots, ou tapez *catalogue* pour voir les catégories.",
                intent="fallback", confidence=_nlp_conf, method=_nlp_method
            )

    return _log(
        "Désolé, je n'ai pas bien compris 😅.\n"
        "Demandez-moi : *produits*, *prix*, *livraison*, *paiement*, ou *je veux commander*.",
        intent="fallback", confidence=_nlp_conf, method=_nlp_method
    )



def _in_session(session_id: str) -> bool:
    from .database import load_order_session
    from .order import ST_NEW
    data = load_order_session(session_id)
    return data is not None and data.get("state", ST_NEW) != ST_NEW


def _get_order(session_id: str):
    from .order import get_session
    return get_session(session_id)["order"]
