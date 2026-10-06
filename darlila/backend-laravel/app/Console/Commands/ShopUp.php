<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;

class ShopUp extends Command
{
    protected $signature = 'shop:up';

    protected $description = 'Désactive le mode maintenance et rouvre la boutique';

    public function handle(): int
    {
        $file = storage_path('framework/down');

        if (is_file($file)) {
            unlink($file);
            $this->info('✅ Boutique réactivée — bienvenue de retour !');
        } else {
            $this->line('Le mode maintenance n\'était pas actif.');
        }

        return self::SUCCESS;
    }
}
