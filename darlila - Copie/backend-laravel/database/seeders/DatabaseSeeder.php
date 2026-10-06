<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    /**
     * Remplit la base avec les données de la boutique Dar Lila.
     *
     * php artisan db:seed
     */
    public function run(): void
    {
        $this->call([
            CategorySeeder::class,
            ProductSeeder::class,
            ReviewSeeder::class,
            GallerySeeder::class,
            SettingSeeder::class,
            BundleSeeder::class,
            UserSeeder::class,
        ]);
    }
}
