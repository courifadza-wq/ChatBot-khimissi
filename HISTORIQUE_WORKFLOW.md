# 📋 HISTORIQUE COMPLET — Bot Khimissi × Laravel API
> Projet : **botkhimissi.br-solution.tech** × **api.khemicishop.com**  
> Rédigé le : 2026-10-17  

---

## 🏗️ ARCHITECTURE GLOBALE

### Vue d'ensemble des composants

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT FINAL                                 │
│              (WhatsApp ou Widget Web sur khemicishop.com)           │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ message texte ("tente", "biberon"...)
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│              BOT FASTAPI — botkhimissi.br-solution.tech             │
│              Docker / Coolify / VPS 46.202.172.143:65002            │
│              GitHub : courifadza-wq/ChatBot-khimissi                │
│                                                                     │
│  ┌──────────┐   ┌──────────┐   ┌────────────┐   ┌──────────────┐  │
│  │  web_chat │──▶│   NLP    │──▶│  catalog   │──▶│ laravel_api  │  │
│  │   .py    │   │   .py    │   │    .py     │   │    .py       │  │
│  └──────────┘   └──────────┘   └────────────┘   └──────┬───────┘  │
│                                      │                  │           │
│                               SQLite fallback           │ HTTP      │
│                               (bot_memory.db)           │ REST      │
└─────────────────────────────────────────────────────────┼───────────┘
                                                          │
                                                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│              LARAVEL API — api.khemicishop.com                      │
│              Hébergé Hostinger / PHP 8.2 / MySQL                    │
│                                                                     │
│  GET /api/products?search=tente&limit=5                             │
│  → {"data":[{id,name_fr,price,slug,is_active,category},...]}        │
│                                                                     │
│  GET /api/categories                                                │
│  → [{id, name_fr, slug, ...}]                                       │
└─────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│              ADMIN KHEMICISHOP — khemicishop.com/admin              │
│              Vue.js SPA / Hostinger                                 │
│                                                                     │
│  /admin/products   → Import Excel → MySQL via Laravel               │
│  /admin/lexique    → Mots darija → lexicon.yaml (sur le bot)        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 FLUX D'UN MESSAGE CLIENT

### Exemple : client écrit "tente"

```
1. Client écrit "tente" dans le widget web
         │
         ▼
2. POST https://botkhimissi.br-solution.tech/web-chat
   Body: {"message":"tente","session_id":"xxx"}
         │
         ▼
3. web_chat.py — Pipeline de traitement :
   
   [A] GARDE SOCIALE → "tente" n'est pas une salutation → continue
   
   [B] PRÉ-DÉTECTION PRODUIT → "tente" est dans _PRODUCT_KW → ✅ MATCH
       → appelle smart_search_with_products("tente")
         │
         ▼
4. catalog.py → smart_search_with_products("tente")
   
   [Niveau 1] search_products_laravel(keyword="tente", limit=5)
              GET api.khemicishop.com/api/products?search=tente&limit=5
              ← {"data":[4 tentes], "meta":{...}}
              → retourne 4 produits ✅
         │
         ▼
5. format_search_results([4 tentes]) → texte WhatsApp formaté

6. Réponse au client :
   🔍 *Résultats pour "tente" :*
   • *Tente de jeux Rose 130cm*
     💰 4700 DZD  |  Réf: tente-de-jeux-rose-130cm
   ...
```

---

## 🐛 LE BUG — Pourquoi "tente" retournait "Aucun produit trouvé"

### Chronologie du bug

**Situation initiale** : Le bot utilisait uniquement SQLite (base locale) pour chercher les produits. Quand tu importais des produits via Excel dans l'admin Laravel, ils allaient dans MySQL mais **pas dans le SQLite du bot** → le bot ne les voyait jamais.

### Les 3 raisons d'échec en cascade

```
Message "tente"
     │
     ▼
❌ Raison 1 — _PRODUCT_KW ne contenait pas "tente"
   La liste des mots-clés produits incluait "tenue" mais pas "tente"
   → Le court-circuit vers la recherche produit ne se déclenchait pas
     │
     ▼
❌ Raison 2 — NLP classifiait "tente" en "fallback"
   Le classifieur n'avait pas "tente" dans ses patterns d'entraînement
   → intent = "fallback" → aucune recherche produit
     │
     ▼
❌ Raison 3 — LA CAUSE RACINE : httpx sans follow_redirects
   laravel_api.py utilisait httpx sans follow_redirects=True
   ni header Accept: application/json
   → Laravel renvoyait une réponse vide (redirect ou HTML)
   → JSONDecodeError → silencieusement return []
   → "Aucun produit trouvé" 😕
```

### Le faux-ami (bug bonus) : "tente" → "TENUE"

Le fuzzy search avait un seuil de similarité à 0.65 (65%).  
TENTE vs TENUE = 80% similaire (1 lettre de différence).  
→ Le bot confondait "tente" avec "TENUE" et retournait des tenues au lieu de tentes.

---

## 🔧 CORRECTIONS APPLIQUÉES — Détail commit par commit

### `35c15f0` — feat: laravel_api.py (nouvelle couche)
**Fichier créé : `app/laravel_api.py`**

Création du pont entre le bot et l'API Laravel :
- `search_products_laravel(keyword, category, max_price, min_price, limit)` 
- `get_categories_laravel()`
- `count_products_laravel()`

**Fichiers modifiés :**
- `app/catalog.py` → utilise Laravel en priorité, SQLite en fallback
- `app/config.py` → ajout `LARAVEL_API_URL` et `LARAVEL_API_TIMEOUT`

---

### `468d31d` — fix: parsing réponse paginée Laravel

**Problème** : Laravel retourne `{"data":[...], "meta":{...}}` pas `[...]` directement.

**Fix dans `laravel_api.py`** :
```python
# Avant
items = data  # ← échouait car data = {"data":[], "meta":{}}

# Après
items = data.get("data", data) if isinstance(data, dict) else data
```

---

### `ddd1a98` — fix: fuzzy search "tente" → "tenue" corrigé

**Problème** : seuil de similarité trop bas → "tente" matchait "TENUE".

**Fix dans `app/database.py`** — fonction `fuzzy_keyword()` :
```python
# Avant
SEUIL = 0.65  # trop permissif

# Après  
SEUIL = 0.82  # strict
+ même première lettre obligatoire
+ différence de longueur ≤ 2 caractères
+ mot minimum 5 lettres
```

---

### `c18f6af` — fix: "tente" dans _PRODUCT_KW + fallback Laravel

**Problème** : "tente" absent de la liste de détection rapide.

**Fix dans `app/web_chat.py`** :
```python
_PRODUCT_KW = {
    ...existants...,
    # Jouets plein air ← AJOUTÉ
    "tente", "toboggan", "balancoire", "trampoline",
    "piscine", "voiture", "velo", "poupee", "puzzle",
    "poussette", "berceau", "matelas",
}
```

Et le fallback final utilise désormais `smart_search_with_products()` (Laravel) au lieu de SQLite seul.

---

### `def4671` — fix: "tente" dans _DARIJA_FR

**Problème** : Quand le lexique darija classifiait "tente" → `produit_tente`, le bot cherchait "tente" dans `_DARIJA_FR` pour trouver le mot-clé français. "tente" était absent → `fr_kw = ""` → recherche vide.

**Fix dans `app/web_chat.py`** :
```python
_DARIJA_FR = {
    ...existants...,
    # Jouets plein air ← AJOUTÉ
    "tente": "tente", "tente de jeux": "tente",
    "khayma": "tente", "khaima": "tente",
    "toboggan": "toboggan", "trampoline": "trampoline",
    "balancoire": "balançoire", "piscine": "piscine",
    "poupee": "poupée", "puzzle": "puzzle",
}
```

---

### `0c5077e` — debug: endpoint /debug/laravel

Ajout d'un endpoint de diagnostic dans `app/main.py` :
```
GET https://botkhimissi.br-solution.tech/debug/laravel?q=tente
```
Permet de tester depuis l'extérieur ce que voit le container Docker.

---

### `c013854` — debug: afficher réponse brute HTTP

Amélioration du debug endpoint pour afficher :
- `http_status` : code HTTP reçu de Laravel
- `content_type` : type de réponse (JSON ou HTML ?)
- `raw_200chars` : premiers 200 caractères de la réponse brute

**Ce diagnostic a révélé la cause racine** :
```json
{
  "count": 4,           ✅ Laravel répond bien avec 4 tentes
  "smart_search_count": 0   ❌ search_products_laravel() retourne vide
}
```
→ La même API marchait en debug mais pas dans `laravel_api.py`. Différence = `follow_redirects` et `Accept` header.

---

### `0fcf240` — fix ROOT CAUSE : follow_redirects + Accept header

**LA VRAIE CAUSE RACINE** trouvée et corrigée.

**Problème** : `httpx.Client` par défaut ne suit pas les redirections HTTP.  
L'API Laravel renvoyait une redirection (ou nécessitait le header `Accept: application/json` pour retourner du JSON).  
Sans ces deux éléments → corps de réponse vide → `JSONDecodeError` → `return []` silencieux.

**Fix dans `app/laravel_api.py`** — toutes les fonctions :
```python
# Avant (ne marchait pas)
with httpx.Client(timeout=API_TIMEOUT, verify=False) as client:
    resp = client.get(url, params=params)

# Après (fonctionne ✅)
headers = {"Accept": "application/json"}
with httpx.Client(timeout=API_TIMEOUT, verify=False, follow_redirects=True) as client:
    resp = client.get(url, params=params, headers=headers)
```

---

## 🧪 TESTS DE VALIDATION FINAUX

```
✅ debug/laravel?q=tente → count:4, smart_search_count:4
✅ web-chat "tente"      → 4 tentes avec prix et références
✅ web-chat "biberon"    → produits Laravel en temps réel
✅ web-chat "catalogue"  → catégories depuis Laravel
✅ Fuzzy : "tente" ≠ "TENUE" (plus de confusion)
```

---

## 🔗 CONNEXION SITE WEB ↔ BOT — Comment ça fonctionne

### 1. Import de produits (Admin → Laravel → Bot)

```
Admin khemicishop.com
        │
        │ Upload Excel
        ▼
Laravel API (api.khemicishop.com)
        │ Stocke dans MySQL
        ▼
Bot (botkhimissi.br-solution.tech)
        │ Appelle Laravel en temps réel à chaque recherche client
        │ GET /api/products?search=xxx
        ▼
Client WhatsApp/Web reçoit les produits à jour ✅
```

**Important** : Il n'y a **pas de synchronisation** à faire manuellement. Les produits importés via Excel dans l'admin sont **immédiatement disponibles** dans le bot.

### 2. Widget Chat Web (khemicishop.com → Bot)

Le widget chat sur `khemicishop.com` envoie les messages directement au bot :

```javascript
// Dans ChatBotWidget.vue (frontend Vue.js)
fetch("https://botkhimissi.br-solution.tech/web-chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: userText, session_id: sessionId })
})
```

**CORS configuré** dans `app/main.py` pour autoriser `khemicishop.com`.

### 3. Lexique Darija (Admin → Bot directement)

```
Admin khemicishop.com/admin/lexique
        │
        │ POST /api/lexicon/add
        ▼
Bot FastAPI → data/lexicon.yaml (volume Docker persistant)
        │ Injecte les patterns dans le classifieur NLP en mémoire
        │ Ré-entraîne le modèle ML en arrière-plan
        ▼
Bot reconnaît le nouveau mot immédiatement ✅
```

---

## 📁 STRUCTURE DES FICHIERS CLÉS

```
chatbot_whatsapp/
├── app/
│   ├── main.py           # FastAPI : routes /web-chat, /webhook, /debug/laravel
│   ├── web_chat.py       # Pipeline principal de traitement des messages
│   ├── nlp.py            # Classifieur d'intentions (rules + ML TF-IDF)
│   ├── catalog.py        # Recherche produits (Laravel → SQLite fallback)
│   ├── laravel_api.py    # ← NOUVEAU : pont vers api.khemicishop.com
│   ├── database.py       # SQLite local (clients, commandes, fallback produits)
│   ├── responses.py      # Réponses par intention
│   ├── order.py          # Machine à états commande
│   ├── config.py         # Variables d'environnement
│   └── darija/
│       ├── lexicon.py    # Gestion du lexique darija
│       ├── engine.py     # Générateur de variantes arabizi/arabe
│       └── api.py        # Routes /api/lexicon/*
├── data/
│   ├── intents.yaml      # Intentions NLP de base
│   ├── lexicon.yaml      # Lexique darija (volume Docker persistant)
│   └── bot_memory.db     # SQLite : clients + commandes
└── Dockerfile            # Image Python FastAPI
```

---

## 🌐 URLS ET ACCÈS

| Service | URL |
|---------|-----|
| Bot web-chat | `https://botkhimissi.br-solution.tech/web-chat` |
| Bot health | `https://botkhimissi.br-solution.tech/health` |
| Bot debug Laravel | `https://botkhimissi.br-solution.tech/debug/laravel?q=xxx` |
| Admin lexique | `https://khemicishop.com/admin/lexique` |
| Laravel API | `https://api.khemicishop.com/api/products?search=xxx` |
| GitHub bot | `https://github.com/courifadza-wq/ChatBot-khimissi` |

---

## ⚙️ VARIABLES D'ENVIRONNEMENT (Coolify)

| Variable | Valeur | Rôle |
|----------|--------|------|
| `LARAVEL_API_URL` | `https://api.khemicishop.com/api` | URL de l'API Laravel |
| `LARAVEL_API_TIMEOUT` | `4.0` | Timeout en secondes |
| `NL_MODE` | `hybrid` | Mode NLP (rules + ML) |

---

## 🚀 DÉPLOIEMENT

Le bot est déployé via **Coolify** sur VPS `46.202.172.143`.  
Chaque `git push origin main` déclenche automatiquement un rebuild Docker et redéploiement (~3-5 minutes).

```bash
# Workflow de mise à jour
git add .
git commit -m "description du changement"
git push origin main
# → Coolify rebuild automatique
# → Bot redémarré avec le nouveau code
```

---

*Document généré le 2026-10-17 — Projet Khimissi Bot*
