<?php
/**
 * =====================================================================
 *  PLANET KIDS — Installation des catégories et sous-catégories
 * =====================================================================
 *  À placer dans le dossier  public/  du backend (api.khemicishop.com)
 *  puis à ouvrir UNE SEULE FOIS dans le navigateur :
 *
 *      https://api.khemicishop.com/setup-subcategories.php
 *
 *  Le script :
 *    1. exécute la migration (colonne parent_id sur les catégories) ;
 *    2. crée les 4 catégories principales + 16 sous-catégories ;
 *    3. repositionne les anciennes catégories APRÈS les nouvelles.
 *
 *  Il est RÉPÉTABLE sans risque (rien n'est dupliqué).
 *  ⚠️ SUPPRIMEZ CE FICHIER après utilisation. ⚠️
 * =====================================================================
 */

require __DIR__.'/../vendor/autoload.php';
$app = require_once __DIR__.'/../bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

use App\Models\Category;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Schema;

header('Content-Type: text/html; charset=utf-8');

echo "<html><head><meta charset='utf-8'>";
echo "<title>Planet Kids — Installation des sous-catégories</title></head>";
echo "<body style='font-family:system-ui,sans-serif;padding:40px;background:#fdf9fc;color:#2d3590'>";
echo "<h1 style='color:#ea2f90'>🧸 Planet Kids — Sous-catégories</h1>";

/* ------------------------------------------------------------------ */
/* 1. Migration : colonne parent_id                                    */
/* ------------------------------------------------------------------ */
echo "<h2>1️⃣ Migration de la base de données</h2>";

if (Schema::hasColumn('categories', 'parent_id')) {
    echo "<p>✅ La colonne <code>parent_id</code> existe déjà (migration déjà appliquée).</p>";
} else {
    Artisan::call('migrate', ['--force' => true]);
    echo '<pre style="background:#fff;border:1px solid #f3d0e3;border-radius:8px;padding:14px;white-space:pre-wrap">'.htmlspecialchars(Artisan::output()).'</pre>';

    if (! Schema::hasColumn('categories', 'parent_id')) {
        echo "<p style='color:#c0392b;font-weight:700'>❌ La migration a échoué — vérifiez le message ci-dessus.</p>";
        echo '</body></html>';
        exit;
    }
    echo "<p>✅ Colonne <code>parent_id</code> ajoutée avec succès.</p>";
}

/* ------------------------------------------------------------------ */
/* 2. Les 4 catégories principales + 16 sous-catégories                */
/* ------------------------------------------------------------------ */
echo "<h2>2️⃣ Création des catégories</h2>";

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
            ['slug' => 'peluches', 'name_fr' => 'Peluches',         'name_ar' => 'دمى قطيفة'],
        ],
    ],
    [
        'slug' => 'cadeaux',
        'name_fr' => 'Cadeaux',
        'name_ar' => 'هدايا',
        'description_fr' => 'Idées cadeaux pour toutes les occasions.',
        'description_ar' => 'أفكار هدايا لجميع المناسبات.',
        'position' => 40,
        'children' => [
            ['slug' => 'naissance',        'name_fr' => 'Naissance',        'name_ar' => 'المولود الجديد'],
            ['slug' => 'anniversaire',     'name_fr' => 'Anniversaire',    'name_ar' => 'عيد الميلاد'],
            ['slug' => 'coffrets-cadeaux', 'name_fr' => 'Coffrets cadeaux','name_ar' => 'علب الهدايا'],
        ],
    ],
];

$newSlugs = [];
foreach ($tree as $main) {
    $newSlugs[] = $main['slug'];
    foreach ($main['children'] as $child) {
        $newSlugs[] = $child['slug'];
    }
}

/* --- 2a. Repositionner les anciennes catégories APRÈS les nouvelles --- */
$oldMains = Category::query()
    ->whereNull('parent_id')
    ->whereNotIn('slug', $newSlugs)
    ->orderBy('position')
    ->orderBy('id')
    ->get();

if ($oldMains->isNotEmpty()) {
    foreach ($oldMains as $index => $old) {
        $old->update(['position' => 100 + $index * 10]);
    }
    echo '<p>🔁 '.count($oldMains).' ancienne(s) catégorie(s) repositionnée(s) après les nouvelles (elles restent visibles avec leurs produits).</p>';
}

/* --- 2b. Créer / mettre à jour principales et sous-catégories --- */
echo "<ul style='line-height:1.9'>";
foreach ($tree as $main) {
    $mainCategory = Category::updateOrCreate(
        ['slug' => $main['slug']],
        [
            'parent_id' => null,
            'name_fr' => $main['name_fr'],
            'name_ar' => $main['name_ar'],
            'description_fr' => $main['description_fr'],
            'description_ar' => $main['description_ar'],
            'position' => $main['position'],
        ]
    );
    echo "<li><strong>{$main['name_fr']}</strong> — {$main['name_ar']}";
    echo "<ul>";

    foreach ($main['children'] as $index => $child) {
        Category::updateOrCreate(
            ['slug' => $child['slug']],
            [
                'parent_id' => $mainCategory->id,
                'name_fr' => $child['name_fr'],
                'name_ar' => $child['name_ar'],
                'description_fr' => null,
                'description_ar' => null,
                'position' => ($index + 1) * 10,
            ]
        );
        echo "<li>↳ {$child['name_fr']} — {$child['name_ar']}</li>";
    }
    echo '</ul></li>';
}
echo '</ul>';

/* ------------------------------------------------------------------ */
/* 3. Récapitulatif                                                    */
/* ------------------------------------------------------------------ */
$totalMain = Category::whereNull('parent_id')->count();
$totalSub = Category::whereNotNull('parent_id')->count();

echo "<h2>3️⃣ Récapitulatif</h2>";
echo "<p style='font-size:17px'>✅ <strong>{$totalMain}</strong> catégorie(s) principale(s) et <strong>{$totalSub}</strong> sous-catégorie(s) en base.</p>";
echo "<p style='background:#fff;border:1px solid #f3d0e3;border-radius:8px;padding:14px'>";
echo "🛒 La boutique affiche désormais les 4 grandes familles ; cliquer sur une famille fait apparaître ses sous-catégories.<br>";
echo "📦 Dans l'admin (Produits → Modifier), le sélecteur de catégorie est désormais <strong>regroupé par famille</strong>.<br>";
echo "♻️ Les anciennes catégories (Parfums, Cosmétiques…) sont conservées avec leurs produits — reclassez-les à votre rythme, puis supprimez-les quand elles sont vides.";
echo '</p>';

echo "<p style='color:#c0392b;font-weight:700'>⚠️ Supprimez maintenant ce fichier (setup-subcategories.php) du serveur !</p>";
echo "<p><a href='https://khemicishop.com' style='color:#ea2f90;font-weight:700'>&larr; Retour à la boutique</a></p>";
echo '</body></html>';
