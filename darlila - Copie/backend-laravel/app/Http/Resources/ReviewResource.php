<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/**
 * @mixin \App\Models\Review
 */
class ReviewResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'author_name' => $this->author_name,
            'city_fr' => $this->city_fr,
            'city_ar' => $this->city_ar,
            'content_fr' => $this->content_fr,
            'content_ar' => $this->content_ar,
            'rating' => $this->rating,
        ];
    }
}
