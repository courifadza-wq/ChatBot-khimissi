<?php

namespace Database\Seeders;

use App\Models\Setting;
use Illuminate\Database\Seeder;

class SettingSeeder extends Seeder
{
    /**
     * Réglages publics de la boutique.
     * Le numéro WhatsApp est prioritairement lu depuis .env (WHATSAPP_NUMBER),
     * la valeur en base servant de repli / de personnalisation via l'admin.
     */
    public function run(): void
    {
        $settings = [
            'whatsapp_number' => env('WHATSAPP_NUMBER', '213554698746'),

            // adresse e-mail qui reçoit la notification « nouvelle commande »
            'seller_email' => env('SELLER_EMAIL', 'admin@planetkids.dz'),

            'shop_name_fr' => 'Planet Kids — Boudouaou',
            'shop_name_ar' => 'بلانيت كيدز — خيميسي شوب',
            'shop_address_fr' => 'Rue des Frères Aoudia, Boudouaou, Boumerdès, Algérie',
            'shop_address_ar' => 'شارع الإخوة عودية، بودواو، بومرداس',
            'shop_hours_fr' => 'Tous les jours : 09h à 21h · Vendredi : 14h30 à 21h',
            'shop_hours_ar' => 'كل الأيام: 9 صباحاً إلى 9 مساءً · الجمعة: 2:30 إلى 9 مساءً',
            'shop_phone_display' => '+213 554 69 87 46',
            'shop_email' => 'contact@planetkids.dz',

            'hero_image' => 'https://arsenaldza-coif.github.io/boutique1/assets/hero-professional.jpg',
            'maps_query' => 'Rue des Frères Aoudia, Boudouaou, Boumerdès, Algérie',
            'whatsapp_group_url' => 'https://chat.whatsapp.com/KJLlKQ6cbQe8GGFmy7UhL6',
            'instagram_url' => 'https://www.instagram.com/planetekids_',
            'facebook_url' => 'https://www.facebook.com/share/19YwPnT6jg/',
            'tiktok_url' => 'https://www.tiktok.com/@planetkids_',
        ];

        foreach ($settings as $key => $value) {
            Setting::updateOrCreate(['key' => $key], ['value' => $value]);
        }
    }
}
