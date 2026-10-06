# Plan de correction : Catégories, Sous-catégories et Affectation Produit

Deux ajustements majeurs sont apportés au frontend Vue.js pour répondre aux besoins de gestion du catalogue :

## 1. Affectation Produit (Catégorie Principale + Sous-Catégorie)
Dans le formulaire de création/édition de produit (`AdminProductForm.vue`), remplacer l'unique menu déroulant par **deux sélecteurs indépendants et réactifs** :
- **Sélecteur 1 : Catégorie principale** (liste des catégories mères).
- **Sélecteur 2 : Sous-catégorie** (se met à jour automatiquement selon la catégorie mère choisie).
  - Si la catégorie mère possède des sous-catégories, l'utilisateur peut en choisir une spécifique.
  - Si aucune sous-catégorie n'est choisie (ou s'il n'y en a pas), le produit est affecté directement à la catégorie mère.

## 2. Création de Catégorie Mère avec Sous-Catégories Simultanées
Dans la vue de gestion des catégories (`AdminCategoriesView.vue`) :
- Lors de la création d'une **Catégorie principale**, ajout d'une section dynamique **« Sous-catégories à créer simultanément »**.
- L'utilisateur peut cliquer sur **« + Ajouter une sous-catégorie »** pour ajouter autant de sous-catégories qu'il le souhaite (avec nom FR et nom AR) avant de valider le formulaire en une seule fois.

---

## Fichiers à modifier

### [frontend-vue](file:///c:/Users/Fujitsu/Downloads/APP/darlila/frontend-vue)

#### [MODIFY] [AdminProductForm.vue](file:///c:/Users/Fujitsu/Downloads/APP/darlila/frontend-vue/src/components/admin/AdminProductForm.vue)
- Ajouter `mainCategoryId` et `subCategoryId` réactifs.
- Remplacer le sélecteur unique avec `<optgroup>` par 2 sélecteurs :
  1. Catégorie principale (obligatoire)
  2. Sous-catégorie (optionnelle, filtrée selon la catégorie principale).
- Synchroniser automatiquement `form.category_id` avec la sous-catégorie sélectionnée (ou la catégorie principale par défaut).

#### [MODIFY] [AdminCategoriesView.vue](file:///c:/Users/Fujitsu/Downloads/APP/darlila/frontend-vue/src/views/AdminCategoriesView.vue)
- Ajouter la liste dynamique `subCategoriesToAdd` au formulaire de création de catégorie.
- Afficher un bloc d'ajout de sous-catégories lorsque `parent_id` est `null` (Catégorie principale).
- Dans `submit()`, créer la catégorie principale puis enchaîner la création des sous-catégories spécifiées.

---

## Plan de vérification

### Tests Manuels
1. **Création d'une catégorie mère avec sous-catégories :**
   - Aller dans Administration -> Catégories.
   - Cliquer sur `+ Nouvelle catégorie`.
   - Remplir le nom FR/AR de la catégorie principale (ex: *Bébé & Éveil*).
   - Cliquer sur `+ Ajouter une sous-catégorie` et saisir (ex: *Jouets d'éveil*, *Doudous*).
   - Enregistrer et vérifier l'affichage dans l'arbre hiérarchique.

2. **Création / Édition de produit avec double sélecteur :**
   - Aller dans Administration -> Produits.
   - Cliquer sur `+ Nouveau produit`.
   - Sélectionner la *Catégorie principale*.
   - Vérifier que le sélecteur *Sous-catégorie* se met à jour immédiatement avec la liste correspondante.
   - Sélectionner une sous-catégorie et enregistrer le produit.
   - Éditer à nouveau le produit pour vérifier la préservation exacte des deux sélecteurs.
