<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/**
 * @mixin \App\Models\Product
 */
class ProductResource extends JsonResource
{
    /**
     * Transforme un produit en tableau JSON.
     *
     * Les champs _fr et _ar sont tous renvoyés afin que le front Vue.js
     * puisse changer de langue instantanément sans refetch.
     */
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'slug' => $this->slug,
            'name_fr' => $this->name_fr,
            'name_ar' => $this->name_ar,
            'description_fr' => $this->description_fr,
            'description_ar' => $this->description_ar,
            'price' => $this->price,
            'image' => \App\Http\Resources\ResolvesCdnUrls::image($this->image),
            'is_featured' => $this->is_featured,
            'is_active' => $this->is_active,
            'promo_quantity' => $this->promo_quantity,
            'promo_percent' => $this->promo_percent,
            'promo_active' => $this->hasPromo(),
            'category' => new CategoryResource($this->whenLoaded('category')),
            'created_at' => $this->created_at?->toISOString(),
        ];
    }
}
