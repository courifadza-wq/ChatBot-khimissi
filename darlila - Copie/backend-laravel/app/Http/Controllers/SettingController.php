<?php

namespace App\Http\Controllers;

use App\Models\Setting;
use Illuminate\Http\JsonResponse;

class SettingController extends Controller
{
    /**
     * Réglages publics de la boutique (clé => valeur).
     * GET /api/settings
     */
    public function __invoke(): JsonResponse
    {
        return response()->json([
            'data' => Setting::allAsArray(),
        ]);
    }
}
