<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/**
 * @mixin \App\Models\Bundle
 */
class BundleResource extends JsonResource
{
    /**
     * Lot public : composition, prix cumulé barré, économie réalisée.
     */
    public function toArray(Request $request): array
    {
        $regularTotal = $this->regularTotal();
        $savings = max(0, $regularTotal - $this->price);
        $savingsPercent = $regularTotal > 0 ? round($savings / $regularTotal * 100) : 0;

        return [
            'id' => $this->id,
            'slug' => $this->slug,
            'name_fr' => $this->name_fr,
            'name_ar' => $this->name_ar,
            'description_fr' => $this->description_fr,
            'description_ar' => $this->description_ar,
            'price' => $this->price,
            'image' => \App\Http\Resources\ResolvesCdnUrls::image($this->resolvedImage()),
            'regular_total' => $regularTotal,
            'savings' => $savings,
            'savings_percent' => (int) $savingsPercent,
            'is_active' => $this->is_active,
            'is_featured' => $this->is_featured,
            'items' => $this->whenLoaded('items', fn () => $this->items->map(fn ($item) => [
                'id' => $item->id,
                'quantity' => $item->quantity,
                'product' => [
                    'id' => $item->product->id,
                    'slug' => $item->product->slug,
                    'name_fr' => $item->product->name_fr,
                    'name_ar' => $item->product->name_ar,
                    'description_fr' => $item->product->description_fr,
                    'description_ar' => $item->product->description_ar,
                    'price' => $item->product->price,
                    'image' => \App\Http\Resources\ResolvesCdnUrls::image($item->product->image),
                ],
            ])),
        ];
    }
}
