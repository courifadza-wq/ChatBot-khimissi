#!/usr/bin/env python3
"""
Exporte les colonnes mot+famille depuis la DB locale vers un fichier SQL.
Applique ensuite ce fichier sur le VPS.

Usage local  : python scripts/export_enrichment.py
Usage VPS    : cat enrichment.sql | docker exec -i <container> sqlite3 /app/data/bot_memory.db
"""

import sqlite3
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "bot_memory.db"
OUT_SQL = ROOT / "data" / "enrichment.sql"


def export_sql() -> None:
    print(f"📂 Lecture de la DB locale ({DB_PATH})...")
    conn = sqlite3.connect(DB_PATH)

    # Vérifier que les colonnes existent et sont remplies
    rows = conn.execute(
        "SELECT designation, mot, famille FROM products "
        "WHERE mot IS NOT NULL AND mot != '' LIMIT 5"
    ).fetchall()

    if not rows:
        print("❌ La DB locale n'est pas encore enrichie. Lance d'abord enrich_from_yaml.py")
        conn.close()
        return

    print(f"   Exemple : {rows[0]}")

    # Générer les UPDATE SQL
    all_rows = conn.execute(
        "SELECT designation, mot, famille FROM products"
    ).fetchall()
    conn.close()

    print(f"✅ {len(all_rows)} produits à exporter")

    with open(OUT_SQL, "w", encoding="utf-8") as f:
        f.write("-- Enrichissement mot + famille — généré automatiquement\n")
        f.write("BEGIN TRANSACTION;\n\n")
        f.write("ALTER TABLE products ADD COLUMN mot TEXT DEFAULT '';\n")
        f.write("ALTER TABLE products ADD COLUMN famille TEXT DEFAULT '';\n\n")

        for designation, mot, famille in all_rows:
            desig_safe   = (designation or "").replace("'", "''")
            mot_safe     = (mot         or "").replace("'", "''")
            famille_safe = (famille     or "").replace("'", "''")
            f.write(
                f"UPDATE products SET mot='{mot_safe}', famille='{famille_safe}' "
                f"WHERE designation='{desig_safe}';\n"
            )

        f.write("\nCOMMIT;\n")


    size_kb = OUT_SQL.stat().st_size // 1024
    print(f"💾 Fichier SQL exporté : {OUT_SQL.name} ({size_kb} Ko)")
    print()
    print("📋 Pour appliquer sur le VPS, copie ce fichier et exécute :")
    print()
    print("  # Depuis ton PC Windows :")
    print(f"  scp data/enrichment.sql root@187.124.173.103:/tmp/")
    print()
    print("  # Sur le VPS :")
    cid = "$(docker ps | grep vkgblr | awk '{print $1}')"
    print(f"  docker cp /tmp/enrichment.sql {cid}:/tmp/enrichment.sql")
    print(f"  docker exec {cid} sqlite3 /app/data/bot_memory.db < /tmp/enrichment.sql 2>/dev/null || \\")
    print(f"  docker exec {cid} sqlite3 /app/data/bot_memory.db '.read /tmp/enrichment.sql'")


if __name__ == "__main__":
    export_sql()
