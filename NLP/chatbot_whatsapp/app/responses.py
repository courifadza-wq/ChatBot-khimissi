"""Réponses par intention (FR / AR-derja). Les familles produits sont générées dynamiquement."""
from __future__ import annotations

from .catalog import catalog
from .config import settings
from .nlp import detect_lang

HUMAN = settings.HUMAN_PHONE or ""


def _h(lang: str) -> str:
    if not HUMAN:
        return ""
    return (f"\n📞 للاستعجال: {HUMAN}" if lang == "ar" else f"\n📞 Urgent : {HUMAN}")


# --------------------------------------------------------------------------
#  Réponses statiques  {intent: {"fr": ..., "ar": ...}}
# --------------------------------------------------------------------------
R: dict[str, dict[str, str]] = {
    "greeting": {
        "fr": "Bonjour et bienvenue chez {store} 👋\nJe peux vous renseigner sur nos produits, les prix, la livraison — ou enregistrer votre commande.\nQue cherchez-vous ?",
        "ar": "السلام عليكم ومرحبا بيك في {store} 👋\nنقدر نعاونك في المنتجات، الأسعار، التوصيل، ولا نسجلك طلبية.\nواش تحوس عليه؟",
    },
    "goodbye": {
        "fr": "Merci de votre visite 🙏 À bientôt chez {store} !",
        "ar": "شكرا على زيارتك 🙏 نتلاقاو في {store}!",
    },
    "thanks": {
        "fr": "Avec plaisir 😊 Autre chose ?",
        "ar": "العفو 😊 تحب حاجة أخرى؟",
    },
    "affirm": {"fr": "Parfait 👍", "ar": "مليح 👍"},
    "deny": {"fr": "Très bien, dites-moi ce qui vous conviendrait.", "ar": "ماشي مشكل، قولي واش يناسبك."},
    "bot_challenge": {
        "fr": "Je suis l'assistant automatique de {store} 🤖. Je peux aussi vous passer un conseiller.",
        "ar": "أنا المساعد الآلي تاع {store} 🤖. نقدر نحولك لمستشار إذا حبيت.",
    },
    "help_menu": {
        "fr": "Je peux vous aider à :\n1️⃣ Voir les produits et les prix\n2️⃣ Vérifier la disponibilité\n3️⃣ Connaître la livraison et le paiement\n4️⃣ Passer une commande\n5️⃣ Suivre une commande\n\nÉcrivez par exemple : « je veux commander » ou « bchhal biberon ».",
        "ar": "نقدر نعاونك في:\n1️⃣ المنتجات والأسعار\n2️⃣ التوفر\n3️⃣ التوصيل والدفع\n4️⃣ تسجيل طلبية\n5️⃣ متابعة طلبية\n\nاكتب مثلا: «بغيت نطلب» ولا «بشحال البيبرون».",
    },
    "repeat": {"fr": "Je reformule : que souhaitez-vous exactement — un produit, un prix, ou une commande ?",
               "ar": "نعاودلك: واش تحب بالضبط — منتج، ثمن، ولا طلبية؟"},
    "waiting": {"fr": "Je reste disponible, prenez votre temps 🙂", "ar": "راني هنا، خود وقتك 🙂"},
    "compliment": {"fr": "Merci beaucoup, ça fait plaisir 🙏", "ar": "شكرا بزاف، يعيشك 🙏"},
    "insult": {"fr": "Je comprends votre mécontentement. Je transmets immédiatement à un responsable.",
               "ar": "فهمت انزعاجك. راني نحول القضية لمسؤول دروك."},
    "language_preference": {"fr": "Écrivez-moi en français, arabe ou derja — je comprends les trois 🙂",
                            "ar": "اكتبلي بالعربية، بالدارجة ولا بالفرنسية — نفهم الثلاثة 🙂"},

    # ---------- catalogue ----------
    "products": {"fr": "{catalog}", "ar": "{catalog}"},
    "product_categories": {"fr": "{catalog}", "ar": "{catalog}"},
    "produits_specifiques": {
        "fr": "Dites-moi la marque ou le type d'article et je vérifie tout de suite dans le stock.",
        "ar": "قولي الماركة ولا نوع المنتج ونشوفلك في المخزون دروك.",
    },
    "product_info": {"fr": "Donnez-moi le nom ou la référence du produit, je vous envoie le détail 👍",
                     "ar": "عطيني اسم المنتج ولا المرجع، نبعثلك التفاصيل 👍"},
    "prices": {"fr": "Dites-moi quel article vous intéresse et je vous donne le prix exact 💰\n(ex : « bchhal biberon », « prix tablier »)",
               "ar": "قولي على أي منتج ونعطيك الثمن بالضبط 💰\n(مثال: «بشحال البيبرون»، «ثمن المريول»)"},
    "availability": {"fr": "Donnez-moi le nom ou la référence et je vérifie le stock en direct 📦",
                     "ar": "عطيني الاسم ولا المرجع ونشوفلك المخزون دروك 📦"},
    "quantity_available": {"fr": "Précisez l'article, je vous dis combien il en reste exactement.",
                           "ar": "حدد المنتج، نقولك شحال باقي بالضبط."},
    "size_help": {"fr": "Nos vêtements vont du nouveau-né au 16 ans, les chaussures de la pointure 15 à 37.\nDonnez-moi l'âge de l'enfant et je vous propose la bonne taille 👕",
                  "ar": "الحوايج عندنا من المولود حتى 16 سنة، والصباط من قياس 15 حتى 37.\nعطيني عمر الطفل ونقترحلك القياس المناسب 👕"},
    "colors": {"fr": "Dites-moi le modèle et la couleur souhaitée, je vérifie ce qui est disponible 🎨",
               "ar": "قولي الموديل واللون اللي تحب، ونشوف واش متوفر 🎨"},
    "photos_request": {"fr": "Je vous envoie les photos du produit — précisez la référence 📸",
                       "ar": "نبعثلك تصاور المنتج — عطيني المرجع 📸"},

    # ---------- logistique ----------
    "delivery": {"fr": "{delivery}", "ar": "{delivery}"},
    "delivery_wilaya": {"fr": "{delivery}", "ar": "{delivery}"},
    "delivery_time": {"fr": "{delivery}", "ar": "{delivery}"},
    "delivery_mode": {"fr": "{delivery}\n\n📍 Au choix : livraison à domicile ou retrait au bureau (stop desk).",
                      "ar": "{delivery}\n\n📍 على حسابك: توصيل للدار ولا سحب من المكتب (ستوب ديسك)."},
    "free_delivery": {"fr": "{delivery}", "ar": "{delivery}"},
    "delivery_company": {"fr": "Nous expédions via nos partenaires (Yalidine / ZR Express) vers les 58 wilayas.",
                         "ar": "نبعثو مع الشركاء (يالدين / ZR Express) لـ 58 ولاية."},
    "payment": {"fr": "{payment}", "ar": "{payment}"},
    "payment_methods_local": {"fr": "{payment}", "ar": "{payment}"},
    "installment_payment": {"fr": "Le paiement se fait en une fois (à la livraison ou en ligne). Pour un gros volume, un acompte est possible — je vous mets en relation avec le responsable.",
                            "ar": "الدفع يكون دفعة وحدة (عند التسليم ولا أونلاين). للكميات الكبيرة ممكن تسبيق — نحولك للمسؤول."},
    "invoice": {"fr": "Oui, nous délivrons une facture. Donnez-moi la raison sociale et le NIF et je transmets 🧾",
                "ar": "إيه، نوفرو فاتورة. عطيني اسم الشركة والرقم الجبائي ونمرر الطلب 🧾"},
    "hours": {"fr": "🕘 Samedi → jeudi : 9h00 – 21h00\n🕝 Vendredi : 14h30 – 21h00\nLe bot, lui, répond 24h/24 🙂",
              "ar": "🕘 من السبت للخميس: 9:00 – 21:00\n🕝 الجمعة: 14:30 – 21:00\nأما البوت يجاوب 24/24 🙂"},
    "closed_days": {"fr": "Ouvert 7j/7. Le vendredi, uniquement l'après-midi : 14h30 – 21h00. Horaires spéciaux en Ramadan.",
                    "ar": "محلولين 7 أيام. نهار الجمعة غير العشية: 14:30 – 21:00. في رمضان التوقيت يتبدل."},
    "location": {"fr": "📍 Planet Kids — Rue des Frères Aoudia, Boudouaou (Boumerdès).\n🕘 Sam–Jeu 9h–21h · Ven 14h30–21h\n☎️ +213 554 69 87 46\nNous livrons aussi partout en Algérie 🚚",
                 "ar": "📍 بلانيت كيدز — شارع إخوان عودية، بودواو (بومرداس).\n🕘 السبت–الخميس 9:00–21:00 · الجمعة 14:30–21:00\n☎️ 0554 69 87 46\nونوصلو لكامل الوطن 🚚"},
    "points_de_vente": {"fr": "Notre magasin : Rue des Frères Aoudia, Boudouaou (Boumerdès) — et la livraison partout en Algérie. Indiquez votre wilaya 🙂",
                        "ar": "المحل: شارع إخوان عودية، بودواو (بومرداس) — والتوصيل لكامل الوطن. قولي ولايتك 🙂"},
    "phone_contact": {"fr": "Vous pouvez nous écrire ici sur WhatsApp à tout moment." + (f"\n📞 {HUMAN}" if HUMAN else ""),
                      "ar": "تقدر تكتبلنا هنا في الواتساب في أي وقت." + (f"\n📞 {HUMAN}" if HUMAN else "")},
    "social_media": {"fr": "📱 Retrouvez-nous :\n• Instagram : @planetekids_\n• Facebook : Planet Kids\n• TikTok : @planetkids_\n• Site : khemicishop.com",
                     "ar": "📱 تلقاونا في:\n• انستغرام: @planetekids_\n• فيسبوك: Planet Kids\n• تيك توك: @planetkids_\n• الموقع: khemicishop.com"},
    "website_online": {"fr": "🌐 Notre boutique en ligne : khemicishop.com — ou commandez directement ici, c'est le plus rapide 🚀",
                       "ar": "🌐 متجرنا على الأنترنت: khemicishop.com — ولا اطلب مباشرة هنا، هذا أسرع 🚀"},

    # ---------- commercial ----------
    "discount": {"fr": "🎁 Nous avons régulièrement des promotions et des prix dégressifs par quantité.\nDites-moi ce qui vous intéresse et je vérifie les offres en cours.",
                 "ar": "🎁 دايما عندنا تخفيضات وأسعار خاصة حسب الكمية.\nقولي واش يهمك ونشوفلك العروض الموجودة."},
    "price_negotiation": {"fr": "Nos prix sont déjà serrés 🙂 Mais à partir de plusieurs pièces, je peux demander un geste au responsable.",
                          "ar": "أسعارنا مدروسة 🙂 بصح إذا خذيت كمية، نقدر نطلب تخفيض من المسؤول."},
    "wholesale": {"fr": "Oui, nous faisons la vente en gros 📦 Donnez-moi les articles et les quantités, je vous fais un devis.",
                  "ar": "إيه، نبيعو بالجملة 📦 عطيني المنتجات والكميات، ونحضرلك عرض سعر."},
    "loyalty_program": {"fr": "Nos clients réguliers bénéficient d'avantages — parlez-en au responsable lors du retrait.",
                        "ar": "الزبائن الدائمين عندهم امتيازات — هدر مع المسؤول وقت السحب."},
    "produit_en_promo": {"fr": "Dites-moi le rayon qui vous intéresse (vêtements, chaussures, puériculture…) et je vous liste ce qui est en promo.",
                         "ar": "قولي أي قسم يهمك (حوايج، صباط، مستلزمات بيبي...) ونوريك واش في البرومو."},

    # ---------- après-vente ----------
    "track_order": {"fr": "📦 Donnez-moi votre numéro de commande ou votre numéro de téléphone, je vérifie le suivi.",
                    "ar": "📦 عطيني رقم الطلبية ولا رقم الهاتف، ونشوفلك فين وصلت."},
    "cancel_order": {"fr": "Je transmets votre demande d'annulation. Donnez-moi votre numéro de commande ou de téléphone.",
                     "ar": "نمرر طلب الإلغاء. عطيني رقم الطلبية ولا رقم الهاتف."},
    "order_modify": {"fr": "Pas de souci. Indiquez votre numéro de commande et la modification souhaitée ✏️",
                     "ar": "ماشي مشكل. عطيني رقم الطلبية والتعديل اللي تحب ✏️"},
    "complaint": {"fr": "Je suis désolé pour ce désagrément 😔 Décrivez le problème (photo bienvenue), je transmets immédiatement au responsable.",
                  "ar": "نعتذرلك على هاد المشكل 😔 وصفلي المشكل (ابعث تصويرة إذا ممكن)، ونمرر دروك للمسؤول."},
    "delivery_delay_complaint": {"fr": "Désolé pour le retard 😔 Donnez-moi votre numéro de commande, je fais le point avec le transporteur.",
                                 "ar": "نعتذرو على التأخير 😔 عطيني رقم الطلبية ونتابع مع شركة التوصيل."},
    "delivery_failed": {"fr": "Pas de souci, on peut reprogrammer la livraison. Donnez-moi votre numéro de commande.",
                        "ar": "ماشي مشكل، نعاودو التوصيل. عطيني رقم الطلبية."},
    "echange_conditions": {"fr": "🔁 Échange possible sous 48h, article non utilisé et dans son emballage, avec le ticket.\nLes sous-vêtements et les sucettes ne sont pas échangeables (hygiène).",
                           "ar": "🔁 التبديل ممكن في 48 ساعة، المنتج ما مستعملش وفي علبته، مع الوصل.\nالملابس الداخلية والسوسيت ما يتبدلوش (نظافة)."},
    "refund": {"fr": "Le remboursement se fait après contrôle de l'article retourné. Donnez-moi votre numéro de commande.",
               "ar": "الاسترجاع يكون بعد مراقبة المنتج المرجّع. عطيني رقم الطلبية."},
    "warranty": {"fr": "🛡 Les articles électriques (tire-lait, chauffe-biberon, veilleuses…) sont garantis. Conservez bien votre ticket.",
                 "ar": "🛡 المنتجات الكهربائية (شافطة الحليب، سخان الرضاعة، الضوء الليلي...) عليها ضمان. احتفظ بالوصل."},
    "warranty_claim": {"fr": "Pour faire jouer la garantie : apportez l'article + le ticket, ou envoyez-moi une vidéo du défaut.",
                       "ar": "باش تستعمل الضمان: جيب المنتج + الوصل، ولا ابعثلي فيديو للعيب."},
    "contact_human": {"fr": "Je vous mets en relation avec un conseiller 👤 Il vous répond dans les plus brefs délais." + _h("fr"),
                      "ar": "راني نحولك لمستشار 👤 يجاوبك في أقرب وقت." + _h("ar")},
    "produit_indisponible": {"fr": "Si l'article est en rupture, je peux vous prévenir dès le réapprovisionnement. Vous voulez que je vous ajoute à la liste ?",
                             "ar": "إذا المنتج نفذ، نقدر نخبرك كي يوصل الجديد. تحب نزيدك في القائمة؟"},
    "stock_notify": {"fr": "D'accord, je note votre demande et je vous préviens dès l'arrivée 🔔",
                     "ar": "صافي، نسجل طلبك ونخبرك كي يوصل 🔔"},

    # ---------- recherche guidée ----------
    "recherche_par_age": {"fr": "Donnez-moi l'âge exact (ex : 6 mois, 2 ans, 8 ans) et le type d'article, je filtre le catalogue 👶",
                          "ar": "عطيني العمر بالضبط (مثلا 6 شهور، سنتين، 8 سنين) ونوع المنتج، ونفلترلك الكتالوج 👶"},
    "recherche_par_taille": {"fr": "Indiquez la taille ou la pointure et l'article recherché 📏",
                             "ar": "قولي القياس ولا البوانتير والمنتج اللي تحوس عليه 📏"},
    "recherche_par_genre": {"fr": "C'est pour une fille ou un garçon ? Et quel âge ?",
                            "ar": "للبنت ولا للولد؟ وشحال عمره؟"},
    "recherche_par_marque": {"fr": "Nous travaillons avec Chicco, Avent, Suavinex, Mustela, Biolane et des marques turques. Quelle marque cherchez-vous ?",
                             "ar": "نخدمو مع شيكو، أفنت، سوافينكس، موستيلا، بيولان وماركات تركية. أنهي ماركة تحوس عليها؟"},
    "recherche_par_budget": {"fr": "Donnez-moi votre budget et le type d'article, je vous propose ce qui rentre dedans 💰",
                             "ar": "عطيني الميزانية ونوع المنتج، ونقترحلك اللي يدخل فيها 💰"},
    "recherche_par_couleur_motif": {"fr": "Quelle couleur souhaitez-vous ? Et pour quel article ?",
                                    "ar": "أنهي لون تحب؟ وعلى أي منتج؟"},
    "recherche_par_saison": {"fr": "Été ou hiver ? Je vous sors la collection correspondante ☀️❄️",
                             "ar": "صيفي ولا شتوي؟ نخرجلك المجموعة المناسبة ☀️❄️"},
    "recherche_par_reference": {"fr": "Envoyez-moi la référence exacte, je la cherche dans le stock 🔎",
                                "ar": "ابعثلي المرجع بالضبط، ونقلبلك عليه في المخزون 🔎"},
    "pack_naissance": {"fr": "👶 Pack naissance : body, pyjama, nid d'ange, bavettes, serviette, biberon, sucette, brosse, couverture.\nJe peux vous préparer une liste complète selon votre budget.",
                       "ar": "👶 تجهيز المولود: بودي، بيجاما، نيد دانج، بافيت، سرفيت، بيبرون، سوسيت، فرشاة، غطاء.\nنقدر نحضرلك ليستة كاملة حسب ميزانيتك."},
    "rentree_scolaire": {"fr": "🎒 Rentrée scolaire : tabliers, cartables, chaussures, serviettes. Donnez-moi l'âge et je vous propose.",
                         "ar": "🎒 الدخول المدرسي: مرايل، كارطابل، صباط، سرفيات. عطيني العمر ونقترحلك."},

    # ---------- divers ----------
    "job_application": {"fr": "Merci de votre intérêt 🙂 Envoyez votre CV par email, nous revenons vers vous si un poste se libère.",
                        "ar": "شكرا على اهتمامك 🙂 ابعث السيفي بالإيميل، ونرجعولك إذا تحل بلاصة."},
    "partnership": {"fr": "Pour un partenariat ou une offre fournisseur, je transmets votre message au responsable 🤝",
                    "ar": "للشراكة ولا عرض مورد، نمرر رسالتك للمسؤول 🤝"},
    "influencer_ads": {"fr": "Pour toute collaboration, envoyez votre proposition — le responsable vous répondra.",
                       "ar": "لأي تعاون، ابعث عرضك — المسؤول يجاوبك."},
    "data_privacy": {"fr": "🔒 Vos informations servent uniquement à traiter la commande (nom, téléphone, adresse). Aucune diffusion à des tiers.",
                     "ar": "🔒 معلوماتك تستعمل غير باش نكملو الطلبية (الاسم، الهاتف، العنوان). ما نعطوهاش لحتى حد."},
    "newsletter": {"fr": "Je vous ajoute à la liste des nouveautés 🔔",
                   "ar": "نزيدك في قائمة الجديد 🔔"},
    "recharge": {"fr": "Dites-moi exactement quelle recharge vous voulez et je vérifie la disponibilité.",
                 "ar": "قولي بالضبط أنهي ريشارج تحب ونشوفلك واش متوفر."},
    "gift": {"fr": "🎁 Nous avons des coffrets cadeaux naissance et des emballages cadeau. Quel budget souhaitez-vous ?",
             "ar": "🎁 عندنا كوفري كادو للمولود وتغليف هدايا. شحال الميزانية؟"},
    "reservation": {"fr": "Je peux réserver l'article 24h. Donnez-moi la référence et votre nom 📝",
                    "ar": "نقدر نحجزلك المنتج 24 ساعة. عطيني المرجع واسمك 📝"},
    "minimum_order": {"fr": "Aucun minimum : vous pouvez commander une seule pièce 👍",
                      "ar": "ما كاين حتى حد أدنى: تقدر تطلب قطعة وحدة 👍"},
    "order_requirements": {"fr": "Pour enregistrer la commande il me faut : le produit, la quantité, votre nom, votre téléphone et l'adresse (wilaya + commune).",
                           "ar": "باش نسجل الطلبية نحتاج: المنتج، الكمية، اسمك، رقم الهاتف، والعنوان (الولاية + البلدية)."},
    "payment_proof": {"fr": "Envoyez la capture du versement ici, je la transmets au service commandes ✅",
                      "ar": "ابعث تصويرة الوصل هنا، ونمررها لمصلحة الطلبيات ✅"},
    "recommendation": {"fr": "Avec plaisir 🙂 Dites-moi l'âge de l'enfant, le type d'article et votre budget.",
                       "ar": "بكل سرور 🙂 قولي عمر الطفل، نوع المنتج والميزانية."},
    "product_comparison": {"fr": "Donnez-moi les deux références et je vous compare prix, taille et stock.",
                           "ar": "عطيني المرجعين ونقارنلك الثمن، القياس والمخزون."},
    "product_material": {"fr": "Précisez l'article : je vous donne la composition exacte indiquée par le fournisseur.",
                         "ar": "حدد المنتج: نعطيك المكونات بالضبط كيما جات من المورد."},
    "product_origin": {"fr": "Nous travaillons surtout avec des fournisseurs turcs et européens, et quelques marques locales.",
                       "ar": "نخدمو بالأغلب مع موردين أتراك وأوروبيين، وشوية ماركات محلية."},
    "product_care": {"fr": "🧺 Lavage à 30°C, à l'envers, sans javel. Les articles en laine se lavent à la main.",
                     "ar": "🧺 الغسيل في 30 درجة، مقلوب، بلا جافيل. حوايج الصوف تتغسل باليد."},
    "age_recommendation": {"fr": "Indiquez l'âge et je vous dis si l'article convient 👶",
                           "ar": "عطيني العمر ونقولك واش المنتج يناسب 👶"},

    # ---------- repli ----------
    "fallback": {
        "fr": "Je n'ai pas bien compris 🤔\nVous pouvez écrire par exemple :\n• « bchhal biberon » (un prix)\n• « vous avez des tabliers ? » (disponibilité)\n• « je veux commander »\n• « parler à un conseiller »",
        "ar": "ما فهمتش مليح 🤔\nتقدر تكتب مثلا:\n• «بشحال البيبرون» (الثمن)\n• «عندكم مرايل؟» (التوفر)\n• «بغيت نطلب»\n• «بغيت نهدر مع مستشار»",
    },
}


def _contact_answer(intent: str, lang: str) -> str | None:
    """Construit la réponse à partir de la fiche du client (jamais de texte en dur)."""
    c = getattr(catalog, "contact", None) or {}
    if not c:
        return None
    ar = lang == "ar"
    name = catalog.store_name
    addr = (c.get("address_ar") if ar else c.get("address_fr")) or c.get("address_fr", "")
    hours = (c.get("hours_ar") if ar else c.get("hours_fr")) or c.get("hours_fr", "")
    phone = c.get("phone", "")

    if intent in ("location", "points_de_vente", "adresse"):
        if not addr:
            return None
        out = (f"📍 {name}\n{addr}") if not ar else (f"📍 {name}\n{addr}")
        if hours:
            out += f"\n🕘 {hours}"
        if phone:
            out += f"\n☎️ {phone}"
        return out + ("\nونوصلو لكامل الوطن 🚚" if ar else "\nLivraison partout en Algérie 🚚")

    if intent in ("hours", "closed_days", "horaires"):
        if not hours:
            return None
        return (f"🕘 {hours}\nوالبوت يجاوب 24/24 🙂" if ar
                else f"🕘 {hours}\nLe bot, lui, répond 24h/24 🙂")

    if intent == "social_media":
        links = [("Instagram", c.get("instagram")), ("Facebook", c.get("facebook")),
                 ("TikTok", c.get("tiktok")), ("Site", c.get("site") or (catalog.store or {}).get("site"))]
        links = [f"• {k} : {v}" for k, v in links if v]
        if not links:
            return None
        return ("📱 تلقاونا في:\n" if ar else "📱 Retrouvez-nous :\n") + "\n".join(links)

    if intent in ("phone_contact", "contact"):
        if not phone:
            return None
        return (f"☎️ {phone}\n{name}" if not ar else f"☎️ {phone}\n{name}")
    return None


def render(intent: str, text: str = "", lang: str | None = None) -> str:
    """Construit la réponse finale pour une intention donnée."""
    lang = lang or detect_lang(text)

    # 1) intention produit -> fiche famille dynamique
    fam = catalog.family_by_intent(intent)
    if fam is None and intent.startswith("produit_"):
        fam = catalog.find_family(text)
    if fam is not None:
        body = catalog.family_text(fam, lang)
        hits = catalog.search_items(text, limit=3)
        if hits:
            lines = "\n".join(
                f"• {h['name']} — {h['price']} " + ("دج" if lang == "ar" else "DZD")
                + (f" ({'متوفر' if lang == 'ar' else 'stock'} : {h['stock']})")
                for h in hits
            )
            body += ("\n\n🔎 الأقرب لطلبك:\n" if lang == "ar" else "\n\n🔎 Le plus proche de votre demande :\n") + lines
        body += ("\n\nتحب نسجلك طلبية؟ اكتب «بغيت نطلب»." if lang == "ar"
                 else "\n\nVous voulez commander ? Écrivez « je veux commander ».")
        return body

    # 2) coordonnées réelles du client (adresse, horaires, réseaux) si renseignées
    dyn = _contact_answer(intent, lang)
    if dyn:
        return dyn

    # 3) réponse statique
    tpl = R.get(intent, R["fallback"])[lang]
    return tpl.format(
        store=catalog.store_name,
        catalog=catalog.catalog_text(lang),
        delivery=catalog.delivery_text(lang),
        payment=catalog.payment_text(lang),
    )



# ---------------------------------------------------------------------------
# Mots qui déclenchent une réponse de salutation même quand le NLP retombe
# en fallback (confiance trop basse mais message clairement non-commercial).
# ---------------------------------------------------------------------------
_GREETING_TOKENS: set[str] = {
    # arabizi / latin
    "salam", "salem", "slm", "sl", "sala", "salm",
    "slt", "slt", "hello", "hi", "hey", "bonjour", "bonsoir",
    "salut", "coucou", "ahlan", "merhba", "labas", "lbas",
    "wesh", "kirak", "kifach", "wach", "saha",
    # arabe script
    "سلام", "سلا", "مرحبا", "أهلا", "أهلين", "صباح", "مساء",
    "السلام", "لاباس",
}
# Mots qui ne doivent JAMAIS déclencher une recherche produit même en fallback
_SOCIAL_INTENTS: frozenset[str] = frozenset({
    "greeting", "goodbye", "thanks", "affirm", "deny",
    "bot_challenge", "help_menu", "repeat", "waiting",
    "compliment", "insult", "language_preference",
})


def smart_answer(intent: str, text: str, lang: str | None = None) -> str:
    """Réponse + recherche produit de secours quand l'intention est inconnue."""
    lang = lang or detect_lang(text)

    # — Ne jamais faire de recherche produit sur les intentions sociales ——
    if intent in _SOCIAL_INTENTS:
        return render(intent, text, lang)

    if intent in ("fallback", ""):
        # — Détection d'une salutation manquée par le NLP ——————————————
        words = set(text.lower().split())
        if words & _GREETING_TOKENS or words.issubset(_GREETING_TOKENS):
            # Renvoyer la réponse de bienvenue
            return render("greeting", text, lang)

        # — Message trop court (1-2 mots) non commercial : aide, pas produit ——
        if len(words) <= 2 and not any(c.isdigit() for c in text):
            return render("fallback", text, lang)

        hits = catalog.search_items(text, limit=4)
        if hits:
            lines = "\n".join(
                f"• {h['name']} — {h['price']} " + ("دج" if lang == "ar" else "DZD")
                + f" ({'متوفر' if lang == 'ar' else 'stock'} : {h['stock']})"
                for h in hits
            )
            head = ("🔎 لقيت هذي في الكتالوج:\n" if lang == "ar"
                    else "🔎 J'ai trouvé ceci dans le catalogue :\n")
            tail = ("\n\nتحب تطلب وحدة منهم؟" if lang == "ar"
                    else "\n\nVous voulez commander l'un d'eux ?")
            return head + lines + tail

    return render(intent, text, lang)

