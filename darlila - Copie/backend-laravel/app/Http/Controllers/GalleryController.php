<?php

namespace App\Http\Controllers;

use App\Http\Resources\GalleryResource;
use App\Models\GalleryImage;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;

class GalleryController extends Controller
{
    /**
     * Images de la galerie.
     * GET /api/gallery
     */
    public function index(): AnonymousResourceCollection
    {
        $images = GalleryImage::query()
            ->orderBy('position')
            ->orderBy('id')
            ->get();

        return GalleryResource::collection($images);
    }
}
