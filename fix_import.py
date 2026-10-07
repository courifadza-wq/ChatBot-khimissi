import re

with open(r'c:\Users\Fujitsu\Desktop\Docs\bot\chatbot_whatsapp\scripts\import_products.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_func = r'''def import_excel(excel_path: Path) -> None:
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
'''

content = re.sub(r'def import_excel\(excel_path: Path\) -> None:.*?if __name__ == "__main__":', new_func + '\n\nif __name__ == "__main__":', content, flags=re.DOTALL)

with open(r'c:\Users\Fujitsu\Desktop\Docs\bot\chatbot_whatsapp\scripts\import_products.py', 'w', encoding='utf-8') as f:
    f.write(content)
