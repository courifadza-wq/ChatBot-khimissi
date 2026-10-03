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
        """)
    logger.info("Base de données initialisée : %s", DB_PATH)


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
) -> list[dict]:
    """Recherche des produits selon plusieurs critères combinés."""
    with _get_conn() as conn:
        conditions = ["stock > 0"]
        params: list = []

        if keyword:
            # Filtrer les mots vides, normaliser les accents, garder >=3 chars
            meaningful = [
                _no_accent(w) for w in keyword.split()
                if len(w) >= 3 and w.lower() not in SEARCH_STOP_WORDS
            ]
            if meaningful:
                kw_conditions = []
                kw_params = []
                for w in meaningful:
                    # Mot complet normalisé
                    kw_conditions.append("designation LIKE ?")
                    kw_params.append(f"%{w}%")
                    # Préfixe 6 chars pour morphologie française
                    # ex: CHAUSSURES → CHAUSS, BIBERON → BIBERO
                    if len(w) > 7:
                        kw_conditions.append("designation LIKE ?")
                        kw_params.append(f"%{w[:6]}%")
                # OR entre toutes les variantes
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
