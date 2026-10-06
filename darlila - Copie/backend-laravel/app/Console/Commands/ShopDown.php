<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;

class ShopDown extends Command
{
    protected $signature = 'shop:down
        {--message= : Message personnalisé affiché sur la page d\'attente}
        {--retry=300 : Délai suggéré avant nouvelle tentative (secondes)}';

    protected $description = 'Active le mode maintenance de la boutique (page d\'attente)';

    public function handle(): int
    {
        file_put_contents(storage_path('framework/down'), json_encode([
            'message' => $this->option('message'),
            'retry' => (int) $this->option('retry'),
            'since' => now()->toISOString(),
        ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

        $this->info('🛠️  Mode maintenance ACTIVÉ — la boutique affiche sa page d\'attente.');
        $this->line('    L\'administration reste accessible : <votre-frontend>/admin');
        $this->line('    Pour rouvrir la boutique :  php artisan shop:up');

        return self::SUCCESS;
    }
}
