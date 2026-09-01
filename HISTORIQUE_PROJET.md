# 📋 Historique du projet — Bot WhatsApp pour commerce

> Journal des étapes réalisées. Mise à jour au fil de l'avancement.

---

## 🏁 Contexte

- **But** : créer un chatbot WhatsApp pour un client (commerce de produits physiques) qui :
  - répond aux questions des utilisateurs (produits, prix, livraison, horaires…)
  - récupère les commandes pas à pas
  - envoie chaque commande par email au commerçant (SMTP)
- **Langues** : français + arabe + derja algérienne + arabizi
- **Stack** : Python (FastAPI) + Docker + Coolify sur VPS Hostinger

---

## ✅ Étape 1 — Construction du code Python (TERMINÉ)

- Bot complet en Python/FastAPI :
  - `app/main.py` — webhook WhatsApp (GET vérification + POST messages)
  - `app/whatsapp.py` — client API WhatsApp Cloud (Meta Graph)
  - `app/nlp.py` — classifieur d'intentions (règles + scikit-learn, multilingue)
  - `app/responses.py` — réponses par intention
  - `app/order.py` — machine à états de commande
  - `app/catalog.py` — chargement catalogue produits
  - `app/email_sender.py` — envoi email SMTP
  - `app/config.py` — variables d'environnement
- **Testé** : classifieur 25/25, commande complète avec total correct, webhook complet.

## ✅ Étape 2 — Multilingue (arabe + derja) (TERMINÉ)

- Normalisation adaptée pour conserver l'arabe + chiffres arabizi (3/7/9…)
- `data/intents.yaml` très détaillé : **25 intentions** en arabe, derja, arabizi et français
- Alias produits en arabe/derja (`كاسك`, `تيشيرت`, `شاحن`, `حذاء`…)
- Confirmation de commande en arabe (`نعم`, `اه`, `ايوا`…)

## ✅ Étape 3 — Interface d'admin locale (TERMINÉ)

- **`admin_server.py`** — petit serveur Python (bibliothèque standard uniquement) qui écrit
  réellement dans `data/intents.yaml`.
- **`interface_admin.html`** — formulaire pour ajouter/modifier/supprimer des intentions.
- **`demarrer_admin.bat`** — lanceur Windows (double-clic).
- Corrigé le bug de sauvegarde (sync automatique des champs) et le bug de suppression
  (la suppression s'écrit désormais dans le fichier).

## ✅ Étape 4 — Déploiement VPS (TERMINÉ)

- Dockerfile validé (installe dépendances automatiquement)
- Code poussé sur **GitHub** : `courifadza-wq/ChatBot-khimissi`
- Application créée dans **Coolify** (Build Pack Dockerfile, port 8000)
- Déploiement réussi (rolling update completed)
- URL HTTPS temporaire obtenue : `https://jhcs2fooalz7vf6lzggkteix.187.124.173.103.sslip.io/`
- Vérifications : `/health` → `{"status":"ok"}`, `/webhook` → 403 (normal) et POST → ignored

## ✅ Étape 5 — Domaine propre + DNS (TERMINÉ)

- **Domaine** : `br-solution.tech` (DNS géré par **Cloudflare**)
- **VPS IP** : `187.124.173.103`
- Enregistrement DNS **A** créé sur Cloudflare :
  - `botkimissi.br-solution.tech` → `187.124.173.103` (DNS only / nuage gris)
- Vérifié : `ping botkimissi.br-solution.tech` → `187.124.173.103` ✅
- Domaine **ajouté dans Coolify** (Proxy → Domains), SSL automatique généré
- **Ancienne URL `sslip.io` retirée**

### ✅ URL finale du bot (EN LIGNE)
```
https://botkhimissi.br-solution.tech/health   →   {"status":"ok"}
```

### 🎯 URL du webhook (à utiliser pour Meta)
```
https://botkhimissi.br-solution.tech/webhook
```

---

## ⏳ Étape 6 — À FAIRE : Configuration Meta / WhatsApp

> À reprendre. Il faut :
1. Créer l'**application Meta** (developers.facebook.com) + produit **WhatsApp**
2. Récupérer :
   - **`WHATSAPP_TOKEN`** (System User token permanent)
   - **`WHATSAPP_PHONE_ID`** (Phone Number ID)
3. Configurer le **webhook** :
   - Callback URL : `https://botkhimissi.br-solution.tech/webhook`
   - Verify token : celui de `WHATSAPP_VERIFY_TOKEN` (dans `.env`)
   - Champs : **`messages`**
4. Remplir `WHATSAPP_TOKEN` + `WHATSAPP_PHONE_ID` dans les variables d'environnement
   Coolify, puis **redéployer**
5. Tester avec le **numéro de test** Meta, puis passer au **vrai numéro** du client

---

## 📌 Accès / comptes concernés

- **Client** : compte Meta Business (inviter le prestataire comme admin — sans donner de mot de passe)
- **Prestataire** : admin de l'application Meta
- **Domaine** : `br-solution.tech`, DNS sur Cloudflare
- **VPS** : Hostinger, `187.124.173.103`, Coolify

---

## 🧰 Fichiers clés du projet

| Fichier | Rôle |
|---|---|
| `app/main.py` | Webhook WhatsApp |
| `data/intents.yaml` | Intentions (à enrichir) |
| `data/products.yaml` | Catalogue produits |
| `admin_server.py` + `interface_admin.html` | Interface d'admin locale |
| `Dockerfile` | Build production |
| `demarrer_admin.bat` | Lanceur admin Windows |
| `HISTORIQUE_PROJET.md` | Ce fichier (journal) |
