# 🤖 Bot WhatsApp — Ventes & Commandes (Python)

Chatbot WhatsApp en Python (FastAPI) qui :
- répond aux **questions** des utilisateurs (produits, prix, livraison, horaires…)
- **récupère les commandes** pas à pas (machine à états)
- **envoie chaque commande par email** au commerçant (SMTP)

Zéro dépendance LLM payante par défaut : reconnaissance d'intention par **règles + classifieur ML** (scikit-learn).

### 🌍 Multilingue
Le bot comprend **4 formes** en simultané :
- **Arabe littéral** (فصحى)
- **Derja algérienne** (دارجة) — très détaillée
- **Arabizi** (derja en lettres latines : `bchhal`, `kifach`, `3lach`, `fin talbi`…)
- **Français**

→ Ajoute tes variantes dans `data/intents.yaml` (plus d'exemples = meilleure reconnaissance).
→ Les produits acceptent des **alias en arabe/derja** (`data/products.yaml`) : `كاسك` → Casque, `تيشيرت` → T-shirt, etc.

---

## 🧱 Stack
- **FastAPI + uvicorn** (API)
- **scikit-learn** (classifieur d'intention TF-IDF + LogisticRegression)
- **PyYAML** (catalogue + intentions configurables)
- **smtplib** (envoi email)
- Déploiement : **Docker** via **Coolify** sur VPS Hostinger

---

## 📁 Structure
```
chatbot_whatsapp/
├── app/
│   ├── config.py         # variables d'environnement
│   ├── main.py           # webhook FastAPI
│   ├── whatsapp.py       # client API WhatsApp Cloud
│   ├── nlp.py            # classifieur d'intentions
│   ├── responses.py      # réponses par intention
│   ├── order.py          # machine à états de commande
│   ├── catalog.py        # chargement du catalogue
│   └── email_sender.py   # envoi email SMTP
├── app/
│   └── admin_app.py      # interface d'admin locale (ajouter intentions)
├── admin/
│   └── editor.html       # page web de l'interface d'admin
├── data/
│   ├── products.yaml     # catalogue produits + livraison + paiement
│   └── intents.yaml      # intentions + exemples d'entraînement
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

## 🚀 Démarrage en local (dev)

```bash
cp .env.example .env   # puis remplir .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Vérifier : `GET http://localhost:8000/health` → `{"status":"ok"}`

---

## ☁️ Déploiement sur Coolify (VPS Hostinger)

### 1. Pousser le code sur un dépôt Git (GitHub/GitLab)
### 2. Dans Coolify
1. **New Resource → Application** → connecte ton dépôt.
2. **Build Pack : `Dockerfile`** (Coolify le détectera).
3. Règle le **port** : `8000`.
4. Dans **Environment Variables**, ajoute tout le contenu de `.env` :
   - `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID`, `WHATSAPP_VERIFY_TOKEN`
   - `SMTP_HOST/PORT/USER/PASSWORD`, `STORE_EMAIL_TO`
   - `PORT=8000`
5. **Deploy**.

Coolify génère une URL HTTPS du type `https://ton-bot.example.com`.

---

## 📲 Configuration WhatsApp Business (Meta) — essentiel

> ⚠️ C'est la partie la plus longue (approbation). À lancer **en 1er**.

1. Crée un **compte Meta Business** + une **application** dans le **Meta for Developers**.
2. Ajoute le produit **WhatsApp** → **Set up**.
3. **Ajoute le numéro** WhatsApp Business (ou test number). Le numéro doit être approuvé pour la production.
4. Récupère :
   - le **Token d'accès** (System User token permanent de préférence)
   - le **Phone Number ID**
5. Configure le **Webhook** dans l'appli :
   - **Callback URL** : `https://ton-bot.example.com/webhook`
   - **Verify token** : `WHATSAPP_VERIFY_TOKEN` (celui de ton `.env`)
   - **Subscribe to fields** : `messages`
6. Clique **Verify and Save**.

> Le webhook doit être accessible en HTTPS — Coolify fournit ça automatiquement.

---

## 🧪 Test de bout en bout

Envoie un message WhatsApp au numéro du bot :
1. `bonjour` → réponse de bienvenue
2. `quels sont vos produits` → catalogue
3. `je veux commander` → machine à états
4. Réponds : nom, adresse, produit (`2 casque bluetooth pro`), paiement, `oui`
5. → L'email part chez le commerçant + confirmation WhatsApp

---

## 🖥 Interface d'admin locale (alimenter le bot sans coder)

Un petit outil web **en local sur ton PC** pour ajouter/modifier des intentions
en **français, arabe ou derja**, re-entraîner le classifieur et tester en direct.

```bash
# dans le dossier du projet
source .venv/bin/activate
uvicorn app.admin_app:app --port 8080
# puis ouvre dans le navigateur :
#   http://localhost:8080
```

Ce que tu peux faire :
- ➕ Ajouter une **nouvelle intention** (ex: `recharge`)
- 📝 Ajouter des **phrases d'exemple** (plus il y en a, mieux c'est)
- 🔁 **Re-entraîner** le classifieur immédiatement
- 🧪 **Tester** une phrase → voir l'intention détectée
- 🛍 Modifier le **catalogue produits** et les **alias** arabes

> ⚠️ **Local uniquement** : ne pas exposer publiquement (aucune sécurité d'auth).
> Après l'édition, la sauvegarde s'écrit dans `data/intents.yaml` et `data/products.yaml`.
> Le **bot principal** charge les données à son démarrage → il suffit de le **redéployer**
> (ou redémarrer) après une session d'admin, OU de re-trainer via `/api/intents`.

## 🛠 Personnaliser

- **Produits / livraison / paiement** : édite `data/products.yaml` (ou via l'admin)
- **Intentions / phrases d'exemple** : édite `data/intents.yaml` (ou via l'admin)
- **Réponses** : édite `app/responses.py`
- **Fallback intelligent** : si le bot ne comprend pas, il redirige vers le responsable.

---

## 🔒 Sécurité & production
- Ne jamais commiter le `.env`.
- Pour la mémoire des sessions en production (multi-instance), remplacer le dict en mémoire par **Redis**.
- Mettre un **plafond** côté Meta et, si tu ajoutes un LLM, côté fournisseur.

---
*Projet construit pour un client — déploiement VPS Hostinger + Coolify.*
