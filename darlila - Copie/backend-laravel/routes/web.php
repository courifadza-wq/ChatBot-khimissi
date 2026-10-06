<?php

use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return response()->json([
        'name' => config('app.name'),
        'status' => 'ok',
        'docs' => 'API Dar Lila — voir /api/products, /api/categories, /api/reviews, /api/gallery, /api/settings, POST /api/orders',
    ]);
});
