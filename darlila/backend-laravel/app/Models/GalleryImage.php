<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class GalleryImage extends Model
{
    protected $fillable = [
        'image',
        'alt_fr',
        'alt_ar',
        'position',
    ];
}
