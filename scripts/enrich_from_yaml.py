#!/usr/bin/env python3
"""
Script d'enrichissement DB : products.yaml → SQLite
Ajoute les colonnes `mot` et `famille` depuis products.yaml.
Pas de dépendances externes (parser YAML maison).

Usage :
    python scripts/enrich_from_yaml.py
    python scripts/enrich_from_yaml.py --dry-run
"""

import re
import sys
import sqlite3
import argparse
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
DATA_YAML = ROOT / "data" / "products.yaml"
DB_PATH   = ROOT / "data" / "bot_memory.db"


# ── Parser YAML maison (sans PyYAML) ─────────────────────────────────────────

def load_yaml_products(path: Path) -> list[dict]:
    """
    Parse products.yaml ligne par ligne — aucune dépendance externe.
    Format de chaque entrée :
      - id: a00001
        name: "BANDANA ..."
        mot: "BANDANA"
        famille: "Accessoires cheveux"
        ref: "9168 FIND"
        price: 350
        stock: 13
    """
    print(f"📂 Lecture de {path.name} ({path.stat().st_size // 1024} Ko)...")
    products: list[dict] = []
    current: dict | None = None

    # Regex : ligne "  - id: a00001"
    re_item  = re.compile(r'^\s+-\s+id:\s*(.+?)\s*$')
    # Regex : ligne "    key: valeur" ou '    key: "valeur"'
    re_field = re.compile(r'^\s+(\w+):\s*(.*?)\s*$')

    NUMERIC = {"price", "stock"}
    WANTED  = {"name", "mot", "famille", "ref", "category", "price", "stock"}

    with open(path, encoding="utf-8") as f:
        for line in f:
            # Nouvelle entrée produit
            m = re_item.match(line)
            if m:
                if current:
                    products.append(current)
                current = {"id": m.group(1)}
                continue

            if current is None:
                continue

            m = re_field.match(line)
            if not m:
                continue

            key = m.group(1)
            if key not in WANTED:
                continue

            raw = m.group(2).strip().strip('"')

            if key in NUMERIC:
                try:
                    current[key] = float(raw) if key == "price" else int(float(raw))
                except (ValueError, TypeError):
                    current[key] = 0
            else:
                current[key] = raw

    if current:
        products.append(current)

    print(f"✅ {len(products)} produits chargés depuis YAML")
    return products


# ── DB helpers ───────────────────────────────────────────────────────────────

def ensure_columns(conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(products)").fetchall()}
    added = []
    for col in ("mot", "famille"):
        if col not in cols:
            conn.execute(f"ALTER TABLE products ADD COLUMN {col} TEXT DEFAULT ''")
            added.append(col)
    if added:
        conn.commit()
        print(f"  ✔ Colonnes ajoutées : {', '.join(added)}")
    else:
        print("  ✔ Colonnes déjà présentes")


def load_db_products(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT rowid as rowid, designation, reference FROM products"
    ).fetchall()
    return [{"rowid": r[0], "designation": r[1], "reference": r[2]} for r in rows]



# ── Matching ─────────────────────────────────────────────────────────────────

def _normalize(s: str) -> str:
    return " ".join(str(s).strip().lower().split())


def build_indexes(yaml_products: list[dict]) -> tuple[dict, dict]:
    """
    Retourne deux index :
      - by_ref  : ref normalisée → produit YAML
      - by_name : nom normalisé  → produit YAML
    """
    by_ref  = {}
    by_name = {}
    for p in yaml_products:
        ref = _normalize(p.get("ref", ""))
        if ref:
            by_ref[ref] = p
        name = _normalize(p.get("name", ""))
        if name:
            by_name[name] = p
    return by_ref, by_name


def find_yaml_match(db_ref: str, db_desig: str,
                    by_ref: dict, by_name: dict) -> dict | None:
    # 1) Correspondance référence exacte
    ref_norm = _normalize(db_ref)
    if ref_norm and ref_norm in by_ref:
        return by_ref[ref_norm]

    # 2) Correspondance désignation exacte
    desig_norm = _normalize(db_desig)
    if desig_norm in by_name:
        return by_name[desig_norm]

    # 3) La désignation DB est incluse dans le nom YAML (ou l'inverse)
    for name_key, yp in by_name.items():
        if desig_norm in name_key or name_key in desig_norm:
            return yp

    return None


# ── Main ─────────────────────────────────────────────────────────────────────

def enrich(dry_run: bool = False) -> None:
    print("\n🔧 Enrichissement DB — mot + famille depuis products.yaml\n")

    yaml_products   = load_yaml_products(DATA_YAML)
    by_ref, by_name = build_indexes(yaml_products)

    conn = sqlite3.connect(DB_PATH)

    print("\n📋 Vérification des colonnes...")
    ensure_columns(conn)

    db_products = load_db_products(conn)
    print(f"📦 {len(db_products)} produits dans la DB\n")

    print("🔍 Matching en cours...")
    updates     = []
    matched     = 0
    not_matched = 0

    for db_p in db_products:
        yp = find_yaml_match(
            db_p.get("reference", ""),
            db_p.get("designation", ""),
            by_ref, by_name,
        )
        if yp:
            mot     = str(yp.get("mot",     "")).strip()
            famille = str(yp.get("famille", "")).strip()
            updates.append((mot, famille, db_p["rowid"]))
            matched += 1
        else:
            not_matched += 1

    print(f"  ✅ {matched} produits matchés ({matched*100//len(db_products)}%)")
    print(f"  ⚠️  {not_matched} sans correspondance YAML")

    if dry_run:
        print("\n🧪 DRY RUN — aucune modification en DB")
        print("   Exemples de ce qui serait mis à jour :\n")
        shown = 0
        for mot, famille, rowid in updates:
            if mot or famille:
                row = next(p for p in db_products if p["rowid"] == rowid)
                print(f"   {row['designation'][:45]:<45} mot={mot!r:15} famille={famille!r}")
                shown += 1
                if shown >= 15:
                    print(f"   ... ({matched - shown} autres)")
                    break
    else:
        print(f"\n💾 Application de {len(updates)} mises à jour...")
        conn.executemany(
            "UPDATE products SET mot = ?, famille = ? WHERE rowid = ?",
            updates
        )
        conn.commit()
        print("🎉 Enrichissement terminé !\n")

        # Statistiques
        stats = conn.execute(
            "SELECT famille, COUNT(*) as n FROM products "
            "WHERE famille IS NOT NULL AND famille != '' "
            "GROUP BY famille ORDER BY n DESC"
        ).fetchall()
        print("📊 Répartition par famille :")
        for fam, n in stats:
            print(f"   {fam:<40} {n:>5} produits")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enrichit la DB SQLite avec mot+famille depuis products.yaml"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche les changements sans modifier la DB")
    args = parser.parse_args()

    if not DATA_YAML.exists():
        print(f"❌ {DATA_YAML} introuvable")
        sys.exit(1)
    if not DB_PATH.exists():
        print(f"❌ {DB_PATH} introuvable — lance d'abord import_products.py")
        sys.exit(1)

    enrich(dry_run=args.dry_run)
