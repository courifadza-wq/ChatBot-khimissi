<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Bundle extends Model
{
    protected $fillable = [
        'slug',
        'name_fr',
        'name_ar',
        'description_fr',
        'description_ar',
        'price',
        'image',
        'is_active',
        'is_featured',
        'position',
    ];

    protected $casts = [
        'price' => 'integer',
        'is_active' => 'boolean',
        'is_featured' => 'boolean',
    ];

    public function items(): HasMany
    {
        return $this->hasMany(BundleItem::class)->orderBy('id');
    }

    public function localizedName(string $lang): string
    {
        return $lang === 'ar' ? $this->name_ar : $this->name_fr;
    }

    /**
     * Prix cumulé des articles du lot, hors remise.
     */
    public function regularTotal(): int
    {
        return $this->items
            ->reduce(fn (int $sum, BundleItem $item) => $sum + $item->product->price * $item->quantity, 0);
    }

    /**
     * Image du lot : la sienne, sinon celle du premier article.
     */
    public function resolvedImage(): ?string
    {
        if ($this->image) {
            return $this->image;
        }

        return $this->items->first()?->product->image;
    }
}
