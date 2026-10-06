#!/usr/bin/env python3
"""
Script d'import du catalogue Excel → SQLite
Usage : python scripts/import_products.py
"""
import re
import sys
from pathlib import Path

# Ajouter le répertoire racine au path pour importer app.database
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    import openpyxl
except ImportError:
    print("Installation de openpyxl...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "openpyxl", "-q"])
    import openpyxl

from app.database import init_db, bulk_insert_products

# ── Mapping catégories (mots-clés → catégorie) ──────────────────────────────
CATEGORY_RULES = [
    # Vêtements
    (["VESTE", "VEST", "BLOUSON", "MANTEAU", "PARKA", "GILET", "PULL", "TRICO",
      "ROBE", "JUPE", "COMBINAISON", "SALOPETTE", "BODY", "PYJAMA", "GRENOUILLE",
      "PANTALON", "JEAN", "LEGGING", "SHORT", "BERMUDA", "T-SHIRT", "POLO",
      "SWEAT", "CHEMISE", "CARDIGAN", "MAILLOT", "COMBI", "ENSEMBLE", "SET",
      "CAPUCHE", "PYJAMAS", "JOGGING", "TENUE", "HABIT"], "Vêtements"),

    # Chaussures
    (["CHAUSSURE", "CHAUSS", "SANDALE", "BOTTE", "BOTTINE", "BASKET",
      "SNEAKER", "BALLERINE", "MOC", "CLAQUETTE", "ESPADRILLE",
      "PANTOUFLE", "SOCQUETTE", "CHAUSSETTE"], "Chaussures & Chaussettes"),

    # Puériculture / Bébé
    (["BIBERON", "TETINE", "SUCETTE", "TÉTINE", "ANNEAU DENT", "GOUPILLON",
      "TIRE LAIT", "CHAUFFE", "STERILISATEUR", "POUSSETTE", "SIEGE AUTO",
      "COSY", "NACELLE", "PARC", "TRANSAT", "BAIGNOIRE", "BAIGNE",
      "TAPIS EVEIL", "MOBILE", "VEILLEUSE", "THERMOMETRE"], "Puériculture"),

    # Alimentation bébé
    (["CUILLERE", "CUILLER", "FOURCHETTE", "ASSIETTE", "BOL", "GOBELET",
      "COUPE", "BAVETTE", "BAVOIR", "LAIT", "CEREALE", "COMPOTE",
      "FARINE", "ALIMENTATION", "REPAS"], "Alimentation bébé"),

    # Hygiène & Soin
    (["SAVON", "GEL", "CREME", "CRÈME", "SHAMPOOING", "LOTION", "LAIT CORPS",
      "LINGETTE", "COTON", "BROSSE", "PEIGNE", "BAIN MOUSSANT", "HUILE",
      "TALC", "MUSTELA", "JOHNSON", "BEPANTHEN"], "Hygiène & Soin"),

    # Couches & Linge
    (["COUCHE", "LAYER", "COUVERTURE", "COUETTE", "DRAP", "TAIE",
      "ALESE", "GIGOTEUSE", "TURBULETTE", "LANGE", "MOUFLE", "BONNET",
      "GANT", "ECHARPE", "BAVOIR"], "Linge & Couches"),

    # Jouets & Éveil
    (["JOUET", "JEU", "PUZZLE", "PELUCHE", "DOUDOU", "POUPEE", "VOITURE",
      "CUBE", "BLOCK", "LEGO", "TRAIN", "CIRCUIT", "BALLE", "BALLON",
      "TRICYCLE", "TROTTINETTE", "VELO", "GUN", "PISTOLET", "BULLE",
      "HOCHET", "ACTIVITE", "MUSICAL", "PIANO"], "Jouets & Éveil"),

    # Coffrets & Cadeaux
    (["COFFRET", "SET CADEAU", "CADEAU", "KIT", "TROUSSE", "BOITE"], "Coffrets & Cadeaux"),
]

# ── Extraction de la tranche d'âge ──────────────────────────────────────────
AGE_PATTERNS = [
    (r'\b0[/\-]?[13]M\b', "0-3 mois"),
    (r'\b0[/\-]?6M\b', "0-6 mois"),
    (r'\b0[/\-]?2M\b', "0-2 mois"),
    (r'\b[36][/\-]?12M\b', "3-12 mois"),
    (r'\b6[/\-]?18M\b', "6-18 mois"),
    (r'\b6[/\-]?24M\b', "6-24 mois"),
    (r'\b[01]2[/\-]?24M\b', "12-24 mois"),
    (r'\b[12][/\-]?4A\b', "2-4 ans"),
    (r'\b[24][/\-]?8A\b', "4-8 ans"),
    (r'\b[48][/\-]?16A\b', "8-16 ans"),
    (r'\bBEBE\b', "Bébé"),
    (r'\bNOUVEAU[- ]?NE\b', "Nouveau-né"),
]


def extract_category(designation: str) -> str:
    upper = designation.upper()
    for keywords, cat in CATEGORY_RULES:
        if any(kw in upper for kw in keywords):
            return cat
    return "Divers"


def extract_age(designation: str) -> str:
    upper = designation.upper()
    for pattern, label in AGE_PATTERNS:
        if re.search(pattern, upper):
            return label
    return ""


def clean_name(designation: str) -> str:
    """Nettoie les espaces et caractères en début de désignation."""
    return designation.strip().lstrip(".").strip()


def import_excel(excel_path: Path) -> None:
    print(f"Lecture de {excel_path.name}...")
    wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
    ws = wb.active

    # Lire les headers (ligne 1)
    headers = [str(c.value).lower().strip() if c.value else "" for c in ws[1]]
    
    # Trouver les index des colonnes utiles
    idx_desig = 0
    if "désignation" in headers: idx_desig = headers.index("désignation")
    elif "designation" in headers: idx_desig = headers.index("designation")
    elif "name_fr" in headers: idx_desig = headers.index("name_fr")
    elif "name" in headers: idx_desig = headers.index("name")
    
    idx_ref = 1
    if "référence" in headers: idx_ref = headers.index("référence")
    elif "reference" in headers: idx_ref = headers.index("reference")
    elif "sku" in headers: idx_ref = headers.index("sku")
    
    idx_stock = 2
    if "stock réel" in headers: idx_stock = headers.index("stock réel")
    elif "stock reel" in headers: idx_stock = headers.index("stock reel")
    elif "stock" in headers: idx_stock = headers.index("stock")
    elif "quantite" in headers: idx_stock = headers.index("quantite")
    
    idx_price = 3
    if "prix de vente  ttc" in headers: idx_price = headers.index("prix de vente  ttc")
    elif "prix de vente ttc" in headers: idx_price = headers.index("prix de vente ttc")
    elif "prix" in headers: idx_price = headers.index("prix")
    elif "price" in headers: idx_price = headers.index("price")
    
    idx_img = -1
    if "image" in headers: idx_img = headers.index("image")
    elif "image_url" in headers: idx_img = headers.index("image_url")
    elif "lien_image" in headers: idx_img = headers.index("lien_image")

    products = []
    skipped = 0

    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if not row: continue
            
        designation = row[idx_desig] if idx_desig < len(row) else None
        
        # Si la nouvelle template n'a pas de reference (idx_ref introuvable ou vide), on utilise un format fallback
        if "référence" not in headers and "reference" not in headers and "sku" not in headers:
            reference = f"REF-{i+1}"
        else:
            reference = row[idx_ref] if idx_ref < len(row) else None

        stock = row[idx_stock] if idx_stock < len(row) else 0
        price = row[idx_price] if idx_price < len(row) else None
        
        image_url = ""
        if idx_img != -1 and idx_img < len(row):
            val = row[idx_img]
            if val and isinstance(val, str) and val.startswith("http"):
                image_url = val.strip()

        # Ignorer les lignes incompletes
        if not designation or price is None:
            skipped += 1
            continue

        try:
            price_val = float(price)
            stock_val = int(stock) if stock is not None else 0
        except (ValueError, TypeError):
            skipped += 1
            continue

        name = clean_name(str(designation))
        products.append({
            "designation": name,
            "reference":   str(reference).strip() if reference else "",
            "stock":       stock_val,
            "price":       price_val,
            "category":    extract_category(name),
            "age_range":   extract_age(name),
            "image_url":   image_url
        })

    wb.close()
    print(f"{len(products)} produits valides ({skipped} ignores)")

    print("Import dans SQLite...")
    init_db()
    inserted = bulk_insert_products(products)
    print(f"{inserted} produits importes avec succes !")


if __name__ == "__main__":
    excel_file = ROOT / "BASE DE DONNEES PK.xlsx"
    if not excel_file.exists():
        # Chercher dans le répertoire courant
        excel_file = Path("BASE DE DONNEES PK.xlsx")
    if not excel_file.exists():
        print("❌ Fichier Excel introuvable. Placez-le dans le répertoire chatbot_whatsapp/")
        sys.exit(1)

    import_excel(excel_file)
