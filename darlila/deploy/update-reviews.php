<?php
require __DIR__.'/../vendor/autoload.php';
$app = require_once __DIR__.'/../bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();
use App\Models\Review;

header('Content-Type: text/html; charset=utf-8');
echo "<html><head><meta charset='utf-8'></head><body style='font-family:sans-serif;padding:40px;background:#f0f2f5'>";

$deleted = Review::query()->delete();
echo "<p>🗑 $deleted ancien(s) avis supprimé(s)</p>";

$reviews = [
    [
        "author_name" => "Amine Amino",
        "city_fr" => "Boudouaou",
        "city_ar" => "بودواو",
        "content_fr" => "Le magasin est super, Dieu merci le service est merveilleux.",
        "content_ar" => "محل مشاء الله معاملة روعة بتوفيق",
        "rating" => 5,
    ],
    [
        "author_name" => "Imene",
        "city_fr" => "Boudouaou",
        "city_ar" => "بودواو",
        "content_fr" => "Service et qualite excellents.",
        "content_ar" => "خدمة وجودة ممتازة",
        "rating" => 5,
    ],
    [
        "author_name" => "Raouf Daas",
        "city_fr" => "Boudouaou",
        "city_ar" => "بودواو",
        "content_fr" => "Ce magasin est excellent, offrant un service impeccable et des produits de grande qualite a des prix abordables. Que Dieu leur accorde le succes.",
        "content_ar" => "هذا المحل ممتاز، خدمة راقية ومنتجات عالية الجودة بأثمنة معقولة. الله يوفقهم",
        "rating" => 5,
    ],
    [
        "author_name" => "Nabila Kouara",
        "city_fr" => "Boudouaou",
        "city_ar" => "بودواو",
        "content_fr" => "Que Dieu benisse ce produit de qualite superieure !",
        "content_ar" => "الله يبارك، منتج ذو جودة عالية",
        "rating" => 5,
    ],
    [
        "author_name" => "Ismail Ismail",
        "city_fr" => "Boudouaou",
        "city_ar" => "بودواو",
        "content_fr" => "Katakit Boudouaou",
        "content_ar" => "قطيطة بودواو",
        "rating" => 5,
    ],
];

$inserted = 0;
foreach ($reviews as $index => $review) {
    Review::create($review + [
        "is_approved" => true,
        "position" => ($index + 1) * 10,
    ]);
    $inserted++;
    echo "<p>✓ {$review['author_name']}</p>";
}

Illuminate\Support\Facades\Cache::forget('darlila.settings');

echo "<h2>✅ $inserted avis insérés !</h2>";
echo "<p><b>⚠️ SUPPRIMEZ CE FICHIER maintenant !</b></p>";
echo "</body></html>";
