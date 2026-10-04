"""
generate_intents.py — Générateur de patterns darija/arabizi/arabe pour intents.yaml
======================================================================================
Aucune dépendance externe. Utilise uniquement la stdlib Python.
Lance depuis la racine du projet :
    python scripts/generate_intents.py

Résultat : data/intents.yaml mis à jour avec les nouveaux patterns générés.
"""
import re
import itertools
from pathlib import Path

INTENTS_FILE = Path(__file__).parent.parent / "data" / "intents.yaml"

# ══════════════════════════════════════════════════════════════════════════════
# PORTEURS — phrases porteuses par registre de langue
# ══════════════════════════════════════════════════════════════════════════════

PORTEURS = {
    "fr":  ["vous avez", "c'est quoi", "c'est comment", "j'aimerais savoir",
            "dites moi", "je veux savoir", "quel est", "pouvez vous me dire",
            "je cherche", "avez vous", "comment"],
    "ar":  ["واش عندكم", "شنو", "كيفاش", "قولي على", "أش هو", "ما هو",
            "أخبرني عن", "نبغي نعرف"],
    "drj": ["wach", "ach", "chnou", "kifach", "goli", "3tini",
            "nhab n3ref", "bghit n3ref", "قولي", "علمني"],
    "arz": ["wach kayen", "wesh 3andkom", "3andkom", "fin", "wein",
            "bchhal", "chhal", "ndir"],
}

# ══════════════════════════════════════════════════════════════════════════════
# TOPICS PAR INTENTION (mots-clés du sujet)
# ══════════════════════════════════════════════════════════════════════════════

TOPICS: dict[str, list[str]] = {

    # ── Horaires ────────────────────────────────────────────────────────
    "hours": [
        # Français
        "vos horaires", "horaires d ouverture", "horaires de fermeture",
        "heure ouverture", "heure fermeture", "vous ouvrez a quelle heure",
        "vous fermez a quelle heure", "ouvert maintenant", "fermé maintenant",
        "vous etes ouverts", "c est ouvert",
        # Arabe standard
        "ساعات العمل", "وقت الافتتاح", "وقت الإغلاق", "هل انتم مفتوحين",
        "هل انتم مغلقين", "ساعات الفتح", "موعد الفتح", "موعد الإغلاق",
        # Darija arabe
        "سا9ات الخدمة", "واش مسكر", "واش مفتوح", "وقتاه تحل",
        "وقتاه تسكر", "علاش مسكر", "فين ساعات", "ساعات ديالكم",
        "يفتحو قداش", "يسكرو قداش",
        # Darija arabizi
        "msakker", "mftu7", "sa3at khedma", "wa9tach thal",
        "wa9tach tsker", "waktech thal", "waktech tsker",
        "msakar wla maftuh", "wach msakker", "wach mftu7",
        "saat diyalkom", "lwaqt", "horaire ntayakom",
        # Formules complètes darija
        "wach rak msakker", "wach laboutique msakra",
        "fin horaire", "fin saat", "sa3at lfetah",
    ],

    # ── Localisation ────────────────────────────────────────────────────
    "location": [
        # Français
        "votre adresse", "adresse du magasin", "ou etes vous",
        "ou se trouve le magasin", "ou vous trouver",
        "comment venir", "plan acces", "google maps",
        # Arabe
        "عنوانكم", "اين موقعكم", "اين يوجد المحل", "عنوان المحل",
        "وين المحل", "فين المحل", "وين تلقاوهم",
        # Darija
        "wein lmahal", "fin lboutique", "fin t9a3ou", "wein t9a3ou",
        "adresse ntayakom", "boudouaou fin", "boumerdes fin",
        "kifach njik 3andkom", "wech l3enwan",
        "fin lmHal dyalkom", "wein lmHal",
    ],

    # ── Livraison ────────────────────────────────────────────────────────
    "delivery": [
        # Français
        "frais livraison", "cout livraison", "livraison gratuite",
        "délai livraison", "vous livrez ou", "vous livrez a",
        "livraison wilaya", "livraison rapide", "livraison express",
        "livraison domicile", "vous livrez boumerdes",
        # Arabe
        "ثمن التوصيل", "مجاني التوصيل", "توصلو لي", "وقت التوصيل",
        "كاش عند التسليم", "توصيل للدار", "توصلو لأي ولاية",
        # Darija
        "bchhal twassal", "wach twassal", "twasslaw lfin",
        "kifach twassal", "twassal ldar", "twassal lwilaya",
        "frais delivri", "twassal bchhal", "twassal gniya",
        "wach twasslaw lboumerdes", "wach twasslaw l3andna",
        "bchhal lyewm", "wach twassal bla frais",
        "delivri bchhal", "livraison bchhal", "chhal twassal",
    ],

    # ── Paiement ─────────────────────────────────────────────────────────
    "payment": [
        # Français
        "comment payer", "modes paiement", "paiement livraison",
        "carte bancaire", "virement bancaire", "ccp", "baridimob",
        "payer en ligne", "paiement especes", "cash a la livraison",
        # Arabe
        "كيف أدفع", "طرق الدفع", "الدفع عند الاستلام",
        "بطاقة دفع", "تحويل بنكي", "دفع الكتروني",
        # Darija
        "kifach nkhaless", "nkhaless kifach", "nkhaless belcash",
        "nkhaless lcard", "nkhaless 3and twassal",
        "ach nkhaless bih", "wach 3andkom ccp",
        "wach 3andkom baridimob", "dfa3 3and lwassal",
        "wach nkhaless lbank", "kifach lhsab",
        "cash wla carte", "nkhaless ach", "flous kifach",
    ],

    # ── Commande ─────────────────────────────────────────────────────────
    "order_start": [
        # Français
        "je commande", "passer commande", "je prends", "je veux acheter",
        "ajouter au panier", "commander maintenant",
        # Arabe
        "بغيت نطلب", "نريد نطلب", "أريد الشراء",
        # Darija arabe
        "حابب نطلب", "بغيت ناخد", "حابب نشري", "نحب نطلب",
        "بغيت نكومندي", "نكومندي", "حابب نكومندي",
        # Darija arabizi
        "bghit ntalab", "hab nchri", "nhab nchri",
        "bghit nakhed", "bghit nkommandi", "nkommandi",
        "hab nkommandi", "kifach nkommander",
        "bghit nchri had", "bghit njib", "bghit n9der nchri",
        "wech ndir bach nchri", "bghit nkhod",
    ],

    # ── Catalogue / Produits ──────────────────────────────────────────────
    "products": [
        # Français
        "votre catalogue", "liste produits", "ce que vous vendez",
        "vos articles", "voir les produits",
        # Arabe
        "كتالوجكم", "منتجاتكم", "ماذا تبيعون", "ارونا منتجاتكم",
        # Darija
        "wesh 3andkom", "chnou 3andkom", "catalogue ntayakom",
        "wesh tbi3ou", "chnou tbi3ou", "3tini catalogue",
        "goli chnou 3andkom", "wach 3andkom", "liste produits",
        "wesh 3andkom mn les produits", "koulchi wesh 3andkom",
        "wesh tbi3ou mn chiya", "rani nhawes",
    ],

    # ── Prix ─────────────────────────────────────────────────────────────
    "prices": [
        # Français
        "le prix de", "combien coute", "tarif", "quel prix",
        # Arabe
        "كم ثمنو", "الثمن تاعو", "بكم هذا",
        # Darija
        "bchhal had", "chhal had", "bchhal", "chhal yeswa",
        "bchhal yeswa", "thman dyalo", "thman taa",
        "bchhal hada", "chhal hada", "bchhal fl",
        "chhal fl", "b9adach", "b9adach had",
        "bchhal lki", "chhal lki", "thman chhal",
    ],

    # ── Disponibilité ────────────────────────────────────────────────────
    "availability": [
        # Français
        "vous l avez", "c est disponible", "en stock", "toujours dispo",
        # Arabe
        "موجود ولا لا", "متوفر ولا لا", "عندكم هذا",
        # Darija
        "wach 3andkom", "wach kayen", "3andkom wala la",
        "kayen wala la", "dispo wala la", "wach dispo",
        "3andkom had lhaja", "wach mazal 3andkom",
        "fin kayen", "wach 3andkom fl stock",
        "mazal kayen wala khlas", "wach bga 3andkom",
    ],

    # ── Garantie / Retour ────────────────────────────────────────────────
    "warranty": [
        # Français
        "garantie produit", "retour produit", "echanger produit",
        "remboursement", "politique retour",
        # Arabe
        "ضمان المنتج", "إرجاع المنتج", "تبديل المنتج",
        # Darija
        "wach 3andkom dhaman", "dhaman bchhal",
        "wach n9der nrje3", "kifach nrje3 lmanta3",
        "wach tqablaw rje3", "nrje3 lmanta3 kifach",
        "wach nbeddel lmanta3", "nbeddel wala la",
        "politique retour kifach", "retour kifach",
    ],

    # ── Promotions ────────────────────────────────────────────────────────
    "discount": [
        # Français
        "promotions en cours", "code promo", "reduction disponible",
        "soldes", "offre speciale",
        # Darija
        "wach 3andkom promo", "3andkom tkhfidh",
        "promo kayen wala la", "wach kayen promo",
        "code promo wach kayen", "3andkom soldes",
        "wach 3andkom offre", "3andkom reduction",
        "wach 3andkom tkhfid", "promo kifach",
    ],

    # ── Suivi commande ────────────────────────────────────────────────────
    "track_order": [
        # Français
        "suivre ma commande", "ou est ma commande", "statut commande",
        # Darija
        "fin talbi", "wach talbi wassal", "talbi wassal wala la",
        "wach twassal ltabi3i", "fin lpackage dyali",
        "suivi talbi", "kifach ntabe3 talbi",
        "wach twassal", "talbi wesh sir", "matba3t talbi",
    ],
}

# ══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEUR
# ══════════════════════════════════════════════════════════════════════════════

def generate_patterns(intent: str, topics: list[str]) -> list[str]:
    """Génère des phrases en croisant porteurs × topics."""
    generated = []
    drj_porteurs = PORTEURS["drj"] + PORTEURS["arz"]

    for porteur, topic in itertools.product(drj_porteurs, topics[:10]):
        generated.append(f"{porteur} {topic}")

    fr_topics = [t for t in topics if all(ord(c) < 0x600 for c in t)]
    for porteur, topic in itertools.product(PORTEURS["fr"][:5], fr_topics[:5]):
        generated.append(f"{porteur} {topic}")

    return generated


def update_intents_yaml():
    """
    Lit intents.yaml comme texte, trouve chaque section intent,
    et y injecte les nouveaux patterns sans dépendance externe.
    """
    content = INTENTS_FILE.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Parse les patterns existants par intent (pour éviter doublons)
    existing: dict[str, set[str]] = {}
    current = None
    in_patterns = False
    for line in lines:
        m = re.match(r'^  "(\w+)":', line)
        if m:
            current = m.group(1)
            existing.setdefault(current, set())
            in_patterns = False
        if current and '"patterns"' in line:
            in_patterns = True
        if in_patterns and current:
            m2 = re.match(r'^\s+- "(.*)"', line)
            if m2:
                existing[current].add(m2.group(1))

    total_added = 0

    # Pour chaque intent, trouve le bon endroit et injecte les patterns
    new_lines = list(lines)
    offset = 0  # décalage dû aux insertions précédentes

    for intent_name, topics in TOPICS.items():
        if intent_name not in existing:
            print(f"  ⚠️  '{intent_name}' introuvable — ignoré")
            continue

        new_patterns = generate_patterns(intent_name, topics)
        to_add = [p for p in new_patterns
                  if p.strip() and p not in existing[intent_name] and len(p) > 3]

        if not to_add:
            print(f"  ✅ {intent_name}: rien à ajouter (déjà à jour)")
            continue

        # Trouve la dernière ligne de pattern de cet intent
        # On cherche le bloc `  "intent_name":` puis les lignes `      - "`
        insert_pos = None
        in_block = False
        in_pats = False
        for i, line in enumerate(new_lines):
            m = re.match(r'^  "(\w+)":', line)
            if m:
                if m.group(1) == intent_name:
                    in_block = True
                    in_pats = False
                elif in_block:
                    # Fin du bloc de cet intent
                    break
            if in_block and '"patterns"' in line:
                in_pats = True
            if in_block and in_pats and re.match(r'^\s+- "', line):
                insert_pos = i

        if insert_pos is None:
            print(f"  ⚠️  Pas de patterns trouvés pour '{intent_name}'")
            continue

        # Insère les nouveaux patterns après insert_pos
        new_entries = [f'      - "{p}"' for p in to_add]
        new_lines = new_lines[:insert_pos + 1] + new_entries + new_lines[insert_pos + 1:]

        existing[intent_name].update(to_add)
        total_added += len(to_add)
        print(f"  ✅ {intent_name}: +{len(to_add)} patterns ({len(existing[intent_name])} total)")

    INTENTS_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"\n✨ Total ajouté : {total_added} patterns → {INTENTS_FILE}")
    print("➡️  Commit + push + Coolify redeploy pour appliquer.")


if __name__ == "__main__":
    print("🔄 Génération des patterns darija/arabizi/arabe...\n")
    update_intents_yaml()
