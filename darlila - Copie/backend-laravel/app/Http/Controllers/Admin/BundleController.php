<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Http\Resources\BundleResource;
use App\Models\Bundle;
use App\Models\Product;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Support\Str;
use Illuminate\Validation\Rule;

/**
 * CRUD des lots (bundles) — espace admin.
 * Un lot regroupe plusieurs produits à un prix réduit ; la boutique
 * affiche le prix cumulé barré et le prix du lot.
 */
class BundleController extends Controller
{
    /**
     * GET /api/admin/bundles — tous les lots (actifs et inactifs).
     */
    public function index(Request $request): AnonymousResourceCollection
    {
        $bundles = Bundle::query()
            ->with('items.product')
            ->when(
                $request->filled('search'),
                function ($query) use ($request) {
                    $like = '%'.str_replace('%', '\%', trim($request->string('search'))).'%';

                    return $query->where(
                        fn ($w) => $w
                            ->where('name_fr', 'like', $like)
                            ->orWhere('name_ar', 'like', $like)
                            ->orWhere('slug', 'like', $like)
                    );
                }
            )
            ->orderBy('position')
            ->orderBy('id')
            ->get();

        return BundleResource::collection($bundles);
    }

    /**
     * POST /api/admin/bundles — création.
     * {
     *   "name_fr": "Lot Découverte", "name_ar": "…", "price": 15900,
     *   "image": null, "is_active": true,
     *   "items": [ {"product_id": 9, "quantity": 1}, … ]
     * }
     */
    public function store(Request $request): BundleResource
    {
        $validated = $this->validatedPayload($request, null);

        $validated['slug'] = $this->uniqueSlug($validated['slug'] ?? Str::slug($validated['name_fr']));

        $bundle = Bundle::create($validated);
        $this->syncItems($bundle, $request);

        return new BundleResource($bundle->load('items.product'));
    }

    /**
     * PUT/PATCH /api/admin/bundles/{bundle}
     */
    public function update(Request $request, Bundle $bundle): BundleResource
    {
        $validated = $this->validatedPayload($request, $bundle);

        if (isset($validated['slug']) && $validated['slug'] !== $bundle->slug) {
            $validated['slug'] = $this->uniqueSlug($validated['slug'], $bundle->id);
        }

        $bundle->update($validated);

        if ($request->has('items')) {
            $this->syncItems($bundle, $request);
        }

        return new BundleResource($bundle->load('items.product'));
    }

    /**
     * DELETE /api/admin/bundles/{bundle}
     */
    public function destroy(Bundle $bundle)
    {
        $bundle->delete();

        return response()->json([
            'data' => ['deleted' => true, 'slug' => $bundle->slug],
        ]);
    }

    /**
     * POST /api/admin/bundles/bulk-delete — suppression en masse.
     */
    public function bulkDelete(Request $request)
    {
        $validated = $request->validate([
            'ids' => ['required', 'array', 'min:1'],
            'ids.*' => ['required', 'integer', 'exists:bundles,id'],
        ]);

        $deleted = Bundle::whereIn('id', $validated['ids'])->delete();

        return response()->json([
            'data' => ['deleted' => $deleted],
        ]);
    }

    /* ---------------------------------------------------------------- */

    private function validatedPayload(Request $request, ?Bundle $existing): array
    {
        $validated = $request->validate([
            'slug' => [
                'sometimes', 'nullable', 'string', 'max:180',
                'regex:/^[a-z0-9]+(?:-[a-z0-9]+)*$/',
                Rule::unique('bundles', 'slug')->ignore($existing),
            ],
            'name_fr' => ['sometimes', 'required', 'string', 'max:180'],
            'name_ar' => ['sometimes', 'required', 'string', 'max:180'],
            'description_fr' => ['sometimes', 'nullable', 'string', 'max:2000'],
            'description_ar' => ['sometimes', 'nullable', 'string', 'max:2000'],
            'price' => ['sometimes', 'required', 'integer', 'min:0', 'max:999999999'],
            'image' => ['sometimes', 'nullable', 'url', 'max:500'],
            'is_active' => ['sometimes', 'boolean'],
            'is_featured' => ['sometimes', 'boolean'],
            'items' => ['sometimes', 'array'],
            'items.*.product_id' => ['required_with:items', 'integer', Rule::exists('products', 'id')],
            'items.*.quantity' => ['required_with:items', 'integer', 'min:1', 'max:99'],
        ]);

        if ($request->has('is_active')) {
            $validated['is_active'] = $request->boolean('is_active');
        }
        if ($request->has('is_featured')) {
            $validated['is_featured'] = $request->boolean('is_featured');
        }

        unset($validated['items']);

        return $validated;
    }

    /**
     * Remplace la composition du lot (simple et sûr : delete + recreate).
     */
    private function syncItems(Bundle $bundle, Request $request): void
    {
        $bundle->items()->delete();

        foreach ((array) $request->input('items', []) as $item) {
            $productId = (int) ($item['product_id'] ?? 0);
            $quantity = max(1, min(99, (int) ($item['quantity'] ?? 1)));

            if (Product::query()->whereKey($productId)->exists()) {
                $bundle->items()->create([
                    'product_id' => $productId,
                    'quantity' => $quantity,
                ]);
            }
        }
    }

    private function uniqueSlug(?string $slug, ?int $ignoreId = null): string
    {
        $slug = $slug ?: Str::slug('lot-'.Str::lower(Str::random(6)));
        $base = $slug;

        $query = Bundle::query()->where('slug', $slug);
        if ($ignoreId !== null) {
            $query->where('id', '!=', $ignoreId);
        }

        while ($query->exists()) {
            $slug = $base.'-'.Str::lower(Str::random(4));
            $query = Bundle::query()->where('slug', $slug);
            if ($ignoreId !== null) {
                $query->where('id', '!=', $ignoreId);
            }
        }

        return $slug;
    }
}
