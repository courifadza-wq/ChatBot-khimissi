<?php

namespace Database\Seeders;

use App\Models\Bundle;
use App\Models\Product;
use Illuminate\Database\Seeder;

class BundleSeeder extends Seeder
{
    /**
     * Lots de démonstration : plusieurs produits regroupés à prix réduit.
     * La boutique affiche le prix cumulé barré + le prix du lot.
     */
    public function run(): void
    {
        $bySlug = fn (string $slug) => Product::query()->where('slug', $slug)->first();

        $bundles = [
            [
                'slug' => 'lot-decouverte-parfums',
                'name_fr' => 'Lot Découverte Parfums',
                'name_ar' => 'طقم اكتشاف العطور',
                'description_fr' => 'Trois fragrances signature pour trouver votre préférée.',
                'description_ar' => 'ثلاث عطور مميزة لتكتشف عطرك المفضل.',
                'price' => 15900,
                'is_featured' => true, // affiché en tête de la section « Nos lots »
                'items' => [
                    ['eau-de-parfum-jasmin', 1],
                    ['parfum-oud-dorient', 1],
                    ['brume-parfumee-fleur-doranger', 1],
                ],
            ],
            [
                'slug' => 'lot-douceur-bebe',
                'name_fr' => 'Lot Douceur Bébé',
                'name_ar' => 'طقم النعومة للطفل',
                'description_fr' => 'L\'essentiel pour la toilette et le confort de bébé.',
                'description_ar' => 'الأساسيات للاستحمام وراحة طفلك.',
                'price' => 9900,
                'items' => [
                    ['coffret-douceur-bebe', 1],
                    ['doudou-lapin-en-coton', 1],
                    ['shampoing-doux-bebe', 1],
                ],
            ],
            [
                'slug' => 'duo-beaute',
                'name_fr' => 'Duo Beauté',
                'name_ar' => 'ثنائي الجمال',
                'description_fr' => 'Soin complet visage : coffret + crème hydratante.',
                'description_ar' => 'عناية كاملة بالوجه: طقم + كريم مرطب.',
                'price' => 6900,
                'items' => [
                    ['coffret-soin-visage', 1],
                    ['creme-hydratante-douceur', 1],
                ],
            ],
        ];

        foreach ($bundles as $index => $data) {
            $bundle = Bundle::updateOrCreate(
                ['slug' => $data['slug']],
                [
                    'name_fr' => $data['name_fr'],
                    'name_ar' => $data['name_ar'],
                    'description_fr' => $data['description_fr'],
                    'description_ar' => $data['description_ar'],
                    'price' => $data['price'],
                    'image' => null,
                    'is_active' => true,
                    'is_featured' => $data['is_featured'] ?? false,
                    'position' => ($index + 1) * 10,
                ]
            );

            $bundle->items()->delete();

            foreach ($data['items'] as [$slug, $quantity]) {
                $product = $bySlug($slug);

                if ($product !== null) {
                    $bundle->items()->create([
                        'product_id' => $product->id,
                        'quantity' => $quantity,
                    ]);
                }
            }
        }
    }
}
