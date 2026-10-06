<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class UserSeeder extends Seeder
{
    /**
     * Compte administrateur de la boutique.
     *
     * Identifiants par défaut (personnalisables via .env) :
     *   admin@darlila.dz / password
     *
     * ⚠️ En production : changez ADMIN_PASSWORD et régénérez la clé APP_KEY.
     */
    public function run(): void
    {
        User::updateOrCreate(
            ['email' => env('ADMIN_EMAIL', 'admin@planetkids.dz')],
            [
                'name' => 'Administrateur Planet Kids',
                'password' => Hash::make(env('ADMIN_PASSWORD', 'password')),
                'is_admin' => true,
                'email_verified_at' => now(),
            ]
        );
    }
}
