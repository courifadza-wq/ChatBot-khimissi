<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Http\Resources\ProductResource;
use App\Models\Category;
use App\Models\Product;
use App\Services\BunnyStorage;
use App\Services\ImageOptimizer;
use App\Support\EncodesCsv;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;
use Illuminate\Validation\Rule;

/**
 * Gestion des produits (espace admin) — pensée pour les gros catalogues :
 * liste paginée + recherche serveur, CRUD unitaire, import/export CSV
 * pour créer ou mettre à jour des centaines de produits d'un coup.
 *
 * Toutes les routes sont protégées par auth:sanctum + admin.
 */
class ProductController extends Controller
{
    use EncodesCsv;
    
    /**
     * GET /api/admin/products?search=&category=&page=&per_page=
     * Liste paginée (défaut 20/page) de tous les produits, actifs inclus.
     */
    public function index(Request $request): AnonymousResourceCollection
    {
        $query = Product::query()
            ->with('category')
            ->when(
                $request->filled('search'),
                function ($q) use ($request) {
                    $like = '%'.str_replace('%', '\%', trim($request->string('search'))).'%';

                    return $q->where(
                        fn ($w) => $w
                            ->where('name_fr', 'like', $like)
                            ->orWhere('name_ar', 'like', $like)
                            ->orWhere('slug', 'like', $like)
                    );
                }
            )
            ->when(
                $request->filled('category'),
                fn ($q) => $q->inCategory($request->string('category')->toString())
            )
            ->orderBy('position')
            ->orderBy('id');

        $perPage = min(max($request->integer('per_page', 20), 5), 100);

        return ProductResource::collection(
            $query->paginate($perPage)->withQueryString()
        );
    }

    /**
     * POST /api/admin/products — création.
     *
     * Accepte :
     *  - JSON { ..., image_url: "https://…" }
     *  - multipart/form-data avec un fichier « image » (jpg, png, webp ≤ 2 Mo)
     *    stocké sur Bunny Storage si configuré, sinon disque « public ».
     */
    public function store(Request $request): ProductResource
    {
        $validated = $this->validatedPayload($request, null);

        $validated['slug'] = $this->uniqueSlug(
            $validated['slug'] ?? Str::slug($validated['name_fr'])
        );

        $product = Product::create($validated);

        return new ProductResource($product->load('category'));
    }

    /**
     * PUT|PATCH /api/admin/products/{product} — mise à jour complète ou
     * partielle (ex. uniquement { is_active: false } depuis la liste).
     */
    public function update(Request $request, Product $product): ProductResource
    {
        $validated = $this->validatedPayload($request, $product);

        if (isset($validated['slug']) && $validated['slug'] !== $product->slug) {
            $validated['slug'] = $this->uniqueSlug($validated['slug'], $product->id);
        }

        // L'image n'est remplacée que si un fichier ou une URL est fournie
        $image = $this->resolveImage($request);
        if ($image !== null) {
            $validated['image'] = $image;
        }

        $product->update($validated);

        return new ProductResource($product->load('category'));
    }

    /**
     * DELETE /api/admin/products/{product}
     */
    public function destroy(Product $product)
    {
        // Nettoyage best-effort de l'image hébergée sur Bunny
        $bunny = BunnyStorage::make();
        if ($bunny !== null) {
            $bunnyPath = $bunny->pathFromUrl((string) $product->image);

            if ($bunnyPath !== null) {
                rescue(fn () => $bunny->delete($bunnyPath), null, false);
            }
        }

        $product->delete();

        return response()->json([
            'data' => ['deleted' => true, 'slug' => $product->slug],
        ]);
    }

    /**
     * POST /api/admin/products/bulk-delete — suppression en masse.
     * { "ids": [1, 2, 3, ...] }
     */
    public function bulkDelete(Request $request)
    {
        $validated = $request->validate([
            'ids' => ['required', 'array', 'min:1'],
            'ids.*' => ['required', 'integer', 'exists:products,id'],
        ]);

        $deleted = Product::whereIn('id', $validated['ids'])->delete();

        return response()->json([
            'data' => ['deleted' => $deleted],
        ]);
    }

    /* ==================================================================
     |  IMPORT / EXPORT CSV — indispensable pour les catalogues 1000+
     * ================================================================== */

    /**
     * Colonnes reconnues (en-tête insensible à la casse) :
     * category (slug ou nom FR), name_fr*, name_ar*, description_fr,
     * description_ar, price*, image (URL), slug, is_active, is_featured.
     *
     * Séparateur , ou ; détecté automatiquement. Un produit existant
     * (même slug) est mis à jour, sinon créé.
     *
     * POST /api/admin/products/import (multipart, champ « file »)
     */
    public function import(Request $request)
    {
        $request->validate([
            'file' => ['required', 'file', 'mimes:csv,txt', 'max:5120'],
        ]);

        $rows = $this->readCsv($request->file('file')->getRealPath());

        if ($rows === []) {
            return response()->json([
                'message' => 'Le fichier CSV est vide ou illisible.',
            ], 422);
        }

        $categories = Category::query()->get();
        $created = 0;
        $updated = 0;
        $errors = [];

        foreach ($rows as $index => $row) {
            $line = $index + 2; // +1 en-tête, +1 numérotation humaine

            $nameFr = trim((string) ($row['name_fr'] ?? ''));
            $nameAr = trim((string) ($row['name_ar'] ?? ''));
            $descFr = trim((string) ($row['description_fr'] ?? ''));
            $descAr = trim((string) ($row['description_ar'] ?? ''));
            $price = $row['price'] ?? null;

            if ($nameFr === '' || $nameAr === '') {
                $errors[] = "Ligne $line : name_fr et name_ar sont obligatoires.";
                continue;
            }

            if ($descFr === '' || $descAr === '') {
                $errors[] = "Ligne $line : description_fr et description_ar sont obligatoires.";
                continue;
            }

            if (! is_numeric($price) || (int) $price < 0) {
                $errors[] = "Ligne $line : prix invalide (« $price »).";
                continue;
            }

            $image = trim((string) ($row['image'] ?? ''));
            if ($image === '') {
                $errors[] = "Ligne $line : l'URL de l'image (Bunny CDN) est obligatoire.";
                continue;
            }

            // Catégorie : par sous-catégorie (category), sinon par catégorie mère (category_parent)
            $categoryKey = trim((string) ($row['category'] ?? ''));
            if ($categoryKey === '') {
                $categoryKey = trim((string) ($row['category_parent'] ?? ''));
            }

            $category = $categories->first(
                fn ($c) => $c->slug === $categoryKey
                    || $c->name_fr === $categoryKey
                    || $c->name_ar === $categoryKey
            ) ?? $categories->first();

            if ($category === null) {
                $errors[] = "Ligne $line : aucune catégorie disponible.";
                continue;
            }

            $slug = trim((string) ($row['slug'] ?? ''));
            $slug = $slug !== '' ? $slug : Str::slug($nameFr);

            $payload = [
                'category_id' => $category->id,
                'name_fr' => $nameFr,
                'name_ar' => $nameAr,
                'description_fr' => $descFr,
                'description_ar' => $descAr,
                'price' => (int) $price,
                'image' => $image,
                'is_active' => $this->csvBool($row['is_active'] ?? '1'),
                'is_featured' => $this->csvBool($row['is_featured'] ?? '0'),
            ];

            $image = trim((string) ($row['image'] ?? ''));
            if ($image !== '') {
                $payload['image'] = $image;
            }

            $existing = Product::query()->where('slug', $slug)->first();

            if ($existing !== null) {
                $existing->update($payload + ['slug' => $slug]);
                $updated++;
            } else {
                $payload['slug'] = $slug;
                Product::create($payload);
                $created++;
            }
        }

        return response()->json([
            'data' => [
                'created' => $created,
                'updated' => $updated,
                'errors' => $errors,
                'rows' => count($rows),
            ],
        ]);
    }

    /**
     * GET /api/admin/products/export — CSV de tout le catalogue
     * (modèle réutilisable pour l'import).
     */
    public function export()
    {
        $lines = ['category;name_fr;name_ar;description_fr;description_ar;price;image;slug;is_active;is_featured'];

        Product::query()
            ->with('category')
            ->orderBy('position')
            ->orderBy('id')
            ->chunk(500, function ($products) use (&$lines) {
                foreach ($products as $product) {
                    $lines[] = implode(';', [
                        $product->category->slug ?? '',
                        $this->csvCell($product->name_fr),
                        $this->csvCell($product->name_ar),
                        $this->csvCell($product->description_fr),
                        $this->csvCell($product->description_ar),
                        $product->price,
                        $this->csvCell($product->image),
                        $product->slug,
                        (int) $product->is_active,
                        (int) $product->is_featured,
                    ]);
                }
            });

        return response(implode("\n", $lines), 200, [
            'Content-Type' => 'text/csv; charset=UTF-8',
            'Content-Disposition' => 'attachment; filename="darlila-produits.csv"',
        ]);
    }

    /* ---------------------------------------------------------------- */

    private function validatedPayload(Request $request, ?Product $existing): array
    {
        $validated = $request->validate([
            'category_id' => ['sometimes', 'required', 'integer', Rule::exists('categories', 'id')],
            'slug' => [
                'sometimes', 'nullable', 'string', 'max:180',
                'regex:/^[a-z0-9]+(?:-[a-z0-9]+)*$/',
                Rule::unique('products', 'slug')->ignore($existing),
            ],
            'name_fr' => ['sometimes', 'required', 'string', 'max:180'],
            'name_ar' => ['sometimes', 'required', 'string', 'max:180'],
            'description_fr' => ['sometimes', 'nullable', 'string', 'max:2000'],
            'description_ar' => ['sometimes', 'nullable', 'string', 'max:2000'],
            'price' => ['sometimes', 'required', 'integer', 'min:0', 'max:999999999'],
            'image_url' => ['sometimes', 'nullable', 'url', 'max:500'],
            // Promotion « achetez N → -X % » (null/vide = inactive)
            'promo_quantity' => ['sometimes', 'nullable', 'integer', 'min:2', 'max:99'],
            'promo_percent' => ['sometimes', 'nullable', 'integer', 'min:1', 'max:99'],
        ]);

        // Une promo n'est valide que si les DEUX champs sont fournis
        if (array_key_exists('promo_quantity', $validated) xor array_key_exists('promo_percent', $validated)) {
            throw \Illuminate\Validation\ValidationException::withMessages([
                'promo_quantity' => 'Renseignez la quantité ET le pourcentage de réduction (ou laissez les deux vides).',
            ]);
        }

        // Les booléens peuvent arriver en JSON (true/false) ou en multipart
        // (« 1 »/« 0 ») : $request->boolean() normalise les deux formats.
        if ($request->has('is_featured')) {
            $validated['is_featured'] = $request->boolean('is_featured');
        }
        if ($request->has('is_active')) {
            $validated['is_active'] = $request->boolean('is_active');
        }

        if ($request->hasFile('image')) {
            $request->validate([
                'image' => ['file', 'image', 'mimes:jpg,jpeg,png,webp', 'max:2048'],
            ]);
        }

        return $validated;
    }

    /**
     * URL ou fichier téléversé → valeur du champ « image » en base.
     *
     * 1. Compression automatique : le fichier est converti en WebP
     *    (30-70 % de poids en moins) et redimensionné — voir
     *    App\Services\ImageOptimizer (extension GD requise).
     * 2. Stockage : Bunny Storage si configuré (URL CDN absolue),
     *    sinon disque local (/storage/products/…). Repli local
     *    automatique si Bunny échoue.
     */
    private function resolveImage(Request $request): ?string
    {
        if ($request->hasFile('image')) {
            $file = $request->file('image');

            $contents = file_get_contents($file->getRealPath());
            $extension = strtolower($file->getClientOriginalExtension() ?: 'jpg');

            // Conversion WebP automatique (sauf si GD indisponible)
            if (ImageOptimizer::available()) {
                $webp = (new ImageOptimizer())->toWebp($contents);

                if ($webp !== null) {
                    $contents = $webp;
                    $extension = 'webp';
                }
            }

            $bunny = BunnyStorage::make();
            if ($bunny !== null) {
                $path = 'produits/'.Str::uuid()->toString().'.'.$extension;

                $url = rescue(fn () => $bunny->upload($path, $contents), null, false);

                if ($url !== null) {
                    return $url;
                }
            }

            // Repli local : disque « public » → /storage/products/…
            $name = 'products/'.Str::uuid()->toString().'.'.$extension;
            Storage::disk('public')->put($name, $contents);

            return '/storage/'.$name;
        }

        $url = $request->string('image_url')->trim()->toString();

        return $url !== '' ? $url : null;
    }

    /**
     * Garantit un slug unique (suffixe aléatoire en cas de conflit).
     */
    private function uniqueSlug(?string $slug, ?int $ignoreId = null): string
    {
        $slug = $slug ?: Str::slug('produit-'.Str::lower(Str::random(6)));
        $base = $slug;

        $query = Product::query()->where('slug', $slug);
        if ($ignoreId !== null) {
            $query->where('id', '!=', $ignoreId);
        }

        while ($query->exists()) {
            $slug = $base.'-'.Str::lower(Str::random(4));
            $query = Product::query()->where('slug', $slug);
            if ($ignoreId !== null) {
                $query->where('id', '!=', $ignoreId);
            }
        }

        return $slug;
    }

    /* --- helpers CSV --- */

    private function readCsv(string $path): array
    {
        $contents = (string) file_get_contents($path);
        $contents = preg_replace('/^\xEF\xBB\xBF/', '', $contents); // BOM UTF-8
        $lines = preg_split('/\r\n|\r|\n/', trim($contents));

        if ($lines === false || count($lines) < 2) {
            return [];
        }

        // Détection du séparateur : ; ou ,
        $separator = substr_count($lines[0], ';') >= substr_count($lines[0], ',') ? ';' : ',';

        $header = array_map(
            fn ($cell) => Str::slug(trim($cell), '_'),
            str_getcsv($lines[0], $separator) ?: []
        );

        $rows = [];
        foreach (array_slice($lines, 1) as $line) {
            if (trim($line) === '') {
                continue;
            }
            $cells = str_getcsv($line, $separator) ?: [];
            $row = [];
            foreach ($header as $index => $key) {
                if ($key !== '') {
                    $row[$key] = $cells[$index] ?? '';
                }
            }
            $rows[] = $row;
        }

        return $rows;
    }

    private function csvBool($value): bool
    {
        return in_array(strtolower(trim((string) $value)), ['1', 'true', 'vrai', 'oui', 'yes', 'actif'], true);
    }

}
