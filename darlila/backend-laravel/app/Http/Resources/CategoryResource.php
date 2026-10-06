<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/**
 * @mixin \App\Models\Category
 */
class CategoryResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'parent_id' => $this->parent_id,
            'slug' => $this->slug,
            'name_fr' => $this->name_fr,
            'name_ar' => $this->name_ar,
            'description_fr' => $this->description_fr,
            'description_ar' => $this->description_ar,
            'position' => $this->position,
            'products_count' => $this->whenCounted('products'),
        ];
    }
}
