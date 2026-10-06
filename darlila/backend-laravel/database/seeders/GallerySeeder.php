<?php

namespace Database\Seeders;

use App\Models\GalleryImage;
use Illuminate\Database\Seeder;

class GallerySeeder extends Seeder
{
    /**
     * Galerie de la boutique.
     */
    public function run(): void
    {
        $images = [
            ['image' => 'https://images.unsplash.com/photo-1611591437281-460bfbe1220a?q=80&w=900&auto=format&fit=crop', 'alt_fr' => 'Bijoux', 'alt_ar' => 'مجوهرات'],
            ['image' => 'https://images.unsplash.com/photo-1520006403909-838d6b92c22e?q=80&w=700&auto=format&fit=crop', 'alt_fr' => 'Caftan brodé', 'alt_ar' => 'قفطان مطرز'],
            ['image' => 'https://images.unsplash.com/photo-1578500494198-246f612d3b3d?q=80&w=700&auto=format&fit=crop', 'alt_fr' => 'Poterie', 'alt_ar' => 'فخار'],
            ['image' => 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?q=80&w=900&auto=format&fit=crop', 'alt_fr' => 'Sac en cuir', 'alt_ar' => 'حقيبة جلدية'],
            ['image' => 'https://images.unsplash.com/photo-1596704017254-9b121068fb31?q=80&w=700&auto=format&fit=crop', 'alt_fr' => 'Tapis', 'alt_ar' => 'لباس تقليدي'],
            ['image' => 'https://images.unsplash.com/photo-1591195853828-11db59a44f6b?q=80&w=700&auto=format&fit=crop', 'alt_fr' => 'Théière traditionnelle', 'alt_ar' => 'إبريق شاي تقليدي'],
            ['image' => 'https://images.unsplash.com/photo-1590736969955-71cc94901144?q=80&w=700&auto=format&fit=crop', 'alt_fr' => 'Atelier artisanal', 'alt_ar' => 'ورشة حرفية'],
            ['image' => 'https://images.unsplash.com/photo-1517502884422-41eaead166d4?q=80&w=700&auto=format&fit=crop', 'alt_fr' => 'Vitrine boutique', 'alt_ar' => 'واجهة المتجر'],
        ];

        foreach ($images as $index => $image) {
            GalleryImage::updateOrCreate(
                ['image' => $image['image']],
                $image + ['position' => ($index + 1) * 10]
            );
        }
    }
}
