<?php

namespace Database\Seeders;

use App\Models\Review;
use Illuminate\Database\Seeder;

class ReviewSeeder extends Seeder
{
    /**
     * Avis réels récupérés de Google Maps — Planète Kids (4.9/5, 11 avis).
     * https://www.google.com/maps/place/Plan\u00e8te+kids/
     */
    public function run(): void
    {
        $reviews = [
            [
                'author_name' => 'Amine A.',
                'city_fr' => 'Boudouaou',
                'city_ar' => 'بودواو',
                'content_fr' => '« Le magasin est vraiment top, Dieu merci le service est merveilleux. Je recommande vivement ! »',
                'content_ar' => '«المتجر رائع، الحمد لله الخدمة ممتازة. أنصح به بشدة!»',
            ],
            [
                'author_name' => 'Iméne',
                'city_fr' => 'Boudouaou',
                'city_ar' => 'بودواو',
                'content_fr' => '« Excellent service et qualité. Des produits de marque pour nos enfants. »',
                'content_ar' => '«خدمة وجودة ممتازة. منتجات ذات جودة عالية لأطفالنا.»',
            ],
            [
                'author_name' => 'Ismail I.',
                'city_fr' => 'Boudouaou',
                'city_ar' => 'بودواو',
                'content_fr' => '« Boutique très bien organisée, personnel accueillant. Katakit Boudouaou ! »',
                'content_ar' => '«متجر منظم جداً وموظفون ودودون. قطيطة بودواو!»',
            ],
        ];

        foreach ($reviews as $index => $review) {
            Review::updateOrCreate(
                ['author_name' => $review['author_name']],
                $review + ['rating' => 5, 'is_approved' => true, 'position' => ($index + 1) * 10]
            );
        }
    }
}
