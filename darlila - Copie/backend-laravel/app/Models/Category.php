<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Category extends Model
{
    protected $fillable = [
        'parent_id',
        'slug',
        'name_fr',
        'name_ar',
        'description_fr',
        'description_ar',
        'position',
    ];

    public function products(): HasMany
    {
        return $this->hasMany(Product::class);
    }

    /**
     * Catégorie parent (NULL pour une catégorie principale).
     */
    public function parent(): BelongsTo
    {
        return $this->belongsTo(self::class, 'parent_id');
    }

    /**
     * Sous-catégories directes (triées comme les catégories).
     */
    public function children(): HasMany
    {
        return $this->hasMany(self::class, 'parent_id')
            ->orderBy('position')
            ->orderBy('id');
    }

    /**
     * Une catégorie « principale » n'a pas de parent ; une
     * « sous-catégorie » en a un (2 niveaux maximum).
     */
    public function isMain(): bool
    {
        return $this->parent_id === null;
    }
}
