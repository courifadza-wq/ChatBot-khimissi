<?php

namespace App\Http\Resources;

/**
 * Petit helper partagé par les Resources : préfixe les chemins d'images
 * relatifs (/storage/…) avec l'URL du CDN Bunny.net si elle est configurée,
 * ce qui met les images en cache sur les serveurs edge sans changer la base.
 */
class ResolvesCdnUrls
{
    public static function image(?string $path): ?string
    {
        if ($path === null || $path === '' || ! str_starts_with($path, '/')) {
            return $path; // URL absolue (http…) → renvoyée telle quelle
        }

        $cdn = rtrim((string) config('app.bunny_cdn_url'), '/');

        return $cdn !== '' ? $cdn.$path : $path;
    }
}
