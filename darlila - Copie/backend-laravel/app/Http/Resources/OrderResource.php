<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/**
 * @mixin \App\Models\Order
 */
class OrderResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'reference' => $this->reference,
            'customer_name' => $this->customer_name,
            'customer_phone' => $this->customer_phone,
            'wilaya' => $this->wilaya,
            'address' => $this->address,
            'notes' => $this->notes,
            'total' => $this->total,
            'status' => $this->status,
            'items' => OrderItemResource::collection($this->whenLoaded('items')),
            'created_at' => $this->created_at?->toISOString(),
        ];
    }
}
