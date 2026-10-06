# 🧸 Mise à jour — Catégories & Sous-catégories

Cette mise à jour ajoute les **sous-catégories** (2 niveaux) :

```
Chaussures & Accessoires   → Chaussures · Sacs · Bonnets & Chapeaux · Chaussettes · Accessoires cheveux
Puériculture               → Repas & Biberons · Sommeil · Toilette & Soins · Promenade & Sorties · Équipement bébé
Jouets & Éveil             → Jouets · Éveil · Peluches
Cadeaux                    → Naissance · Anniversaire · Coffrets cadeaux
```

## Ce qui change

- **Boutique** : cliquer sur une catégorie principale fait apparaître une rangée
  de sous-catégories. Filtrer par une principale affiche AUSSI les produits
  de toutes ses sous-catégories.
- **Admin → Catégories** : formulaire avec « Catégorie parent » (Aucune =
  principale), tableau hiérarchique (sous-catégories en retrait ↳), bouton
  « + Sous-catégorie » sur chaque ligne principale.
- **Admin → Produits** : le sélecteur de catégorie est groupé par famille.

## Déploiement (3 étapes, ~10 minutes)

### Étape 1 — Backend : `2-BACKEND-api.khemicishop.com.zip`

1. hPanel → **Gestionnaire de fichiers** → `domains/api.khemicishop.com/`
2. Uploadez le ZIP et **Extrayez-le ici** (répondez **Remplacer** aux fichiers
   existants). Les fichiers concernés : `app/`, `database/migrations/`,
   `routes/api.php`.

### Étape 2 — Créer les catégories : `setup-subcategories.php`

1. Uploadez `setup-subcategories.php` dans
   `domains/api.khemicishop.com/public_html/`
2. Ouvrez dans le navigateur : **https://api.khemicishop.com/setup-subcategories.php**
3. Le script exécute la migration + crée les 4 catégories et 16
   sous-catégories (répétable sans risque).
4. **Supprimez le fichier** du serveur après utilisation. ⚠️ Important !

### Étape 3 — Frontend : `1-FRONTEND-khemicishop.com.zip`

1. hPanel → Gestionnaire de fichiers → `domains/khemicishop.com/public_html/`
2. Supprimez l'ancien dossier `assets` puis uploadez + extrayez le ZIP
   (Remplacer tout).
3. Videz le cache PWA : F12 → Application → Storage → **Clear site data**
   (ou Ctrl+Maj+R plusieurs fois).

## Et les anciennes catégories ?

Les catégories existantes (Parfums, Cosmétiques, Articles pour bébé…) sont
**conservées** avec leurs produits, repositionnées après les nouvelles. Pour
chacune d'elles :

1. **Admin → Produits** : modifiez chaque produit (ou ré-importez votre
   Excel avec la colonne `category` = slug de la sous-catégorie, ex.
   `toilette-soins`) ;
2. quand une ancienne catégorie est vide : **Admin → Catégories → Supprimer**.

### Slugs des sous-catégories (pour l'import Excel/CSV)

```
chaussures-accessoires : chaussures, sacs, bonnets-chapeaux, chaussettes, accessoires-cheveux
puericulture           : repas-biberons, sommeil, toilette-soins, promenade-sorties, equipement-bebe
jouets-eveil           : jouets, eveil, peluches
cadeaux                : naissance, anniversaire, coffrets-cadeaux
```
