# 🚀 Déploiement du bot sur ton VPS (Hostinger + Coolify)

Ce guide te montre comment faire tourner le bot en **production** sur ton VPS,
puis obtenir l'URL HTTPS à brancher sur Meta/WhatsApp.

---

## 0. Prérequis

- Ton **VPS** avec **Coolify** déjà installé (accessible via un navigateur)
- Le code de ce projet **sur un dépôt Git** (GitHub ou GitLab) — voir étape 1
- Un **domaine** (optionnel mais recommandé pour avoir une URL propre et HTTPS)

---

## 1. Pousser le code sur GitHub

Depuis ton PC, dans le dossier `chatbot_whatsapp/` :

```bash
# 1) initialiser git (si pas déjà fait)
git init
git add .
git commit -m "Bot WhatsApp v1"

# 2) créer un dépôt sur GitHub, puis :
git remote add origin https://github.com/TON_COMPTE/bot-whatsapp.git
git push -u origin main
```

> Le `.gitignore` exclut déjà `.env`, `.venv`, les logs. **Ne pousse jamais ton `.env`.**

---

## 2. Créer l'application dans Coolify

1. Connecte-toi à **Coolify** (ton VPS).
2. Menu **New → Resource → Application**.
3. Choisis ta **source Git** (GitHub) et sélectionne le dépôt `bot-whatsapp`.
4. Coolify va détecter le **Dockerfile** automatiquement :
   - **Build Pack** : `Dockerfile`
   - **Port** : `8000`
5. Clique **Save**.

---

## 3. Ajouter les variables d'environnement (CRUCIAL)

Dans l'application Coolify → onglet **Environment Variables**, ajoute **toutes** les
variables du bot. Copie le contenu de ton `.env` ici (sans commentaires si tu veux).

```
PORT=8000
HOST=0.0.0.0

# WhatsApp (à remplir après config Meta)
WHATSAPP_TOKEN=
WHATSAPP_PHONE_ID=
WHATSAPP_VERIFY_TOKEN=monsecretunique

# Email (SMTP du commerçant)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=monmagasin@gmail.com
SMTP_PASSWORD=mdp_application
SMTP_USE_TLS=true
STORE_EMAIL_TO=responsable@duclient.com
EMAIL_FROM_NAME=Mon Magasin

# NLP
NL_MODE=hybrid
```

Puis **Save** et **Deploy**.

---

## 4. Obtenir l'URL HTTPS du bot

Après le premier build/deploy, Coolify te donne une URL de type :
- `https://bot-xxxxx.sous-domaine-de-ton-vps` (si tu as configuré un domaine)
- ou `http://IP_DU_VPS:8000`

**Pour un webhook WhatsApp, tu as besoin de HTTPS.** Deux options :
- **Option A (simple)** : associe un sous-domaine de TON domaine à cette app dans
  Coolify (Proxy → Domains → `bot.ton-domaine.com`). Coolify gère le certificat SSL
  automatiquement (Let's Encrypt).
- **Option B (si pas de domaine)** : utilise l'URL HTTPS fournie par Coolify.

> Note bien l'URL finale → **c'est elle qu'on mettra dans le webhook Meta.**

---

## 5. Vérifier que le bot répond

Une fois déployé, teste l'URL dans ton navigateur :

```
https://bot.ton-domaine.com/health
```

Tu dois voir :
```json
{"status":"ok","nl_mode":"hybrid"}
```

Et le webhook (vérification GET, sans token valide renverra 403) :
```
https://bot.ton-domaine.com/webhook?hub.mode=subscribe&hub.verify_token=XXX&hub.challenge=1
```

---

## 6. (Ensuite) Brancher sur WhatsApp

Une fois l'URL HTTPS obtenue, on la met dans le dashboard Meta :
- **Webhook URL** : `https://bot.ton-domaine.com/webhook`
- **Verify token** : celui de `WHATSAPP_VERIFY_TOKEN`
- Champs : `messages`

> C'est la partie qu'on fera juste après, avec la config Meta.

---

## 7. Mise à jour du bot (après avoir enrichi les intentions)

1. Modifie `data/intents.yaml` (avec ton interface locale) et pousse sur Git :
   ```bash
   git add data/intents.yaml
   git commit -m "ajout intentions"
   git push
   ```
2. Dans Coolify, clique **Deploy** (ou active le déploiement auto).

---

## 🔧 Débogage rapide

| Symptôme | Cause probable | Solution |
|---|---|---|
| Page `/health` ne répond pas | Le build a échoué | Voir les logs du build dans Coolify |
| Erreur SMTP au test | SMTP mal configuré | Vérifier SMTP_USER/PASSWORD (mot de passe applicatif) |
| Webhook Meta = "403" | verify token différent | Mettre le même token dans Meta et `.env` |
| `import sklearn` échoue | Dépendances pas installées | Vérifier `requirements.txt` + logs build |
