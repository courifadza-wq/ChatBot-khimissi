# 📊 Guide & Canevas d'Importation Excel / CSV des Produits

Ce document sert de **guide d'instruction** pour votre client afin qu'il puisse remplir correctement son fichier Excel/CSV de produits avant de l'importer dans l'administration.

---

## 📌 Structure des Colonnes du Fichier Excel / CSV

Le fichier doit obligatoirement posséder les en-têtes de colonnes suivants sur la première ligne :

| Nom de la Colonne | Obligatoire | Description / Instructions de Remplissage | Exemple |
|---|---|---|---|
| `category` | **Oui** | Le **slug** ou le **nom** de la catégorie (principale ou sous-catégorie). | `chaussures`, `puericulture`, `jouets` |
| `name_fr` | **Oui** | Le nom du produit en **Français**. | `Baskets Bébé Cuir Souple` |
| `name_ar` | **Oui** | Le nom du produit en **Arabe**. | `حذاء رضع من الجلد الناعم` |
| `price` | **Oui** | Le prix du produit en Dinar Algérien (**DA**), sans espace ni symbole `DA`. | `2800` |
| `image` | Optionnel | L'URL publique de l'image (obtenue après téléversement sur Bunny.net). | `https://khemicishop.b-cdn.net/produits/baskets.jpg` |
| `description_fr` | Optionnel | La description détaillée du produit en **Français**. | `Baskets confortables en cuir souple pour premiers pas.` |
| `description_ar` | Optionnel | La description détaillée du produit en **Arabe**. | `حذاء مريح من الجلد الناعم للخطوات الأولى.` |
| `is_active` | Optionnel | Produit actif/visible sur la boutique ? `1` = Oui, `0` = Non (défaut : `1`). | `1` |
| `is_featured` | Optionnel | Produit affiché en Vedette en haut de la boutique ? `1` = Oui, `0` = Non (défaut : `0`). | `1` |
| `slug` | Optionnel | L'identifiant URL unique. Si laissé vide, il sera généré automatiquement depuis `name_fr`. | `baskets-bebe-cuir` |

---

## 🐰 Étape par Étape : Gestion des Images sur Bunny.net (Bunny CDN)

1. **Uploader les images sur Bunny.net** :
   - Connectez-vous sur votre tableau de bord **BunnyStorage / Bunny CDN**.
   - Allez dans votre dossier de stockage (ex: `produits/`).
   - Uploadez les photos de vos produits (`baskets-bebe.jpg`, `biberon-260ml.jpg`...).

2. **Copier les liens CDN des images** :
   - Pour chaque photo uploadée, copiez son URL publique Bunny CDN.
   - Exemple de lien : `https://khemicishop.b-cdn.net/produits/baskets-bebe.jpg`

3. **Coller le lien dans le fichier Excel** :
   - Dans votre tableau Excel, collez cette URL dans la colonne **`image`** de la ligne du produit correspondant.

---

## 🏷️ Répertoire des Catégories & Sous-Catégories Valides

Voici la liste exacte des mots à écrire dans la colonne **`category`** :

### 1. Univers : **Chaussures & Accessoires**
- `chaussures-accessoires` *(Catégorie mère)*
- `chaussures` *(Sous-catégorie)*
- `sacs` *(Sous-catégorie)*
- `bonnets-chapeaux` *(Sous-catégorie)*
- `chaussettes` *(Sous-catégorie)*
- `accessoires-cheveux` *(Sous-catégorie)*

### 2. Univers : **Puériculture**
- `puericulture` *(Catégorie mère)*
- `repas-biberons` *(Sous-catégorie)*
- `sommeil` *(Sous-catégorie)*
- `toilette-soins` *(Sous-catégorie)*
- `promenade-sorties` *(Sous-catégorie)*
- `equipement-bebe` *(Sous-catégorie)*

### 3. Univers : **Jouets & Éveil**
- `jouets-eveil` *(Catégorie mère)*
- `jouets` *(Sous-catégorie)*
- `eveil` *(Sous-catégorie)*
- `peluches` *(Sous-catégorie)*

### 4. Univers : **Cadeaux**
- `cadeaux` *(Catégorie mère)*
- `naissance` *(Sous-catégorie)*
- `anniversaire` *(Sous-catégorie)*
- `coffrets-cadeaux` *(Sous-catégorie)*

---

## 💾 Procédure d'Enregistrement sous Excel (Format CSV UTF-8)

1. Remplissez vos produits dans Microsoft Excel.
2. Cliquez sur **Fichier → Enregistrer sous**.
3. Dans le menu déroulant **Type de fichier**, choisissez **CSV UTF-8 (séparateur : point-virgule ou virgule) (*.csv)**.
4. Cliquez sur **Enregistrer**.
5. Rendez-vous dans **Admin → Produits → Importer Excel / CSV**, sélectionnez ce fichier et cliquez sur **Valider l'import**.
