<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Services tiers
    |--------------------------------------------------------------------------
    |
    | Bunny.net (CDN + stockage d'images) :
    |  - BUNNY_CDN_URL          : pull zone devant le site (cache /storage/…)
    |  - BUNNY_STORAGE_*        : storage zone pour le téléversement direct
    |                              depuis l'admin (voir App\Services\BunnyStorage)
    |
    */

    'bunny' => [
        'storage_zone' => env('BUNNY_STORAGE_ZONE'),
        'storage_key' => env('BUNNY_STORAGE_KEY'),
        'storage_cdn_url' => env('BUNNY_STORAGE_CDN_URL', env('BUNNY_CDN_URL')),
    ],

];
