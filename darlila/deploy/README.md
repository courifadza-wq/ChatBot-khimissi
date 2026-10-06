# 🚀 Déploiement Dar Lila → Hostinger

Outil Node.js multiplateforme (Windows / macOS / Linux) qui déploie
**tout le projet en une commande** : build du frontend, upload SFTP du
backend Laravel (avec `public/` renommé `public_html/`), upload du
frontend avec `.htaccess` SPA, `composer install` distant, `.env` de
production, migrations + seeders, caches Laravel.

## Installation (une fois)

```bash
cd deploy
npm install          # installe ssh2 (client SFTP/SSH)
```

## Configuration

1. Dans **hPanel Hostinger** :
   - *Sites web → Tableau de bord → Avancé → Accès SSH* → notez `hôte`, `port`, `utilisateur`, `mot de passe`
   - *Bases de données MySQL* → créez base + utilisateur
   - Créez le **sous-domaine** `api.votre-domaine.com` (son dossier sera utilisé pour Laravel)
2. Copiez la configuration d'exemple et remplissez vos accès :

```bash
cp deploy.config.example.json deploy.config.json
# puis éditez deploy.config.json (hôte SSH, chemins distants, MySQL, SMTP…)
```

> 🔒 `deploy.config.json` contient des secrets → il est **ignoré par Git**.

### Chemins distants (structure Hostinger)

```
/home/uXXXXXXX/domains/khemicishop.com/public_html        ← frontend Vue (dist)
/home/uXXXXXXX/domains/api.khemicishop.com/public_html    ← Laravel public/ renommé
/home/uXXXXXXX/domains/api.khemicishop.com/               ← reste de Laravel (app/, …)
```

Le script mappe automatiquement `backend-laravel/public/*` vers
`public_html/` et écrit un `index.php` compatible mutualisé
(`usePublicPath`) — aucun réglage supplémentaire.

## Utilisation

```bash
# Simulation complète (build + plan, rien n'est envoyé) :
npm run dry-run
# ou : node deploy.mjs --dry-run --config deploy.config.json

# Déploiement réel :
npm run deploy
# ou : node deploy.mjs --config deploy.config.json
```

### Options

| Option | Effet |
|---|---|
| `--dry-run` | affiche le plan sans rien envoyer |
| `--skip-build` | réutilise le `dist/` existant |
| `--with-vendor` | uploade `vendor/` local (si composer indisponible à distance) |
| `--force-env` | écrase le `.env` distant avec celui de la config |
| `--no-seed` | lance les migrations sans les seeders |

## Mises à jour ultérieures

Relancez simplement `npm run deploy` : les fichiers sont re-envoyés,
les migrations relancées (idempotentes) et les caches rafraîchis.
Le `.env` distant est **conservé** (sauf `--force-env`).

## Tester le déploiement SANS compte Hostinger

Un serveur **Hostinger simulé** est fourni (`test/fake-hostinger.py` — Python + paramiko) :
SSH avec mot de passe, SFTP mappé sur `test/server-root/` et commandes
`composer` / `php artisan` simulées avec des sorties réalistes.

```bash
# Terminal 1 : serveur simulé (identifiants u123456789 / test123, port 2222)
cd deploy/test
python3 -m pip install paramiko   # une seule fois
python3 fake-hostinger.py

# Terminal 2 : déploiement complet contre le serveur simulé
cd deploy
npm install
npm run deploy -- --config test/deploy.test.config.json

# Résultat : inspectez les fichiers réellement déployés
ls test/server-root/home/u123456789/domains/
```

Le test end-to-end vérifie : build du frontend, connexion SSH, création des
dossiers imbriqués, upload des 83 fichiers backend (`public/` → `public_html/`),
upload du frontend + `.htaccess` SPA, écriture du `.env`, enchaînement des
commandes serveur, et vérifications HTTP finales. Relancez une seconde fois
pour constater que le `.env` distant est **conservé** lors des mises à jour.

## Dépannage

| Problème | Solution |
|---|---|
| `composer indisponible` | relancez avec `--with-vendor` (vendor/ local) |
| migrate échoue | vérifiez `DB_*` dans le `.env` distant (hPanel → Bases de données) |
| API injoignable | vérifiez que le sous-domaine pointe vers `…/api.khemicishop.com/public_html`, attendez la propagation DNS/SSL |
| Images 404 | `php artisan storage:link` sur le serveur (le script le fait) |
| 500 après édition du .env | `php artisan config:cache` pour rafraîchir |
