<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/**
 * @mixin \App\Models\GalleryImage
 */
class GalleryResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'image' => \App\Http\Resources\ResolvesCdnUrls::image($this->image),
            'alt_fr' => $this->alt_fr,
            'alt_ar' => $this->alt_ar,
        ];
    }
}
