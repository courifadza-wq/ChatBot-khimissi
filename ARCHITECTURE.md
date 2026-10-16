# 🤖 Architecture du bot Khemicishop — Machine Learning & NLP

> **Dernière mise à jour :** 16 octobre 2026  
> **Statut :** ✅ Bot opérationnel — bug `salem → bonjour` résolu

---

## 📐 Vue d'ensemble — Pipeline complet

```
👤 Client envoie "salem"
        │
        ▼
┌─────────────────────────────────────────────┐
│  normalize()   ·   nlp.py                  │
│  minuscules, arabizi, harakat supprimés     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐  ← PRIORITÉ 1
│  🛡️  GARDE SOCIALE  ·  web_chat.py L.44    │
│  salem / slm / sba7 / bonjour / merhba…    │
│  → reply_for("greeting")  STOP IMMÉDIAT    │
└──────────────────┬──────────────────────────┘
                   │ (si pas une salutation)
                   ▼
┌─────────────────────────────────────────────┐  ← PRIORITÉ 2
│  AR_MENU  ·  correspondances arabes fixes   │
│  سلام → greeting  /  كتالوج → products     │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐  ← PRIORITÉ 3
│  PRÉ-DÉTECTION PRODUIT  ·  mots-clés FR/AR  │
│  robe, basket, biberon, لباس, حذاء…        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐  ← PRIORITÉ 4
│  KEYWORD_INTENT  ·  livraison, paiement…   │
│  horaires, adresse, garantie, promo…       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐  ← PRIORITÉ 5
│  🧠  NLP CLASSIFIEUR  ·  nlp.py            │
│  Mode RULES  : motifs YAML (intents.yaml)  │
│  Mode HYBRID : TF-IDF + LogReg scikit      │
│               (entraîné sur lexicon.yaml)  │
└──────────────────┬──────────────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
   intent = produit_*   intent = greeting /
   → Recherche          delivery / payment…
     catalogue          → reply_for(intent)
     (DB + slug)        → Réponse texte
```

---

## 🗂️ Fichiers clés

| Fichier | Rôle | Lignes |
|---|---|---|
| `app/web_chat.py` | Logique bot web — orchestrateur principal | 525 |
| `app/main.py` | Logique bot WhatsApp | ~600 |
| `app/nlp.py` | Classifieur TF-IDF + règles | 152 |
| `app/normalize.py` | Normalisation arabizi/arabe | ~80 |
| `app/responses.py` | Réponses par intent | ~200 |
| `app/darija/lexicon.py` | Moteur génération darija + persistance | 494 |
| `app/darija/engine.py` | Gabarits darija (arabizi ↔ arabe) | ~400 |
| `app/darija/api.py` | Routes API admin `/api/lexicon/*` | 122 |
| `app/darija/page.html` | Interface admin `/admin/lexique` | ~380 |
| `data/intents.yaml` | Patterns NLP de base (25 614 lignes) | 25 614 |
| `data/lexicon.yaml` | Mémoire darija enrichie (sur serveur) | ~variable |
| `data/darija_variants.json` | Dictionnaire arabizi → arabe (450 KB) | ~12 000 |

---

## 🧠 Les 3 couches d'apprentissage

### Couche 1 — `data/intents.yaml` : Règles de base

Le fichier fondamental. Chaque **intent** a une liste de `patterns` (phrases exemples) et une `response`.

```yaml
intents:
  greeting:
    patterns:
      - "bonjour"
      - "salem"
      - "slm"
      - "sba7 khir"
      - "السلام عليكم"
      - "مرحبا"
    response: |
      Bonjour 👋 Bienvenue chez Planète Kids !
      ...

  delivery:
    patterns:
      - "livraison"
      - "twassal"       ← arabizi
      - "توصيل"         ← arabe
    response: "Nous livrons dans toute l'Algérie..."
```

**Géré via :** `/admin/intents` (formulaire — 1ère capture d'écran)

---

### Couche 2 — `data/lexicon.yaml` : Mémoire darija enrichie

Le lexique permet d'**apprendre de nouveaux mots** au bot sans toucher au code.  
Pour chaque entrée, le moteur `engine.py` génère automatiquement des dizaines de variantes.

**Exemple — ajout du mot `"rda3a"` (biberon en arabizi) :**

```
Mot latin  : rda3a          Mot arabe : رضاعة
Mode       : produit        Cible     : produit_biberon
Niveau     : 2 (standard)

→ Génère automatiquement ~160 formulations :
  "rda3a", "rda3ah", "rda3at", "rda3iya"        ← variantes arabizi
  "bghit nchri rda3a", "3andkom rda3a ?"         ← tournures commerciales
  "ch7al rda3a", "wach kayen rda3a"              ← questions prix/dispo
  "رضاعة", "بغيت رضاعة", "عندكم رضاعة ?"       ← arabe complet
  [+ ~150 autres formulations]

→ Injecté dans le NLP : intent "produit_biberon"
→ Ré-entraînement ML automatique en arrière-plan
```

**Géré via :** `/admin/lexique` (interface)

---

### Couche 3 — TF-IDF + Régression Logistique (scikit-learn)

Le classifieur ML s'entraîne sur **tous** les patterns (intents.yaml + lexicon.yaml).

```
intents.yaml  (25 000+ patterns)
     +
lexicon.yaml  (patterns générés automatiquement)
     │
     ▼
TfidfVectorizer.fit_transform()
     │
     ▼
LogisticRegression.fit()
     │
     ▼
Modèle en RAM  →  predict(text) → intent + confidence %
```

- Activé si `NL_MODE=hybrid` dans les variables d'environnement
- Ré-entraîné automatiquement (`_train_async()`) après chaque ajout au lexique
- Rechargé au redémarrage du service

---

## 🎯 Intentions disponibles

| Intent | Déclencheurs | Réponse |
|---|---|---|
| `greeting` | salem, bonjour, slm, سلام, مرحبا | Message de bienvenue FR ou AR selon la langue |
| `goodbye` | bye, au revoir, مع السلامة | Au revoir |
| `thanks` | merci, shukran, شكرا, يعطيك الصحة | De rien |
| `products` | catalogue, اسعار, كتالوج | Liste des catégories |
| `delivery` | livraison, twassal, توصيل, wilaya | Infos livraison + wilayas |
| `payment` | paiement, baridimob, دفع, flous | Modes de paiement |
| `order_start` | je veux commander, bghit nchri, اطلب | Démarrage du flux commande |
| `location` | adresse, wein, عنوان, boudouaou | Adresse + localisation boutique |
| `hours` | horaires, msakker, مواعيد, yiftah | Horaires d'ouverture |
| `discount` | promo, تخفيض, solde | Promotions en cours |
| `warranty` | garantie, ضمان, retour, reje3 | Politique retour/échange |
| `availability` | dispo, kayen, متوفر, stock | Disponibilité produit |
| `produit_*` | rda3a, chaussure, roba, serwal… | Recherche catalogue DB |

---

## 🔍 Cause racine du bug `salem → "Aucun produit trouvé pour bonjour"`

### Ce qui s'était passé (12 octobre 2026)

Quelqu'un avait ajouté dans `/admin/lexique` :

```
Mot      : "salem"
Équiv.   : "BONJOUR"     ← mis comme équivalent arabe (champ word_ar)
Mode     : 🛍️ Produit    ← ERREUR : c'est une salutation, pas un produit !
Cible    : produit_salem
```

Le moteur darija a généré **160 formulations** dont `"bonjour"` (transcription du champ `word_ar`),  
toutes injectées dans l'intent `produit_salem`.

**Flux erroné :**
```
Client envoie "salem"
   → NLP prédit : produit_salem  (160 patterns > quelques patterns greeting)
   → slug = "salem" → fr_keyword = "BONJOUR"
   → Recherche catalogue avec mot-clé "bonjour"
   → 0 résultat → "😕 Aucun produit trouvé pour bonjour"
```

### Corrections appliquées

| # | Action | Fichier / Outil | Date |
|---|---|---|---|
| 1 | Suppression `salem@produit_salem` (160 formulations) | API DELETE production | 16 oct. 2026 |
| 2 | Suppression `salem alikoum@produit_salem_alikoum` (160 formulations) | API DELETE production | 16 oct. 2026 |
| 3 | Garde sociale remontée **en TOUT PREMIER** (avant NLP) | `app/web_chat.py` L.44 | 16 oct. 2026 |
| 4 | Même garde ajoutée dans `app/main.py` (WhatsApp) | `app/main.py` | 15 oct. 2026 |
| 5 | Interface `/admin/lexique` : ajout du type **👋 Salutation** | `app/darija/page.html` | 16 oct. 2026 |

---

## 🛡️ Protection double (empêche la récidive)

### Protection 1 — Garde sociale dans le code

```python
# app/web_chat.py — ligne ~44 (AVANT tout NLP)
_GREETING_TOKENS = {
    "salem", "slm", "sba7", "bonjour", "merhba", "ahla",
    "wach labas", "wach rak", "labas", ...
}
_txt_social = text.strip().lower()
if _txt_social in _GREETING_TOKENS and not _in_session(session_id):
    return reply_for("greeting", ...)   # STOP — jamais de recherche produit
```

### Protection 2 — Type "👋 Salutation" dans l'interface admin

L'interface `/admin/lexique` propose désormais **3 types** :

```
🛍️ un produit   |   💬 une question   |   👋 salutation
```

Le type **👋 salutation** :
- Filtre la liste de cibles → affiche uniquement `greeting`, `thanks`, `goodbye`
- Sélectionne `greeting` automatiquement
- Affiche un avertissement explicatif
- Envoie `mode=intention` au backend (pas de génération de formulations produit)

---

## 📋 Guide — Comment apprendre de nouveaux mots au bot

### ✅ Ajouter un produit (ex: nouveau type de vêtement)

1. Aller sur `https://botkhimissi.br-solution.tech/lexique`
2. **Mot** : `ballerina` — **Équivalent arabe** : `بالرينا`
3. **Type** : 🛍️ **un produit**
4. **Cible** : `produit_ballerine` (ou créer une nouvelle famille)
5. **Profondeur** : 2 (standard) ou 3 (maximal si mot très utilisé)
6. Cliquer **Aperçu** → vérifier les formulations générées
7. Cliquer **Enregistrer** → le ML se ré-entraîne automatiquement

### ✅ Ajouter une question (ex: question sur les retours)

1. **Mot** : `retour produit` — **Équivalent arabe** : `رجع بضاعة`
2. **Type** : 💬 **une question**
3. **Cible** : `warranty`
4. Enregistrer

### ✅ Ajouter une salutation (ex: nouveau mot darija)

1. **Mot** : `salam wa3alaykom`
2. **Type** : 👋 **salutation** ← UTILISER CE TYPE OBLIGATOIREMENT
3. **Cible** : `greeting` (sélectionnée automatiquement)
4. Enregistrer

> ⚠️ **RÈGLE D'OR** : Ne JAMAIS mettre une salutation (salem, bonjour, sba7…)  
> avec le type 🛍️ "produit". Cela casserait le bot.

---

## 🏗️ Architecture de déploiement

```
Site web khemicishop.com  (Hostinger)
    └── ChatBotWidget.vue
          └── POST /chat-proxy.php
                └── https://botkhimissi.br-solution.tech/web-chat
                                  ▲
                        Bot Python FastAPI
                        (serveur br-solution.tech)
                        Déployé via : Coolify / Docker

GitHub repo : courifadza-wq/ChatBot-khimissi
    └── main branch → CI/CD → serveur de prod
```

### Variables d'environnement (Coolify)

| Variable | Description |
|---|---|
| `NL_MODE` | `hybrid` (TF-IDF+ML) ou `rules` (règles seules) |
| `ADMIN_TOKEN` | Token pour protéger `/admin/*` (vide = accès libre) |
| `WHATSAPP_TOKEN` | Token Meta API WhatsApp |
| `SMTP_*` | Config email pour les commandes |

---

## 🧪 Tester le bot en production (PowerShell)

```powershell
# Tester une salutation
$body = '{"message":"salem","session_id":"test-001"}'
[Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-RestMethod -Uri "https://botkhimissi.br-solution.tech/web-chat" `
    -Method POST -Body $body -ContentType "application/json"

# Ou avec curl (plus fiable)
curl -k -s -X POST "https://botkhimissi.br-solution.tech/web-chat" `
    -H "Content-Type: application/json" `
    --data-raw '{"message":"salem","session_id":"test-001"}'
```

### Résultats attendus ✅

| Message | Réponse attendue |
|---|---|
| `salem` | 👋 Bienvenue chez Planète Kids ! |
| `slm` | 👋 Bienvenue chez Planète Kids ! |
| `sba7` | 👋 Bienvenue chez Planète Kids ! |
| `bonjour` | 👋 Bienvenue chez Planète Kids ! |
| `merhba` | 👋 Bienvenue chez Planète Kids ! |
| `wach labas` | وعليكم السلام 👋 (réponse en arabe) |
| `3andkom rda3a` | 📦 Résultats produits biberon |
| `livraison` | 🚚 Infos livraison wilaya |
