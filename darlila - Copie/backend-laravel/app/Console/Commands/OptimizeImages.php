<?php

namespace App\Console\Commands;

use App\Models\Product;
use App\Services\BunnyStorage;
use App\Services\ImageOptimizer;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Str;

/**
 * Convertit en masse les images produit en WebP optimisé.
 *
 *   php artisan shop:images:webp
 *   php artisan shop:images:webp --limit=100 --quality=80 --width=1400
 *
 * Conçu pour les catalogues importés en masse (CSV) dont les images
 * sont des URL externes ou des fichiers locaux : chaque image est
 * téléchargée/lue, compressée en WebP (30-70 % de poids en moins),
 * stockée sur Bunny (si configuré) ou en local, puis la base est mise
 * à jour avec la nouvelle URL.
 */
class OptimizeImages extends Command
{
    protected $signature = 'shop:images:webp
        {--limit=0 : Nombre maximum d\images à traiter (0 = toutes)}
        {--width=1600 : Dimension maximale en pixels}
        {--quality=82 : Qualité WebP (0-100)}';

    protected $description = 'Convertit les images produit en WebP optimisé (compression 30-70 %)';

    public function handle(): int
    {
        if (! ImageOptimizer::available()) {
            $this->error('L\'extension GD de PHP est requise (absente ou intervention/image non installé).');

            return self::FAILURE;
        }

        $optimizer = new ImageOptimizer((int) $this->option('width'), (int) $this->option('quality'));
        $bunny = BunnyStorage::make();

        $query = Product::query()
            ->where('image', 'not like', '%.webp')
            ->orderBy('id');

        $limit = (int) $this->option('limit');
        if ($limit > 0) {
            $query->limit($limit);
        }

        $products = $query->get();

        if ($products->isEmpty()) {
            $this->info('Aucune image à convertir — tout est déjà en WebP.');

            return self::SUCCESS;
        }

        $this->info(sprintf('📦 %d image(s) à convertir (WebP, %d px max, qualité %d)…',
            $products->count(), $this->option('width'), $this->option('quality')));

        $bar = $this->output->createProgressBar($products->count());
        $bar->start();

        $optimized = 0;
        $failed = [];
        $bytesBefore = 0;
        $bytesAfter = 0;

        foreach ($products as $product) {
            $bar->advance();

            $contents = $this->fetchImageContents((string) $product->image);

            if ($contents === null) {
                $failed[] = $product->slug;
                continue;
            }

            $webp = $optimizer->toWebp($contents);

            if ($webp === null || strlen($webp) >= strlen($contents)) {
                // déjà très compressée ou illisible : on garde l'originale
                $failed[] = $product->slug;
                continue;
            }

            $newUrl = $this->store($webp, $bunny);

            if ($newUrl === null) {
                $failed[] = $product->slug;
                continue;
            }

            $bytesBefore += strlen($contents);
            $bytesAfter += strlen($webp);
            $product->image = $newUrl;
            $product->save();
            $optimized++;
        }

        $bar->finish();
        $this->newLine(2);

        $this->info(sprintf('✅ %d image(s) convertie(s) en WebP.', $optimized));

        if ($optimized > 0 && $bytesBefore > 0) {
            $saving = round(100 - ($bytesAfter / $bytesBefore * 100));
            $this->line(sprintf('   Poids : %s → %s (- %d %%)',
                $this->formatBytes($bytesBefore),
                $this->formatBytes($bytesAfter),
                $saving
            ));
        }

        if ($failed !== []) {
            $this->warn(sprintf('⚠ %d image(s) non convertie(s) : %s',
                count($failed), implode(', ', array_slice($failed, 0, 8)).(count($failed) > 8 ? '…' : '')));
        }

        return self::SUCCESS;
    }

    /**
     * Lit le contenu d'une image depuis une URL externe ou le disque local.
     */
    private function fetchImageContents(string $image): ?string
    {
        if (str_starts_with($image, 'http://') || str_starts_with($image, 'https://')) {
            try {
                $response = Http::timeout(20)->get($image);

                return $response->successful() ? $response->body() : null;
            } catch (\Throwable) {
                return null;
            }
        }

        if (str_starts_with($image, '/storage/')) {
            $path = substr($image, strlen('/storage/'));

            try {
                return Storage::disk('public')->get($path);
            } catch (\Throwable) {
                return null;
            }
        }

        return null;
    }

    /**
     * Stocke le WebP sur Bunny (si configuré) ou en local → URL publique.
     */
    private function store(string $webp, ?BunnyStorage $bunny): ?string
    {
        if ($bunny !== null) {
            $url = rescue(fn () => $bunny->upload('produits/'.Str::uuid()->toString().'.webp', $webp), null, false);

            if ($url !== null) {
                return $url;
            }
        }

        $path = 'products/'.Str::uuid()->toString().'.webp';

        try {
            Storage::disk('public')->put($path, $webp);

            return '/storage/'.$path;
        } catch (\Throwable) {
            return null;
        }
    }

    private function formatBytes(int $bytes): string
    {
        if ($bytes >= 1048576) {
            return round($bytes / 1048576, 1).' Mo';
        }

        return round($bytes / 1024).' Ko';
    }
}
