<?php

namespace Database\Seeders;

use App\Models\Category;
use App\Models\Product;
use Illuminate\Database\Seeder;

class ProductSeeder extends Seeder
{
    /**
     * Les 22 produits de la boutique (prix en DA, images bilingues FR/AR).
     *
     * Le champ "image" accepte aussi bien une URL externe qu'un chemin
     * local (ex. "storage/produits/jasmin.jpg" après `php artisan storage:link`).
     */
    public function run(): void
    {
        $categoryIds = Category::query()->pluck('id', 'slug');

        $products = [
            // ---------- Bijoux traditionnels ----------
            [
                'slug' => 'collier-filigrane-argent',
                'category' => 'bijoux-traditionnels',
                'name_fr' => 'Collier Filigrane Argent',
                'name_ar' => 'قلادة فضية بالفتيلة',
                'description_fr' => 'Collier artisanal en argent massif, motifs filigranés traditionnels, fait main à Alger.',
                'description_ar' => 'قلادة حرفية من الفضة الخالصة، بزخارف الفتيلة التقليدية، صنعت يدويًا بالجزائر العاصمة.',
                'price' => 8500,
                'image' => 'https://images.unsplash.com/photo-1611591437281-460bfbe1220a?q=80&w=700&auto=format&fit=crop',
            ],
            [
                'slug' => 'boucles-doreilles-berberes',
                'category' => 'bijoux-traditionnels',
                'name_fr' => 'Boucles d\'oreilles Berbères',
                'name_ar' => 'أقراط أمازيغية',
                'description_fr' => 'Boucles en argent ciselé, inspirées des bijoux berbères ancestraux.',
                'description_ar' => 'أقراط من الفضة المنقوشة، مستوحاة من الحلي الأمازيغية العريقة.',
                'price' => 4200,
                'image' => 'https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?q=80&w=700&auto=format&fit=crop',
            ],

            // ---------- Vêtements brodés ----------
            [
                'slug' => 'caftan-brode-or',
                'category' => 'vetements-brodes',
                'name_fr' => 'Caftan Brodé Or',
                'name_ar' => 'قفطان مطرز بالذهب',
                'description_fr' => 'Caftan de cérémonie brodé fil d\'or, tissu velours, coupe traditionnelle.',
                'description_ar' => 'قفطان احتفالي مطرز بخيط ذهبي، قماش مخملي، قصة تقليدية.',
                'price' => 15000,
                'image' => 'https://images.unsplash.com/photo-1520006403909-838d6b92c22e?q=80&w=700&auto=format&fit=crop',
            ],
            [
                'slug' => 'djellaba-brodee',
                'category' => 'vetements-brodes',
                'name_fr' => 'Djellaba Brodée',
                'name_ar' => 'جلابة مطرزة',
                'description_fr' => 'Djellaba légère brodée main, idéale pour les grandes occasions.',
                'description_ar' => 'جلابة خفيفة مطرزة يدويًا، مثالية للمناسبات الكبرى.',
                'price' => 9800,
                'image' => 'https://images.unsplash.com/photo-1596704017254-9b121068fb31?q=80&w=700&auto=format&fit=crop',
            ],

            // ---------- Déco & poterie ----------
            [
                'slug' => 'theiere-en-cuivre-gravee',
                'category' => 'deco-poterie',
                'name_fr' => 'Théière en Cuivre Gravée',
                'name_ar' => 'إبريق شاي نحاسي منقوش',
                'description_fr' => 'Théière traditionnelle en cuivre martelé et gravé à la main.',
                'description_ar' => 'إبريق شاي تقليدي من النحاس المطروق والمنقوش يدويًا.',
                'price' => 6500,
                'image' => 'https://images.unsplash.com/photo-1591195853828-11db59a44f6b?q=80&w=700&auto=format&fit=crop',
            ],
            [
                'slug' => 'assiette-en-poterie-peinte',
                'category' => 'deco-poterie',
                'name_fr' => 'Assiette en Poterie Peinte',
                'name_ar' => 'طبق فخاري مرسوم',
                'description_fr' => 'Assiette décorative en céramique, peinte à la main selon les motifs de Kabylie.',
                'description_ar' => 'طبق زينة من السيراميك، مرسوم يدويًا بزخارف القبائل.',
                'price' => 3200,
                'image' => 'https://images.unsplash.com/photo-1578500494198-246f612d3b3d?q=80&w=700&auto=format&fit=crop',
            ],

            // ---------- Accessoires en cuir ----------
            [
                'slug' => 'sac-a-main-en-cuir',
                'category' => 'accessoires-en-cuir',
                'name_fr' => 'Sac à Main en Cuir',
                'name_ar' => 'حقيبة يد جلدية',
                'description_fr' => 'Sac en cuir véritable tanné artisanalement, doublure cousue main.',
                'description_ar' => 'حقيبة من الجلد الطبيعي المدبوغ حرفيًا، بطانة مخيطة يدويًا.',
                'price' => 7200,
                'image' => 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?q=80&w=700&auto=format&fit=crop',
            ],
            [
                'slug' => 'sandales-en-cuir',
                'category' => 'accessoires-en-cuir',
                'name_fr' => 'Sandales en Cuir',
                'name_ar' => 'صنادل جلدية',
                'description_fr' => 'Sandales en cuir souple, semelle confortable, fabrication locale.',
                'description_ar' => 'صنادل من الجلد الطري، نعل مريح، صناعة محلية.',
                'price' => 4500,
                'image' => 'https://images.unsplash.com/photo-1560343090-f0409e92791a?q=80&w=700&auto=format&fit=crop',
            ],

            // ---------- Parfums ----------
            [
                'slug' => 'eau-de-parfum-jasmin',
                'category' => 'parfums',
                'name_fr' => 'Eau de parfum Jasmin',
                'name_ar' => 'عطر الياسمين',
                'description_fr' => 'Un parfum floral élégant aux notes de jasmin et de musc blanc.',
                'description_ar' => 'عطر زهري أنيق بنفحات الياسمين والمسك الأبيض.',
                'price' => 6800,
                'image' => 'https://arsenaldza-coif.github.io/boutique1/assets/perfume-bottle-product-photography-neutr-2.jpg',
                'is_featured' => true,
                'promo_quantity' => 2, // -15 % dès 2 achetés
                'promo_percent' => 15,
            ],
            [
                'slug' => 'parfum-oud-dorient',
                'category' => 'parfums',
                'name_fr' => 'Parfum Oud d\'Orient',
                'name_ar' => 'عطر عود شرقي',
                'description_fr' => 'Une fragrance chaleureuse et profonde aux notes de oud et d\'ambre.',
                'description_ar' => 'رائحة دافئة وعميقة بنفحات العود والعنبر.',
                'price' => 9200,
                'image' => 'https://arsenaldza-coif.github.io/boutique1/assets/perfume-bottle-product-photography-neutr-1.webp',
                'is_featured' => true,
            ],
            [
                'slug' => 'brume-parfumee-fleur-doranger',
                'category' => 'parfums',
                'name_fr' => 'Brume parfumée Fleur d\'oranger',
                'name_ar' => 'رذاذ زهر البرتقال المعطر',
                'description_fr' => 'Une brume légère et fraîche aux notes délicates de fleur d\'oranger.',
                'description_ar' => 'رذاذ خفيف ومنعش بنفحات زهر البرتقال الرقيقة.',
                'price' => 3200,
                'image' => 'https://arsenaldza-coif.github.io/boutique1/assets/perfume-bottle-product-photography-neutr-1.webp',
            ],
            [
                'slug' => 'coffret-parfum-elegance',
                'category' => 'parfums',
                'name_fr' => 'Coffret Parfum Élégance',
                'name_ar' => 'طقم عطر الأناقة',
                'description_fr' => 'Coffret parfum raffiné à offrir, avec une fragrance douce et longue tenue.',
                'description_ar' => 'طقم عطر راقٍ كهدية، برائحة ناعمة وثبات طويل.',
                'price' => 7400,
                'image' => 'https://arsenaldza-coif.github.io/boutique1/assets/perfume-bottle-product-photography-neutr-2.jpg',
            ],

            // ---------- Cosmétiques ----------
            [
                'slug' => 'coffret-soin-visage',
                'category' => 'cosmetiques',
                'name_fr' => 'Coffret Soin Visage',
                'name_ar' => 'طقم العناية بالوجه',
                'description_fr' => 'Coffret beauté avec nettoyant, crème hydratante et sérum.',
                'description_ar' => 'طقم جمال يضم منظفًا وكريم ترطيب وسيروم.',
                'price' => 5400,
                'image' => 'https://arsenaldza-coif.github.io/boutique1/assets/cosmetics-skincare-products-product-phot-1.jpg',
                'promo_quantity' => 2, // -10 % dès 2 achetés
                'promo_percent' => 10,
            ],
            [
                'slug' => 'huile-naturelle-pour-cheveux',
                'category' => 'cosmetiques',
                'name_fr' => 'Huile naturelle pour cheveux',
                'name_ar' => 'زيت طبيعي للشعر',
                'description_fr' => 'Huile nourrissante aux plantes pour des cheveux doux et brillants.',
                'description_ar' => 'زيت مغذٍ بالنباتات لشعر ناعم ولامع.',
                'price' => 3900,
                'image' => 'https://arsenaldza-coif.github.io/boutique1/assets/cosmetics-skincare-products-product-phot-2.jpg',
            ],
            [
                'slug' => 'creme-hydratante-douceur',
                'category' => 'cosmetiques',
                'name_fr' => 'Crème Hydratante Douceur',
                'name_ar' => 'كريم الترطيب والنعومة',
                'description_fr' => 'Crème visage et corps pour une peau souple, fraîche et parfaitement hydratée.',
                'description_ar' => 'كريم للوجه والجسم لبشرة ناعمة ومنتعشة ورطبة.',
                'price' => 2800,
                'image' => 'https://arsenaldza-coif.github.io/boutique1/assets/cosmetics-skincare-products-product-phot-2.jpg',
            ],
            [
                'slug' => 'palette-maquillage-naturelle',
                'category' => 'cosmetiques',
                'name_fr' => 'Palette Maquillage Naturelle',
                'name_ar' => 'لوحة مكياج طبيعية',
                'description_fr' => 'Palette de teintes naturelles pour un maquillage élégant au quotidien.',
                'description_ar' => 'ألوان طبيعية لمكياج أنيق في كل يوم.',
                'price' => 6100,
                'image' => 'https://arsenaldza-coif.github.io/boutique1/assets/cosmetics-skincare-products-product-phot-1.jpg',
            ],

            // ---------- Articles pour bébé ----------
            [
                'slug' => 'coffret-douceur-bebe',
                'category' => 'articles-pour-bebe',
                'name_fr' => 'Coffret Douceur Bébé',
                'name_ar' => 'طقم عناية للطفل',
                'description_fr' => 'Coffret de soins doux pour la toilette et la peau délicate de bébé.',
                'description_ar' => 'طقم عناية لطيف لبشرة الطفل الحساسة.',
                'price' => 4600,
                'image' => 'https://arsenaldza-coif.github.io/boutique1/assets/baby-products-toys-skincare-product-phot-1.jpg',
            ],
            [
                'slug' => 'doudou-lapin-en-coton',
                'category' => 'articles-pour-bebe',
                'name_fr' => 'Doudou Lapin en coton',
                'name_ar' => 'دمية أرنب قطنية',
                'description_fr' => 'Doudou tout doux en coton, compagnon rassurant dès la naissance.',
                'description_ar' => 'دمية ناعمة من القطن، رفيق مطمئن منذ الولادة.',
                'price' => 3500,
                'image' => 'https://arsenaldza-coif.github.io/boutique1/assets/baby-products-toys-skincare-product-phot-2.jpg',
            ],
            [
                'slug' => 'shampoing-doux-bebe',
                'category' => 'articles-pour-bebe',
                'name_fr' => 'Shampoing Doux Bébé',
                'name_ar' => 'شامبو لطيف للأطفال',
                'description_fr' => 'Shampoing délicat sans rinçage agressif, adapté à la peau sensible de bébé.',
                'description_ar' => 'شامبو لطيف مناسب لبشرة الطفل الحساسة.',
                'price' => 2900,
                'image' => 'https://arsenaldza-coif.github.io/boutique1/assets/baby-products-toys-skincare-product-phot-2.jpg',
            ],
            [
                'slug' => 'cape-de-bain-bebe',
                'category' => 'articles-pour-bebe',
                'name_fr' => 'Cape de Bain Bébé',
                'name_ar' => 'منشفة استحمام للأطفال',
                'description_fr' => 'Cape de bain moelleuse et absorbante pour garder bébé bien au chaud.',
                'description_ar' => 'منشفة ناعمة وماصة تحافظ على دفء طفلك بعد الاستحمام.',
                'price' => 5200,
                'image' => 'https://arsenaldza-coif.github.io/boutique1/assets/baby-products-toys-skincare-product-phot-1.jpg',
            ],

            // ---------- Hygiène bébé ----------
            [
                'slug' => 'lingettes-douces-bebe',
                'category' => 'hygiene-bebe',
                'name_fr' => 'Lingettes Douces Bébé',
                'name_ar' => 'مناديل أطفال ناعمة',
                'description_fr' => 'Lingettes délicates pour la toilette quotidienne, pratiques et douces.',
                'description_ar' => 'مناديل لطيفة للنظافة اليومية، عملية وناعمة.',
                'price' => 2100,
                'image' => 'https://arsenaldza-coif.github.io/boutique1/assets/baby-products-toys-skincare-product-phot-2.jpg',
            ],
            [
                'slug' => 'lait-nettoyant-bebe',
                'category' => 'hygiene-bebe',
                'name_fr' => 'Lait Nettoyant Bébé',
                'name_ar' => 'حليب تنظيف للأطفال',
                'description_fr' => 'Lait nettoyant doux pour le visage et le corps des tout-petits.',
                'description_ar' => 'حليب تنظيف لطيف للوجه والجسم للصغار.',
                'price' => 3300,
                'image' => 'https://arsenaldza-coif.github.io/boutique1/assets/baby-products-toys-skincare-product-phot-1.jpg',
            ],
        ];

        foreach ($products as $index => $product) {
            $categoryId = $categoryIds[$product['category']] ?? null;

            Product::updateOrCreate(
                ['slug' => $product['slug']],
                [
                    'category_id' => $categoryId,
                    'name_fr' => $product['name_fr'],
                    'name_ar' => $product['name_ar'],
                    'description_fr' => $product['description_fr'],
                    'description_ar' => $product['description_ar'],
                    'price' => $product['price'],
                    'image' => $product['image'],
                    'is_featured' => $product['is_featured'] ?? false,
                    'is_active' => true,
                    'promo_quantity' => $product['promo_quantity'] ?? null,
                    'promo_percent' => $product['promo_percent'] ?? null,
                    'position' => ($index + 1) * 10,
                ]
            );
        }
    }
}
