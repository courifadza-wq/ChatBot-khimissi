<?php

namespace App\Http\Controllers;

use App\Http\Resources\CategoryResource;
use App\Models\Category;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;

class CategoryController extends Controller
{
    /**
     * Liste des catégories (principales + sous-catégories), avec le
     * nombre de produits direct de chacune. Chaque sous-catégorie est
     * renvoyée juste après son parent, avec son `parent_id`.
     * GET /api/categories
     */
    public function index(): AnonymousResourceCollection
    {
        $categories = Category::query()
            ->withCount('products')
            // Ordre « famille » : chaque principale suivie de ses sous-
            // catégories, les familles triées par position de la principale.
            ->orderByRaw('COALESCE((SELECT p.position FROM categories p WHERE p.id = categories.parent_id), position) ASC, (parent_id IS NULL) DESC, position ASC, id ASC')
            ->get();

        return CategoryResource::collection($categories);
    }
}
