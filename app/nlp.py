# ============================================================
#  Classifieur d'intentions
#  Mode "rules"  : correspondance par motifs (aucune dépendance IA)
#  Mode "hybrid" : classifieur scikit-learn (TF-IDF + LogReg) prioritaire
#
#  Gère : français + arabe + derja algérienne + arabizi (3/7/9...)
# ============================================================
import logging
import re
import unicodedata

import yaml

from .config import settings

logger = logging.getLogger("nlp")

# Caractères conservés : lettres latines, lettres arabes, chiffres (y c. arabes)
_KEEP = re.compile(r"[^0-9a-z\u0621-\u064A\u0660-\u0669\s]")

# Normalisation des lettres arabes équivalentes
_ARABIC_MAP = str.maketrans({
    "\u0622": "\u0627",  # آ -> ا
    "\u0623": "\u0627",  # أ -> ا
    "\u0625": "\u0627",  # إ -> ا
    "\u0624": "\u0648",  # ؤ -> و
    "\u0626": "\u064A",  # ئ -> ي
    "\u0649": "\u064A",  # ى -> ي
    "\u0640": " ",       # tatweel -> espace
})

# Marquage des mots courts non-significatifs pour le mode "rules"
_WEAK = {
    # français
    "je","tu","il","elle","on","nous","vous","le","la","les","un","une","des","de","du",
    "et","ou","ou","a","au","aux","que","qui","quoi","est","suis","es","etes","me","ma","mon",
    "mes","te","ta","ton","ses","se","ce","ces","dans","pour","avec","sur","sans","par","en",
    # arabe / derja
    "في","ما","لا","من","على","و","ها","هو","هي","انا","انت","انتي","واش","وش","شنو","ا","ة",
}


def normalize(text: str) -> str:
    """Normalise : minuscules, sans accents ni harakat, lettres arabes conservées."""
    text = unicodedata.normalize("NFD", text)
    # Enlève les diacritiques (accents latins + harakat arabes : fatha, damma...)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower()
    text = text.translate(_ARABIC_MAP)
    text = _KEEP.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class IntentClassifier:
    def __init__(self):
        with open(settings.INTENTS_FILE, "r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)
        self.intents = self.data["intents"]
        self._patterns = []  # (intent, mots_normalises)
        self._clf = None
        self._vectorizer = None
        self._build_patterns()
        if settings.NL_MODE == "hybrid":
            self._train_ml()

    def _build_patterns(self):
        for name, conf in self.intents.items():
            for phrase in conf.get("patterns", []):
                norm = normalize(phrase)
                if norm:
                    self._patterns.append((name, norm.split()))

    # ---------- Mode "rules" (motifs complets, robuste aux mots courts) ----------
    def score_rules(self, text: str) -> dict:
        """Score chaque intention selon le meilleur motif qu'elle contient.
        Un motif 'merci au revoir' (3 mots) ne matche 'merci' seul que partiellement."""
        toks = set(normalize(text).split())
        best = {}
        for name, pwords in self._patterns:
            if not pwords:
                continue
            matched = sum(1 for w in pwords if w in toks and w not in _WEAK)
            total = sum(1 for w in pwords if w not in _WEAK)
            if total == 0:
                continue
            ratio = matched / total
            score = ratio * total          # favorise les motifs longs complets
            if matched == total and total >= 2:
                score += 1.0               # bonus correspondance complète
            if score > best.get(name, 0):
                best[name] = score
        return best

    # ---------- Classifieur ML (mode hybrid) ----------
    def _train_ml(self):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
        except ImportError:
            logger.warning("scikit-learn non installé — mode règles uniquement.")
            return
        X, y = [], []
        for name, conf in self.intents.items():
            for phrase in conf.get("patterns", []):
                n = normalize(phrase)
                if n:
                    X.append(n)
                    y.append(name)
        if len(set(y)) < 2 or len(X) < 8:
            logger.warning("Pas assez de données pour le ML (%d exemples).", len(X))
            return
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 3), analyzer="char_wb")
        Xv = self._vectorizer.fit_transform(X)
        self._clf = LogisticRegression(C=6.0, max_iter=2000)
        self._clf.fit(Xv, y)
        logger.info("Classifieur ML entraîné sur %d phrases (%d intentions).",
                    len(X), len(set(y)))

    def predict(self, text: str) -> str:
        t = normalize(text)
        if not t:
            return "fallback"

        # 1) ML prioritaire (meilleur pour les reformulations derja/arabe)
        if self._clf is not None and self._vectorizer is not None:
            vec = self._vectorizer.transform([t])
            proba = self._clf.predict_proba(vec)[0]
            idx = int(proba.argmax())
            if proba[idx] >= 0.30:
                return self._clf.classes_[idx]

        # 2) repli sur les règles
        rules = self.score_rules(t)
        if rules:
            best = max(rules, key=rules.get)
            if rules[best] >= 1.0:
                return best

        return "fallback"


def reload_classifier() -> IntentClassifier:
    """Recharge et re-entraîne le classifieur depuis intents.yaml.
    À utiliser après une modification des données (interface d'admin)."""
    global classifier
    classifier = IntentClassifier()
    return classifier


classifier = IntentClassifier()
