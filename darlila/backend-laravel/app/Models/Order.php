<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Order extends Model
{
    /**
     * Statuts possibles d'une commande.
     */
    public const STATUS_NEW = 'nouvelle';
    public const STATUS_CONFIRMED = 'confirmee';
    public const STATUS_SHIPPED = 'expediee';
    public const STATUS_DELIVERED = 'livree';
    public const STATUS_CANCELLED = 'annulee';

    protected $fillable = [
        'reference',
        'customer_name',
        'customer_phone',
        'wilaya',
        'address',
        'notes',
        'total',
        'status',
    ];

    protected $casts = [
        'total' => 'integer',
    ];

    public function items(): HasMany
    {
        return $this->hasMany(OrderItem::class);
    }
}
