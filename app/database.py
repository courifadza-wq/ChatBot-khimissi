# ============================================================
#  Mémoire long-terme du bot — SQLite
#  Tables : clients, orders
#  Le fichier .db est dans /app/data/ (volume persistant Coolify)
# ============================================================
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("database")

# Le fichier SQLite sera dans le répertoire data/ (monté en volume dans Coolify)
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "bot_memory.db"


# -----------------------------------------------------------
# Connexion
# -----------------------------------------------------------
def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # sécurité concurrence
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# -----------------------------------------------------------
# Initialisation (appelée au démarrage de l'app)
# -----------------------------------------------------------
def init_db() -> None:
    """Crée les tables si elles n'existent pas encore."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS clients (
                phone             TEXT PRIMARY KEY,
                name              TEXT DEFAULT '',
                address           TEXT DEFAULT '',
                preferred_payment TEXT DEFAULT '',
                order_count       INTEGER DEFAULT 0,
                first_seen        TEXT,
                last_seen         TEXT
            );

            CREATE TABLE IF NOT EXISTS orders (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                phone      TEXT NOT NULL,
                name       TEXT,
                address    TEXT,
                items      TEXT,   -- JSON : [{"name":..., "qty":...}]
                total      INTEGER DEFAULT 0,
                payment    TEXT,
                created_at TEXT,
                FOREIGN KEY (phone) REFERENCES clients(phone)
            );

            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                designation TEXT NOT NULL,
                reference   TEXT,
                stock       INTEGER DEFAULT 0,
                price       REAL NOT NULL,
                category    TEXT DEFAULT '',
                age_range   TEXT DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_products_designation
                ON products (designation);
            CREATE INDEX IF NOT EXISTS idx_products_category
                ON products (category);

            CREATE TABLE IF NOT EXISTS order_sessions (
                phone      TEXT PRIMARY KEY,
                state      INTEGER NOT NULL,
                order_json TEXT NOT NULL DEFAULT '{}',
                client_json TEXT DEFAULT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS chat_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                text       TEXT NOT NULL,
                intent     TEXT DEFAULT 'fallback',
                confidence REAL DEFAULT 0.0,
                method     TEXT DEFAULT '',
                responded  INTEGER DEFAULT 0,
                session_id TEXT DEFAULT '',
                source     TEXT DEFAULT 'web',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_chat_log_created
                ON chat_log (created_at);
            CREATE INDEX IF NOT EXISTS idx_chat_log_intent
                ON chat_log (intent);
        """)
    # Auto-cleanup : supprimer les logs > 30 jours
    with _get_conn() as conn:
        conn.execute("DELETE FROM chat_log WHERE created_at < datetime('now', '-30 days')")
    logger.info("Base de données initialisée : %s", DB_PATH)


# -----------------------------------------------------------
# Sessions de commande persistantes (survie aux redémarrages)
# -----------------------------------------------------------
import json as _json


def save_order_session(phone: str, state: int, order_data: dict, client_data=None) -> None:
    with _get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO order_sessions (phone, state, order_json, client_json, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (phone, state, _json.dumps(order_data), _json.dumps(client_data) if client_data else None))


def load_order_session(phone: str) -> dict | None:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT state, order_json, client_json FROM order_sessions WHERE phone = ?",
            (phone,)
        ).fetchone()
        if row:
            return {
                "state": row["state"],
                "order": _json.loads(row["order_json"]),
                "client": _json.loads(row["client_json"]) if row["client_json"] else None,
            }
        return None


def delete_order_session(phone: str) -> None:
    with _get_conn() as conn:
        conn.execute("DELETE FROM order_sessions WHERE phone = ?", (phone,))


# -----------------------------------------------------------
# Recherche de produits
# -----------------------------------------------------------
import unicodedata

SEARCH_STOP_WORDS = {
    "le", "la", "les", "de", "du", "des", "un", "une", "en", "et", "ou",
    "je", "tu", "il", "elle", "nous", "vous", "ils", "moi", "toi", "lui",
    "me", "te", "se", "y", "ca", "ce", "cet", "cette", "ces", "mon", "ton",
    "son", "sa", "ses", "notre", "votre", "leur", "leurs", "avec", "pour",
    "dans", "sur", "par", "pas", "ne", "si", "que", "qui", "quoi", "est",
    "sont", "avez", "avons", "ai", "as", "ait", "avoir", "etre",
    "veux", "voudrais", "cherche", "montrez", "montrer", "afficher",
    "voir", "quel", "quelle", "quels", "quelles", "ici", "voila",
}


def _no_accent(text: str) -> str:
    """Supprime les accents : bébé → BEBE, chaussures → CHAUSSURES."""
    return "".join(
        c for c in unicodedata.normalize("NFD", text.upper())
        if unicodedata.category(c) != "Mn"
    )


def search_products(
    keyword: str = "",
    category: str = "",
    max_price: float = 0,
    min_price: float = 0,
    age_hint: str = "",
    limit: int = 5,
    strict: bool = False,
) -> list[dict]:
    """Recherche des produits. strict=True: tous les mots doivent matcher (mode commande)."""
    with _get_conn() as conn:
        conditions = ["stock > 0", "price > 0"]
        params: list = []

        if keyword:
            meaningful = [
                _no_accent(w) for w in keyword.split()
                if len(w) >= 3 and w.lower() not in SEARCH_STOP_WORDS
            ]
            if meaningful:
                if strict and len(meaningful) > 1:
                    # Mode strict (commande) : TOUS les mots doivent matcher
                    for w in meaningful:
                        conditions.append("(designation LIKE ? OR mot LIKE ?)")
                        params.extend([f"%{w}%", f"%{w}%"])
                else:
                    # Mode souple (catalogue) : designation OR mot
                    kw_conditions = []
                    kw_params = []
                    for w in meaningful:
                        kw_conditions.append("designation LIKE ?")
                        kw_params.append(f"%{w}%")
                        kw_conditions.append("mot LIKE ?")
                        kw_params.append(f"%{w}%")
                        if len(w) > 7:
                            kw_conditions.append("designation LIKE ?")
                            kw_params.append(f"%{w[:6]}%")
                    conditions.append(f"({' OR '.join(kw_conditions)})")
                    params.extend(kw_params)



        if category:
            conditions.append("category LIKE ?")
            params.append(f"%{category}%")

        if max_price > 0:
            conditions.append("price <= ?")
            params.append(max_price)

        if min_price > 0:
            conditions.append("price >= ?")
            params.append(min_price)

        if age_hint:
            age_norm = _no_accent(age_hint)
            conditions.append(
                "(age_range LIKE ? OR designation LIKE ? OR age_range LIKE ? OR designation LIKE ?)"
            )
            params.extend([f"%{age_hint}%", f"%{age_hint}%", f"%{age_norm}%", f"%{age_norm}%"])

        where = " AND ".join(conditions)
        query = f"""
            SELECT designation, reference, stock, price, category, age_range
            FROM products
            WHERE {where}
            ORDER BY price ASC
            LIMIT ?
        """
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]



def count_products() -> int:
    """Retourne le nombre total de produits en stock."""
    with _get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM products WHERE stock > 0").fetchone()
        return row[0] if row else 0


def get_all_mots() -> list[str]:
    """Retourne tous les mots-clés distincts de la colonne mot (pour fuzzy search)."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT mot FROM products WHERE mot IS NOT NULL AND mot != '' AND stock > 0"
        ).fetchall()
        return [r[0] for r in rows]


def fuzzy_keyword(keyword: str, threshold: float = 0.65) -> str | None:
    """
    Cherche le mot-clé le plus proche dans la colonne mot.
    Retourne le mot corrigé ou None si aucun match suffisant.

    Ex: "balrine" → "BALLERINE", "bibron" → "BIBERON"
    """
    from difflib import get_close_matches
    if not keyword or len(keyword) < 3:
        return None
    mots = get_all_mots()
    kw_up = _no_accent(keyword)   # normalisation accent + majuscules
    matches = get_close_matches(kw_up, mots, n=1, cutoff=threshold)
    if matches and matches[0] != kw_up:
        return matches[0]
    return None


def get_categories() -> list[str]:
    """Retourne la liste des catégories disponibles."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM products WHERE stock > 0 AND category != '' ORDER BY category"
        ).fetchall()
        return [r[0] for r in rows]


def bulk_insert_products(products: list[dict]) -> int:
    """Insère en masse des produits. Retourne le nombre inséré."""
    with _get_conn() as conn:
        conn.execute("DELETE FROM products")
        conn.executemany(
            """INSERT INTO products (designation, reference, stock, price, category, age_range)
               VALUES (:designation, :reference, :stock, :price, :category, :age_range)""",
            products,
        )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        logger.info("%d produits importés dans la DB", count)
        return count



# -----------------------------------------------------------
# Lecture d'un profil client
# -----------------------------------------------------------
def get_client(phone: str) -> dict | None:
    """Retourne le profil du client ou None s'il est inconnu."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM clients WHERE phone = ?", (phone,)
        ).fetchone()
        return dict(row) if row else None


# -----------------------------------------------------------
# Sauvegarde / mise à jour d'un profil client
# -----------------------------------------------------------
def upsert_client(phone: str, name: str, address: str, payment: str) -> None:
    """Crée ou met à jour le profil client après une commande confirmée."""
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        existing = conn.execute(
            "SELECT phone FROM clients WHERE phone = ?", (phone,)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE clients
                   SET name = ?, address = ?, preferred_payment = ?,
                       order_count = order_count + 1, last_seen = ?
                   WHERE phone = ?""",
                (name, address, payment, now, phone),
            )
            logger.info("Client mis à jour : %s (%s)", name, phone)
        else:
            conn.execute(
                """INSERT INTO clients
                   (phone, name, address, preferred_payment, order_count, first_seen, last_seen)
                   VALUES (?, ?, ?, ?, 1, ?, ?)""",
                (phone, name, address, payment, now, now),
            )
            logger.info("Nouveau client enregistré : %s (%s)", name, phone)
        conn.commit()


# -----------------------------------------------------------
# Sauvegarde d'une commande
# -----------------------------------------------------------
def save_order(phone: str, name: str, address: str,
               items: list, total: int, payment: str) -> int:
    """Enregistre la commande et retourne son ID."""
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        cursor = conn.execute(
            """INSERT INTO orders (phone, name, address, items, total, payment, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (phone, name, address, json.dumps(items, ensure_ascii=False), total, payment, now),
        )
        conn.commit()
        logger.info("Commande #%d enregistrée pour %s", cursor.lastrowid, phone)
        return cursor.lastrowid


# -----------------------------------------------------------
# Historique des commandes d'un client
# -----------------------------------------------------------
def get_client_orders(phone: str, limit: int = 5) -> list[dict]:
    """Retourne les N dernières commandes d'un client."""
    with _get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM orders
               WHERE phone = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (phone, limit),
        ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["items"] = json.loads(d["items"])
            except (json.JSONDecodeError, TypeError):
                d["items"] = []
            result.append(d)
        return result


# -----------------------------------------------------------
# Mise à jour de la date de dernière visite
# -----------------------------------------------------------
def touch_client(phone: str) -> None:
    """Met à jour last_seen sans modifier les autres champs."""
    now = datetime.now().isoformat()
    with _get_conn() as conn:
        conn.execute(
            "UPDATE clients SET last_seen = ? WHERE phone = ?", (now, phone)
        )
        conn.commit()


# -----------------------------------------------------------
# Journal des messages (chat_log)
# -----------------------------------------------------------
def log_message(text: str, intent: str = "fallback", confidence: float = 0.0,
                method: str = "", responded: bool = False,
                session_id: str = "", source: str = "web") -> None:
    """Enregistre un message client dans le journal."""
    try:
        with _get_conn() as conn:
            conn.execute("""
                INSERT INTO chat_log (text, intent, confidence, method, responded, session_id, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (text[:500], intent, round(confidence, 4), method, int(responded), session_id, source))
    except Exception as e:
        logger.error("Erreur log_message: %s", e)


def get_journal(q: str = "", intent: str = "", min_conf: float = -1,
                max_conf: float = 2, fallback_only: bool = False,
                page: int = 1, per_page: int = 50) -> dict:
    """Retourne les logs paginés avec filtres."""
    with _get_conn() as conn:
        where, params = ["1=1"], []

        if q:
            where.append("text LIKE ?")
            params.append(f"%{q}%")
        if intent:
            where.append("intent = ?")
            params.append(intent)
        if fallback_only:
            where.append("(intent = 'fallback' OR confidence < 0.4)")
        if min_conf >= 0:
            where.append("confidence >= ?")
            params.append(min_conf)
        if max_conf < 2:
            where.append("confidence <= ?")
            params.append(max_conf)

        w = " AND ".join(where)

        total = conn.execute(f"SELECT COUNT(*) FROM chat_log WHERE {w}", params).fetchone()[0]
        offset = (page - 1) * per_page
        rows = conn.execute(
            f"SELECT * FROM chat_log WHERE {w} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [per_page, offset]
        ).fetchall()

        return {
            "items": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "per_page": per_page,
            "last_page": max(1, (total + per_page - 1) // per_page),
        }


def get_journal_stats() -> dict:
    """Statistiques du journal : totaux, taux fallback, top intents, mots non compris."""
    with _get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM chat_log").fetchone()[0]
        fallbacks = conn.execute(
            "SELECT COUNT(*) FROM chat_log WHERE intent = 'fallback' OR confidence < 0.4"
        ).fetchone()[0]
        today = conn.execute(
            "SELECT COUNT(*) FROM chat_log WHERE created_at >= datetime('now', '-1 day')"
        ).fetchone()[0]
        week = conn.execute(
            "SELECT COUNT(*) FROM chat_log WHERE created_at >= datetime('now', '-7 days')"
        ).fetchone()[0]

        # Top intents
        top_intents = conn.execute("""
            SELECT intent, COUNT(*) as cnt, ROUND(AVG(confidence), 2) as avg_conf
            FROM chat_log GROUP BY intent ORDER BY cnt DESC LIMIT 15
        """).fetchall()

        # Mots non compris (fallback) les plus fréquents
        top_fallbacks = conn.execute("""
            SELECT text, COUNT(*) as cnt
            FROM chat_log
            WHERE intent = 'fallback' OR confidence < 0.4
            GROUP BY text ORDER BY cnt DESC LIMIT 20
        """).fetchall()

        return {
            "total": total,
            "fallbacks": fallbacks,
            "fallback_rate": round(fallbacks / max(total, 1) * 100, 1),
            "today": today,
            "week": week,
            "top_intents": [{"intent": r["intent"], "count": r["cnt"], "avg_conf": r["avg_conf"]} for r in top_intents],
            "top_fallbacks": [{"text": r["text"], "count": r["cnt"]} for r in top_fallbacks],
        }


def cleanup_journal(days: int = 30) -> int:
    """Supprime les logs plus vieux que N jours. Retourne le nombre supprimé."""
    with _get_conn() as conn:
        cur = conn.execute(
            f"DELETE FROM chat_log WHERE created_at < datetime('now', '-{days} days')"
        )
        return cur.rowcount
