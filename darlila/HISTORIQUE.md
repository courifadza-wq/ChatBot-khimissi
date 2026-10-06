# 📋 Historique du projet — Chatbot Web Planète Kids (khemicishop.com)

> Généré le 04/10/2026 — Projet : migration WhatsApp → Widget Chat Web

---

## 🎯 Objectif

Le client (Planète Kids) a demandé d'**abandonner le bot WhatsApp** et d'intégrer un chatbot directement sur le site **khemicishop.com**, capable de répondre aux questions sur les produits, la livraison, les commandes — en français et en arabe/darija.

---

## 🏗️ Architecture finale

```
khemicishop.com (Hostinger — Apache/PHP)
├── index.html               ← Site Vue.js 3 + Vite (SPA)
├── assets/                  ← JS + CSS compilés par Vite
│   ├── index-DcSMJIzy.js
│   ├── index-D_hss2HM.css
│   ├── workbox-window.prod.es5-BBnX5xw4.js
│   └── xlsx-CkFp8p6R.js
├── chat-proxy.php           ← Proxy PHP → bot VPS (NOUVEAU)
└── api.khemicishop.com/     ← API Laravel (inchangée)

botkhimissi.br-solution.tech (VPS Coolify — FastAPI)
└── app/
    ├── main.py              ← POST /chat + CORS (MODIFIÉ)
    ├── web_chat.py          ← Logique bot web (CRÉÉ)
    ├── catalog.py           ← smart_search, format_search_results
    ├── database.py          ← SQLite, search_products, fuzzy
    ├── order.py             ← Machine à états commande
    ├── email_sender.py      ← Envoi email + Excel
    └── excel_export.py      ← Génération fichier Excel
```

---

## 📁 Fichiers modifiés / créés

### Backend FastAPI (`chatbot_whatsapp/`)

| Fichier | Action | Description |
|---|---|---|
| `app/main.py` | Modifié | Ajout CORS middleware + `ChatRequest` model + `POST /chat` endpoint |
| `app/web_chat.py` | Créé | Module complet logique bot pour le web (NLP, recherche, commande, email) |
| `app/catalog.py` | Modifié | Header catalogue simplifié (suppression du compteur d'articles) |
| `app/excel_export.py` | Modifié | Fix bug : utilise `it.get("price", 0)` au lieu de `p["name"]` (KeyError corrigé) |

### Frontend Vue.js (`frontend-vue/`)

| Fichier | Action | Description |
|---|---|---|
| `src/components/ChatBotWidget.vue` | Créé | Widget chat complet : bulle flottante, panneau, typing indicator, session UUID |
| `src/views/HomeView.vue` | Modifié | Remplacement `<WhatsAppFloat />` par `<ChatBotWidget />` |
| `.env.production` | Modifié | Ajout `VITE_BOT_URL=https://botkhimissi.br-solution.tech` |

### Hostinger (`public_html/`)

| Fichier | Action | Description |
|---|---|---|
| `chat-proxy.php` | Créé | Proxy PHP : reçoit les requêtes du widget → transmet au bot VPS |

---

## 🔄 Étapes réalisées

### Étape 1 — Endpoint `/chat` sur le bot FastAPI

Ajout dans `app/main.py` :
```python
class ChatRequest(BaseModel):
    message: str
    session_id: str

@app.post("/chat")
async def web_chat_endpoint(body: ChatRequest):
    reply = get_bot_reply(body.session_id, body.message)
    return {"reply": reply}
```
→ Le bot peut recevoir des messages depuis le web, pas seulement WhatsApp.

---

### Étape 2 — CORS pour khemicishop.com

Ajout dans `app/main.py` :
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://khemicishop.com",
        "https://www.khemicishop.com",
        "http://localhost:5173",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```
→ Autorise le navigateur à appeler le bot depuis le site.

---

### Étape 3 — Module `web_chat.py`

Logique bot adaptée pour le web :
- Utilise un **session_id UUID** (localStorage navigateur) au lieu du numéro de téléphone
- Même NLP (scikit-learn), même recherche SQLite, même flux commande
- Retourne une **string** au lieu d'appeler `send_text_message()`
- Sur CONFIRMED : envoie email + Excel, sauvegarde en DB, reset session
- Langues : français + arabe/darija détectés automatiquement

**Fix appliqués dans `web_chat.py` :**
- Utilisation de `smart_search()` (avec fuzzy matching) au lieu de `search_products` direct → résout "0 résultats pour robe"
- Ajout des salutations arabes dans le bail-out de commande → "سلام عليكم" en cours de commande reset proprement la session

---

### Étape 4 — Widget Vue.js `ChatBotWidget.vue`

Composant complet :
```
[💬] ← Bouton FAB rose/bleu en bas à droite
  ↓ (clic)
┌─────────────────────────┐
│ 🛍️ Planète Kids         │
│ En ligne ●              │
├─────────────────────────┤
│  Bonjour 👋 Bienvenue ! │
│                         │
│                [bonjour]│
│  Bonjour ! ...          │
│                         │
│  ● ● ● (typing...)      │
├─────────────────────────┤
│ [Votre message...] [➤]  │
└─────────────────────────┘
```

Fonctionnalités :
- Session persistante via `localStorage` (UUID unique par navigateur)
- Indicateur "en train d'écrire" (typing indicator)
- Couleurs du site : `#2d3590` (bleu) + `#ea2f90` (rose)
- Fonts du site : Baloo 2, Quicksand
- Responsive mobile

---

### Étape 5 — Intégration dans `HomeView.vue`

```vue
<!-- AVANT (ligne 20 + 88) -->
import WhatsAppFloat from '../components/WhatsAppFloat.vue'
...
<WhatsAppFloat />

<!-- APRÈS -->
import ChatBotWidget from '../components/ChatBotWidget.vue'
...
<ChatBotWidget />
```

---

### Étape 6 — Proxy PHP `chat-proxy.php`

**Problème rencontré :** Le navigateur de l'utilisateur (Algérie) ne pouvait pas atteindre `botkhimissi.br-solution.tech` directement (problème réseau/ISP).

**Solution :** Proxy PHP sur Hostinger — même domaine que le site → plus de CORS ni de blocage réseau.

```
Navigateur (Algérie)
    ↓ fetch('/chat-proxy.php')
Hostinger (khemicishop.com)
    ↓ curl → botkhimissi.br-solution.tech/chat
VPS (FastAPI bot)
    ↓ {"reply": "..."}
Navigateur ← réponse affichée dans le widget
```

---

## 🧪 Tests réalisés

| Test | Résultat |
|---|---|
| `POST /chat` depuis VPS (curl) | ✅ `{"reply":"Bonjour 👋 Bienvenue..."}` |
| CORS preflight OPTIONS depuis VPS | ✅ Headers corrects |
| Widget visible sur khemicishop.com | ✅ |
| `chat-proxy.php` → réponse bot | ✅ |
| Email + Excel sur commande confirmée | ✅ (testé précédemment) |

---

## 🔧 Informations techniques

| Paramètre | Valeur |
|---|---|
| **Bot URL** | `https://botkhimissi.br-solution.tech` |
| **VPS** | Hostinger `srv1519486` — IP `187.124.173.103` |
| **Coolify** | v4.3.23 — container `vkgblr0q5yn6uomwylnajei6` |
| **DB bot** | `/app/data/bot_memory.db` (SQLite) — 10 102 produits |
| **Email commandes** | `planetekidshop@gmail.com` |
| **Framework site** | Vue.js 3 + Vite + Pinia |
| **Framework bot** | FastAPI + Uvicorn + scikit-learn |

---

## ✅ Fonctionnalités du bot web

| Fonctionnalité | État |
|---|---|
| Réponses en Français | ✅ |
| Réponses en Arabe / Darija | ✅ |
| Recherche produits (10 102 articles, SQLite) | ✅ |
| Nouveaux produits → connus automatiquement | ✅ |
| Flux commande complet (nom → adresse → articles → confirmation) | ✅ |
| Email + Excel envoyé à planetekidshop@gmail.com | ✅ |
| Salutations arabes reset session commande | ✅ |
| Session persistante par navigateur (UUID localStorage) | ✅ |

---

## ⏳ À faire (prochaines étapes)

- [ ] Corriger les intents arabes/darija dans le NLP (améliorer détection)
- [ ] Supprimer / modifier le bouton "Commander sur WhatsApp" dans le Hero
- [ ] Dashboard admin (voir commandes en temps réel)
- [ ] Vérification Meta pour passer de 250 → 1000 messages/jour (si WhatsApp réactivé)
