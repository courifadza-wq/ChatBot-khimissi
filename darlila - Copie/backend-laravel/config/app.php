<?php

return [

    'name' => env('APP_NAME', 'Laravel'),

    'env' => env('APP_ENV', 'production'),

    'debug' => (bool) env('APP_DEBUG', false),

    'url' => env('APP_URL', 'http://localhost'),

    /*
    |----------------------------------------------------------------------
    | URL du frontend Vue (utilisée pour les liens des e-mails, ex. le
    | bouton « Gérer la commande » de la notification au vendeur).
    |----------------------------------------------------------------------
    */
    /*
    |----------------------------------------------------------------------
    | URL du CDN Bunny.net (facultatif).
    | Si défini, les images relatives (/storage/…) sont servies via le
    | pull zone Bunny : ex. https://darlila.b-cdn.net/storage/products/x.jpg
    |----------------------------------------------------------------------
    */
    'bunny_cdn_url' => env('BUNNY_CDN_URL'),

    'admin_url' => env('FRONTEND_URL', env('APP_URL', 'http://localhost:5173')),

    'timezone' => env('APP_TIMEZONE', 'UTC'),

    'locale' => env('APP_LOCALE', 'fr'),

    'fallback_locale' => env('APP_FALLBACK_LOCALE', 'fr'),

    'faker_locale' => env('APP_FAKER_LOCALE', 'fr_FR'),

    'cipher' => 'AES-256-CBC',

    'key' => env('APP_KEY'),

    'previous_keys' => [
        ...array_filter(
            explode(',', env('APP_PREVIOUS_KEYS', ''))
        ),
    ],

    'maintenance' => [
        'driver' => env('APP_MAINTENANCE_DRIVER', 'file'),
        'store' => env('APP_MAINTENANCE_STORE', 'database'),
    ],

];
