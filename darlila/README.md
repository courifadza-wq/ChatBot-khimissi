# 🛍️ Planet Kids — Khemici Shop (Laravel + Vue.js)

Refonte complète du site **[arsenaldza-coif.github.io/boutique1](https://arsenaldza-coif.github.io/boutique1/)**
(Dar Lila — parfums, cosmétiques & articles bébé) en application moderne :

| Couche | Technologie | Rôle |
|---|---|---|
| **Backend** | Laravel 12 (API REST) | Catalogue, commandes, **authentification Sanctum**, **administration**, **notifications e-mail** |
| **Frontend** | Vue 3 + Vite + Pinia + Vue Router | SPA : boutique publique **+ espace d'administration** |
| **Simulation** | Node.js (zéro dépendance) | `api-mock/` reproduit l'API Laravel (auth + admin incluses) pour développer sans PHP |

---

## ✨ Fonctionnalités

### 🛒 Boutique publique (Vue 3)
- **Design fidèle** au site d'origine : palette ivoire/or/indigo, polices Playfair Display + Jost,
  séparateurs zellige, bandeau WhatsApp défilant, hero avec parallaxe, animations au scroll.
- **Catalogue paginé côté serveur — conçu pour 1000+ produits** : recherche et filtres
  exécutés par l'API (24 produits/page), bouton « Charger plus », hydratation du panier
  par identifiants (`GET /api/products?ids=…`) pour que les articles d'autres pages
  s'affichent toujours correctement.
- **Filtres par catégorie** (puces) + **recherche instantanée** (debounce, FR et AR).
- **Promotions « achetez N → -X % »** : badge sur la carte, prix barré dans la
  fiche produit et le panier dès le seuil atteint, remise recalculée côté
  serveur à la commande (et visible dans le message WhatsApp).
- **Section « Nos lots »** : chaque lot présente ses produits dans un
  **carrousel automatique détaillé** (image, nom, description, quantité,
  prix unitaire par slide, barre de progression, pause au survol, flèches
  et points de navigation), prix cumulé barré + prix du lot + économie.
  Lots « en vedette » (★) en tête de section avec badge dorée.
  Les lots **« en vedette »** (★, bascule dans l'admin) s'affichent en tête
  de la section avec une badge dorée « Notre coup de cœur ».
- **Liens directs produits** : `https://votre-site/produit/{slug}` ouvre la
  fiche (bouton « 🔗 Lien » dans l'admin pour le copier).
- **Fiche produit** en modale : quantité, ajout au panier, commande directe WhatsApp.
- **Panier persistant** (localStorage) avec recommandations produits dans le tiroir.
- **Checkout en 3 étapes** : panier → coordonnées (nom, téléphone, **wilaya parmi les 58**) → confirmation.
- **Commande enregistrée en base** (prix recalculés côté serveur), récapitulatif
  **pré-rempli sur WhatsApp** avec référence, **e-mail automatique au vendeur**.
- **Bilingue FR / AR** avec bascule RTL instantanée, galerie + visionneuse, avis clients,
  localisation + carte Google Maps, responsive mobile.

### 🔐 Espace d'administration (`/admin`)
- **Authentification Sanctum** (tokens Bearer) : `POST /api/auth/login` délivre un token,
  routes `/api/admin/*` protégées par `auth:sanctum` + middleware `admin` (`is_admin` en base).
  Connexion limitée à 6 tentatives/minute (throttle), token révoqué à la déconnexion.
- **Gestion des produits** : création / modification / suppression, champs FR **et** AR,
  prix, slug auto-généré, catégorie, **image par URL ou téléversement de fichier**
  (JPG/PNG/WebP ≤ 2 Mo → disque `public`, servi via `/storage/products/…`).
- **Gros catalogues (1000+ produits)** : liste admin **paginée** (recherche serveur,
  20/page) + **import en masse CSV ou Excel (.xlsx)** (création/mise à jour
  par slug, séparateur `,`/`;` auto-détecté, rapport d'erreurs ligne par
  ligne) et **export CSV ou Excel (.xlsx)**. Indispensable pour saisir
  1000 produits d'un coup. Les fichiers .xlsx sont convertis dans le
  navigateur (SheetJS) — aucune dépendance serveur.
- **Interrupteurs rapides** dans la liste : *en vedette* (★) et *actif* — les produits
  vedettes s'affichent **en tête de la boutique** (premières positions, avant les
  autres) ; un produit désactivé disparaît immédiatement.
- **Compression WebP automatique** : chaque image téléversée via l'admin est
  convertie en WebP optimisé et redimensionnée (1600 px max, qualité 82) via
  Intervention Image — **30 à 70 % de poids en moins**. Pour les catalogues
  importés en masse : `php artisan shop:images:webp [--limit=] [--quality=]`
  convertit toutes les images existantes (URL externes incluses) et met à jour
  la base, avec rapport de compression détaillé.
- **Gestion des catégories** : création, renommage (FR/AR), description,
  ordre d'affichage — suppression **refusée** si des produits y sont
  rattachés (message explicite), compteurs de produits par catégorie.
- **Gestion des lots** : composez un lot (recherche de produits + quantités),
  fixez son prix — la valeur cumulée, l'économie et le % s'affichent partout.
  Mise en vedette (★) et bascule d'activation directement dans la liste.
- **Promotions produits** : deux champs dans le formulaire (quantité
  déclencheuse + pourcentage), validation intégrée.
- **Suivi des commandes** : statistiques (commandes, articles, chiffre d'affaires,
  en attente), filtres par statut, détail dépliable (articles, client, note),
  changement de statut : nouvelle → confirmée → expédiée → livrée / annulée,
  et **export CSV comptable** (`?status=&from=&to=`) : référence, date, client,
  téléphone, wilaya, articles, détail, total DA, statut.

### 📧 Notifications e-mail au vendeur
- À chaque commande : e-mail `App\Notifications\OrderPlaced` (Markdown, tableau des
  articles, montant, coordonnées client, bouton vers l'admin).
- File d'attente (`ShouldQueue`) — envoi immédiat avec `QUEUE_CONNECTION=sync`.
- `rescue()` autour de l'envoi : une panne SMTP n'interrompt jamais la commande.
- `MAIL_MAILER=log` par défaut → le message s'écrit dans `storage/logs/laravel.log`.

---

## 📁 Structure du projet

```
darlila/
├── backend-laravel/               # API REST Laravel 12
│   ├── app/
│   │   ├── Http/Controllers/
│   │   │   ├── AuthController.php        # login / me / logout (Sanctum)
│   │   │   ├── Admin/ProductController.php  # CRUD produits (upload inclus)
│   │   │   ├── Admin/OrderController.php    # suivi + statut des commandes
│   │   │   └── … (catalogue public, commande)
│   │   ├── Http/Middleware/EnsureUserIsAdmin.php
│   │   ├── Http/Resources/            # Product, Category, Review, Gallery, Order…
│   │   ├── Models/                    # + User (HasApiTokens)
│   │   └── Notifications/OrderPlaced.php   # e-mail vendeur
│   ├── database/
│   │   ├── migrations/                # 9 tables (+ users, personal_access_tokens)
│   │   └── seeders/                   # + UserSeeder (compte admin)
│   └── routes/api.php
│
├── frontend-vue/                  # SPA Vue 3 + Vite + Pinia + Vue Router
│   └── src/
│       ├── views/                     # HomeView + Admin (Login/Products/Orders)
│       ├── components/admin/          # AdminLayout, AdminProductForm
│       ├── api/client.js              # fetch + token Bearer + multipart
│       ├── stores/                    # shop, cart, ui + admin (session, toasts)
│       ├── router/                    # routes + garde d'authentification
│       ├── i18n/                      # FR/AR + RTL
│       └── assets/                    # styles boutique + admin
│
└── api-mock/server.js             # Simulation Node de l'API (auth + admin + upload)
```

---

## 🚀 Installation

### Prérequis
- **PHP ≥ 8.2** + Composer (backend) — **Node.js ≥ 18** (frontend)
- **MySQL 5.7+ / MariaDB 10.3+** (ou SQLite pour tester sans installation)

### 1) Backend Laravel

```bash
# 1. Créer la base de données (MySQL) — sur Hostinger : hPanel → Bases de données MySQL
mysql -u root -p -e "CREATE DATABASE darlila CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 2. Installer et configurer
cd backend-laravel
composer install
cp .env.example .env          # DB_CONNECTION=mysql par défaut — ajustez DB_* si besoin
php artisan key:generate

# 3. Migrations + seeders + lien storage (une seule commande)
composer setup

php artisan serve            # → http://127.0.0.1:8000
```

> 💡 **Démo sans MySQL** : commentez le bloc MySQL et décommentez `DB_CONNECTION=sqlite`
> dans `.env` — le fichier se crée tout seul au premier `php artisan migrate`.
> 📧 **E-mails réels** : passez `MAIL_MAILER=smtp` et renseignez `MAIL_HOST`, etc.
> (avec `log`, chaque commande écrit l'e-mail dans `storage/logs/laravel.log`).

### 2) Frontend Vue

```bash
cd frontend-vue
npm install
npm run dev                   # → http://localhost:5173
```

En développement, Vite **proxifie `/api` et `/storage`** vers `http://127.0.0.1:8000`
(modifiable via `API_PROXY_TARGET`). En production : `VITE_API_BASE_URL=https://votre-api.dz`
+ `npm run build` → `dist/`.

### 3) Mode simulation (sans PHP)

```bash
node api-mock/server.js       # mêmes endpoints, auth admin et upload inclus
cd frontend-vue && npm run dev
```

### 4) Accéder à l'administration

| | |
|---|---|
| **URL** | `http://localhost:5173/admin` |
| **E-mail** | `admin@darlila.dz` |
| **Mot de passe** | `password` |

> ⚠️ **Production** : changez `ADMIN_EMAIL` / `ADMIN_PASSWORD` dans `.env`
> **avant** `php artisan db:seed`, et régénérez `APP_KEY`.

---

### 🎬 Vidéos du hero (diaporama)

Déposez simplement vos vidéos dans le dossier **frontend-vue/public/** :

- `frontend-vue/public/hero-video.mp4`
- `frontend-vue/public/hero2-video.mp4`

Elles sont **détectées automatiquement** et intégrées au diaporama du hero :
image (7 s) → vidéo 1 (7 s) → vidéo 2 (7 s) → image… — lecture muette,
fondu enchaîné, parallaxe conservée. Fichiers absents = aucune erreur
(l'image seule s'affiche). En production, Vite les copie dans le build et
l'outil de déploiement les téléverse automatiquement. Conseil : vidéos
muettes H.264 de moins de 10 Mo (voir public/LISEZ-MOI.txt) ; pour des
vidéos lourdes, préférez Bunny Stream.

## 🔌 Endpoints de l'API

### Publics

| Méthode | URI | Description |
|---|---|---|
| `GET` | `/api/settings` | Réglages publics (WhatsApp, adresse, horaires…) |
| `GET` | `/api/categories` | 8 catégories + nombre de produits |
| `GET` | `/api/products` | Produits **actifs** — `?category=&search=&featured=1&page=&per_page=` (paginé, meta incluse) · `?ids=1,5,9` (panier) · `?per_page=all` |
| `GET` | `/api/products/{slug}` | Détail d'un produit (404 si inconnu) |
| `GET` | `/api/reviews` · `/api/gallery` | Avis clients · galerie |
| `GET` | `/api/bundles` | Lots actifs (composition, valeur cumulée, économie) |
| `POST` | `/api/orders` | Commande (produits avec promo **et/ou** lots via `bundle_id`) → référence + lien WhatsApp + **e-mail vendeur** |

### Authentification (Sanctum)

| Méthode | URI | Description |
|---|---|---|
| `POST` | `/api/auth/login` | `{ email, password }` → `{ token, user }` (throttle 6/min) |
| `GET` | `/api/auth/me` | Utilisateur courant — en-tête `Authorization: Bearer <token>` |
| `POST` | `/api/auth/logout` | Révoque le token courant |

### Administration (token admin requis)

| Méthode | URI | Description |
|---|---|---|
| `GET` | `/api/admin/products` | Tous produits — **paginé** `?search=&category=&page=&per_page=` |
| `POST` | `/api/admin/products` | Création — JSON avec `image_url` **ou** multipart avec fichier `image` |
| `POST` | `/api/admin/products/import` | **Import CSV en masse** (multipart, champ `file`) — upsert par slug |
| `GET` | `/api/admin/products/export` | **Export CSV** de tout le catalogue (modèle d'import) |
| `PUT/PATCH` | `/api/admin/products/{id}` | Mise à jour complète ou partielle (`{is_active:false}`) |
| `DELETE` | `/api/admin/products/{id}` | Suppression |
| `GET/POST/PUT/DELETE` | `/api/admin/bundles[/{id}]` | CRUD des lots |
| `GET` | `/api/admin/orders` | Commandes + articles — `?status=nouvelle` |
| `GET` | `/api/admin/orders/export` | **Export CSV comptable** — `?status=&from=&to=` |
| `PATCH` | `/api/admin/orders/{id}/status` | Changement de statut |

### Exemples

**Connexion admin :**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@darlila.dz","password":"password"}'
# → { "data": { "token": "1|abc…", "user": {…} } }
```

**Créer un produit (multipart avec image) :**
```bash
curl -X POST http://127.0.0.1:8000/api/admin/products \
  -H "Authorization: Bearer $TOKEN" \
  -F category_id=5 -F name_fr="Parfum Ambre" -F name_ar="عطر العنبر" \
  -F price=5900 -F is_active=1 -F image=@parfum.jpg
```

**Passer commande (public) :**
```bash
curl -X POST http://127.0.0.1:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"Sarah Benali","customer_phone":"0555 12 34 56",
       "wilaya":"16 — Alger","lang":"fr",
       "items":[{"product_id":9,"quantity":2},{"product_id":13,"quantity":1}]}'
```
→ `201` : référence `DL-…`, total recalculé côté serveur, `whatsapp_url` pré-rempli,
et e-mail envoyé au vendeur (`SELLER_EMAIL`).

**Erreurs de validation (422), format Laravel :**
```json
{ "message": "Les données fournies sont invalides.",
  "errors": { "customer_phone": ["Le format du téléphone est invalide."] } }
```

---

## ⚙️ Personnalisation

| Quoi | Où |
|---|---|
| Identifiants admin | `.env` → `ADMIN_EMAIL` / `ADMIN_PASSWORD` (avant le seed) |
| E-mail vendeur (notifications) | `.env` → `SELLER_EMAIL` (ou réglage `seller_email` en base) |
| Numéro WhatsApp | `.env` → `WHATSAPP_NUMBER` |
| SMTP (vrais e-mails) | `.env` → `MAIL_MAILER=smtp` + `MAIL_HOST`… |
| Images produits | URL externe ou `/storage/products/…` (`php artisan storage:link`) |
| Origines CORS | `.env` → `CORS_ALLOWED_ORIGINS` |
| Traductions interface | `frontend-vue/src/i18n/fr.js` · `ar.js` |

---

### 📲 PWA — installable comme une application

La boutique est une **Progressive Web App** complète (via `vite-plugin-pwa`) :

- **Installable** : invite native sur Android (« Installer Planet Kids ») avec
  icône zellige or/indigo, écran de démarrage et captures d'écran de la
  boutique dans le dialogue d'installation ; bannière d'invitation
  élégante (mémorise le refus 7 jours) ; sur iPhone : instructions
  « Partager → Sur l'écran d'accueil ».
- **Mode hors-ligne / 3G faible** : app shell préchargée (ouverture
  instantanée), catalogue servi depuis le cache en cas de coupure
  (stratégie réseau-d'abord), images en cache prioritaire (150 max,
  30 jours, auto-nettoyage navigateur). Les commandes et l'admin ne
  sont **jamais** mis en cache.
- **Mises à jour automatiques** (`autoUpdate` + `clientsClaim`) : la
  nouvelle version s'active dès le rechargement suivant.
- Impact serveur : ~150 Ko de fichiers supplémentaires ; le cache vit
  dans le téléphone du client (5-30 Mo, éviction automatique).
- Fonctionne aussi en développement (`localhost`) pour tester l'installation.

## 🧪 Testé (Playwright, headless)

- ✅ Boutique : 22 produits, filtres, recherche FR/AR, modale, panier, recommandations,
  checkout validé, commande enregistrée, bascule AR/RTL, lightbox, mobile, zéro erreur console
- ✅ Admin : redirection `/admin` → login sans session, erreur identifiants, connexion,
  CRUD produit (création URL **et** upload multipart), slug auto, désactivation →
  retrait immédiat de la boutique, édition prix, suppression, commandes + stats +
  changement de statut, déconnexion, protection des routes
- ✅ API : 401 sans token, 422 validation, e-mail vendeur déclenché à chaque commande

## 🌍 Déploiement — Hostinger + Bunny.net

### A. Hébergement Hostinger (plan Unlimited / Business)

Le plan **Unlimited** (~$3-4/mo en promo) convient parfaitement pour lancer Dar Lila :
PHP 8.2+, SSH, LiteSpeed, sauvegardes quotidiennes, 50 Go NVMe. Points d'attention :

| Point | Détail |
|---|---|
| ⚠️ **Prix de renouvellement** | La promo (~$3-4/mo) devient **~$17-19/mo** au renouvellement — engagez la durée maximale si le budget est serré (30 jours satisfait ou remboursé pour tester) |
| 🇪🇺 **Datacenter** | Choisissez **France (Paris)** : meilleure latence pour l'Algérie (~30-40 ms) |
| 📧 **E-mails vendeur réels** | Les mailboxes incluses (1 an) donnent un SMTP : `MAIL_MAILER=smtp`, `MAIL_HOST=smtp.hostinger.com`, port 465 — la notification de commande partira en vrai e-mail |
| ⚙️ **Queues** | Pas de worker persistant en mutualisé → c'est déjà prévu : `QUEUE_CONNECTION=sync` envoie la notification immédiatement |
| 🐘 **Base de données** | **MySQL inclus gratuitement** (hPanel → Bases de données) : créez base + utilisateur, renseignez `DB_*` dans `.env` — les migrations tournent à l'identique |

**Architecture recommandée (2 sous-domaines)** :

```
khemicishop.com      → frontend Vue (npm run build → dist/ dans public_html)
api.khemicishop.com  → backend Laravel (public/ de Laravel dans le dossier du sous-domaine)
```

**Étapes Laravel** (via SSH `ssh u123456@server` puis `php`/`composer` si disponibles,
sinon installez en local et uploadez tout par FTP/SFTP) :

```bash
# 1. Côté local
cd backend-laravel
composer install --no-dev --optimize-autoloader
npm --prefix ../frontend-vue run build        # construit le frontend

# 2. .env de production
APP_ENV=production  APP_DEBUG=false
APP_URL=https://api.khemicishop.com
FRONTEND_URL=https://khemicishop.com
DB_CONNECTION=mysql
DB_HOST=localhost          # sur Hostinger, la base est sur le même serveur
DB_DATABASE=u123456789_darlila
DB_USERNAME=u123456789_admin
DB_PASSWORD=<mot de passe MySQL>
MAIL_MAILER=smtp  MAIL_HOST=smtp.hostinger.com  MAIL_PORT=465  MAIL_USERNAME=…  MAIL_PASSWORD=…
CORS_ALLOWED_ORIGINS=https://khemicishop.com
ADMIN_PASSWORD=<un vrai mot de passe>

# 3. Sur le serveur (SSH) — le sous-domaine pointe vers laravel/public
php artisan key:generate && php artisan migrate --seed
php artisan storage:link
php artisan config:cache && php artisan route:cache
```

Le frontend construit avec `VITE_API_BASE_URL=https://api.khemicishop.com/api` appelle
l'API en cross-origin (le CORS est déjà configuré).

### B. CDN Bunny.net — images & vidéos

Excellent choix, imbattable rapport qualité/prix (facturation à l'usage, **minimum $1/mois**) :

| Service Bunny | Prix | Usage Dar Lila |
|---|---|---|
| **CDN** (Standard) | **$0.01/Go** (EU/NA) | Cache des images produit + assets |
| **Storage** | $0.01/Go/mois + **transfert vers CDN gratuit** | Stocker les images uploadées via l'admin |
| **Stream** (vidéo) | $0.01/Go stockage, ~$0.005/Go livraison, **transcodage + player inclus** | Vidéos hero / présentation produits |
| Optimizer | $9.50/mo/site | (Optionnel plus tard) conversion WebP/resize à la volée |

> 💡 **Latence Algérie** : Bunny n'a pas de PoP en Algérie — vos visiteurs seront servis
> depuis les edge européens (Paris/Marseille/Frankfurt), facturés au tarif EU de $0.01/Go
> (la facturation dépend de la région du edge qui sert la requête).

**Intégration déjà prévue dans le code** — trois niveaux au choix :

1. **Pull zone (5 min, zéro code)** : sur bunny.net, créez un *pull zone* pointant
   vers `https://api.khemicishop.com`, puis dans `.env` :
   `BUNNY_CDN_URL=https://khemicishop.b-cdn.net` → toutes les images `/storage/…`
   passent automatiquement par le CDN (voir `config/app.php` + `ResolvesCdnUrls`).
2. **URL absolue** : le champ image de l'admin accepte les URL complètes —
   collez directement un lien `https://khemicishop.b-cdn.net/produits/x.jpg`.
3. **⭐ Storage zone natif (recommandé)** : renseignez `BUNNY_STORAGE_ZONE`,
   `BUNNY_STORAGE_KEY` et `BUNNY_STORAGE_CDN_URL` dans `.env` — le formulaire
   admin téléverse alors les images **directement sur l'edge Bunny**
   (`App\Services\BunnyStorage`, API HTTP officielle, repli local automatique
   en cas d'échec, nettoyage de l'image à la suppression d'un produit).
   Le formulaire affiche automatiquement où seront stockées les images
   (endpoint `GET /api/admin/config`).

Pour les **vidéos** : Bunny Stream fournit un player intégré (iframe) — idéal pour
remplacer les vidéos hero du site d'origine.

### 🛠️ Mode maintenance (page d'attente)

```bash
# Sur le serveur (backend) :
php artisan shop:down --message="Retour à 14h" --retry=600
php artisan shop:up                                  # rouvrir la boutique
```

- La boutique publique affiche une **page d'attente élégante** (FR/AR, RTL) :
  étoile zellige animée, compte à rebours, **bouton WhatsApp** pour commander
  malgré tout, et **retour automatique** dès que `shop:up` est exécuté
  (vérification toutes les 20 s).
- L'**administration reste accessible** pendant la maintenance (routes
  `api/admin/*` et `api/auth/*` exemptées) pour gérer la boutique et rouvrir.
- Les réglages de l'API sont dans `app/Http/Middleware/ShopMaintenance.php` ;
  une page HTML 503 bilingue (`resources/views/errors/503.blade.php`) couvre
  les visites directes de l'API.
- Les commandes natives `php artisan down/up` fonctionnent aussi (même fichier).
- **En mode simulation** (api-mock) : `POST /api/maintenance {"state":"on"}`
  active la page d'attente dans l'aperçu.

### 🚀 Outil de déploiement automatique (`deploy/`)

Tout déployer en une commande (build frontend + upload SFTP + composer distant
+ `.env` production + migrations + caches) :

```bash
cd deploy
npm install                                     # une fois (client SSH/SFTP)
cp deploy.config.example.json deploy.config.json # vos accès hPanel → SSH + MySQL + SMTP
npm run dry-run                                 # simulation : build + plan, rien d'envoyé
npm run deploy                                  # déploiement réel 🚀
```

Le script gère tout seul : le renommage `public/` → `public_html/`
(compatible mutualisé via `usePublicPath` dans `index.php`), le `.htaccess`
SPA du frontend (+ cache navigateur des assets), l'installation des
dépendances via composer distant (ou `--with-vendor`), les migrations
idempotentes, `storage:link` et `php artisan optimize`.

Options : `--dry-run`, `--skip-build`, `--with-vendor`, `--force-env`, `--no-seed`.
Voir `deploy/README.md` pour le guide pas à pas (accès SSH hPanel, chemins, dépannage).

### 💰 Budget estimé pour Dar Lila

| Poste | Coût |
|---|---|
| Hostinger Unlimited (promo, engagement long) | ~$3-4/mo |
| Renouvellement (à prévoir) | ~$17-19/mo |
| Bunny CDN + Storage | ~$1-3/mo (traffic faible) |
| Domaine .com | offert la 1ʳᵉ année, ~$15/an ensuite (.dz à enregistrer auprès du NIC Algérie) |
| **Total au lancement** | **< $8/mois** |

## 📖 Guide PDF récapitulatif

Un **guide PDF de 9 pages** (`GUIDE-PROJET-DARLILA.pdf` à la racine du projet)
récapitule tout : présentation, architecture, structure des dossiers, comptes &
URLs, endpoints API, procédures courantes, déploiement Hostinger + Bunny,
checklist sécurité et dépannage.

La source HTML est conservée dans `docs/guide-source.html` — pour régénérer le
PDF après modification :

```bash
# n'importe où avec Node + Playwright (chromium) installés
node darlila/docs/generate-pdf.cjs
```

## 🗺️ Pistes d'évolution

- Pages/notifications pour le client (suivi de commande par référence)
- Upload multiple + redimensionnement des images (Intervention Image)
- Export CSV des commandes, tableau de bord avec graphiques
- Rôles multiples (vendeur / administrateur) via le champ `is_admin` et des gates
- Paiement en ligne (CIB / Edahabia) en complément du paiement à la livraison
