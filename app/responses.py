# ============================================================
#  Générateur de réponses selon l'intention détectée
# ============================================================
from .catalog import (
    format_catalog,
    get_delivery,
    get_payment,
    get_products,
    get_store,
    find_product,
)


def _delivery_text() -> str:
    d = get_delivery()
    lines = [
        "🚚 *Livraison* :",
        f"• Frais : {d['price']} DZD",
        f"• Gratuite dès {d['free_above']} DZD d'achat",
        f"• Zones : {', '.join(d['zones'])}",
        f"• Délai : {d['delay']}",
    ]
    return "\n".join(lines)


def _payment_text() -> str:
    lines = ["💳 *Moyens de paiement* :"]
    lines += [f"• {p}" for p in get_payment()]
    return "\n".join(lines)


def reply_for(intent: str, message: str = "", client: dict | None = None, lang: str = "fr") -> str | None:
    """Retourne la réponse pour une intention. lang='ar' pour arabe/darija."""
    s = get_store()
    _ar = lang == "ar"

    if intent == "greeting":
        if client and client.get("name"):
            name = client["name"]
            count = client.get("order_count", 0)
            if count >= 1:
                if _ar:
                    return (
                        f"مرحبا *{name}* ! 🎉 يسعدنا عودتك !\n"
                        f"_(راك دارت {count} طلب{'ات' if count > 1 else ''} معانا)_\n\n"
                        "واش تحب :\n"
                        "• 📦 الكتالوج / الأسعار\n"
                        "• 🚚 التوصيل\n"
                        "• 💳 الدفع\n"
                        "• 🛒 تطلب"
                    )
                return (
                    f"Bon retour *{name}* ! 🎉 Content de vous revoir !\n"
                    f"_(Vous avez passé {count} commande{'s' if count > 1 else ''} chez nous)_\n\n"
                    "Comment puis-je vous aider aujourd'hui ?\n"
                    "• 📦 Catalogue / Prix\n"
                    "• 🚚 Livraison\n"
                    "• 💳 Paiement\n"
                    "• 🛒 Commander"
                )
        if _ar:
            return (
                f"وعليكم السلام 👋 أهلا بك في *{s['name']}* !\n\n"
                "نقدر نعاونك في :\n"
                "• 📦 الكتالوج / الأسعار\n"
                "• 🚚 التوصيل\n"
                "• 💳 طريقة الدفع\n"
                "• 🛒 تسجيل طلب\n\n"
                "اكتب سؤالك مباشرة 😊"
            )
        # Bonjour ou Bonsoir selon le message
        salut = "Bonsoir" if "soir" in message.lower() else "Bonjour"
        return (
            f"{salut} 👋 Bienvenue chez *{s['name']}* !\n\n"
            "Je peux vous aider avec :\n"
            "• 📦 Le catalogue / les prix\n"
            "• 🚚 La livraison\n"
            "• 💳 Le paiement\n"
            "• 🛒 Passer une commande\n\n"
            "Écrivez simplement votre question 😊"
        )


    if intent == "goodbye":
        return "مع السلامة ! 👋 نتمنالك يوم زين" if _ar else "Merci et à bientôt ! 👋"

    if intent == "thanks":
        return "العفو 😊 أي سؤال آخر ؟" if _ar else "Avec plaisir ! 😊 N'hésitez pas si vous avez d'autres questions."

    if intent == "products":
        return format_catalog()

    if intent in ("prices", "product_info", "availability", "search"):
        from .catalog import parse_search_query, smart_search
        params = parse_search_query(message) if message else {}
        return smart_search(
            keyword=params.get("keyword", ""),
            max_price=params.get("max_price", 0),
            min_price=params.get("min_price", 0),
            age_hint=params.get("age_hint", ""),
            limit=5,
        )

    if intent == "delivery":
        if _ar:
            d = get_delivery()
            return (
                f"🚚 *التوصيل* :\n"
                f"• الثمن : {d['price']} دج\n"
                f"• مجاني من : {d['free_above']} دج\n"
                f"• المناطق : {', '.join(d['zones'])}\n"
                f"• المدة : {d['delay']}"
            )
        return _delivery_text()

    if intent == "payment":
        if _ar:
            lines = ["💳 *طرق الدفع* :"]
            lines += [f"• {p}" for p in get_payment()]
            return "\n".join(lines)
        return _payment_text()

    if intent == "hours":
        if _ar:
            return "🕘 *أوقات العمل* :\n• الاثنين – السبت : 9h – 19h\n• الأحد : مغلق\n(الطلبات عبر واتساب 24/24 😊)"
        return "🕘 *Horaires d'ouverture* :\n• Lun–Sam : 9h00 – 19h00\n• Dimanche : fermé\n(Commandes WhatsApp 24h/24 😊)"

    if intent == "location":
        return "📍 Notre adresse : Centre-ville, Algérie.\n(Vous pouvez aussi commander via WhatsApp, nous livrons chez vous !)"

    if intent == "contact_human":
        return (
            "Bien sûr ! Je vais transmettre votre demande à notre responsable 📞\n"
            "Il vous recontactera très vite. Merci de votre patience 🙏"
        )

    if intent == "track_order":
        return (
            "📦 Pour suivre votre commande, merci de me donner votre *numéro de commande* "
            "(ou votre nom complet) et je vérifie tout de suite."
        )

    if intent == "complaint":
        return (
            "Désolé pour ce désagrément 😟 Je transmets immédiatement votre réclamation à notre "
            "responsable qui vous recontactera pour un remplacement ou remboursement."
        )

    if intent == "cancel_order":
        return (
            "Merci de me donner votre *numéro de commande* afin que je puisse annuler la commande, "
            "et notre équipe confirmera l'annulation."
        )

    if intent == "size_help":
        return (
            "📏 Pour bien choisir votre taille :\n"
            "• Vêtements : S, M, L, XL, XXL (consultez le guide des tailles)\n"
            "• Chaussures : pointures 39 à 45\n"
            "En cas de doute, précisez-moi votre pointure/taille et je vérifie la disponibilité 😊"
        )

    if intent == "warranty":
        return (
            "🛡️ *Garantie* :\n"
            "• 6 mois de garantie sur tous nos produits\n"
            "• Échange gratuit en cas de défaut dans les 7 jours\n"
            "Pour un échange, contactez-nous avec votre commande."
        )

    if intent == "discount":
        return (
            "🎁 Actuellement, nous proposons des promotions sur certains produits et "
            "la livraison gratuite dès un certain montant d'achat.\n"
            "Consultez notre catalogue et dites-moi ce qui vous intéresse, je vérifie les offres !"
        )

    if intent == "recharge":
        return (
            "📱 *Recharge / Filiyo* :\n"
            "• Nous proposons la recharge téléphonique (Filiyo, Nedjma, Ooredoo, Djezzy)\n"
            "• Indiquez-moi le *numéro* et le *montant* souhaité, je m'occupe du reste !\n"
            "Exemple : *recharge 0550 12 34 56 de 500 DA*"
        )

    if intent == "points_de_vente":
        return (
            "📍 *Points de vente* :\n"
            "• Boutique principale : Alger centre\n"
            "• Nous livrons dans plusieurs wilayas : Algérie, Oran, Constantine, Annaba\n"
            "Précisez-moi votre wilaya, je vous indique le point de vente le plus proche ou la livraison 😊"
        )

    if intent == "echange_conditions":
        return (
            "🔄 *Conditions d'échange & retour* :\n"
            "• Échange ou retour possible sous 7 jours\n"
            "• Produit non utilisé et emballage intact\n"
            "• Pour un produit défectueux : échange ou remboursement sans frais\n"
            "Contactez-nous avec votre numéro de commande pour lancer l'échange."
        )

    if intent == "produits_specifiques":
        return (
            "🏷️ Nous proposons plusieurs marques et nouveautés.\n"
            "Dites-moi quel produit ou quelle marque vous cherchez, "
            "et je vous dis si c'est disponible !\n"
            "(ou demandez le *catalogue* complet)"
        )

    if intent == "solde_carte":
        return (
            "💳 *Carte / solde* :\n"
            "• Nous proposons des cartes de fidélité et le rechargement de comptes.\n"
            "Indiquez-moi ce dont vous avez besoin, je vérifie la disponibilité."
        )

    # Intentions traitées par la machine à états de commande :
    if intent in ("order_start",):
        return None  # signal à la machine à états

    return None
