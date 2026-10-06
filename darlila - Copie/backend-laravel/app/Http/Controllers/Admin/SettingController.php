<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Setting;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

/**
 * Réglages de la boutique — modifiables directement depuis l'admin.
 * Le vendeur peut changer le numéro WhatsApp, l'adresse, les horaires,
 * l'e-mail, etc. sans toucher au code.
 */
class SettingController extends Controller
{
    /**
     * GET /api/admin/settings — tous les réglages.
     */
    public function index(): JsonResponse
    {
        return response()->json([
            'data' => Setting::allAsArray(),
        ]);
    }

    /**
     * PUT /api/admin/settings — mise à jour en masse.
     * N'importe quelle clé peut être envoyée ; seules les clés non nulles sont mises à jour.
     */
    public function update(Request $request): JsonResponse
    {
        $allowed = [
            'whatsapp_number',
            'seller_email',
            'shop_name_fr', 'shop_name_ar',
            'shop_address_fr', 'shop_address_ar',
            'shop_hours_fr', 'shop_hours_ar',
            'shop_phone_display',
            'shop_email',
            'hero_image',
            'maps_query',
            'maps_url',
            'whatsapp_group_url',
            'instagram_url', 'facebook_url', 'tiktok_url',
        ];

        $validated = $request->validate(
            collect($allowed)->mapWithKeys(fn ($key) => [$key => ['sometimes', 'nullable', 'string', 'max:1000']])->all()
        );

        foreach ($validated as $key => $value) {
            if ($value !== null) {
                Setting::updateOrCreate(['key' => $key], ['value' => $value]);
            }
        }

        // purge le cache des réglages
        \Illuminate\Support\Facades\Cache::forget('darlila.settings');

        return response()->json([
            'data' => Setting::allAsArray(),
        ]);
    }
}
