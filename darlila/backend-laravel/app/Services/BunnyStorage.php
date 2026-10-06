<?php

namespace App\Services;

use Illuminate\Http\Client\ConnectionException;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Str;

/**
 * Client minimaliste du Storage Bunny.net (API HTTP officielle, zéro dépendance).
 *
 * Configuration .env :
 *   BUNNY_STORAGE_ZONE=darlila                      (nom du storage zone)
 *   BUNNY_STORAGE_KEY=xxxxxxxx                      (clé API du storage zone)
 *   BUNNY_STORAGE_CDN_URL=https://darlila.b-cdn.net (pull zone relié au storage)
 *
 * Une fois configuré, l'admin téléverse les images produit directement
 * sur Bunny : elles sont servies depuis l'edge mondial (~$0.01/Go) sans
 * consommer les ressources du serveur d'origine.
 */
class BunnyStorage
{
    private const API_URL = 'https://storage.bunnycdn.com';

    public function __construct(
        private string $zone,
        private string $apiKey,
        private string $cdnUrl,
    ) {
    }

    /**
     * Bunny est-il configuré sur cette instance ?
     */
    public static function configured(): bool
    {
        return (bool) config('services.bunny.storage_zone')
            && (bool) config('services.bunny.storage_key');
    }

    /**
     * Fabrique une instance (null si non configuré).
     */
    public static function make(): ?self
    {
        if (! static::configured()) {
            return null;
        }

        return new self(
            (string) config('services.bunny.storage_zone'),
            (string) config('services.bunny.storage_key'),
            rtrim((string) config('services.bunny.storage_cdn_url'), '/'),
        );
    }

    /**
     * Téléverse un fichier et retourne son URL CDN publique,
     * ou null si l'upload échoue (repli local possible).
     */
    public function upload(string $path, string $contents): ?string
    {
        try {
            $response = Http::withHeaders([
                'AccessKey' => $this->apiKey,
            ])
                ->withBody($contents, 'application/octet-stream')
                ->timeout(30)
                ->put(self::API_URL."/{$this->zone}/{$path}");
        } catch (ConnectionException) {
            return null;
        }

        return $response->successful() ? $this->url($path) : null;
    }

    /**
     * Supprime un objet (nettoyage quand un produit est supprimé).
     */
    public function delete(string $path): bool
    {
        try {
            return Http::withHeaders([
                'AccessKey' => $this->apiKey,
            ])
                ->timeout(15)
                ->delete(self::API_URL."/{$this->zone}/{$path}")
                ->successful();
        } catch (ConnectionException) {
            return false;
        }
    }

    /**
     * URL CDN publique d'un objet.
     */
    public function url(string $path): string
    {
        return $this->cdnUrl.'/'.ltrim($path, '/');
    }

    /**
     * Retrouve le chemin Bunny depuis une URL CDN,
     * ou null si l'URL n'appartient pas à ce storage zone.
     */
    public function pathFromUrl(string $url): ?string
    {
        if ($this->cdnUrl === '' || ! str_starts_with($url, $this->cdnUrl.'/')) {
            return null;
        }

        return substr($url, strlen($this->cdnUrl) + 1);
    }

    /**
     * Génère un chemin unique, ex. « produits/3f9c…-a1b2.jpg ».
     */
    public static function uniquePath(string $originalName, string $folder = 'produits'): string
    {
        $extension = strtolower(pathinfo($originalName, PATHINFO_EXTENSION) ?: 'jpg');
        $extension = preg_replace('/[^a-z0-9]/', '', $extension) ?: 'jpg';

        return $folder.'/'.Str::uuid()->toString().'.'.$extension;
    }
}
