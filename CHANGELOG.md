# 📋 HISTORIQUE DES OPÉRATIONS — Chatbot Planète Kids

> Généré le 08/10/2026 — 58 commits au total

---

## 🔴 SESSION DU 08/10/2026 — Enrichissement NLP massif

### Objectif
Intégrer les données NLP récoltées dans `NLP/chatbot_whatsapp/data/` pour rendre le bot plus robuste et riche en connaissances, tout en **préservant intégralement le système lexique existant**.

### Phase 1 — Upgrade intents + mapping darija→français
**Commit:** `79742c4`

| Avant | Après |
|---|---|
| 24 intents génériques | **157 intents spécialisés** |
| 0 intent produit spécifique | **72 intents produit** (poussette, biberon, robe, pantalon, tricot...) |
| 0 intent de recherche/filtre | **9 intents de recherche** (budget, saison, marque, rentrée scolaire...) |
| Paiement basique | **BaridiMob, CCP, Edahabia, virement** |
| Livraison basique | **Par wilaya, Yalidine/ZR, stop-desk/domicile** |
| ~50 mappings `_DARIJA_FR` | **170+ mappings** couvrant toutes les familles |

**Fichiers modifiés :**
- `data/intents.yaml` — Remplacé par la version enrichie (156 KB → 629 KB)
- `app/web_chat.py` — `_DARIJA_FR` étendu (+120 entrées)

---

### Phase 2 — Injection des CSV darija dans les patterns NLP
**Commit:** `439116c`

**Données intégrées :**

| Source CSV | Entrées | Contenu |
|---|---|---|
| `lexique-darija-10k.csv` | 14 275 | Expressions produits (couleurs, tailles, matières, saisons, licences) |
| `lexique-darija-bases.csv` | 169 | Mots de base canoniques (vêtements, chaussures, puériculture) |
| `lexique-darija-bebe.csv` | 44 | Vocabulaire spécialisé bébé (biberon, poussette, tire-lait...) |
| `lexique-darija-expressions.csv` | 14 | Expressions conversationnelles essentielles |

**Résultat :** +20 666 patterns ajoutés (dédupliqués) → **25 076 patterns** au total

**Fichier modifié :**
- `data/intents.yaml` — 629 KB, 25 584 lignes

---

### Phase 3 — Normalisation orthographique darija (pré-NLP)
**Commit:** `dfa3810`

**Principe :** Dictionnaire de 19 134 variantes orthographiques qui corrige automatiquement les fautes de frappe **avant** que le NLP ne traite le message.

| Entrée utilisateur | Normalisé → | Résultat bot |
|---|---|---|
| `seroual` | `serwal` | → Pantalon |
| `cerrousa` | `kerrousa` | → Poussette |
| `kachkol` | `kachkoul` | → Cartable |
| `ssrwal` | `serwal` | → Pantalon |
| `chochou` | `chouchou` | → Accessoire cheveux |
| `elseroual` | `serwal` | → Pantalon |

**Fichiers créés :**
- `data/darija_variants.json` — 439 KB, 19 134 variantes
- `app/darija/normalizer.py` — Module de pré-correction (chargé au démarrage)

**Fichier modifié :**
- `app/web_chat.py` — Hook normalizer (2 lignes ajoutées avant le NLP)

**Vérification encodage arabe :** ✅ 19 426/19 426 entrées UTF-8 valides

---

## 🟡 SESSION DU 07/10/2026 — Résolution 502 + Timeout lexique

### Résolution complète du 502 Bad Gateway
**Commits:** `50f51c6`, `a2e4f29`

**Problèmes résolus :**

1. **DNS Cloudflare** — Le sous-domaine `botkhimissi.br-solution.tech` pointait vers le proxy Cloudflare au lieu du VPS direct. Corrigé en mode "DNS only".

2. **Certificat SSL** — Les proxies PHP Hostinger recevaient "SSL certificate problem". Corrigé avec `CURLOPT_SSL_VERIFYPEER => false`.

3. **Route mismatch** — `main.py` avait `/chat` mais le proxy PHP appelait `/web-chat`. Aligné sur `/web-chat`.

4. **Conteneurs orphelins** — Docker cleanup dans Coolify pour supprimer les conteneurs qui causaient des erreurs Traefik "Router defined multiple times".

### Timeout lexique (ajout de mots)
**Commit:** `a2e4f29`

**Problème :** Ajouter un mot dans le lexique admin causait un timeout de 30s car le ré-entraînement NLP (66K+ patterns) bloquait le worker unique.

**Solution :** Ré-entraînement asynchrone avec `threading.Thread` — la réponse HTTP revient immédiatement, le ML se ré-entraîne en arrière-plan.

**Fichiers modifiés :**
- `app/darija/lexicon.py` — Ajout `_train_async()`, changé `_train()` → `_train_async()` dans `add()` et `delete()`
- `lexicon-api.php` (Hostinger) — Timeout POST augmenté à 90s

---

## 🟢 SESSIONS PRÉCÉDENTES — Construction du bot

### Module Darija NLP complet
**Commits:** `4b223a4`, `9b8ef40`, `b244da5`, `a007f32`

- **Engine NLP** avec 351 gabarits de patterns
- **+2 255 patterns** darija/arabizi
- **Facts Store** (adresse réelle, is_open_now)
- **Pipeline de normalisation** arabizi/darija
- **Lexique admin** `/lexique` avec CRUD complet

### Journal des conversations
**Commits:** `f10f456`, `d132ffc`

- **SQLite logging** de TOUS les messages (entrée + sortie)
- **API `/api/journal`** pour consulter les logs
- **Stats** `/api/journal/stats` (messages/jour, top intents)
- **Auto-cleanup** des logs > 30 jours
- **Page admin** pour visualiser les conversations

### Recherche produits intelligente
**Commits:** `a622900`, `96de01d`, `692a587`, `58cb6c4`

- **Catalogue SQLite** de 10 102 produits
- **Recherche multi-critères** (nom, catégorie, référence, prix)
- **Recherche fuzzy** avec difflib (balrine → BALLERINE, bibron → BIBERON)
- **Pré-détection produit** avant NLP pour les mots-clés évidents
- **Fallback intelligent** quand le NLP ne trouve pas d'intent

### Support multilingue
**Commits:** `a96ded9`, `e5b95b1`, `5a5b4e8`, `ccde8c8`

- **Arabe / Derja** bilingue complet
- **Détection de catégorie** avec aliases arabe/darija
- **Menu arabe** mapping direct (الكتالوج, التوصيل, تطلب)
- **Intents arabes** enrichis avec script d'enrichissement

### Système de commande
**Commits:** `21ad020`, `18cb223`, `45a2b40`, `60f0484`

- **Sessions persistantes** SQLite
- **Panier** avec calcul de prix depuis la DB
- **Option retrait magasin** + livraison
- **Bail-out** automatique (salutations annulent la commande en cours)
- **Recherche AND stricte** en mode commande

### Visuels produits (Web)
**Commits:** `418182e`, `a4e9132`

- **Rendu visuel** des produits dans le widget web (images, prix, référence)
- **Extraction d'URL images** depuis les templates Excel

### Infrastructure & DevOps
**Commits:** `c2866fc` → `b4d850a`

- **Docker** avec Dockerfile optimisé (Python 3.13-slim)
- **Coolify** déploiement automatique via git push
- **Traefik** reverse proxy avec SSL Let's Encrypt
- **Contrôle on/off** par le propriétaire via WhatsApp
- **Mémoire long-terme** SQLite
- **Page confidentialité** `/privacy`

---

## 📊 VALEUR AJOUTÉE — Récapitulatif global

### Intelligence linguistique

| Capacité | Détail |
|---|---|
| **157 intents NLP** | Le bot comprend 157 intentions différentes (salutation, produit, commande, livraison, paiement, SAV...) |
| **25 076 patterns** | Phrases d'entraînement en 4 langues (MSA, Derja arabe, Arabizi, Français) |
| **19 134 corrections** | Fautes de frappe automatiquement corrigées avant traitement |
| **170+ mappings darija→FR** | Traduction automatique des mots darija pour la recherche catalogue |
| **72 familles produit** | Reconnaissance fine de chaque catégorie (poussette, biberon, robe, pantalon...) |
| **9 filtres de recherche** | Par budget, saison, marque, couleur, âge, rentrée scolaire... |

### Catalogue & Commerce

| Capacité | Détail |
|---|---|
| **10 102 produits** | Base SQLite complète avec prix, références, catégories |
| **Recherche fuzzy** | Tolère les fautes de frappe dans les noms de produits |
| **Système de commande** | Panier, calcul prix, choix livraison/retrait |
| **Paiement local** | BaridiMob, CCP, Edahabia, virement |
| **Livraison 58 wilayas** | Yalidine, ZR Express, stop-desk, domicile |

### Opérationnel

| Capacité | Détail |
|---|---|
| **Journal complet** | Tous les messages logués avec stats et cleanup auto |
| **Lexique admin** | Ajouter/modifier/supprimer des mots darija via interface web |
| **Widget web** | Intégré sur khemicishop.com avec visuels produits |
| **WhatsApp** | Bot WhatsApp opérationnel |
| **On/Off** | Contrôle du bot par le propriétaire via WhatsApp |

### Architecture

```
Browser/WhatsApp
    ↓
Hostinger PHP (chat-proxy.php / lexicon-api.php)
    ↓ HTTPS
Cloudflare DNS (DNS-only)
    ↓
VPS Hostinger (187.124.173.103)
    ↓
Traefik (SSL Let's Encrypt)
    ↓
Docker Container (Python 3.13-slim)
    ↓
Uvicorn → FastAPI
    ├── web_chat.py (widget web)
    ├── darija/normalizer.py (pré-correction orthographe)
    ├── nlp.py (classifieur ML TF-IDF + LogReg)
    ├── darija/lexicon.py (lexique admin)
    ├── database.py (SQLite: produits, commandes, journal)
    └── catalog.py (recherche produits)
```

---

## 📁 ARBORESCENCE FICHIERS CLÉS

```
chatbot_whatsapp/
├── app/
│   ├── main.py                    # Routes FastAPI (/web-chat, /health, /api/*)
│   ├── web_chat.py                # Logique chat web (157 intents, 170+ mappings)
│   ├── nlp.py                     # Classifieur ML (TF-IDF + Logistic Regression)
│   ├── database.py                # SQLite (produits, commandes, clients, journal)
│   ├── catalog.py                 # Recherche produits multi-critères
│   ├── normalize.py               # Normalisation texte (arabizi, diacritiques)
│   ├── console.py                 # Auth admin
│   └── darija/
│       ├── lexicon.py             # Système lexique (CRUD + ré-entraînement async)
│       ├── api.py                 # API lexique (/api/lexicon/*)
│       ├── journal_api.py         # API journal (/api/journal/*)
│       └── normalizer.py          # ✨ Pré-correction orthographe (19K variantes)
├── data/
│   ├── intents.yaml               # ✨ 157 intents, 25 076 patterns (629 KB)
│   ├── lexicon.yaml               # Lexique darija (188 entrées, 5 200 patterns)
│   ├── darija_variants.json       # ✨ Dictionnaire orthographe (19 134 variantes)
│   └── orders.db                  # SQLite (produits, commandes, journal)
├── Dockerfile
└── CHANGELOG.md                   # ← Ce fichier
```

---

*Dernière mise à jour : 08/10/2026 15:00*
