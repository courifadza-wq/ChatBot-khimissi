# 🚀 DÉMARRAGE RAPIDE — Planet Kids (Windows)

## 1️⃣ Installation — UNE SEULE FOIS

```powershell
cd C:\Users\Fujitsu\Downloads\boutique\darlila\frontend-vue
npm install
```
⏳ 1 à 2 minutes. À la fin : `added 38 packages`.

---

## 2️⃣ Lancer le site — À CHAQUE FOIS (2 fenêtres PowerShell)

### 🖥️ Terminal 1 — l'API (le moteur)

```powershell
cd C:\Users\Fujitsu\Downloads\boutique\darlila\api-mock
node server.js
```
✅ Vous devez voir :
```
API de simulation Planet Kids démarrée sur http://127.0.0.1:8000
Admin (Sanctum simulé) : admin@planetkids.dz / password
```
⚠️ **Laissez cette fenêtre ouverte !** (fermer = couper le moteur)

### 🖥️ Terminal 2 — le site (nouvelle fenêtre PowerShell)

```powershell
cd C:\Users\Fujitsu\Downloads\boutique\darlila\frontend-vue
npm run dev
```
✅ Vous devez voir :
```
VITE v6.x.x  ready in XXX ms
➜  Local:   http://localhost:5173/
```

---

## 3️⃣ Accéder à la boutique

🌐 **http://localhost:5173**

C'est le site que voient vos clients : catalogue (1000 produits de démo),
recherche, filtres, panier, commande via WhatsApp, langues FR/AR.

---

## 4️⃣ Accéder à l'administration

🌐 **http://localhost:5173/admin**

| | |
|---|---|
| 📧 E-mail | `admin@planetkids.dz` |
| 🔑 Mot de passe | `password` |

### Ce que vous pouvez y faire

| Onglet | Actions |
|---|---|
| **Produits** | Créer / modifier / supprimer, recherche, pagination, ⭐ vedette, interrupteur actif, **Importer CSV** (en masse), **Exporter CSV** (modèle) |
| **Commandes** | Statistiques, filtres par statut, détail dépliable, changer le statut, **Exporter CSV (comptabilité)** |

💡 **Test complet d'une commande** :
1. Sur la boutique → ajoutez au panier → « Commander via WhatsApp »
2. Remplissez nom / téléphone / wilaya → confirmez
3. Dans l'admin → **Commandes** → votre commande apparaît avec sa référence `DL-XXXXXX` !

---

## 5️⃣ Arrêter le site

Dans chaque terminal : **Ctrl + C** (ou fermez simplement les fenêtres).

---

## 🔧 Problèmes fréquents

| Symptôme | Cause | Solution |
|---|---|---|
| `'vite' n'est pas reconnu` | Dépendances non installées | `npm install` dans `frontend-vue` |
| Boutique vide / « Impossible de charger » | Terminal 1 (API) fermé | Relancez `node server.js` dans `api-mock` |
| `Le port 5173 est déjà utilisé` | Un `npm run dev` tourne déjà | Utilisez l'URL alternative affichée (5174) ou fermez l'ancien |
| Page maintenance affichée | Mode maintenance activé | `POST http://127.0.0.1:8000/api/maintenance {"state":"off"}` ou redémarrez l'API |
| Session admin expirée | Token révoqué | Reconnectez-vous (comportement normal) |

---

## 📌 Rappel des adresses

| Adresse | Description |
|---|---|
| `http://localhost:5173` | 🛍️ La boutique |
| `http://localhost:5173/admin` | 🔐 L'administration |
| `http://127.0.0.1:8000/api/products` | ⚙️ L'API (JSON — pour les curieux) |

> **En production** (après déploiement Hostinger) : la boutique sera sur
> `https://votre-domaine.com` et l'admin sur `https://votre-domaine.com/admin` —
> mêmes identifiants, définis dans le `.env` du serveur (ADMIN_EMAIL / ADMIN_PASSWORD).
