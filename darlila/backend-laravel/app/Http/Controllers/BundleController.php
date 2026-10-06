<?php

namespace App\Http\Controllers;

use App\Http\Resources\BundleResource;
use App\Models\Bundle;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;

class BundleController extends Controller
{
    /**
     * GET /api/bundles — lots actifs (avec composition et économies).
     */
    public function index(): AnonymousResourceCollection
    {
        $bundles = Bundle::query()
            ->with('items.product')
            ->where('is_active', true)
            // Les lots « en vedette » s'affichent en tête de la section
            ->orderByDesc('is_featured')
            ->orderBy('position')
            ->orderBy('id')
            ->get();

        return BundleResource::collection($bundles);
    }
}
