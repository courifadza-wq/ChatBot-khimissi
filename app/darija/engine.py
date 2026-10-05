"""Générateur de patterns darija — algérien, arabizi, arabe standard, français.

Objectif : à partir d'un simple mot-clé produit (« biberon » / « رضاعة »), produire
automatiquement des centaines de façons **réalistes** dont un client algérien pose
sa question sur WhatsApp.

Quatre registres couverts :
    fr        français (souvent fautif, sans accents)
    arabizi   darija écrite en lettres latines + chiffres (3, 7, 9, 5, 2)
    ar        darija écrite en caractères arabes
    msa       arabe standard (tournures plus formelles)

Douze familles d'intentions : prix, disponibilité, info, taille, couleur, stock,
promo, commande, livraison, paiement, photo, réservation.

Pipeline de génération :
    mot-clé ──► variantes morphologiques (pluriel, ال, préfixes و/ب/ل, fautes)
            ──► × porteurs de phrase (≈ 350 gabarits)
            ──► × modificateurs (politesse, salutations, emojis, « svp »)
            ──► × bruit clavier (azerty, allongements, lettres collées)
            ──► dédoublonnage normalisé + échantillonnage déterministe

Usage :
    from .darija import generate
    pats = generate("biberon", "رضاعة", kinds=("price", "availability"), level=3)

CLI :
    python3 -m app.darija biberon --ar رضاعة --level 3 --limit 60
    python3 -m app.darija poussette --kinds price,order --out patterns.yaml
"""
from __future__ import annotations

import random
import re
import unicodedata
from typing import Iterable, Sequence

# ===========================================================================
#  1. NORMALISATION
# ===========================================================================
TASHKEEL = re.compile(r"[\u064B-\u0652\u0640]")
AR_FOLD = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي",
                         "ة": "ه", "ؤ": "ء", "ئ": "ء", "ﻻ": "لا"})


def norm(text: str) -> str:
    """Forme canonique servant au dédoublonnage (accents, tashkeel, casse, espaces)."""
    t = unicodedata.normalize("NFKC", str(text or "")).lower().strip()
    t = TASHKEEL.sub("", t).translate(AR_FOLD)
    t = "".join(c for c in unicodedata.normalize("NFD", t)
                if unicodedata.category(c) != "Mn" or "\u0600" <= c <= "\u06FF")
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)                 # saaaalam -> saalam
    t = re.sub(r"[^\w\u0600-\u06FF%+\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def has_arabic(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", str(text or "")))


# ===========================================================================
#  2. TRANSLITTÉRATION ARABIZI ↔ ARABE
# ===========================================================================
#  Le « chat alphabet » algérien : chiffres pour les lettres sans équivalent latin.
LAT2AR_DIGRAPHS = [
    ("tch", "تش"), ("kh", "خ"), ("gh", "غ"), ("ch", "ش"), ("sh", "ش"),
    ("th", "ث"), ("dh", "ذ"), ("ou", "و"), ("ee", "ي"), ("aa", "ا"),
]
LAT2AR = {
    "a": "ا", "b": "ب", "c": "ك", "d": "د", "e": "ي", "f": "ف", "g": "ڤ",
    "h": "ه", "i": "ي", "j": "ج", "k": "ك", "l": "ل", "m": "م", "n": "ن",
    "o": "و", "p": "ب", "q": "ق", "r": "ر", "s": "س", "t": "ت", "u": "و",
    "v": "ف", "w": "و", "x": "كس", "y": "ي", "z": "ز",
    "2": "ء", "3": "ع", "4": "ذ", "5": "خ", "6": "ط", "7": "ح", "8": "غ", "9": "ق",
}
AR2LAT = {
    "ا": "a", "ب": "b", "ت": "t", "ث": "th", "ج": "j", "ح": "7", "خ": "kh",
    "د": "d", "ذ": "dh", "ر": "r", "ز": "z", "س": "s", "ش": "ch", "ص": "s",
    "ض": "d", "ط": "t", "ظ": "dh", "ع": "3", "غ": "gh", "ف": "f", "ق": "9",
    "ك": "k", "ل": "l", "م": "m", "ن": "n", "ه": "h", "و": "ou", "ي": "i",
    "ء": "2", "ة": "a", "ى": "a", "ڤ": "g", "پ": "p", "چ": "tch",
}


def to_arabic(text: str) -> str:
    """Arabizi -> caractères arabes (approximation, suffisante pour l'indexation)."""
    t = str(text or "").lower()
    for lat, ar in LAT2AR_DIGRAPHS:
        t = t.replace(lat, ar)
    return "".join(LAT2AR.get(c, c) for c in t)


def to_arabizi(text: str) -> str:
    """Caractères arabes -> arabizi."""
    return "".join(AR2LAT.get(c, c) for c in str(text or ""))


# Variantes orthographiques fréquentes en arabizi (le même mot s'écrit de 5 façons)
#  bidirectionnelles : les deux graphies existent réellement
SWAPS_BIDIR = [("ch", "sh"), ("ou", "u"), ("9", "k"), ("9", "q"), ("7", "h"),
               ("kh", "5"), ("gh", "8"), ("dj", "j"), ("i", "y")]
#  unidirectionnelles : simplification seulement (jamais l'inverse)
SWAPS_ONEWAY = [("é", "e"), ("è", "e"), ("ph", "f"), ("ck", "k"), ("ee", "i"),
                ("au", "o"), ("eau", "o"), ("qu", "k"), ("ss", "s"), ("tt", "t")]


def arabizi_spellings(word: str, limit: int = 6) -> list[str]:
    """« bghit » -> bghit, b8it, bghyt… — la forme d'origine reste TOUJOURS en tête."""
    base = str(word or "").lower().strip()
    if not base or has_arabic(base):
        return [base] if base else []
    out = [base]
    for a, b in SWAPS_ONEWAY:
        if a in base:
            out.append(base.replace(a, b))
    for a, b in SWAPS_BIDIR:                      # une seule substitution à la fois
        if a in base:
            out.append(base.replace(a, b))
        if b in base:
            out.append(base.replace(b, a))
    return [w for w in dict.fromkeys(out) if w][:limit]


# ===========================================================================
#  3. VARIANTES MORPHOLOGIQUES DU MOT-CLÉ
# ===========================================================================
AR_PREFIXES = ("ال", "لل", "ب", "و", "ف")          # article, « pour », « avec », « et », « dans »
FR_PLURALS = ("s", "x")
TYPO_NEIGHBORS = {                                  # voisins clavier AZERTY
    "a": "qz", "b": "vn", "c": "xv", "d": "sf", "e": "zr", "f": "dg", "g": "fh",
    "h": "gj", "i": "uo", "j": "hk", "k": "jl", "l": "km", "m": "lp", "n": "b",
    "o": "ip", "p": "om", "q": "as", "r": "et", "s": "qd", "t": "ry", "u": "yi",
    "v": "cb", "w": "x", "x": "cw", "y": "tu", "z": "ae",
}


def keyword_variants(key: str, level: int = 2, rnd: random.Random | None = None) -> list[str]:
    """Décline un mot-clé dans SON écriture : pluriel, article, préfixes, fautes.

    Ne mélange jamais latin et arabe : utiliser keyword_pools() pour obtenir les deux.
    """
    rnd = rnd or random.Random(7)
    k = str(key or "").strip().lower()
    if not k:
        return []
    out = {k}

    if has_arabic(k):
        bare = k
        for p in AR_PREFIXES:
            if bare.startswith(p) and len(bare) > len(p) + 2:
                bare = bare[len(p):]
                break
        ordered = [k, bare]
        if " " not in bare:                     # ال/لل uniquement sur un mot simple
            ordered += ["ال" + bare, "لل" + bare]
        else:                                   # annexion : « عربة الطفل » -> « لعربة الطفل »
            ordered.append("ل" + bare)
        if level >= 3:
            ordered.append(bare.replace("ة", "ه"))
        return [v for v in dict.fromkeys(ordered) if v]
    else:
        ordered = [k]                                # la forme exacte d'abord, toujours
        if not k.endswith("s"):
            ordered.append(k + "s")
        elif len(k) > 4:
            ordered.append(k[:-1])
        if level >= 2:
            ordered += arabizi_spellings(k, limit=3)[1:]
        if level >= 3:                               # fautes de frappe réalistes
            words = [w for w in k.split() if len(w) > 4]
            for w in words[:1]:
                i = rnd.randrange(1, len(w) - 1)
                nb = TYPO_NEIGHBORS.get(w[i], "")
                if nb:
                    ordered.append(k.replace(w, w[:i] + rnd.choice(nb) + w[i + 1:]))
                ordered.append(k.replace(w, w[:i] + w[i + 1:]))      # lettre manquante
                ordered.append(k.replace(w, w[:i] + w[i] * 2 + w[i + 1:]))  # lettre doublée
        return [v for v in dict.fromkeys(ordered) if v]
    return [v for v in dict.fromkeys(out) if v]


def keyword_pools(key_fr: str, key_ar: str = "", level: int = 2,
                  rnd: random.Random | None = None, max_each: int = 3) -> tuple[list[str], list[str]]:
    """Renvoie (formes latines, formes arabes) — chaque registre reçoit la bonne écriture."""
    rnd = rnd or random.Random(11)
    lat = keyword_variants(key_fr, level, rnd) if key_fr else []
    ar = keyword_variants(key_ar, level, rnd) if key_ar else []
    if key_ar and level >= 2:
        lat.append(to_arabizi(_strip_al(key_ar)))        # رضاعة -> rda3a (écrit en arabizi)
    if key_ar and " " in _strip_al(key_ar):
        head = _strip_al(key_ar).split()[0]               # « معقم الرضاعات » -> « معقم »
        if len(head) >= 3:
            ar.append(head)
            ar.append("ال" + head)
    if not ar and key_fr and level >= 2:
        ar.append(to_arabic(key_fr))                     # secours : translittération inverse
    dedup = lambda xs: [x for x in dict.fromkeys(xs) if x and len(x) > 1]
    #  +1 place pour le mot de tête arabe, qui est souvent ce que tape le client
    return dedup(lat)[:max_each], dedup(ar)[:max_each + 1]


def _strip_al(w: str) -> str:
    for p in ("ال", "لل"):
        if w.startswith(p) and len(w) > len(p) + 2:
            return w[len(p):]
    return w


# ===========================================================================
#  4. PORTEURS DE PHRASE (le cœur du générateur) — ≈ 350 gabarits
# ===========================================================================
C: dict[str, dict[str, list[str]]] = {

    # ---------------------------------------------------------------- PRIX
    "price": {
        "fr": [
            "prix {k}", "le prix du {k}", "le prix de {k}", "prix des {k}",
            "combien coute {k}", "combien coûte le {k}", "ça coûte combien {k}",
            "c'est combien {k}", "c'est combien le {k}", "quel est le prix de {k}",
            "tarif {k}", "{k} prix", "{k} combien", "{k} c'est combien",
            "vous vendez {k} à combien", "à combien le {k}", "il coute combien le {k}",
            "donnez moi le prix du {k}", "je veux savoir le prix du {k}",
            "le {k} coûte combien", "prix {k} svp", "combien pour un {k}",
        ],
        "arabizi": [
            "bchhal {k}", "bch7al {k}", "b chhal {k}", "chhal {k}", "ch7al {k}",
            "bichhal {k}", "kaddach {k}", "9adech {k}", "bch7al rah {k}",
            "soum {k}", "soumt {k}", "soumt ta3 {k}", "prix ta3 {k}", "prix dyal {k}",
            "{k} bchhal", "{k} chhal", "{k} b chhal rahou", "chhal yswa {k}",
            "chhal taman ta3 {k}", "3tini prix ta3 {k}", "bghit na3raf chhal {k}",
            "goulili chhal {k}", "wach rah ghali {k}", "rakhis {k} wla la",
            "chhal thabat {k}", "bchhal takhdem {k}",
        ],
        "ar": [
            "بشحال {k}", "شحال {k}", "بشحال راه {k}", "قداش {k}", "قداش راه {k}",
            "سومة {k}", "السومة تاع {k}", "الثمن تاع {k}", "بالاش {k}",
            "شحال يسوى {k}", "شحال تبيعو {k}", "عطيني السومة تاع {k}",
            "بغيت نعرف سومة {k}", "قوليلي بشحال {k}", "واش راه غالي {k}",
            "{k} بشحال", "{k} شحال", "{k} السومة", "راه رخيص {k} ولا لا",
            "شحال يكلف {k}", "بشحال الواحد تاع {k}",
        ],
        "msa": [
            "ما هو سعر {k}", "كم سعر {k}", "كم يكلف {k}", "سعر {k} من فضلك",
            "أريد معرفة ثمن {k}", "ما ثمن {k}", "هل يمكنني معرفة سعر {k}",
        ],
    },

    # -------------------------------------------------------- DISPONIBILITÉ
    "availability": {
        "fr": [
            "vous avez {k}", "vous avez des {k}", "avez vous {k}", "est ce que vous avez {k}",
            "{k} disponible", "{k} dispo", "{k} est disponible", "il y a {k}",
            "y a t il des {k}", "vous en avez encore {k}", "{k} en stock",
            "est ce qu'il reste des {k}", "je cherche {k}", "je cherche un {k}",
            "{k} dispo ou pas", "vous vendez des {k}", "{k} toujours disponible",
        ],
        "arabizi": [
            "3andkom {k}", "3andkoum {k}", "3andek {k}", "3andkom chi {k}",
            "wach 3andkom {k}", "wach kayen {k}", "kayen {k}", "kayn {k}",
            "rah kayen {k}", "mazal kayen {k}", "baqi 3andkom {k}",
            "wach mawjoud {k}", "mawjoud {k}", "{k} kayen wla la",
            "{k} mawjouda", "3awedtou {k}", "jatkom {k}", "dkhlat {k}",
            "wach tsibo {k}", "n7awes 3la {k}", "nahwas 3la {k}", "chft {k} 3andkom",
        ],
        "ar": [
            "عندكم {k}", "واش عندكم {k}", "عندك {k}", "عندكم شي {k}",
            "كاين {k}", "واش كاين {k}", "راه كاين {k}", "مازال كاين {k}",
            "باقي عندكم {k}", "واش موجود {k}", "موجود {k}", "{k} موجود ولا لا",
            "{k} متوفر", "واش توفر {k}", "جاتكم {k}", "دخلات {k}",
            "نحوس على {k}", "راني نقلب على {k}", "واش تلقاو {k}",
        ],
        "msa": [
            "هل {k} متوفر", "هل لديكم {k}", "أبحث عن {k}", "هل يوجد {k} لديكم",
            "ما مدى توفر {k}", "أريد الاستفسار عن توفر {k}",
        ],
    },

    # ----------------------------------------------------------- INFOS
    "info": {
        "fr": [
            "{k}", "info sur {k}", "parlez moi du {k}", "c'est quoi {k}",
            "donnez moi les détails du {k}", "caractéristiques {k}",
            "montrez moi les {k}", "je veux voir les {k}", "vos {k}",
            "qu'est ce que vous avez comme {k}", "quels {k} vous avez",
        ],
        "arabizi": [
            "{k}", "wach 3andkom f {k}", "goulili 3la {k}", "chwiya d'info 3la {k}",
            "wrili {k}", "warini {k}", "chouf liya {k}", "bghit nchouf {k}",
            "ch7al min naw3 ta3 {k}", "kifach {k}", "wach men {k} 3andkom",
        ],
        "ar": [
            "{k}", "واش عندكم في {k}", "قوليلي على {k}", "وريلي {k}",
            "بغيت نشوف {k}", "شوفلي {k}", "واش من {k} عندكم",
            "شحال من نوع تاع {k}", "كيفاش {k}", "اعطيني تفاصيل {k}",
        ],
        "msa": ["معلومات عن {k}", "أخبرني عن {k}", "ما هي مواصفات {k}", "أرني {k}"],
    },

    # ----------------------------------------------------------- TAILLES
    "size": {
        "fr": ["quelle taille pour {k}", "{k} taille", "vous avez {k} en grande taille",
               "{k} pour quel age", "{k} 3 mois", "{k} taille 2 ans", "les tailles du {k}"],
        "arabizi": ["ch7al men taille f {k}", "{k} taille chhal", "3andkom {k} kbir",
                    "{k} sghir wla kbir", "{k} l 3am", "{k} l chhar", "tayel ta3 {k}"],
        "ar": ["شحال من مقاس في {k}", "{k} مقاس شحال", "عندكم {k} كبير",
               "{k} صغير ولا كبير", "{k} لعمر قداش", "المقاسات تاع {k}"],
        "msa": ["ما هي المقاسات المتوفرة لـ {k}", "هل {k} متوفر بمقاسات أخرى"],
    },

    # ----------------------------------------------------------- COULEURS
    "color": {
        "fr": ["{k} quelle couleur", "vous avez {k} en rose", "les couleurs du {k}",
               "{k} en bleu", "{k} autre couleur", "{k} couleur disponible"],
        "arabizi": ["{k} chno l couleur", "3andkom {k} wardi", "lwan ta3 {k}",
                    "{k} azrak", "{k} couleur okhra", "wach 3andkom {k} byad"],
        "ar": ["{k} واش من لون", "عندكم {k} وردي", "الألوان تاع {k}",
               "{k} أزرق", "{k} لون آخر", "واش عندكم {k} أبيض"],
        "msa": ["ما هي الألوان المتوفرة لـ {k}", "هل يتوفر {k} بلون آخر"],
    },

    # ----------------------------------------------------------- STOCK
    "stock": {
        "fr": ["il vous reste combien de {k}", "combien de {k} en stock",
               "{k} en rupture", "quand vous recevez les {k}", "{k} réapprovisionné quand"],
        "arabizi": ["ch7al baqi 3andkom men {k}", "{k} khlas", "{k} salat",
                    "wa9tach tjikom {k}", "wa9tach yrja3 {k}", "khlaw {k}"],
        "ar": ["شحال باقي عندكم من {k}", "{k} خلاص", "{k} سالات",
               "وقتاش تجيكم {k}", "وقتاش يرجع {k}", "خلاو {k}"],
        "msa": ["كم بقي لديكم من {k}", "متى يتوفر {k} مجددا"],
    },

    # ----------------------------------------------------------- PROMO
    "promo": {
        "fr": ["{k} en promo", "y a une remise sur {k}", "vous faites des promos sur {k}",
               "{k} soldé", "réduction sur {k}", "prix spécial {k}"],
        "arabizi": ["{k} f promo", "kayen remise 3la {k}", "takhfid 3la {k}",
                    "{k} b takhfid", "3andkom solde 3la {k}", "dirouli chwiya f prix ta3 {k}"],
        "ar": ["{k} في تخفيض", "كاين تخفيض على {k}", "عندكم بروومو على {k}",
               "{k} بالتخفيض", "ديرولي شوية في السومة تاع {k}"],
        "msa": ["هل هناك تخفيض على {k}", "ما هي عروض {k}"],
    },

    # ----------------------------------------------------------- COMMANDE
    "order": {
        "fr": ["je veux commander {k}", "je prends {k}", "commander {k}",
               "je voudrais acheter {k}", "réservez moi un {k}", "mettez moi 2 {k}",
               "je veux acheter {k}", "comment commander {k}"],
        "arabizi": ["bghit nchri {k}", "bghit ncommandi {k}", "bghit {k}",
                    "habit nakhod {k}", "dirli {k}", "7abess liya {k}",
                    "ndir commande ta3 {k}", "n7eb nechri {k}", "3tini jouj {k}",
                    "khalilia {k}", "bghit nakhod {k}"],
        "ar": ["بغيت نشري {k}", "بغيت نطلب {k}", "بغيت {k}", "حبيت ناخذ {k}",
               "ديرلي {k}", "حبسلي {k}", "ندير طلبية تاع {k}", "عطيني زوج {k}",
               "خليهالي {k}", "نحب نشري {k}"],
        "msa": ["أريد شراء {k}", "أريد طلب {k}", "كيف أطلب {k}", "احجز لي {k}"],
    },

    # ----------------------------------------------------------- LIVRAISON
    "delivery": {
        "fr": ["vous livrez {k}", "livraison pour {k}", "{k} livré chez moi",
               "combien la livraison du {k}", "vous envoyez {k} par yalidine"],
        "arabizi": ["twaslo {k}", "tjibo {k} l dar", "livraison ta3 {k} bchhal",
                    "tab3atou {k} yalidine", "youssel {k} l wilaya ta3i"],
        "ar": ["توصلو {k}", "تجيبو {k} للدار", "التوصيل تاع {k} بشحال",
               "تبعثو {k} يالدين", "يوصل {k} لولايتي"],
        "msa": ["هل توصلون {k}", "كم تكلفة توصيل {k}"],
    },

    # ----------------------------------------------------------- PAIEMENT
    "payment": {
        "fr": ["je paye comment {k}", "{k} paiement à la livraison",
               "vous acceptez ccp pour {k}", "je peux payer {k} par baridimob"],
        "arabizi": ["nkhalas kifach {k}", "{k} khalas 3and listilam",
                    "ta9bdou ccp ta3 {k}", "n7awel flous ta3 {k} baridimob"],
        "ar": ["نخلص كيفاش {k}", "{k} الخلاص عند الاستلام",
               "تقبلو سيسيبي تاع {k}", "نحول دراهم {k} بريدي موب"],
        "msa": ["كيف أدفع ثمن {k}", "هل الدفع عند الاستلام لـ {k}"],
    },

    # ----------------------------------------------------------- PHOTO
    "photo": {
        "fr": ["envoyez moi une photo du {k}", "photo {k}", "je peux voir {k} en photo",
               "vous avez des images du {k}", "vidéo du {k}"],
        "arabizi": ["ab3atli tswira ta3 {k}", "tswira ta3 {k}", "chouf liya photo ta3 {k}",
                    "3andkom tsawer ta3 {k}", "video ta3 {k}"],
        "ar": ["ابعثلي تصويرة تاع {k}", "تصويرة تاع {k}", "وريني صورة {k}",
               "عندكم صور تاع {k}", "فيديو تاع {k}"],
        "msa": ["أرسل لي صورة {k}", "هل لديكم صور لـ {k}"],
    },

    # ----------------------------------------------------------- RÉSERVATION
    "reserve": {
        "fr": ["vous pouvez me garder un {k}", "réservez moi {k} jusqu'à demain",
               "mettez de côté {k}", "je passe le prendre {k}"],
        "arabizi": ["7abess liya {k}", "7abeslhali {k} hta ghadwa",
                    "khalih liya {k}", "nji njibou {k} ghadwa"],
        "ar": ["حبسلي {k}", "حبسهالي {k} حتى غدوة", "خليه ليا {k}", "نجي ناخذو {k} غدوة"],
        "msa": ["هل يمكنكم حجز {k} لي", "احجزوا لي {k} حتى الغد"],
    },
}

# ---------------------------------------------------------------- modificateurs
PREFIX = {
    "fr": ["", "", "bonjour ", "salut ", "bsr ", "svp "],
    "arabizi": ["", "", "salam ", "slm ", "slam 3alikom ", "aslema "],
    "ar": ["", "", "سلام ", "السلام عليكم ", "صباح الخير "],
    "msa": ["", "", "مرحبا ", "السلام عليكم "],
}
POLITE_SUFFIX = {
    "fr": ["", "", " svp", " s'il vous plait", " merci", " merci d'avance"],
    "arabizi": ["", "", " 3afak", " rebi y7afdek", " choukran", " brk", " men fadlek"],
    "ar": ["", "", " من فضلك", " عافاك", " بارك الله فيك", " يعطيك الصحة"],
    "msa": ["", "", " من فضلك", " لو سمحت", " شكرا"],
}
SUFFIX = {
    "fr": ["", "", "", " ?", " ??", " 🙏", " 😊"],
    "arabizi": ["", "", "", " ?", " ??", " 🙏", " wela la", " ou la"],
    "ar": ["", "", "", " ؟", " ؟؟", " 🙏", " ولا لا"],
    "msa": ["", "", " ؟"],
}

REGISTERS: tuple[str, ...] = ("fr", "arabizi", "ar", "msa")
KINDS: tuple[str, ...] = tuple(C.keys())


# ===========================================================================
#  5. BRUIT CLAVIER (messages WhatsApp réels)
# ===========================================================================
def noisy(text: str, rnd: random.Random) -> str:
    """Applique une déformation réaliste : allongement, lettre sautée, collage."""
    t = text
    if has_arabic(t):                                   # pas de bruit clavier sur l'arabe
        return t + rnd.choice([" ؟", "..", " ؟؟"])
    pick = rnd.random()
    if pick < 0.3:                                     # allongement expressif
        words = [w for w in t.split() if len(w) > 3]
        if words:
            w = rnd.choice(words)
            i = rnd.randrange(1, len(w))
            t = t.replace(w, w[:i] + w[i - 1] * 2 + w[i:], 1)
    elif pick < 0.55:                                  # lettre manquante
        words = [w for w in t.split() if len(w) > 4]
        if words:
            w = rnd.choice(words)
            i = rnd.randrange(1, len(w) - 1)
            t = t.replace(w, w[:i] + w[i + 1:], 1)
    elif pick < 0.75:                                  # espaces supprimés
        t = t.replace(" ", "", 1)
    elif pick < 0.9:                                   # tout en majuscules
        t = t.upper()
    else:                                              # ponctuation parasite
        t = t + rnd.choice(["...", "!!", " ?", ".."])
    return t


# ===========================================================================
#  6. GÉNÉRATEUR PRINCIPAL
# ===========================================================================
LEVELS = {
    #                gabarits  variantes   politesse  bruit   plafond par défaut
    1: {"carriers": 4,  "kw_variants": 1, "polite": 0.00, "noise": 0.00, "cap": 28},
    2: {"carriers": 10, "kw_variants": 2, "polite": 0.30, "noise": 0.05, "cap": 160},
    3: {"carriers": 99, "kw_variants": 3, "polite": 0.50, "noise": 0.20, "cap": None},
}


def generate(
    key_fr: str,
    key_ar: str = "",
    kinds: Sequence[str] = ("price", "availability", "info"),
    registers: Sequence[str] = REGISTERS,
    level: int = 2,
    cap: int | None = None,
    seed: int = 1337,
    include_bare: bool = True,
) -> list[str]:
    """Génère les formulations clients pour un mot-clé.

    key_fr      mot-clé latin (« biberon », « siege auto »)
    key_ar      mot-clé arabe équivalent (« رضاعة ») — fortement recommandé
    kinds       familles d'intentions (price, availability, info, size, color,
                stock, promo, order, delivery, payment, photo, reserve)
    registers   fr | arabizi | ar | msa
    level       1 = compact · 2 = standard · 3 = étendu (variantes + bruit)
    cap         nombre maximum de patterns renvoyés (échantillonnage déterministe)
    """
    rnd = random.Random(f"{seed}:{key_fr}:{key_ar}")
    cfg = LEVELS.get(level, LEVELS[2])
    kinds = [k for k in kinds if k in C] or ["price"]
    registers = [r for r in registers if r in REGISTERS] or ["fr"]

    kv_lat, kv_ar = keyword_pools(key_fr, key_ar, level, rnd, max_each=cfg["kw_variants"])
    if cap is None:
        cap = cfg.get("cap")

    out: list[str] = []
    seen: set[str] = set()

    def push(p: str) -> None:
        p = re.sub(r"\s+", " ", p).strip()
        n = norm(p)
        if not n or len(n) < 2 or n in seen:
            return
        seen.add(n)
        out.append(p)

    if include_bare:
        for v in kv_lat + kv_ar:
            push(v)

    for kind in kinds:
        for reg in registers:
            carriers = C[kind].get(reg, [])
            if not carriers:
                continue
            carriers = carriers[: cfg["carriers"]]
            keys = kv_ar if reg in ("ar", "msa") else kv_lat
            if not keys:
                continue
            for carrier in carriers:
                for k in keys:
                    base = carrier.format(k=k)
                    push(base)
                    if rnd.random() < cfg["polite"]:
                        pre = rnd.choice(PREFIX[reg])
                        suf = rnd.choice(POLITE_SUFFIX[reg] + SUFFIX[reg])
                        push(f"{pre}{base}{suf}")
                    if rnd.random() < cfg["noise"]:
                        push(noisy(base, rnd))

    if cap and len(out) > cap:
        head = out[: min(len(kv_lat) + len(kv_ar), cap)]        # on garde les formes nues
        rest = out[len(head):]
        rnd.shuffle(rest)
        out = head + rest[: cap - len(head)]
    return out


def generate_for_product(name_fr: str, name_ar: str = "", level: int = 2,
                         cap: int | None = None) -> list[str]:
    """Raccourci produit : prix + disponibilité + info + commande + photo."""
    from ..learner import keyword, keyword_ar          # import tardif (évite les cycles)
    k = keyword(name_fr)
    kar = keyword_ar(name_ar) if name_ar else ""
    kinds = ("price", "availability", "info") if level == 1 else \
            ("price", "availability", "info", "stock", "order", "photo", "promo")
    return generate(k, kar, kinds=kinds, level=level, cap=cap)


def stats() -> dict:
    """Taille du corpus de gabarits disponible."""
    per_kind = {k: {r: len(v.get(r, [])) for r in REGISTERS} for k, v in C.items()}
    total = sum(sum(r.values()) for r in per_kind.values())
    return {"familles_intentions": len(C), "registres": list(REGISTERS),
            "gabarits_total": total, "detail": per_kind}


def preview(key_fr: str, key_ar: str = "", level: int = 3, n: int = 40) -> str:
    pats = generate(key_fr, key_ar, kinds=KINDS, level=level)
    head = pats[:n]
    return (f"{len(pats)} patterns générés pour « {key_fr} »"
            + (f" / « {key_ar} »" if key_ar else "") + f" (niveau {level})\n"
            + "\n".join(f"  • {p}" for p in head)
            + (f"\n  … et {len(pats) - n} autres" if len(pats) > n else ""))


# ===========================================================================
#  7. CLI
# ===========================================================================
