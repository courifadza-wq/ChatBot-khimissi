<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Review extends Model
{
    protected $fillable = [
        'author_name',
        'city_fr',
        'city_ar',
        'content_fr',
        'content_ar',
        'rating',
        'is_approved',
        'position',
    ];

    protected $casts = [
        'rating' => 'integer',
        'is_approved' => 'boolean',
    ];
}
