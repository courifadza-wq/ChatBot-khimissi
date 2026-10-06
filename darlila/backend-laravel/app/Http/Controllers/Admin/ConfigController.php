<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Services\BunnyStorage;
use App\Services\ImageOptimizer;
use Illuminate\Http\JsonResponse;

/**
 * Capacités de l'instance, utilisées par le frontend admin
 * (où sont stockées les images, compression WebP disponible…).
 */
class ConfigController extends Controller
{
    /**
     * GET /api/admin/config
     */
    public function __invoke(): JsonResponse
    {
        return response()->json([
            'data' => [
                'image_driver' => BunnyStorage::configured() ? 'bunny' : 'local',
                'webp' => ImageOptimizer::available(),
            ],
        ]);
    }
}
