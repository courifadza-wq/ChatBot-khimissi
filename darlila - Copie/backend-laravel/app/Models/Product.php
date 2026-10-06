<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Product extends Model
{
    protected $fillable = [
        'category_id',
        'slug',
        'name_fr',
        'name_ar',
        'description_fr',
        'description_ar',
        'price',
        'image',
        'is_featured',
        'is_active',
        'promo_quantity',
        'promo_percent',
        'position',
    ];

    protected $casts = [
        'price' => 'integer',
        'is_featured' => 'boolean',
        'is_active' => 'boolean',
        'promo_quantity' => 'integer',
        'promo_percent' => 'integer',
    ];

    /**
     * Une promotion « achetez N → -X % » est-elle active sur ce produit ?
     */
    public function hasPromo(): bool
    {
        return $this->promo_quantity !== null
            && $this->promo_quantity >= 2
            && $this->promo_percent !== null
            && $this->promo_percent >= 1
            && $this->promo_percent <= 99;
    }

    /**
     * Prix unitaire réel pour une quantité donnée : remise appliquée
     * dès que la quantité atteint le seuil promo (arrondi au dinar).
     */
    public function unitPriceFor(int $quantity): int
    {
        if (! $this->hasPromo() || $quantity < $this->promo_quantity) {
            return $this->price;
        }

        return (int) round($this->price * (100 - $this->promo_percent) / 100);
    }

    public function category(): BelongsTo
    {
        return $this->belongsTo(Category::class);
    }

    /**
     * Nom localisé selon la langue demandée (fr par défaut).
     */
    public function localizedName(string $lang): string
    {
        return $lang === 'ar' ? $this->name_ar : $this->name_fr;
    }

    /**
     * Description localisée selon la langue demandée.
     */
    public function localizedDescription(string $lang): ?string
    {
        return $lang === 'ar' ? $this->description_ar : $this->description_fr;
    }

    /**
     * Prix formaté, ex. « 8 500 DA » (ou « ٨٬٥٠٠ دج » en arabe).
     */
    public function formattedPrice(string $lang): string
    {
        $formatted = number_format(
            $this->price,
            0,
            '.',
            $lang === 'ar' ? '٬' : "\u{202F}"
        );

        return $lang === 'ar' ? $formatted.' دج' : $formatted.' DA';
    }

    /**
     * Produits visibles dans la boutique publique.
     */
    public function scopeActive(Builder $query): Builder
    {
        return $query->where('is_active', true);
    }

    /**
     * Filtre par slug de catégorie.
     *
     * Si le slug désigne une catégorie PRINCIPALE, les produits de
     * toutes ses sous-catégories sont inclus (ex. « Puériculture »
     * → Repas & Biberons, Sommeil, Toilette & Soins…).
     * Si le slug désigne une sous-catégorie, filtrage direct.
     */
    public function scopeInCategory(Builder $query, string $categorySlug): Builder
    {
        $category = Category::query()->where('slug', $categorySlug)->first();

        // Slug inconnu → aucun résultat (chips désynchronisés, etc.)
        if ($category === null) {
            return $query->whereRaw('1 = 0');
        }

        $ids = [$category->id];

        // Catégorie principale → inclure ses sous-catégories.
        if ($category->parent_id === null) {
            $ids = array_merge($ids, $category->children()->pluck('id')->all());
        }

        return $query->whereIn('category_id', $ids);
    }

    /**
     * Recherche plein texte simple sur les noms FR et AR.
     */
    public function scopeSearch(Builder $query, string $term): Builder
    {
        $like = '%'.str_replace('%', '\%', trim($term)).'%';

        return $query->where(
            fn (Builder $query) => $query
                ->where('name_fr', 'like', $like)
                ->orWhere('name_ar', 'like', $like)
                ->orWhere('description_fr', 'like', $like)
                ->orWhere('description_ar', 'like', $like)
        );
    }
}
