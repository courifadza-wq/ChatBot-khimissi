<?php

namespace App\Services;

use Intervention\Image\Drivers\Gd\Driver;
use Intervention\Image\ImageManager;

/**
 * Compression automatique des images produit : conversion WebP +
 * redimensionnement (1600 px max par défaut).
 *
 * WebP pèse en général 30 à 70 % de moins que le JPG/PNG équivalent —
 * crucial pour un catalogue de 1000+ images servies via Bunny CDN.
 *
 * Nécessite l'extension PHP GD (incluse chez Hostinger).
 */
class ImageOptimizer
{
    public function __construct(
        private readonly int $maxDimension = 1600,
        private readonly int $quality = 82,
    ) {
    }

    /**
     * GD + Intervention Image sont-ils disponibles ?
     */
    public static function available(): bool
    {
        return extension_loaded('gd') && class_exists(ImageManager::class);
    }

    /**
     * Convertit des octets d'image en WebP optimisé.
     * Retourne null si l'image est illisible (format non supporté, corrompue…).
     */
    public function toWebp(string $contents): ?string
    {
        try {
            $image = (new ImageManager(new Driver()))->read($contents);

            // scaleDown : ne réduit que si l'image dépasse la taille maximale
            $image->scaleDown($this->maxDimension, $this->maxDimension);

            return $image->toWebp($this->quality)->toString();
        } catch (\Throwable) {
            return null;
        }
    }
}
