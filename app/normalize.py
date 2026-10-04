"""
normalize.py — Pipeline de normalisation multilingue (FR · AR · Darija · Arabizi).
Appliqué à CHAQUE message entrant avant tout traitement.

Pipeline :
  1. Unicode NFKC
  2. Suppression tashkeel (diacritiques arabes)
  3. Normalisation orthographe arabe (أإآ→ا, ى→ي, ة→ه)
  4. Réduction élongations (salaaam→salam, خخخ→خخ)
  5. Vocabulaire arabizi connu (mots entiers → arabe/français)
  6. Lowercase
"""
import re
import unicodedata

# ── Vocabulaire arabizi connu (mots entiers, prioritaire) ──────────────────
# Format : mot_arabizi → équivalent reconnaissable par le bot
_ARABIZI_VOCAB: dict[str, str] = {
    # Salutations
    "salam": "سلام", "slm": "سلام", "salem": "سلام",
    "wach": "واش", "wesh": "واش", "wash": "واش", "wesh": "واش",
    "labas": "لاباس", "lbes": "لاباس", "la bas": "لاباس",
    "ahla": "اهلا", "ahlan": "اهلا",
    # Questions fréquentes
    "3andkom": "عندكم", "3andkum": "عندكم", "andkom": "عندكم",
    "kayen": "كاين", "kayan": "كاين", "kayn": "كاين",
    "wach kayen": "واش كاين", "wesh kayen": "واش كاين",
    "fin": "فين", "feen": "فين",
    "kifah": "كيفاه", "kifeh": "كيفاه",
    # Recherche produit
    "bghit": "بغيت", "nhab": "نحب", "nrid": "نريد",
    "nahwas": "نحوس", "ndawer": "ندور",
    "bchhal": "بشحال", "beshhal": "بشحال", "chhal": "شحال",
    "souma": "سومة", "soumt": "سومة",
    # Horaires
    "msakker": "مسكر", "msakar": "مسكر", "msaker": "مسكر",
    "mftu7": "مفتوح", "meftou7": "مفتوح", "meftuh": "مفتوح",
    "sa3a": "ساعة", "sa3at": "ساعات",
    "waqt": "وقت", "wa9t": "وقت",
    "lyom": "اليوم", "lioum": "اليوم",
    "ghda": "غدا", "ghedwa": "غدا",
    # Commande
    "ncomandi": "commander", "ncommandi": "commander",
    "hbet": "commander", "7bet": "commander",
    "twassal": "توصيل", "tawsil": "توصيل",
    "livraison": "livraison",  # conservé tel quel (français)
    # Correction ortho française fréquente
    "bibron": "biberon", "biberoon": "biberon", "bibéron": "biberon",
    "poussett": "poussette", "pousete": "poussette",
    "couchet": "couche", "kouche": "couche",
    # Arabizi chiffres isolés courants
    "3la": "على", "3nd": "عند", "m3a": "مع",
    "f": "في", "b": "بـ", "l": "لـ",
}

# ── Détection arabizi (chiffres arabes dans un mot latin) ──────────────────
_RE_ARABIZI = re.compile(r"\b\w*[37925]\w*\b")


def normalize(text: str) -> str:
    """
    Normalise un message pour la comparaison et la détection d'intentions.
    Retourne le texte nettoyé (lowercase, sans diacritiques, arabizi converti).
    """
    # 1. Unicode NFKC (unifie les variantes de caractères)
    text = unicodedata.normalize("NFKC", text)

    # 2. Suppression tashkeel (diacritiques U+064B–U+0652) + tatweel (U+0640)
    text = re.sub(r"[\u064B-\u0652\u0640]", "", text)

    # 3. Normalisation orthographe arabe
    text = re.sub(r"[أإآٱ]", "ا", text)
    text = text.replace("ى", "ي")
    text = text.replace("ة", "ه")
    text = re.sub(r"[ؤئ]", "ء", text)

    # 4. Réduction élongations : 3+ répétitions → 2 max
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)

    # 5. Lowercase avant lookup
    text_lower = text.lower()

    # 6. Substitution vocabulaire arabizi (mots entiers)
    words = text_lower.split()
    normalized_words = []
    for w in words:
        normalized_words.append(_ARABIZI_VOCAB.get(w, w))
    text_lower = " ".join(normalized_words)

    return text_lower.strip()


def detect_lang(text: str) -> str:
    """
    Détecte la langue dominante du message.
    Retourne : 'ar' | 'arabizi' | 'fr'
    """
    arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
    total_alpha = len(re.findall(r"[a-zA-Z\u0600-\u06FF]", text))

    if total_alpha == 0:
        return "fr"

    arabic_ratio = arabic_chars / total_alpha

    if arabic_ratio >= 0.4:
        return "ar"
    if _RE_ARABIZI.search(text):
        return "arabizi"
    return "fr"
