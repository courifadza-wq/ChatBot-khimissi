<?php

namespace Database\Seeders;

use App\Models\Category;
use Illuminate\Database\Seeder;

class CategorySeeder extends Seeder
{
    /**
     * Les catégories et sous-catégories officielles Planet Kids.
     */
    public function run(): void
    {
        $tree = [
            [
                'slug' => 'chaussures-accessoires',
                'name_fr' => 'Chaussures & Accessoires',
                'name_ar' => 'أحذية وإكسسوارات',
                'description_fr' => 'Chaussures, sacs, bonnets, chaussettes et accessoires cheveux.',
                'description_ar' => 'أحذية وحقائب وطواقي وجوارب وإكسسوارات الشعر.',
                'position' => 10,
                'children' => [
                    ['slug' => 'chaussures',           'name_fr' => 'Chaussures',           'name_ar' => 'أحذية'],
                    ['slug' => 'sacs',                 'name_fr' => 'Sacs',                 'name_ar' => 'حقائب'],
                    ['slug' => 'bonnets-chapeaux',     'name_fr' => 'Bonnets & Chapeaux',   'name_ar' => 'طواقي وقبعات'],
                    ['slug' => 'chaussettes',          'name_fr' => 'Chaussettes',          'name_ar' => 'جوارب'],
                    ['slug' => 'accessoires-cheveux',  'name_fr' => 'Accessoires cheveux',  'name_ar' => 'إكسسوارات الشعر'],
                ],
            ],
            [
                'slug' => 'puericulture',
                'name_fr' => 'Puériculture',
                'name_ar' => 'مستلزمات الطفل',
                'description_fr' => 'Tout pour les premiers mois : repas, sommeil, toilette, sorties.',
                'description_ar' => 'كل ما يلزم للأشهر الأولى: الطعام والنوم والاستحمام والخروج.',
                'position' => 20,
                'children' => [
                    ['slug' => 'repas-biberons',      'name_fr' => 'Repas & Biberons',      'name_ar' => 'الوجبات والرضّاعات'],
                    ['slug' => 'sommeil',             'name_fr' => 'Sommeil',               'name_ar' => 'النوم'],
                    ['slug' => 'toilette-soins',      'name_fr' => 'Toilette & Soins',      'name_ar' => 'الاستحمام والعناية'],
                    ['slug' => 'promenade-sorties',   'name_fr' => 'Promenade & Sorties',   'name_ar' => 'التنزه والخروج'],
                    ['slug' => 'equipement-bebe',     'name_fr' => 'Équipement bébé',       'name_ar' => 'تجهيزات الرضيع'],
                ],
            ],
            [
                'slug' => 'jouets-eveil',
                'name_fr' => 'Jouets & Éveil',
                'name_ar' => 'ألعاب وتنمية',
                'description_fr' => "Jouets, jeux d'éveil et peluches pour grandir en s'amusant.",
                'description_ar' => 'ألعاب وأنشطة تنموية ودمى قطيفة للنمو والمرح.',
                'position' => 30,
                'children' => [
                    ['slug' => 'jouets',   'name_fr' => 'Jouets',           'name_ar' => 'ألعاب'],
                    ['slug' => 'eveil',    'name_fr' => 'Éveil',            'name_ar' => 'تنمية مهارات'],
                    ['slug' => 'peluches', 'name_fr' => 'Peluches',          'name_ar' => 'دمى قطيفة'],
                ],
            ],
            [
                'slug' => 'cadeaux',
                'name_fr' => 'Cadeaux',
                'name_ar' => 'هدايا',
                'description_fr' => 'Idées cadeaux pour naissance, anniversaire et coffrets.',
                'description_ar' => 'أفكار هدايا للمواليد وأعياد الميلاد وصناديق الهدايا.',
                'position' => 40,
                'children' => [
                    ['slug' => 'naissance',    'name_fr' => 'Naissance',        'name_ar' => 'مولود جديد'],
                    ['slug' => 'anniversaire', 'name_fr' => 'Anniversaire',     'name_ar' => 'عيد ميلاد'],
                    ['slug' => 'coffrets-cadeaux', 'name_fr' => 'Coffrets cadeaux', 'name_ar' => 'صناديق هدايا'],
                ],
            ],
        ];

        foreach ($tree as $parentData) {
            $children = $parentData['children'] ?? [];
            unset($parentData['children']);

            $parent = Category::updateOrCreate(
                ['slug' => $parentData['slug']],
                $parentData + ['parent_id' => null]
            );

            foreach ($children as $subIndex => $childData) {
                Category::updateOrCreate(
                    ['slug' => $childData['slug']],
                    $childData + [
                        'parent_id' => $parent->id,
                        'position' => $parent->position + ($subIndex + 1) * 10,
                    ]
                );
            }
        }
    }
}
