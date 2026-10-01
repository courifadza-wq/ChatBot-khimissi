# 💾 Configuration du Volume Persistant — Coolify (VPS Hostinger)

> Ce guide explique comment configurer le volume persistant pour que la mémoire
> long-terme du bot (base SQLite `bot_memory.db`) **survive aux redémarrages**
> et aux mises à jour du conteneur.

---

## Pourquoi c'est important ?

Sans volume persistant :
- ❌ À chaque redémarrage ou nouveau déploiement → la DB est effacée
- ❌ Tous les clients et commandes sont perdus
- ❌ Le bot redevient comme "neuf" à chaque mise à jour

Avec le volume persistant :
- ✅ La DB survit aux mises à jour du code
- ✅ La DB survit aux redémarrages du conteneur
- ✅ Les données clients et commandes sont permanentes

---

## Étape 1 — Ouvrir l'application dans Coolify

1. Connecte-toi à ton **Coolify** (ton VPS Hostinger)
2. Va dans **Projects → ChatBot-Khimissi → production**
3. Clique sur **chat-bot-khimissi**

---

## Étape 2 — Ajouter le volume persistant

1. Dans l'application, clique sur l'onglet **"Storages"** (ou "Volumes")
2. Clique **"+ Add"** (Ajouter un volume)
3. Remplis les champs :

   | Champ | Valeur |
   |---|---|
   | **Source (Host Path)** | `/data/chatbot-khimissi` |
   | **Destination (Container Path)** | `/app/data` |
   | **Type** | Bind Mount |

4. Clique **Save** puis **Redeploy**

> ⚠️ Le chemin `/app/data` est **obligatoire** — c'est là que le bot cherche `bot_memory.db`.

---

## Étape 3 — Vérifier que la mémoire fonctionne

Après le redéploiement, teste dans le terminal de Coolify (ou via SSH) :

```bash
# Vérifie que le fichier DB existe sur le VPS
ls -la /data/chatbot-khimissi/
# → doit afficher : bot_memory.db

# Vérifie son contenu
sqlite3 /data/chatbot-khimissi/bot_memory.db ".tables"
# → doit afficher : clients   orders
```

Ou via l'API admin du bot :
```
GET https://botkhimissi.soluciontech.../api/stats
```
Réponse attendue :
```json
{
  "total_clients": 0,
  "total_orders": 0,
  "ca_total_dzd": 0,
  "top_clients": []
}
```

---

## Étape 4 — Pousser le code mis à jour sur GitHub

Depuis ton PC, dans le dossier `chatbot_whatsapp/` :

```bash
git add app/database.py app/main.py app/order.py app/responses.py app/admin_app.py Dockerfile
git commit -m "feat: mémoire long-terme SQLite (clients + commandes)"
git push
```

Puis dans Coolify → **Deploy** (ou le déploiement auto se déclenche).

---

## Ce qui change pour le client (expérience utilisateur)

### Nouveau client (première commande)
```
Client  : "Je veux commander"
Bot     : "Très bien ! Pour enregistrer votre commande, quel est votre nom complet ?"
Client  : "Karim Benaissa"
Bot     : "Merci ! Quelle est votre adresse de livraison ?"
...
Bot     : "✅ Commande confirmée !"  ← profil sauvegardé en DB
```

### Client fidèle (2ème commande +)
```
Client  : "Bonjour"
Bot     : "Bon retour Karim ! 🎉 (Vous avez passé 1 commande chez nous)"

Client  : "Je veux commander"
Bot     : "Parfait 🛒 ! Je vous reconnais, Karim !
           Voulez-vous commander avec les mêmes infos ?
           • Nom    : Karim Benaissa
           • Adresse : 12 Rue Didouche, Alger
           Répondez oui pour confirmer."

Client  : "oui"
Bot     : "Parfait ! 👤 Karim  📍 12 Rue Didouche
           Quel(s) produit(s) voulez-vous ?"
           ← NOM + ADRESSE pré-remplis automatiquement !
```

---

## Endpoints admin disponibles (en local)

Lancer l'admin : `uvicorn app.admin_app:app --port 8080`

| Endpoint | Description |
|---|---|
| `GET /api/clients` | Liste de tous les clients connus |
| `GET /api/clients/{phone}/orders` | Historique d'un client spécifique |
| `GET /api/stats` | Statistiques globales (clients, commandes, CA) |
| `GET /api/health` | Santé du serveur |

Exemple :
```bash
curl http://localhost:8080/api/stats
```

---

## Structure de la base de données

### Table `clients`
| Colonne | Type | Description |
|---|---|---|
| `phone` | TEXT | Numéro WhatsApp (clé primaire) |
| `name` | TEXT | Nom complet |
| `address` | TEXT | Dernière adresse de livraison |
| `preferred_payment` | TEXT | Dernier mode de paiement |
| `order_count` | INTEGER | Nombre total de commandes |
| `first_seen` | TEXT | Date de première commande |
| `last_seen` | TEXT | Date de dernière activité |

### Table `orders`
| Colonne | Type | Description |
|---|---|---|
| `id` | INTEGER | Identifiant auto-incrémenté |
| `phone` | TEXT | Numéro WhatsApp |
| `name` | TEXT | Nom à la commande |
| `address` | TEXT | Adresse à la commande |
| `items` | TEXT | JSON : `[{"name": "Casque", "qty": 2}]` |
| `total` | INTEGER | Montant total en DZD |
| `payment` | TEXT | Mode de paiement choisi |
| `created_at` | TEXT | Date/heure ISO 8601 |

---

## 🔒 Sécurité

> [!WARNING]
> Le fichier `bot_memory.db` contient les **données personnelles** des clients
> (noms, adresses, téléphones). Il ne doit jamais être exposé publiquement.

- Le volume `/data/chatbot-khimissi` est accessible uniquement sur le VPS
- L'interface admin (`/api/clients`) est **locale uniquement** — ne pas exposer sur le domaine public
- Prévoir une **sauvegarde régulière** du fichier DB (ex: cron + copie vers S3)

---

## Sauvegarde automatique (optionnel)

Ajouter un cron sur le VPS pour sauvegarder la DB chaque nuit :

```bash
# Sur le VPS (via SSH ou terminal Coolify)
# Édite le cron : crontab -e

# Sauvegarde à 2h du matin, garde les 7 derniers jours
0 2 * * * cp /data/chatbot-khimissi/bot_memory.db /data/chatbot-khimissi/backup_$(date +\%Y\%m\%d).db && find /data/chatbot-khimissi -name "backup_*.db" -mtime +7 -delete
```
