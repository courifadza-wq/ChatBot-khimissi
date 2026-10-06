#!/usr/bin/env node
/**
 * ============================================================
 *  DÉPLOIEMENT DAR LILA → HOSTINGER (SFTP / SSH)
 * ============================================================
 *  En une commande :
 *   1. construit le frontend Vue (npm run build, avec la bonne URL d'API)
 *   2. téléverse le backend Laravel (public/ renommé public_html)
 *   3. téléverse le frontend (+ .htaccess SPA + cache navigateur)
 *   4. installe les dépendances (composer sur le serveur si disponible)
 *   5. écrit le .env de production, lance les migrations + seeders
 *   6. active les caches Laravel (php artisan optimize)
 *
 *  Usage :
 *    node deploy.mjs --config deploy.config.json
 *    node deploy.mjs --dry-run      (plan sans rien envoyer)
 *    node deploy.mjs --skip-build   (ne reconstruit pas le frontend)
 *    node deploy.mjs --with-vendor  (uploade vendor/ si pas de composer distant)
 *    node deploy.mjs --force-env    (écrase le .env distant)
 *    node deploy.mjs --no-seed      (ne lance pas les seeders)
 *
 *  Prérequis : Node.js ≥ 18 + `npm install` dans ce dossier.
 * ============================================================
 */
import { exec } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { promisify } from 'node:util'

const run = promisify(exec)

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url))
const ROOT_DIR = path.resolve(SCRIPT_DIR, '..')
const BACKEND_DIR = path.join(ROOT_DIR, 'backend-laravel')
const FRONTEND_DIR = path.join(ROOT_DIR, 'frontend-vue')

const C = {
  reset: '\x1b[0m', bold: '\x1b[1m', dim: '\x1b[2m',
  gold: '\x1b[33m', green: '\x1b[32m', red: '\x1b[31m', blue: '\x1b[36m',
}
const log = (msg = '') => console.log(msg)
const step = (title) => log(`\n${C.bold}${C.gold}▶ ${title}${C.reset}`)
const info = (msg) => log(`${C.dim}  ${msg}${C.reset}`)
const ok = (msg) => log(`${C.green}  ✓ ${msg}${C.reset}`)
const warn = (msg) => log(`${C.gold}  ⚠ ${msg}${C.reset}`)
const fail = (msg) => log(`${C.red}  ✗ ${msg}${C.reset}`)

/* ------------------------------------------------------------------ */
/* Arguments                                                           */
/* ------------------------------------------------------------------ */

const args = process.argv.slice(2)
const argValue = (name) => {
  const i = args.indexOf(`--${name}`)
  return i !== -1 && args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : null
}
const hasFlag = (name) => args.includes(`--${name}`)

const DRY_RUN = hasFlag('dry-run')
const SKIP_BUILD = hasFlag('skip-build')
const WITH_VENDOR = hasFlag('with-vendor')
const FORCE_ENV = hasFlag('force-env')
const NO_SEED = hasFlag('no-seed')

const CONFIG_PATH = path.resolve(SCRIPT_DIR, argValue('config') || 'deploy.config.json')

/* ------------------------------------------------------------------ */
/* Chargement et validation de la configuration                        */
/* ------------------------------------------------------------------ */

function loadConfig() {
  if (!fs.existsSync(CONFIG_PATH)) {
    fail(`Configuration introuvable : ${CONFIG_PATH}`)
    log(`  Copiez deploy.config.example.json vers deploy.config.json puis remplissez vos accès.`)
    process.exit(1)
  }

  const cfg = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'))

  const required = ['host', 'username', 'remote.frontendDir', 'remote.backendDir', 'apiBaseUrl']
  for (const key of required) {
    const value = key.split('.').reduce((acc, part) => acc?.[part], cfg)
    if (!value) {
      fail(`Champ manquant dans deploy.config.json : "${key}"`)
      process.exit(1)
    }
  }

  if (!cfg.password && !cfg.privateKeyFile) {
    fail('Renseignez "password" ou "privateKeyFile" dans la configuration.')
    process.exit(1)
  }

  cfg.remote ??= {}
  cfg.remote.publicSubdir ??= 'public_html'
  cfg.remote.phpBinary ??= 'php'
  cfg.remote.composerBinary ??= 'composer'

  return cfg
}

const cfg = loadConfig()
// Sécurité : remplace le placeholder [VOTRE_U] par le nom d'utilisateur SSH réel
const backendDir = cfg.remote.backendDir
  .replace(/\/+$/, '')
  .replace(/\[VOTRE_U\]/g, cfg.username)
const frontendDir = cfg.remote.frontendDir
  .replace(/\/+$/, '')
  .replace(/\[VOTRE_U\]/g, cfg.username)
const backendPublicDir = `${backendDir}/${cfg.remote.publicSubdir}`
const php = cfg.remote.phpBinary

/* ------------------------------------------------------------------ */
/* Parcours des fichiers locaux                                        */
/* ------------------------------------------------------------------ */

/** Fichiers du backend à ignorer (dépendances, secrets, fichiers runtime). */
function isIgnoredBackend(rel) {
  if (rel === '.env') return true
  if (rel.startsWith('vendor/') || rel.startsWith('node_modules/')) return true
  if (rel.startsWith('.git/') || rel.startsWith('.phpunit.cache/')) return true
  if (rel.startsWith('database/database.sqlite')) return true

  // Contenu runtime du storage : on ne garde que les .gitignore (dossiers requis)
  const runtimeDirs = [
    'storage/logs',
    'storage/framework/sessions',
    'storage/framework/views',
    'storage/framework/cache',
  ]
  for (const dir of runtimeDirs) {
    if (rel.startsWith(`${dir}/`)) {
      return path.basename(rel) !== '.gitignore'
    }
  }
  return false
}

function collectFiles(dir, filter = () => true) {
  const files = []
  if (!fs.existsSync(dir)) return files

  const walk = (current) => {
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const full = path.join(current, entry.name)
      const rel = path.relative(dir, full).split(path.sep).join('/')
      if (!filter(rel)) continue
      if (entry.isDirectory()) walk(full)
      else files.push({ local: full, rel })
    }
  }
  walk(dir)
  return files
}

/* ------------------------------------------------------------------ */
/* Étape 1 : build du frontend                                         */
/* ------------------------------------------------------------------ */

async function buildFrontend() {
  step('Construction du frontend Vue')

  // Dépendances du frontend installées ? (sinon message clair)
  if (!fs.existsSync(path.join(FRONTEND_DIR, 'node_modules'))) {
    fail('Les dépendances du frontend ne sont pas installées.')
    log(`  → lancez d'abord :  cd frontend-vue  puis  npm install`)
    process.exit(1)
  }

  if (SKIP_BUILD) {
    if (!fs.existsSync(path.join(FRONTEND_DIR, 'dist', 'index.html'))) {
      fail('--skip-build demandé mais dist/ n’existe pas.')
      process.exit(1)
    }
    info('build ignoré (--skip-build), dist/ existant utilisé')
    return
  }

  info(`npm run build  (VITE_API_BASE_URL=${cfg.apiBaseUrl})`)
  try {
    await run('npm run build', {
      cwd: FRONTEND_DIR,
      env: { ...process.env, VITE_API_BASE_URL: cfg.apiBaseUrl },
    })
    ok('frontend construit → frontend-vue/dist/')
  } catch (error) {
    fail(`build échoué : ${error.stderr || error.message}`)
    process.exit(1)
  }
}

/** Nom de dossier parent au format POSIX (utilisé pour mkdirp distant). */
const posixDir = (p) => p.split('/').slice(0, -1).join('/') || '/'

/* ------------------------------------------------------------------ */
/* Étape 2 : plan des fichiers                                         */
/* ------------------------------------------------------------------ */

function buildPlan() {
  const backendFiles = collectFiles(BACKEND_DIR, (rel) => !isIgnoredBackend(rel) && !rel.startsWith('public/'))
  const backendPublicFiles = collectFiles(path.join(BACKEND_DIR, 'public'))
  const frontendFiles = collectFiles(path.join(FRONTEND_DIR, 'dist'))

  return {
    backend: backendFiles.map((f) => ({ ...f, remote: `${backendDir}/${f.rel}` })),
    backendPublic: backendPublicFiles.map((f) => ({ ...f, remote: `${backendPublicDir}/${f.rel}` })),
    frontend: frontendFiles.map((f) => ({ ...f, remote: `${frontendDir}/${f.rel}` })),
  }
}

/* ------------------------------------------------------------------ */
/* Environnement .env de production                                    */
/* ------------------------------------------------------------------ */

function buildEnvContent(overrides = {}) {
  const examplePath = path.join(BACKEND_DIR, '.env.example')
  const lines = fs.readFileSync(examplePath, 'utf8').split(/\r?\n/)
  const remaining = new Set(Object.keys(overrides))

  const output = lines.map((line) => {
    const match = line.match(/^([A-Z0-9_]+)\s*=/)
    if (match && remaining.has(match[1])) {
      remaining.delete(match[1])
      return `${match[1]}=${overrides[match[1]]}`
    }
    return line
  })

  for (const key of remaining) output.push(`${key}=${overrides[key]}`)
  return output.join('\n').trimEnd() + '\n'
}

/* ------------------------------------------------------------------ */
/* Petit pool de concurrence                                           */
/* ------------------------------------------------------------------ */

async function runPool(items, worker, concurrency = 5) {
  const queue = [...items]
  let done = 0
  let failed = 0

  async function runner() {
    while (queue.length > 0) {
      const item = queue.shift()
      try {
        await worker(item)
      } catch (error) {
        failed += 1
        warn(`échec : ${item.rel} — ${error.message}`)
      }
      done += 1
      if (done % 50 === 0 || done === items.length) {
        info(`${done}/${items.length} fichiers…`)
      }
    }
  }

  await Promise.all(Array.from({ length: Math.min(concurrency, items.length) }, runner))
  return failed
}

/* ------------------------------------------------------------------ */
/* Client SSH/SFTP (ssh2)                                              */
/* ------------------------------------------------------------------ */

async function connect() {
  // Le paquet ssh2 est-il installé ? (sinon message clair)
  let Client
  try {
    ;({ Client } = await import('ssh2'))
  } catch {
    fail('Le paquet « ssh2 » est manquant dans ce dossier.')
    log('  → lancez d\'abord :  npm install   (dans le dossier deploy/)')
    process.exit(1)
  }

  const options = {
    host: cfg.host,
    port: cfg.port || 22,
    username: cfg.username,
    readyTimeout: 30000,
    keepaliveInterval: 15000,
  }
  if (cfg.privateKeyFile) {
    options.privateKey = fs.readFileSync(path.resolve(SCRIPT_DIR, cfg.privateKeyFile))
  } else {
    options.password = cfg.password
  }

  const conn = new Client()
  await new Promise((resolve, reject) => {
    conn.on('ready', resolve)
    conn.on('error', reject)
    conn.connect(options)
  })

  const sftp = await new Promise((resolve, reject) => {
    conn.sftp((error, sftpSession) => (error ? reject(error) : resolve(sftpSession)))
  })

  return { conn, sftp }
}

function sshExec(conn, command) {
  return new Promise((resolve, reject) => {
    conn.exec(command, (error, stream) => {
      if (error) return reject(error)
      let stdout = ''
      let stderr = ''
      stream.on('data', (data) => (stdout += data.toString()))
      stream.stderr.on('data', (data) => (stderr += data.toString()))
      stream.on('close', (code) => resolve({ code, stdout, stderr }))
    })
  })
}

/* --- Helpers SFTP promisifiés --- */
const stat = (sftp, p) => new Promise((resolve) => sftp.stat(p, (err, st) => resolve(err ? null : st)))
const mkdirRaw = (sftp, p) => new Promise((resolve, reject) => sftp.mkdir(p, (err) => (err ? reject(err) : resolve())))
const fastPut = (sftp, local, remote) => new Promise((resolve, reject) => sftp.fastPut(local, remote, (err) => (err ? reject(err) : resolve())))
const writeFile = (sftp, remote, content) => new Promise((resolve, reject) => sftp.writeFile(remote, content, (err) => (err ? reject(err) : resolve())))
const readFile = (sftp, remote) => new Promise((resolve, reject) => sftp.readFile(remote, (err, buf) => (err ? reject(err) : resolve(buf.toString('utf8')))))
const unlinkRaw = (sftp, p) => new Promise((resolve, reject) => sftp.unlink(p, (err) => (err ? reject(err) : resolve())))
const rmdirRaw = (sftp, p) => new Promise((resolve, reject) => sftp.rmdir(p, (err) => (err ? reject(err) : resolve())))
const readdir = (sftp, p) => new Promise((resolve, reject) => sftp.readdir(p, (err, list) => (err ? reject(err) : resolve(list))))

async function mkdirp(sftp, dir) {
  if (await stat(sftp, dir)) return
  const parts = dir.split('/').filter(Boolean)
  let current = dir.startsWith('/') ? '' : '.'
  for (const part of parts) {
    current = `${current}/${part}`
    if (!(await stat(sftp, current))) {
      try {
        await mkdirRaw(sftp, current)
      } catch {
        /* créé entre-temps : on continue */
      }
    }
  }
}

async function removeRemoteTree(sftp, dir) {
  const entries = await readdir(sftp, dir).catch(() => [])
  for (const entry of entries) {
    const full = `${dir}/${entry.filename}`
    if (entry.attrs.isDirectory()) {
      await removeRemoteTree(sftp, full)
      await rmdirRaw(sftp, full).catch(() => {})
    } else {
      await unlinkRaw(sftp, full).catch(() => {})
    }
  }
}

/* ------------------------------------------------------------------ */
/* .htaccess SPA pour le frontend                                      */
/* ------------------------------------------------------------------ */

const SPA_HTACCESS = `# Dar Lila — SPA Vue (routage historique HTML5)
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule ^ index.html [L]
</IfModule>

# Cache long pour les assets fingerprintés (Vite)
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType application/javascript "access plus 1 year"
  ExpiresByType font/woff2 "access plus 1 year"
  ExpiresByType image/jpeg "access plus 1 month"
  ExpiresByType image/png "access plus 1 month"
  ExpiresByType image/webp "access plus 1 month"
  ExpiresByType image/svg+xml "access plus 1 month"
</IfModule>

<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json image/svg+xml
</IfModule>
`

/* ------------------------------------------------------------------ */
/* Déroulé du déploiement                                              */
/* ------------------------------------------------------------------ */

async function main() {
  log(`\n${C.bold}${C.blue}╔══════════════════════════════════════════════╗${C.reset}`)
  log(`${C.bold}${C.blue}║   🛍️  PLANET KIDS — déploiement Hostinger        ║${C.reset}`)
  log(`${C.bold}${C.blue}╚══════════════════════════════════════════════╝${C.reset}`)
  if (DRY_RUN) warn('MODE DRY-RUN : rien ne sera envoyé sur le serveur\n')

  await buildFrontend()

  const plan = buildPlan()

  step('Plan du déploiement')
  ok(`backend  : ${plan.backend.length + plan.backendPublic.length} fichiers → ${backendDir}`)
  info(`           (public/ de Laravel → ${cfg.remote.publicSubdir}/)`)
  ok(`frontend : ${plan.frontend.length} fichiers → ${frontendDir}`)

  if (DRY_RUN) {
    step('Aperçu (dry-run)')
    const preview = [...plan.backend.slice(0, 8), ...plan.backendPublic.slice(0, 4), ...plan.frontend.slice(0, 6)]
    preview.forEach((f) => info(`${f.local.replace(ROOT_DIR, '.')}  →  ${f.remote}`))
    if (plan.backend.length + plan.backendPublic.length + plan.frontend.length > preview.length) {
      info(`… et ${plan.backend.length + plan.backendPublic.length + plan.frontend.length - preview.length} autres`)
    }
    log('')
    ok('Dry-run terminé : configuration valide, prêt à déployer (relancez sans --dry-run).')
    return
  }

  /* ---------- Connexion ---------- */
  step(`Connexion SSH à ${cfg.username}@${cfg.host}`)
  const { conn, sftp } = await connect()
  ok(`connecté à ${cfg.host}:${cfg.port || 22}`)

  try {
    /* ---------- Nettoyage optionnel du frontend ---------- */
    if (cfg.cleanFrontend) {
      step('Nettoyage du dossier frontend distant')
      await removeRemoteTree(sftp, frontendDir)
      await mkdirp(sftp, frontendDir)
      ok('dossier frontend vidé (cleanFrontend: true)')
    }

    /* ---------- Upload backend ---------- */
    step('Téléversement du backend Laravel')

    // Tous les dossiers parents nécessaires (y compris imbriqués :
    // app/Http/Controllers/Admin/…), plus les dossiers runtime de Laravel
    const backendDirs = new Set([
      backendDir,
      backendPublicDir,
      `${backendDir}/storage/app/public`,
      `${backendDir}/storage/framework/cache/data`,
      `${backendDir}/storage/framework/sessions`,
      `${backendDir}/storage/framework/views`,
      `${backendDir}/storage/logs`,
      `${backendDir}/bootstrap/cache`,
      ...plan.backend.map((f) => posixDir(f.remote)),
      ...plan.backendPublic.map((f) => posixDir(f.remote)),
    ])
    for (const dir of [...backendDirs].sort()) {
      await mkdirp(sftp, dir)
    }

    let failed = 0
    failed += await runPool(plan.backend, (f) => fastPut(sftp, f.local, f.remote))
    failed += await runPool(plan.backendPublic, (f) => fastPut(sftp, f.local, f.remote))
    if (failed > 0) warn(`${failed} fichier(s) en échec — vérifiez les permissions.`)
    else ok(`${plan.backend.length + plan.backendPublic.length} fichiers envoyés`)

    /* ---------- Upload frontend + .htaccess ---------- */
    step('Téléversement du frontend (dist + .htaccess SPA)')
    await mkdirp(sftp, frontendDir)
    for (const dir of new Set(plan.frontend.map((f) => posixDir(f.remote)))) {
      await mkdirp(sftp, dir)
    }
    failed = await runPool(plan.frontend, (f) => fastPut(sftp, f.local, f.remote))
    await writeFile(sftp, `${frontendDir}/.htaccess`, SPA_HTACCESS)
    ok(`${plan.frontend.length} fichiers + .htaccess envoyés`)

    /* ---------- Dépendances PHP ---------- */
    step('Installation des dépendances PHP')
    const composerCheck = await sshExec(conn, `command -v ${cfg.remote.composerBinary}`)
    let vendorReady = false

    if (composerCheck.code === 0) {
      const install = await sshExec(
        conn,
        `cd ${backendDir} && ${cfg.remote.composerBinary} install --no-dev --optimize-autoloader --no-interaction 2>&1`
      )
      if (install.code === 0) {
        vendorReady = true
        ok('composer install exécuté sur le serveur')
      } else {
        warn(`composer distant a échoué : ${install.stdout.trim().slice(0, 200)}`)
      }
    } else {
      warn('composer indisponible sur le serveur.')
    }

    if (!vendorReady) {
      if (WITH_VENDOR || fs.existsSync(path.join(BACKEND_DIR, 'vendor'))) {
        if (WITH_VENDOR) {
          const vendorFiles = collectFiles(path.join(BACKEND_DIR, 'vendor'))
          if (vendorFiles.length > 0) {
            warn(`upload de vendor/ (${vendorFiles.length} fichiers — cela peut prendre du temps)`)
            const failedVendor = await runPool(vendorFiles, (f) => fastPut(sftp, f.local, `${backendDir}/vendor/${f.rel}`), 8)
            vendorReady = failedVendor === 0
          }
        }
      }
      if (!vendorReady && !WITH_VENDOR) {
        warn('sans composer distant : relancez avec --with-vendor pour uploader vendor/ local.')
      }
    }

    /* ---------- .env de production ---------- */
    step('Configuration .env de production')
    let envCreated = false
    const remoteEnvPath = `${backendDir}/.env`
    const remoteEnvExists = Boolean(await stat(sftp, remoteEnvPath))

    if (cfg.env && (!remoteEnvExists || FORCE_ENV)) {
      const content = buildEnvContent(cfg.env)
      await writeFile(sftp, remoteEnvPath, content)
      envCreated = true
      ok('.env de production écrit (depuis deploy.config.json)')
    } else if (remoteEnvExists) {
      ok('.env distant conservé (utilisez --force-env pour l’écraser)')
      const current = await readFile(sftp, remoteEnvPath).catch(() => '')
      if (!/APP_KEY=base64:/.test(current) && cfg.env) {
        envCreated = true
      }
    } else {
      await fastPut(sftp, path.join(BACKEND_DIR, '.env.example'), remoteEnvPath)
      envCreated = true
      warn('.env créé depuis l’exemple — éditez-le sur le serveur (DB, mail, ADMIN_PASSWORD…)')
    }

    /* ---------- Artisan ---------- */
    step('Migrations & caches Laravel')

    if (envCreated || FORCE_ENV) {
      const key = await sshExec(conn, `cd ${backendDir} && ${php} artisan key:generate --force 2>&1`)
      key.code === 0 ? ok('APP_KEY générée') : warn(`key:generate → ${key.stdout.trim().slice(0, 120)}`)
    }

    const seedArg = NO_SEED || cfg.runSeeder === false ? '' : ' --seed'
    const migrate = await sshExec(conn, `cd ${backendDir} && ${php} artisan migrate --force${seedArg} 2>&1`)
    if (migrate.code === 0) {
      ok(`migrations appliquées${seedArg ? ' + seeders (idempotents)' : ''}`)
    } else {
      fail(`migrate : ${migrate.stdout.trim().slice(0, 300)}`)
      warn('vérifiez les accès DB dans le .env distant puis relancez.')
    }

    await sshExec(conn, `cd ${backendDir} && ${php} artisan storage:link 2>&1 || true`)
    ok('lien storage créé (public_html/storage)')

    const optimize = await sshExec(conn, `cd ${backendDir} && ${php} artisan optimize 2>&1`)
    optimize.code === 0 ? ok('caches config/routes/vues activés') : warn(`optimize : ${optimize.stdout.trim().slice(0, 120)}`)

    /* ---------- Vérifications HTTP ---------- */
    step('Vérifications')
    await verifyUrl(`${cfg.apiBaseUrl}/settings`, 'API Laravel')
    if (cfg.frontendUrl) await verifyUrl(cfg.frontendUrl, 'Frontend')

    /* ---------- Résumé ---------- */
    log(`\n${C.bold}${C.green}╔══════════════════════════════════════════════╗${C.reset}`)
    log(`${C.bold}${C.green}║        🎉 DÉPLOIEMENT TERMINÉ                 ║${C.reset}`)
    log(`${C.bold}${C.green}╚══════════════════════════════════════════════╝${C.reset}`)
    log(`  Boutique  : ${C.bold}${cfg.frontendUrl || '(voir configuration)'}${C.reset}`)
    log(`  API       : ${C.bold}${cfg.apiBaseUrl}${C.reset}`)
    log(`  Admin     : ${C.bold}${(cfg.frontendUrl || '').replace(/\/+$/, '')}/admin${C.reset}`)
    log(`  Identifiants admin : définis dans le .env distant (ADMIN_EMAIL / ADMIN_PASSWORD)`)
    log('')
    log(`  Prochaines actions suggérées :`)
    log(`   • changez ADMIN_PASSWORD dans le .env distant puis relancez ${php} artisan db:seed --class=UserSeeder`)
    log(`   • configurez Bunny (BUNNY_STORAGE_ZONE / KEY / CDN_URL) pour les images`)
    log(`   • après toute modification du .env : ${php} artisan config:cache`)
  } finally {
    conn.end()
  }
}

async function verifyUrl(url, label) {
  try {
    const response = await fetch(url, { redirect: 'manual' })
    if (response.ok) ok(`${label} → ${response.status} ${url}`)
    else warn(`${label} → HTTP ${response.status} (DNS/SSL peut-être pas encore propagés)`)
  } catch {
    warn(`${label} → injoignable (${url}) — propagation DNS ou SSL en cours ?`)
  }
}

main().catch((error) => {
  fail(error.message || String(error))
  process.exit(1)
})
