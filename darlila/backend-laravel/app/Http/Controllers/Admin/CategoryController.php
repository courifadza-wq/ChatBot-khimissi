<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Http\Resources\CategoryResource;
use App\Models\Category;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Support\Str;
use Illuminate\Validation\Rule;

/**
 * Gestion des catégories (espace admin) — 8 catégories préremplies
 * par le seeder, libres d'évoluer avec le catalogue.
 *
 * Sécurité : une catégorie utilisée par des produits ne peut pas être
 * supprimée (il faut d'abord déplacer ou supprimer ses produits).
 */
class CategoryController extends Controller
{
    /**
     * GET /api/admin/categories — avec le nombre de produits,
     * chaque sous-catégorie juste après sa catégorie parent.
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

    /**
     * POST /api/admin/categories
     */
    public function store(Request $request): CategoryResource
    {
        $validated = $request->validate($this->rules(null), $this->messages());

        $validated['slug'] = $this->uniqueSlug(
            $validated['slug'] ?? Str::slug($validated['name_fr'])
        );

        $category = Category::create($validated);

        return new CategoryResource($category);
    }

    /**
     * PUT/PATCH /api/admin/categories/{category}
     */
    public function update(Request $request, Category $category): CategoryResource
    {
        $validated = $request->validate($this->rules($category), $this->messages());

        if (isset($validated['slug']) && $validated['slug'] !== $category->slug) {
            $validated['slug'] = $this->uniqueSlug($validated['slug'], $category->id);
        }

        $category->update($validated);

        return new CategoryResource($category);
    }

    /**
     * DELETE /api/admin/categories/{category} — refusé si des produits
     * y sont rattachés ou si elle possède des sous-catégories
     * (évite les produits orphelins et les sous-catégories perdues).
     */
    public function destroy(Category $category)
    {
        $count = $category->products()->count();

        if ($count > 0) {
            return response()->json([
                'message' => sprintf(
                    'Impossible de supprimer « %s » : %d produit(s) y sont rattachés. Déplacez ou supprimez d\'abord ces produits.',
                    $category->name_fr,
                    $count
                ),
            ], 422);
        }

        $children = $category->children()->count();

        if ($children > 0) {
            return response()->json([
                'message' => sprintf(
                    'Impossible de supprimer « %s » : elle possède %d sous-catégorie(s). Supprimez d\'abord ses sous-catégories.',
                    $category->name_fr,
                    $children
                ),
            ], 422);
        }

        $category->delete();

        return response()->json([
            'data' => ['deleted' => true, 'slug' => $category->slug],
        ]);
    }

    /* ---------------------------------------------------------------- */

    private function rules(?Category $existing): array
    {
        return [
            'slug' => [
                'sometimes', 'nullable', 'string', 'max:180',
                'regex:/^[a-z0-9]+(?:-[a-z0-9]+)*$/',
                Rule::unique('categories', 'slug')->ignore($existing),
            ],
            // NULL = catégorie principale ; sinon identifiant d'une
            // catégorie PRINCIPALE (2 niveaux maximum, pas de petits-enfants).
            'parent_id' => [
                'sometimes', 'nullable', 'integer',
                Rule::exists('categories', 'id')->where('parent_id', null),
                Rule::prohibitedIf(fn () => $existing !== null
                    && (int) request()->integer('parent_id', 0) === $existing->id),
            ],
            'name_fr' => ['sometimes', 'required', 'string', 'max:180'],
            'name_ar' => ['sometimes', 'required', 'string', 'max:180'],
            'description_fr' => ['sometimes', 'nullable', 'string', 'max:2000'],
            'description_ar' => ['sometimes', 'nullable', 'string', 'max:2000'],
            'position' => ['sometimes', 'nullable', 'integer', 'min:0', 'max:9999'],
        ];
    }

    private function messages(): array
    {
        return [
            'parent_id.exists' => "La catégorie parent est introuvable ou n'est pas une catégorie principale (2 niveaux maximum).",
            'parent_id.prohibited' => 'Une catégorie ne peut pas être son propre parent.',
        ];
    }

    private function uniqueSlug(?string $slug, ?int $ignoreId = null): string
    {
        $slug = $slug ?: Str::slug('categorie-'.Str::lower(Str::random(6)));
        $base = $slug;

        $query = Category::query()->where('slug', $slug);
        if ($ignoreId !== null) {
            $query->where('id', '!=', $ignoreId);
        }

        while ($query->exists()) {
            $slug = $base.'-'.Str::lower(Str::random(4));
            $query = Category::query()->where('slug', $slug);
            if ($ignoreId !== null) {
                $query->where('id', '!=', $ignoreId);
            }
        }

        return $slug;
    }
}
