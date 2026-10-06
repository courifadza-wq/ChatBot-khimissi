<?php

namespace App\Http\Controllers;

use App\Http\Resources\ProductResource;
use App\Models\Product;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;

class ProductController extends Controller
{
    /**
     * Liste paginée des produits actifs — conçue pour les gros catalogues
     * (1000+ produits) : filtrage, recherche et pagination côté serveur.
     *
     * GET /api/products
     *   ?category=parfums        filtre par slug de catégorie
     *   &search=oud              recherche sur les noms/descriptions FR et AR
     *   &featured=1              produits en vedette uniquement
     *   &page=2&per_page=24      pagination (per_page : 4 à 100, ou « all »)
     *   &ids=1,5,9               sélection d'identifiants (non paginé)
     *
     * Réponse paginée : { "data": [...], "meta": { total, current_page,
     * last_page, per_page } } — sans meta quand « all » ou « ids ».
     */
    public function index(Request $request): AnonymousResourceCollection
    {
        $query = Product::query()
            ->active()
            ->with('category')
            ->when(
                $request->filled('category'),
                fn ($q) => $q->inCategory($request->string('category')->toString())
            )
            ->when(
                $request->filled('search'),
                fn ($q) => $q->search($request->string('search')->toString())
            )
            ->when(
                $request->boolean('featured'),
                fn ($q) => $q->where('is_featured', true)
            )
            ->when(
                $request->filled('ids'),
                fn ($q) => $q->whereIn('id', collect(explode(',', $request->string('ids')))
                    ->filter(fn ($id) => is_numeric(trim($id)))
                    ->map(fn ($id) => (int) trim($id))
                    ->take(100)
                    ->all())
            )
            // Les produits « en vedette » sont affichés EN PREMIER
            // dans la boutique (avant les autres, quel que soit leur ordre).
            ->orderByDesc('is_featured')
            ->orderBy('position')
            ->orderBy('id');

        // Sélection explicite d'identifiants (hydration du panier) → non paginé
        if ($request->filled('ids')) {
            return ProductResource::collection($query->get());
        }

        // Catalogue complet (sitemap, exports…) → non paginé
        if ($request->string('per_page')->lower()->toString() === 'all') {
            return ProductResource::collection($query->get());
        }

        $perPage = min(max($request->integer('per_page', 24), 4), 100);

        return ProductResource::collection(
            $query->paginate($perPage)->withQueryString()
        );
    }

    /**
     * Détail d'un produit par son slug.
     * GET /api/products/{slug}
     */
    public function show(string $slug): ProductResource
    {
        $product = Product::query()
            ->active()
            ->with('category')
            ->where('slug', $slug)
            ->firstOrFail();

        return new ProductResource($product);
    }
}
