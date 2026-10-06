/**
 * ============================================================
 *  API DE SIMULATION — Planet Kids
 * ============================================================
 *  Ce petit serveur Node (AUCUNE dépendance) reproduit fidèlement
 *  les endpoints de l'API Laravel (backend-laravel/), y compris
 *  l'authentification Sanctum et l'espace d'administration :
 *
 *    GET  /api/settings            réglages de la boutique
 *    GET  /api/categories          8 catégories (+ nombre de produits)
 *    GET  /api/products            produits ACTIFS (?category=&search=&featured=)
 *    GET  /api/products/{slug}     détail d'un produit (404 si inconnu)
 *    GET  /api/reviews             avis clients
 *    GET  /api/gallery             images de la galerie
 *    POST /api/orders              enregistre une commande (+ « e-mail » vendeur)
 *
 *    POST /api/auth/login          admin@planetkids.dz / password → token Bearer
 *    GET  /api/auth/me             utilisateur courant
 *    POST /api/auth/logout         révoque le token
 *
 *    GET    /api/admin/products    tous les produits (actifs + inactifs)
 *    POST   /api/admin/products    création (JSON ou multipart avec image)
 *    PUT    /api/admin/products/{id}   mise à jour (JSON, ou multipart _method=PUT)
 *    DELETE /api/admin/products/{id}  suppression
 *    GET    /api/admin/orders      commandes avec articles
 *    PATCH  /api/admin/orders/{id}/status  changement de statut
 *
 *    GET  /storage/products/{f}    images téléversées (équivalent storage:link)
 *
 *  Les données sont identiques à celles des seeders Laravel et les
 *  réponses respectent le format { "data": ... } des Resources.
 *
 *  Utilisation :  node api-mock/server.js   (port 8000 par défaut)
 * ============================================================
 */
const http = require('http')
const crypto = require('crypto')
const fs = require('fs')
const path = require('path')

const PORT = process.env.PORT || 8000
const UPLOAD_DIR = path.join(__dirname, 'storage', 'products')
/** Fichier « down » : mode maintenance (équivalent Laravel storage/framework/down) */
const DOWN_FILE = path.join(__dirname, 'storage', 'down')

function readMaintenance() {
  try {
    return JSON.parse(fs.readFileSync(DOWN_FILE, 'utf8'))
  } catch {
    return null
  }
}

function maintenancePayload() {
  const data = readMaintenance() || {}
  return {
    message: data.message || 'La boutique Planet Kids est momentanément en maintenance. Nous revenons très vite !',
    maintenance: true,
    retry_after: Math.max(30, data.retry || 300),
  }
}

/* ------------------------------------------------------------------ */
/* Compte administrateur (miroir de UserSeeder)                        */
/* ------------------------------------------------------------------ */

const ADMIN = {
  id: 1,
  name: 'Administrateur Planet Kids',
  email: 'admin@planetkids.dz',
  password: 'password', // simulation uniquement — jamais en clair côté Laravel !
  is_admin: true,
}

/** tokens Sanctum simulés : token → user */
const tokens = new Map()

/* ------------------------------------------------------------------ */
/* Données (miroir des seeders Laravel)                                */
/* ------------------------------------------------------------------ */

const ASSETS = 'https://arsenaldza-coif.github.io/boutique1/assets'
const UNSPLASH = (id, w = 700) => `https://images.unsplash.com/${id}?q=80&w=${w}&auto=format&fit=crop`

const SETTINGS = {
  whatsapp_number: '213554698746',
  seller_email: 'admin@planetkids.dz',
  shop_name_fr: 'Planet Kids — Boudouaou',
  shop_name_ar: 'بلانيت كيدز — خيميسي شوب',
  shop_address_fr: 'Rue des Frères Aoudia, Boudouaou, Boumerdès, Algérie',
  shop_address_ar: 'شارع الإخوة عودية، بودواو، بومرداس',
  shop_hours_fr: 'Tous les jours : 09h à 21h · Vendredi : 14h30 à 21h',
  shop_hours_ar: 'كل الأيام: 9 صباحاً إلى 9 مساءً · الجمعة: 2:30 إلى 9 مساءً',
  shop_phone_display: '+213 554 69 87 46',
  shop_email: 'contact@planetkids.dz',
  hero_image: `${ASSETS}/hero-professional.jpg`,
  maps_query: 'Rue des Frères Aoudia, Boudouaou, Boumerdès, Algérie',
  whatsapp_group_url: 'https://chat.whatsapp.com/KJLlKQ6cbQe8GGFmy7UhL6',
  instagram_url: 'https://www.instagram.com/planetekids_',
  facebook_url: 'https://www.facebook.com/share/19YwPnT6jg/',
  tiktok_url: 'https://www.tiktok.com/@planetkids_',
}

const CATEGORIES = [
  /* --- Nouvelles catégories principales (miroir du setup en production) --- */
  { id: 9, parent_id: null, position: 10, slug: 'chaussures-accessoires', name_fr: 'Chaussures & Accessoires', name_ar: 'أحذية وإكسسوارات', description_fr: 'Chaussures, sacs, bonnets, chaussettes et accessoires cheveux.', description_ar: 'أحذية وحقائب وطواقي وجوارب وإكسسوارات الشعر.' },
  { id: 13, parent_id: 9, position: 10, slug: 'chaussures', name_fr: 'Chaussures', name_ar: 'أحذية', description_fr: null, description_ar: null },
  { id: 14, parent_id: 9, position: 20, slug: 'sacs', name_fr: 'Sacs', name_ar: 'حقائب', description_fr: null, description_ar: null },
  { id: 15, parent_id: 9, position: 30, slug: 'bonnets-chapeaux', name_fr: 'Bonnets & Chapeaux', name_ar: 'طواقي وقبعات', description_fr: null, description_ar: null },
  { id: 16, parent_id: 9, position: 40, slug: 'chaussettes', name_fr: 'Chaussettes', name_ar: 'جوارب', description_fr: null, description_ar: null },
  { id: 17, parent_id: 9, position: 50, slug: 'accessoires-cheveux', name_fr: 'Accessoires cheveux', name_ar: 'إكسسوارات الشعر', description_fr: null, description_ar: null },
  { id: 10, parent_id: null, position: 20, slug: 'puericulture', name_fr: 'Puériculture', name_ar: 'مستلزمات الطفل', description_fr: 'Tout pour les premiers mois : repas, sommeil, toilette, sorties.', description_ar: 'كل ما يلزم للأشهر الأولى: الطعام والنوم والاستحمام والخروج.' },
  { id: 18, parent_id: 10, position: 10, slug: 'repas-biberons', name_fr: 'Repas & Biberons', name_ar: 'الوجبات والرضّاعات', description_fr: null, description_ar: null },
  { id: 19, parent_id: 10, position: 20, slug: 'sommeil', name_fr: 'Sommeil', name_ar: 'النوم', description_fr: null, description_ar: null },
  { id: 20, parent_id: 10, position: 30, slug: 'toilette-soins', name_fr: 'Toilette & Soins', name_ar: 'الاستحمام والعناية', description_fr: null, description_ar: null },
  { id: 21, parent_id: 10, position: 40, slug: 'promenade-sorties', name_fr: 'Promenade & Sorties', name_ar: 'التنزه والخروج', description_fr: null, description_ar: null },
  { id: 22, parent_id: 10, position: 50, slug: 'equipement-bebe', name_fr: 'Équipement bébé', name_ar: 'تجهيزات الرضيع', description_fr: null, description_ar: null },
  { id: 11, parent_id: null, position: 30, slug: 'jouets-eveil', name_fr: 'Jouets & Éveil', name_ar: 'ألعاب وتنمية', description_fr: 'Jouets, jeux d\'éveil et peluches pour grandir en s\'amusant.', description_ar: 'ألعاب وأنشطة تنموية ودمى قطيفة للنمو والمرح.' },
  { id: 23, parent_id: 11, position: 10, slug: 'jouets', name_fr: 'Jouets', name_ar: 'ألعاب', description_fr: null, description_ar: null },
  { id: 24, parent_id: 11, position: 20, slug: 'eveil', name_fr: 'Éveil', name_ar: 'تنمية مهارات', description_fr: null, description_ar: null },
  { id: 25, parent_id: 11, position: 30, slug: 'peluches', name_fr: 'Peluches', name_ar: 'دمى قطيفة', description_fr: null, description_ar: null },
  { id: 12, parent_id: null, position: 40, slug: 'cadeaux', name_fr: 'Cadeaux', name_ar: 'هدايا', description_fr: 'Idées cadeaux pour toutes les occasions.', description_ar: 'أفكار هدايا لجميع المناسبات.' },
  { id: 26, parent_id: 12, position: 10, slug: 'naissance', name_fr: 'Naissance', name_ar: 'المولود الجديد', description_fr: null, description_ar: null },
  { id: 27, parent_id: 12, position: 20, slug: 'anniversaire', name_fr: 'Anniversaire', name_ar: 'عيد الميلاد', description_fr: null, description_ar: null },
  { id: 28, parent_id: 12, position: 30, slug: 'coffrets-cadeaux', name_fr: 'Coffrets cadeaux', name_ar: 'علب الهدايا', description_fr: null, description_ar: null },
  /* --- Anciennes catégories (produits historiques pas encore reclassés) --- */
  { id: 1, parent_id: null, position: 100, slug: 'bijoux-traditionnels', name_fr: 'Bijoux traditionnels', name_ar: 'مجوهرات تقليدية', description_fr: 'Argent, filigrane et pierres naturelles.', description_ar: 'فضة وفتيلة وأحجار طبيعية.' },
  { id: 2, parent_id: null, position: 110, slug: 'vetements-brodes', name_fr: 'Vêtements brodés', name_ar: 'ملابس مطرزة', description_fr: 'Caftans et tenues brodées main.', description_ar: 'قفاطين وأزياء مطرزة يدويًا.' },
  { id: 3, parent_id: null, position: 120, slug: 'deco-poterie', name_fr: 'Déco & poterie', name_ar: 'ديكور وفخار', description_fr: 'Céramiques peintes à la main.', description_ar: 'سيراميك مرسوم يدويًا.' },
  { id: 4, parent_id: null, position: 130, slug: 'accessoires-en-cuir', name_fr: 'Accessoires en cuir', name_ar: 'إكسسوارات جلدية', description_fr: 'Sacs et sandales en cuir véritable.', description_ar: 'حقائب وصنادل من الجلد الطبيعي.' },
  { id: 5, parent_id: null, position: 140, slug: 'parfums', name_fr: 'Parfums', name_ar: 'عطور', description_fr: 'Des fragrances élégantes pour chaque moment.', description_ar: 'روائح أنيقة لكل لحظة.' },
  { id: 6, parent_id: null, position: 150, slug: 'cosmetiques', name_fr: 'Cosmétiques', name_ar: 'مستحضرات التجميل', description_fr: 'Soins et beauté pour prendre soin de vous.', description_ar: 'منتجات للعناية والجمال.' },
  { id: 7, parent_id: null, position: 160, slug: 'articles-pour-bebe', name_fr: 'Articles pour bébé', name_ar: 'مستلزمات الأطفال', description_fr: 'Des essentiels doux et sûrs pour bébé.', description_ar: 'احتياجات ناعمة وآمنة لطفلك.' },
  { id: 8, parent_id: null, position: 170, slug: 'hygiene-bebe', name_fr: 'Hygiène bébé', name_ar: 'نظافة الطفل', description_fr: 'Des soins quotidiens doux pour les tout-petits.', description_ar: 'منتجات لطيفة للعناية اليومية بصغيرك.' },
]

const P = (id, catId, slug, name_fr, name_ar, description_fr, description_ar, price, image, is_featured = false, promo_quantity = null, promo_percent = null) => ({
  id, category_id: catId, slug, name_fr, name_ar, description_fr, description_ar, price, image, is_featured, is_active: true, promo_quantity, promo_percent,
})

const PRODUCTS = [
  P(1, 1, 'collier-filigrane-argent', 'Collier Filigrane Argent', 'قلادة فضية بالفتيلة', 'Collier artisanal en argent massif, motifs filigranés traditionnels, fait main à Alger.', 'قلادة حرفية من الفضة الخالصة، بزخارف الفتيلة التقليدية، صنعت يدويًا بالجزائر العاصمة.', 8500, UNSPLASH('photo-1611591437281-460bfbe1220a')),
  P(2, 1, 'boucles-doreilles-berberes', "Boucles d'oreilles Berbères", 'أقراط أمازيغية', 'Boucles en argent ciselé, inspirées des bijoux berbères ancestraux.', 'أقراط من الفضة المنقوشة، مستوحاة من الحلي الأمازيغية العريقة.', 4200, UNSPLASH('photo-1535632066927-ab7c9ab60908')),
  P(3, 2, 'caftan-brode-or', 'Caftan Brodé Or', 'قفطان مطرز بالذهب', "Caftan de cérémonie brodé fil d'or, tissu velours, coupe traditionnelle.", 'قفطان احتفالي مطرز بخيط ذهبي، قماش مخملي، قصة تقليدية.', 15000, UNSPLASH('photo-1520006403909-838d6b92c22e')),
  P(4, 2, 'djellaba-brodee', 'Djellaba Brodée', 'جلابة مطرزة', 'Djellaba légère brodée main, idéale pour les grandes occasions.', 'جلابة خفيفة مطرزة يدويًا، مثالية للمناسبات الكبرى.', 9800, UNSPLASH('photo-1596704017254-9b121068fb31')),
  P(5, 3, 'theiere-en-cuivre-gravee', 'Théière en Cuivre Gravée', 'إبريق شاي نحاسي منقوش', 'Théière traditionnelle en cuivre martelé et gravé à la main.', 'إبريق شاي تقليدي من النحاس المطروق والمنقوش يدويًا.', 6500, UNSPLASH('photo-1591195853828-11db59a44f6b')),
  P(6, 3, 'assiette-en-poterie-peinte', 'Assiette en Poterie Peinte', 'طبق فخاري مرسوم', 'Assiette décorative en céramique, peinte à la main selon les motifs de Kabylie.', 'طبق زينة من السيراميك، مرسوم يدويًا بزخارف القبائل.', 3200, UNSPLASH('photo-1578500494198-246f612d3b3d')),
  P(7, 14, 'sac-a-main-en-cuir', 'Sac à Main en Cuir', 'حقيبة يد جلدية', 'Sac en cuir véritable tanné artisanalement, doublure cousue main.', 'حقيبة من الجلد الطبيعي المدبوغ حرفيًا، بطانة مخيطة يدويًا.', 7200, UNSPLASH('photo-1553062407-98eeb64c6a62')),
  P(8, 13, 'sandales-en-cuir', 'Sandales en Cuir', 'صنادل جلدية', 'Sandales en cuir souple, semelle confortable, fabrication locale.', 'صنادل من الجلد الطري، نعل مريح، صناعة محلية.', 4500, UNSPLASH('photo-1560343090-f0409e92791a')),
  P(9, 5, 'eau-de-parfum-jasmin', 'Eau de parfum Jasmin', 'عطر الياسمين', 'Un parfum floral élégant aux notes de jasmin et de musc blanc.', 'عطر زهري أنيق بنفحات الياسمين والمسك الأبيض.', 6800, `${ASSETS}/perfume-bottle-product-photography-neutr-2.jpg`, true, 2, 15),
  P(10, 5, 'parfum-oud-dorient', "Parfum Oud d'Orient", 'عطر عود شرقي', "Une fragrance chaleureuse et profonde aux notes de oud et d'ambre.", 'رائحة دافئة وعميقة بنفحات العود والعنبر.', 9200, `${ASSETS}/perfume-bottle-product-photography-neutr-1.webp`, true),
  P(11, 6, 'coffret-soin-visage', 'Coffret Soin Visage', 'طقم العناية بالوجه', 'Coffret beauté avec nettoyant, crème hydratante et sérum.', 'طقم جمال يضم منظفًا وكريم ترطيب وسيروم.', 5400, `${ASSETS}/cosmetics-skincare-products-product-phot-1.jpg`, false, 2, 10),
  P(12, 6, 'huile-naturelle-pour-cheveux', 'Huile naturelle pour cheveux', 'زيت طبيعي للشعر', 'Huile nourrissante aux plantes pour des cheveux doux et brillants.', 'زيت مغذٍ بالنباتات لشعر ناعم ولامع.', 3900, `${ASSETS}/cosmetics-skincare-products-product-phot-2.jpg`),
  P(13, 20, 'coffret-douceur-bebe', 'Coffret Douceur Bébé', 'طقم عناية للطفل', 'Coffret de soins doux pour la toilette et la peau délicate de bébé.', 'طقم عناية لطيف لبشرة الطفل الحساسة.', 4600, `${ASSETS}/baby-products-toys-skincare-product-phot-1.jpg`),
  P(14, 25, 'doudou-lapin-en-coton', 'Doudou Lapin en coton', 'دمية أرنب قطنية', 'Doudou tout doux en coton, compagnon rassurant dès la naissance.', 'دمية ناعمة من القطن، رفيق مطمئن منذ الولادة.', 3500, `${ASSETS}/baby-products-toys-skincare-product-phot-2.jpg`),
  P(15, 5, 'brume-parfumee-fleur-doranger', "Brume parfumée Fleur d'oranger", 'رذاذ زهر البرتقال المعطر', "Une brume légère et fraîche aux notes délicates de fleur d'oranger.", 'رذاذ خفيف ومنعش بنفحات زهر البرتقال الرقيقة.', 3200, `${ASSETS}/perfume-bottle-product-photography-neutr-1.webp`),
  P(16, 5, 'coffret-parfum-elegance', 'Coffret Parfum Élégance', 'طقم عطر الأناقة', 'Coffret parfum raffiné à offrir, avec une fragrance douce et longue tenue.', 'طقم عطر راقٍ كهدية، برائحة ناعمة وثبات طويل.', 7400, `${ASSETS}/perfume-bottle-product-photography-neutr-2.jpg`),
  P(17, 6, 'creme-hydratante-douceur', 'Crème Hydratante Douceur', 'كريم الترطيب والنعومة', 'Crème visage et corps pour une peau souple, fraîche et parfaitement hydratée.', 'كريم للوجه والجسم لبشرة ناعمة ومنتعشة ورطبة.', 2800, `${ASSETS}/cosmetics-skincare-products-product-phot-2.jpg`),
  P(18, 6, 'palette-maquillage-naturelle', 'Palette Maquillage Naturelle', 'لوحة مكياج طبيعية', 'Palette de teintes naturelles pour un maquillage élégant au quotidien.', 'ألوان طبيعية لمكياج أنيق في كل يوم.', 6100, `${ASSETS}/cosmetics-skincare-products-product-phot-1.jpg`),
  P(19, 7, 'shampoing-doux-bebe', 'Shampoing Doux Bébé', 'شامبو لطيف للأطفال', 'Shampoing délicat sans rinçage agressif, adapté à la peau sensible de bébé.', 'شامبو لطيف مناسب لبشرة الطفل الحساسة.', 2900, `${ASSETS}/baby-products-toys-skincare-product-phot-2.jpg`),
  P(20, 7, 'cape-de-bain-bebe', 'Cape de Bain Bébé', 'منشفة استحمام للأطفال', 'Cape de bain moelleuse et absorbante pour garder bébé bien au chaud.', 'منشفة ناعمة وماصة تحافظ على دفء طفلك بعد الاستحمام.', 5200, `${ASSETS}/baby-products-toys-skincare-product-phot-1.jpg`),
  P(21, 8, 'lingettes-douces-bebe', 'Lingettes Douces Bébé', 'مناديل أطفال ناعمة', 'Lingettes délicates pour la toilette quotidienne, pratiques et douces.', 'مناديل لطيفة للنظافة اليومية، عملية وناعمة.', 2100, `${ASSETS}/baby-products-toys-skincare-product-phot-2.jpg`),
  P(22, 8, 'lait-nettoyant-bebe', 'Lait Nettoyant Bébé', 'حليب تنظيف للأطفال', 'Lait nettoyant doux pour le visage et le corps des tout-petits.', 'حليب تنظيف لطيف للوجه والجسم للصغار.', 3300, `${ASSETS}/baby-products-toys-skincare-product-phot-1.jpg`),
]

/* ------------------------------------------------------------------ */
/* Catalogue volumineux : génération jusqu'à 1000 produits            */
/* (pour tester pagination / recherche / admin à l'échelle réelle)     */
/* ------------------------------------------------------------------ */

const TARGET_PRODUCTS = parseInt(process.env.MOCK_PRODUCTS || '1000', 10)
const VARIANTS_FR = ['Édition Standard', 'Édition Prestige', 'Coffret Découverte', 'Grande Taille', 'Format Voyage', 'Édition Limitée', 'Coffret Duo', 'Série Or']
const VARIANTS_AR = ['إصدار عادي', 'إصدار فاخر', 'طقم اكتشاف', 'حجم كبير', 'حجم السفر', 'إصدار محدود', 'طقم مزدوج', 'سلسلة ذهبية']

if (PRODUCTS.length < TARGET_PRODUCTS) {
  const base = [...PRODUCTS]
  for (let i = PRODUCTS.length; i < TARGET_PRODUCTS; i++) {
    const src = base[i % base.length]
    const v = Math.floor(i / base.length) % VARIANTS_FR.length
    const price = src.price + ((i * 37) % 15) * 100
    PRODUCTS.push({
      id: i + 1,
      category_id: src.category_id,
      slug: `${src.slug}-${i + 1}`,
      name_fr: `${src.name_fr} — ${VARIANTS_FR[v]}`,
      name_ar: `${src.name_ar} — ${VARIANTS_AR[v]}`,
      description_fr: `${src.description_fr} Déclinaison « ${VARIANTS_FR[v]} » (référence ${1000 + i}).`,
      description_ar: `${src.description_ar} نسخة « ${VARIANTS_AR[v]} » (مرجع ${1000 + i}).`,
      price,
      image: src.image,
      is_featured: false,
      is_active: true,
    })
  }
}
let nextProductId = PRODUCTS.length + 1

/* ------------------------------------------------------------------ */
/* Répartition de démonstration : des produits générés sont attribués  */
/* aux 16 nouvelles sous-catégories afin de tester les filtres à      */
/* deux niveaux (catégorie principale → sous-catégorie).              */
/* ------------------------------------------------------------------ */
const DEMO_SUB_IDS = [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28]
PRODUCTS.forEach((p) => {
  if (p.id > 22 && p.id <= 22 + DEMO_SUB_IDS.length * 20) {
    p.category_id = DEMO_SUB_IDS[(p.id - 23) % DEMO_SUB_IDS.length]
  }
})


/* ------------------------------------------------------------------ */
/* Lots (bundles) : plusieurs produits regroupés à prix réduit         */
/* ------------------------------------------------------------------ */

const productBySlug = (slug) => PRODUCTS.find((p) => p.slug === slug)
const productById = (id) => PRODUCTS.find((p) => p.id === id)

const BUNDLE_DEFS = [
  { id: 1, slug: 'lot-decouverte-parfums', name_fr: 'Lot Découverte Parfums', name_ar: 'طقم اكتشاف العطور', description_fr: 'Trois fragrances signature pour trouver votre préférée.', description_ar: 'ثلاث عطور مميزة لتكتشف عطرك المفضل.', price: 15900, image: null, is_active: true, is_featured: true, position: 10,
    items: [['eau-de-parfum-jasmin', 1], ['parfum-oud-dorient', 1], ['brume-parfumee-fleur-doranger', 1]] },
  { id: 2, slug: 'lot-douceur-bebe', name_fr: 'Lot Douceur Bébé', name_ar: 'طقم النعومة للطفل', description_fr: "L'essentiel pour la toilette et le confort de bébé.", description_ar: 'الأساسيات للاستحمام وراحة طفلك.', price: 9900, image: null, is_active: true, position: 20,
    items: [['coffret-douceur-bebe', 1], ['doudou-lapin-en-coton', 1], ['shampoing-doux-bebe', 1]] },
  { id: 3, slug: 'duo-beaute', name_fr: 'Duo Beauté', name_ar: 'ثنائي الجمال', description_fr: 'Soin complet visage : coffret + crème hydratante.', description_ar: 'عناية كاملة بالوجه: طقم + كريم مرطب.', price: 6900, image: null, is_active: true, position: 30,
    items: [['coffret-soin-visage', 1], ['creme-hydratante-douceur', 1]] },
]

const BUNDLES = BUNDLE_DEFS.map((def) => ({
  id: def.id, slug: def.slug, name_fr: def.name_fr, name_ar: def.name_ar,
  description_fr: def.description_fr, description_ar: def.description_ar,
  price: def.price, image: def.image, is_active: def.is_active, is_featured: !!def.is_featured, position: def.position,
  items: def.items.map(([slug, quantity]) => ({ product_id: productBySlug(slug)?.id, quantity }))
    .filter((item) => item.product_id !== undefined),
}))
let nextBundleId = BUNDLES.length + 1

const bundleHasPromo = (p) => Boolean(p.promo_quantity >= 2 && p.promo_percent >= 1)
const unitPriceFor = (p, qty) => (bundleHasPromo(p) && qty >= p.promo_quantity
  ? Math.round(p.price * (100 - p.promo_percent) / 100)
  : p.price)

const bundleResource = (b) => {
  const items = b.items.map((item, index) => {
    const product = productById(item.product_id)
    return {
      id: index + 1,
      quantity: item.quantity,
      product: product
        ? { id: product.id, slug: product.slug, name_fr: product.name_fr, name_ar: product.name_ar, description_fr: product.description_fr, description_ar: product.description_ar, price: product.price, image: product.image }
        : null,
    }
  }).filter((item) => item.product !== null)

  const regularTotal = items.reduce((sum, item) => sum + item.product.price * item.quantity, 0)
  const savings = Math.max(0, regularTotal - b.price)

  return {
    id: b.id, slug: b.slug, name_fr: b.name_fr, name_ar: b.name_ar,
    description_fr: b.description_fr, description_ar: b.description_ar,
    price: b.price,
    image: b.image || items[0]?.product.image || null,
    regular_total: regularTotal,
    savings,
    savings_percent: regularTotal > 0 ? Math.round(savings / regularTotal * 100) : 0,
    is_active: !!b.is_active,
    is_featured: !!b.is_featured,
    items,
  }
}

const REVIEWS = [
  { id: 1, author_name: 'Amine A.', city_fr: 'Boudouaou', city_ar: 'بودواو', rating: 5, content_fr: '« Le magasin est vraiment top, Dieu merci le service est merveilleux. Je recommande vivement ! »', content_ar: '«المتجر رائع، الحمد لله الخدمة ممتازة. أنصح به بشدة!»' },
  { id: 2, author_name: 'Iméne', city_fr: 'Boudouaou', city_ar: 'بودواو', rating: 5, content_fr: '« Excellent service et qualité. Des produits de marque pour nos enfants. »', content_ar: '«خدمة وجودة ممتازة. منتجات ذات جودة عالية لأطفالنا.»' },
  { id: 3, author_name: 'Ismail I.', city_fr: 'Boudouaou', city_ar: 'بودواو', rating: 5, content_fr: '« Boutique très bien organisée, personnel accueillant. Katakit Boudouaou ! »', content_ar: '«متجر منظم جداً وموظفون ودودون. قطيطة بودواو!»' },
]

const GALLERY = [
  { id: 1, image: UNSPLASH('photo-1611591437281-460bfbe1220a', 900), alt_fr: 'Bijoux', alt_ar: 'مجوهرات' },
  { id: 2, image: UNSPLASH('photo-1520006403909-838d6b92c22e'), alt_fr: 'Caftan brodé', alt_ar: 'قفطان مطرز' },
  { id: 3, image: UNSPLASH('photo-1578500494198-246f612d3b3d'), alt_fr: 'Poterie', alt_ar: 'فخار' },
  { id: 4, image: UNSPLASH('photo-1553062407-98eeb64c6a62', 900), alt_fr: 'Sac en cuir', alt_ar: 'حقيبة جلدية' },
  { id: 5, image: UNSPLASH('photo-1596704017254-9b121068fb31'), alt_fr: 'Tapis', alt_ar: 'لباس تقليدي' },
  { id: 6, image: UNSPLASH('photo-1591195853828-11db59a44f6b'), alt_fr: 'Théière traditionnelle', alt_ar: 'إبريق شاي تقليدي' },
  { id: 7, image: UNSPLASH('photo-1590736969955-71cc94901144'), alt_fr: 'Atelier artisanal', alt_ar: 'ورشة حرفية' },
  { id: 8, image: UNSPLASH('photo-1517502884422-41eaead166d4'), alt_fr: 'Vitrine boutique', alt_ar: 'واجهة المتجر' },
]

const orders = [] // commandes enregistrées (en mémoire)

let nextOrderId = 1

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

const categoryById = (id) => CATEGORIES.find((c) => c.id === Number(id))

const productResource = (p) => ({
  id: p.id,
  slug: p.slug,
  name_fr: p.name_fr,
  name_ar: p.name_ar,
  description_fr: p.description_fr,
  description_ar: p.description_ar,
  price: p.price,
  image: p.image,
  is_featured: !!p.is_featured,
  is_active: !!p.is_active,
  promo_quantity: p.promo_quantity ?? null,
  promo_percent: p.promo_percent ?? null,
  promo_active: Boolean(p.promo_quantity >= 2 && p.promo_percent >= 1),
  category: categoryById(p.category_id) || null,
  created_at: p.created_at || '2026-01-01T00:00:00.000Z',
})

const categoryResource = (c) => ({
  ...c,
  products_count: PRODUCTS.filter((p) => p.category_id === c.id).length,
})

/**
 * Ordre « famille » (miroir du ORDER BY SQL de Laravel) : chaque
 * catégorie principale suivie de ses sous-catégories.
 */
const orderedCategories = () => {
  const mains = CATEGORIES.filter((c) => !c.parent_id)
    .sort((a, b) => (a.position || 0) - (b.position || 0) || a.id - b.id)
  const out = []
  for (const main of mains) {
    out.push(main)
    out.push(
      ...CATEGORIES
        .filter((c) => c.parent_id === main.id)
        .sort((a, b) => (a.position || 0) - (b.position || 0) || a.id - b.id),
    )
  }
  // Sécurité : sous-catégories orphelines (parent supprimé)
  const ids = new Set(CATEGORIES.map((c) => c.id))
  out.push(...CATEGORIES.filter((c) => c.parent_id && !ids.has(c.parent_id)))
  return out
}

/** Identifiants d'une catégorie + ses sous-catégories (filtre produits). */
const categoryFamilyIds = (cat) => {
  if (!cat) return null
  return new Set([
    cat.id,
    ...CATEGORIES.filter((c) => c.parent_id === cat.id).map((c) => c.id),
  ])
}

const orderResource = (o) => ({
  id: o.id,
  reference: o.reference,
  customer_name: o.customer_name,
  customer_phone: o.customer_phone,
  wilaya: o.wilaya,
  address: null,
  notes: o.notes,
  total: o.total,
  status: o.status,
  items: o.lines.map((l) => ({
    id: l.id,
    product_id: l.product?.id ?? null,
    product_name: l.name + (l.product ? '' : ' (lot)'),
    unit_price: l.lineTotal / l.quantity,
    quantity: l.quantity,
    line_total: l.lineTotal,
  })),
  created_at: o.created_at,
})

function json(res, status, body) {
  const payload = JSON.stringify(body)
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization',
  })
  res.end(payload)
}

const formatDa = (n) => n.toLocaleString('fr-FR').replace(/[\u202f\u00a0]/g, ' ')

/** Slugify simple (identique au frontend/Laravel). */
function slugifyCsv(value) {
  return String(value).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, '').trim().replace(/[\s-]+/g, '-') || 'produit'
}

/** Parseur CSV minimaliste : séparateur , ou ; (auto-détecté), guillemets, BOM. */
function parseCsv(text) {
  const clean = text.replace(/^\uFEFF/, '')
  const lines = clean.split(/\r\n|\r|\n/).filter((l) => l.trim() !== '')
  if (lines.length < 2) return []

  const separator = (lines[0].split(';').length >= lines[0].split(',').length) ? ';' : ','
  const splitLine = (line) => {
    const cells = []
    let current = ''
    let inQuotes = false
    for (let i = 0; i < line.length; i++) {
      const ch = line[i]
      if (inQuotes) {
        if (ch === '"') {
          if (line[i + 1] === '"') { current += '"'; i++ } else { inQuotes = false }
        } else { current += ch }
      } else if (ch === '"') {
        inQuotes = true
      } else if (ch === separator) {
        cells.push(current); current = ''
      } else {
        current += ch
      }
    }
    cells.push(current)
    return cells
  }

  const header = splitLine(lines[0]).map((cell) =>
    cell.trim().toLowerCase()
      .replace(/[\s-]+/g, '_')
      .replace(/[^a-z0-9_]/g, '')
  )
  return lines.slice(1).map((line) => {
    const cells = splitLine(line)
    const row = {}
    header.forEach((key, index) => {
      if (key) row[key] = cells[index] ?? ''
    })
    return row
  })
}

/** Utilisateur authentifié via l'en-tête Authorization: Bearer … */
function currentUser(req) {
  const header = req.headers['authorization'] || ''
  const match = header.match(/^Bearer\s+(.+)$/i)
  if (!match) return null
  return tokens.get(match[1]) || null
}

function requireAuth(req, res) {
  const user = currentUser(req)
  if (!user) {
    json(res, 401, { message: 'Unauthenticated.' })
    return null
  }
  return user
}

/* ------------------------------------------------------------------ */
/* Parseur multipart/form-data (téléversement d'images, sans dépendance) */
/* ------------------------------------------------------------------ */

function parseMultipart(buffer, contentTypeHeader) {
  const match = /boundary=(?:"([^"]+)"|([^;]+))/i.exec(contentTypeHeader || '')
  if (!match) return null

  const boundary = '--' + (match[1] || match[2])
  const bBoundary = Buffer.from(boundary)
  const fields = {}
  const files = {}

  let start = buffer.indexOf(bBoundary)
  while (start !== -1) {
    const next = buffer.indexOf(bBoundary, start + bBoundary.length)
    if (next === -1) break

    const part = buffer.slice(start + bBoundary.length + 2, next - 2)
    const headerEnd = part.indexOf('\r\n\r\n')
    if (headerEnd !== -1) {
      const headerStr = part.slice(0, headerEnd).toString('utf8')
      const body = part.slice(headerEnd + 4)

      const nameMatch = /name="([^"]*)"/i.exec(headerStr)
      const fileMatch = /filename="([^"]*)"/i.exec(headerStr)
      const name = nameMatch ? nameMatch[1] : null

      if (name) {
        if (fileMatch && fileMatch[1]) {
          const typeMatch = /content-type:\s*([^\r\n]+)/i.exec(headerStr)
          files[name] = { filename: fileMatch[1], contentType: typeMatch ? typeMatch[1].trim() : '', data: body }
        } else {
          fields[name] = body.toString('utf8')
        }
      }
    }
    start = next
  }

  return { fields, files }
}

/** Enregistre un fichier téléversé et retourne son URL /storage/… */
function saveUploadedFile(file) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true })
  const ext = (path.extname(file.filename) || '.jpg').toLowerCase().replace(/[^.a-z]/g, '')
  const safeName = `${Date.now()}-${crypto.randomBytes(4).toString('hex')}${ext}`
  fs.writeFileSync(path.join(UPLOAD_DIR, safeName), file.data)
  return `/storage/products/${safeName}`
}

const MIME = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp' }

/** Sert les fichiers téléversés (équivalent de `php artisan storage:link`). */
function serveUpload(res, fileName) {
  const safe = path.basename(fileName) // anti traversal
  const filePath = path.join(UPLOAD_DIR, safe)

  if (!fs.existsSync(filePath)) {
    res.writeHead(404, { 'Content-Type': 'text/plain' })
    return res.end('Not found')
  }

  const ext = path.extname(safe).toLowerCase()
  res.writeHead(200, {
    'Content-Type': MIME[ext] || 'application/octet-stream',
    'Cache-Control': 'public, max-age=3600',
    'Access-Control-Allow-Origin': '*',
  })
  fs.createReadStream(filePath).pipe(res)
}

/* ------------------------------------------------------------------ */
/* Validation commandes (miroir de OrderController)                    */
/* ------------------------------------------------------------------ */

function validateOrder(body) {
  const errors = {}
  const add = (field, message) => {
    errors[field] = errors[field] || []
    errors[field].push(message)
  }

  const name = typeof body.customer_name === 'string' ? body.customer_name.trim() : ''
  if (name.length < 2 || name.length > 120) add('customer_name', 'Le champ nom complet doit contenir entre 2 et 120 caractères.')

  const phone = typeof body.customer_phone === 'string' ? body.customer_phone.trim() : ''
  if (!/^[0-9+\s().-]{9,20}$/.test(phone)) add('customer_phone', 'Le format du téléphone est invalide.')

  const wilaya = typeof body.wilaya === 'string' ? body.wilaya.trim() : ''
  if (!wilaya || wilaya.length > 100) add('wilaya', 'Le champ wilaya est obligatoire.')

  if (body.notes && typeof body.notes === 'string' && body.notes.length > 1000) {
    add('notes', 'La note ne doit pas dépasser 1000 caractères.')
  }

  if (!Array.isArray(body.items) || body.items.length === 0) {
    add('items', 'La commande doit contenir au moins un article.')
  } else {
    body.items.forEach((item, i) => {
      const hasProduct = item && Number.isInteger(item.product_id) && PRODUCTS.some((p) => p.id === item.product_id)
      const hasBundle = item && Number.isInteger(item.bundle_id) && BUNDLES.some((b) => b.id === item.bundle_id)

      if (!hasProduct && !hasBundle) {
        add(`items.${i}.product_id`, 'Article inconnu (product_id ou bundle_id requis).')
      }
      if (!item || !Number.isInteger(item.quantity) || item.quantity < 1 || item.quantity > 99) {
        add(`items.${i}.quantity`, 'La quantité doit être comprise entre 1 et 99.')
      }
    })
  }

  return errors
}

function buildWhatsAppMessage(order, lines, lang) {
  const isAr = lang === 'ar'
  const intro = isAr ? 'مرحباً، أريد تأكيد طلبي:' : 'Bonjour, je souhaite confirmer ma commande :'
  const itemLines = lines
    .map((l) => {
      const name = isAr
        ? (l.product ? l.product.name_ar : BUNDLES.find((b) => b.name_fr === l.name)?.name_ar || l.name)
        : l.name
      const total = formatDa(l.lineTotal)

      // remise (promo ou lot) → afficher le prix barré
      if (l.regularTotal > l.lineTotal) {
        const regular = formatDa(l.regularTotal)
        return isAr
          ? `- ${name} × ${l.quantity} = ${total} دج (بدل ${regular} دج)`
          : `- ${name} × ${l.quantity} = ${total} DA (au lieu de ${regular} DA)`
      }

      return isAr
        ? `- ${name} × ${l.quantity} = ${total} دج`
        : `- ${name} × ${l.quantity} = ${total} DA`
    })
    .join('\n')
  const labels = isAr
    ? { total: 'المجموع', ref: 'المرجع', name: 'الاسم', phone: 'الهاتف', wilaya: 'الولاية' }
    : { total: 'Total', ref: 'Référence', name: 'Nom', phone: 'Téléphone', wilaya: 'Wilaya' }

  const parts = [
    intro,
    itemLines,
    `${labels.total} : ${formatDa(order.total)}${isAr ? ' دج' : ' DA'}`,
    `${labels.ref} : ${order.reference}`,
    `${labels.name} : ${order.customer_name}`,
    `${labels.phone} : ${order.customer_phone}`,
    `${labels.wilaya} : ${order.wilaya}`,
  ]
  if (order.notes) parts.push(`${isAr ? 'ملاحظة' : 'Note'} : ${order.notes}`)
  return parts.join('\n')
}

/** Simulation de la notification e-mail au vendeur (OrderPlaced côté Laravel). */
function simulateSellerEmail(order) {
  const email = [
    `════════════════════════════════════════════════════`,
    `📧 NOTIFICATION E-MAIL → ${SETTINGS.seller_email}`,
    `Objet : 🛍️ Nouvelle commande ${order.reference} — Planet Kids`,
    `────────────────────────────────────────────────────`,
    `Client     : ${order.customer_name} — ${order.customer_phone}`,
    `Wilaya     : ${order.wilaya}`,
    `Référence  : ${order.reference}`,
    `Articles   :`,
    ...order.lines.map((l) => `  • ${l.name}${l.product ? '' : ' (lot)'} × ${l.quantity} = ${formatDa(l.lineTotal)} DA`),
    `TOTAL      : ${formatDa(order.total)} DA (paiement à la livraison)`,
    `════════════════════════════════════════════════════`,
  ].join('\n')
  console.log(email)
}

/* ------------------------------------------------------------------ */
/* Validation produits (miroir de Admin\ProductController)             */
/* ------------------------------------------------------------------ */

function validateProductPayload(body, existingId) {
  const errors = {}
  const add = (field, message) => {
    errors[field] = errors[field] || []
    errors[field].push(message)
  }

  if (body.category_id !== undefined) {
    if (!Number.isInteger(Number(body.category_id)) || !categoryById(body.category_id)) {
      add('category_id', 'La catégorie sélectionnée est invalide.')
    }
  }
  if (body.name_fr !== undefined && String(body.name_fr).trim().length < 1) {
    add('name_fr', 'Le nom (français) est obligatoire.')
  }
  if (body.name_ar !== undefined && String(body.name_ar).trim().length < 1) {
    add('name_ar', 'الاسم (عربي) مطلوب.')
  }
  if (body.price !== undefined) {
    const price = Number(body.price)
    if (!Number.isInteger(price) || price < 0 || price > 999999999) add('price', 'Le prix doit être un entier positif.')
  }
  if (body.slug) {
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(body.slug)) add('slug', 'Le slug ne peut contenir que des lettres minuscules, chiffres et tirets.')
    else if (PRODUCTS.some((p) => p.slug === body.slug && p.id !== existingId)) add('slug', 'Ce slug est déjà utilisé.')
  }
  if (body.image_url !== undefined && body.image_url !== null && String(body.image_url).trim() !== '' &&
      !/^https?:\/\/.+/i.test(String(body.image_url).trim())) {
    add('image_url', "L'URL de l'image est invalide.")
  }

  return errors
}

const slugify = (value) =>
  String(value).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, '').trim().replace(/[\s-]+/g, '-') || 'produit'

function uniqueSlug(base, existingId) {
  let slug = base
  let i = 1
  while (PRODUCTS.some((p) => p.slug === slug && p.id !== existingId)) {
    slug = `${base}-${++i}`
  }
  return slug
}

/** Extrait un payload produit d'un body JSON ou multipart. */
function productPayloadFrom(body, files) {
  const toBool = (v) => v === true || v === 'true' || v === '1' || v === 1
  const payload = {}

  if (body.category_id !== undefined) payload.category_id = Number(body.category_id)
  if (body.name_fr !== undefined) payload.name_fr = String(body.name_fr).trim()
  if (body.name_ar !== undefined) payload.name_ar = String(body.name_ar).trim()
  if (body.description_fr !== undefined) payload.description_fr = String(body.description_fr).trim() || null
  if (body.description_ar !== undefined) payload.description_ar = String(body.description_ar).trim() || null
  if (body.price !== undefined) payload.price = Number(body.price)
  if (body.slug !== undefined && String(body.slug).trim() !== '') payload.slug = String(body.slug).trim()
  if (body.is_featured !== undefined) payload.is_featured = toBool(body.is_featured)
  if (body.is_active !== undefined) payload.is_active = toBool(body.is_active)
  if (body.image_url !== undefined && String(body.image_url).trim() !== '') payload.image_url = String(body.image_url).trim()

  if (files && files.image) {
    const file = files.image
    const ext = path.extname(file.filename || '').toLowerCase()
    if (!['.jpg', '.jpeg', '.png', '.webp'].includes(ext)) {
      return { payload, error: 'image', message: 'Formats acceptés : JPG, PNG, WebP.' }
    }
    if (file.data.length > 2 * 1024 * 1024) {
      return { payload, error: 'image', message: 'L\u2019image ne doit pas dépasser 2 Mo.' }
    }
    payload.image_path = saveUploadedFile(file)
  }

  return { payload }
}

/* ------------------------------------------------------------------ */
/* Serveur                                                             */
/* ------------------------------------------------------------------ */

function readBody(req) {
  return new Promise((resolve) => {
    const chunks = []
    req.on('data', (chunk) => {
      chunks.push(chunk)
      if (chunks.reduce((s, c) => s + c.length, 0) > 10 * 1024 * 1024) req.destroy()
    })
    req.on('end', () => resolve(Buffer.concat(chunks)))
  })
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`)
  const pathName = url.pathname.replace(/\/+$/, '') || '/'
  const query = url.searchParams
  const method = req.method

  if (method === 'OPTIONS') return json(res, 204, {})

  /* ---------- Mode maintenance (miroir du middleware ShopMaintenance) ----------
   * Routes publiques → 503 { maintenance: true } ; l'admin et l'auth
   * restent accessibles (pour gérer la boutique et rouvrir le site),
   * ainsi que l'endpoint de contrôle /api/maintenance (simulation).
   */
  if (readMaintenance() && !/^\/(?:api\/)?(?:auth|admin|maintenance)(?:\/|$)/.test(pathName)) {
    return json(res, 503, maintenancePayload())
  }

  /* ---------- Fichiers téléversés (storage) ---------- */
  const uploadMatch = pathName.match(/^\/storage\/products\/([^/]+)$/)
  if (method === 'GET' && uploadMatch) return serveUpload(res, decodeURIComponent(uploadMatch[1]))

  /* ---------- GET publics ---------- */
  if (method === 'GET') {
    if (pathName === '/api/settings' || pathName === '/settings') return json(res, 200, { data: SETTINGS })

    if (pathName === '/api/categories' || pathName === '/categories') {
      return json(res, 200, { data: orderedCategories().map(categoryResource) })
    }

    if (pathName === '/api/products' || pathName === '/products') {
      let products = PRODUCTS.filter((p) => p.is_active)

      const category = query.get('category')
      if (category) {
        const cat = CATEGORIES.find((c) => c.slug === category)
        const ids = cat ? categoryFamilyIds(cat) : null
        products = ids ? products.filter((p) => ids.has(p.category_id)) : []
      }

      const search = (query.get('search') || '').trim().toLowerCase()
      if (search) {
        products = products.filter((p) =>
          [p.name_fr, p.name_ar, p.description_fr, p.description_ar]
            .some((v) => (v || '').toLowerCase().includes(search))
        )
      }

      if (query.get('featured') === '1' || query.get('featured') === 'true') {
        products = products.filter((p) => p.is_featured)
      }

      // Sélection d'identifiants (hydration du panier) → non paginé
      const idsParam = query.get('ids')
      if (idsParam) {
        const ids = idsParam.split(',').map((v) => Number(v.trim())).filter(Number.isInteger)
        const byId = new Map(PRODUCTS.map((p) => [p.id, p]))
        const selected = ids.map((id) => byId.get(id)).filter((p) => p && p.is_active)
        return json(res, 200, { data: selected.map(productResource) })
      }

      // Catalogue complet (sitemap) → non paginé
      if (query.get('per_page') === 'all') {
        return json(res, 200, { data: products.map(productResource) })
      }

      // Les produits « en vedette » sont affichés EN PREMIER (tri stable)
      products.sort((a, b) => (b.is_featured ? 1 : 0) - (a.is_featured ? 1 : 0))

      // Pagination (miroir de Laravel : paginate() → meta)
      const perPage = Math.min(Math.max(parseInt(query.get('per_page') || '24', 10), 4), 100)
      const page = Math.max(parseInt(query.get('page') || '1', 10), 1)
      const total = products.length
      const lastPage = Math.max(Math.ceil(total / perPage), 1)
      const current = Math.min(page, lastPage)
      const slice = products.slice((current - 1) * perPage, current * perPage)

      return json(res, 200, {
        data: slice.map(productResource),
        meta: {
          current_page: current,
          from: slice.length ? (current - 1) * perPage + 1 : null,
          last_page: lastPage,
          per_page: perPage,
          to: slice.length ? (current - 1) * perPage + slice.length : null,
          total,
        },
        links: { first: '/api/products?page=1', last: `/api/products?page=${lastPage}` },
      })
    }

    const productMatch = pathName.match(/^\/(?:api\/)?products\/([^/]+)$/)
    if (productMatch) {
      const product = PRODUCTS.find((p) => p.slug === decodeURIComponent(productMatch[1]) && p.is_active)
      if (!product) return json(res, 404, { message: 'Produit introuvable.' })
      return json(res, 200, { data: productResource(product) })
    }

    if (pathName === '/api/bundles' || pathName === '/bundles') {
      const active = BUNDLES
        .filter((b) => b.is_active)
        .sort((a, b) => (b.is_featured ? 1 : 0) - (a.is_featured ? 1 : 0))
        .map(bundleResource)
      return json(res, 200, { data: active })
    }

    if (pathName === '/api/reviews' || pathName === '/reviews') return json(res, 200, { data: REVIEWS })
    if (pathName === '/api/gallery' || pathName === '/gallery') return json(res, 200, { data: GALLERY })

    if (pathName === '/' || pathName === '/api') {
      return json(res, 200, {
        name: 'Planet Kids API (simulation Node)',
        status: 'ok',
        endpoints: ['/api/settings', '/api/categories', '/api/products', '/api/reviews', '/api/gallery', 'POST /api/orders', 'POST /api/auth/login', '/api/admin/*'],
      })
    }

    // Les routes auth/admin (GET /auth/me, GET /admin/products…) sont
    // traitées plus bas : on ne renvoie pas 404 ici.
    if (!/^\/(?:api\/)?(auth|admin)\//.test(pathName)) {
      return json(res, 404, { message: 'Not Found' })
    }
  }

  const rawBody = await readBody(req)
  const contentType = req.headers['content-type'] || ''

  let body = {}
  let files = null

  if (method === 'POST' || method === 'PUT' || method === 'PATCH') {
    if (contentType.includes('multipart/form-data')) {
      const parsed = parseMultipart(rawBody, contentType)
      if (parsed) {
        body = parsed.fields
        files = parsed.files
      }
    } else {
      try {
        body = rawBody.length ? JSON.parse(rawBody.toString('utf8')) : {}
      } catch {
        return json(res, 400, { message: 'JSON invalide.' })
      }
    }
  }

  // Substitution de méthode HTML (multipart ne supporte pas PUT)
  const effectiveMethod = body._method ? String(body._method).toUpperCase() : method

  /* ---------- Contrôle du mode maintenance (SIMULATION UNIQUEMENT) ----------
   * Équivalent mock de `php artisan shop:down` / `shop:up` :
   *   curl -X POST http://127.0.0.1:8000/api/maintenance \
   *        -H "Content-Type: application/json" -d '{"state":"on"}'
   */
  if (pathName === '/api/maintenance' && method === 'POST') {
    fs.mkdirSync(path.dirname(DOWN_FILE), { recursive: true })

    if (body.state === 'on') {
      fs.writeFileSync(DOWN_FILE, JSON.stringify({
        message: body.message || null,
        retry: Number(body.retry) || 300,
        since: new Date().toISOString(),
      }, null, 2))
      console.log("[maintenance] Mode maintenance ACTIVÉ — page d'attente affichée")
      return json(res, 200, { data: { maintenance: true } })
    }

    if (fs.existsSync(DOWN_FILE)) fs.unlinkSync(DOWN_FILE)
    console.log('[maintenance] Boutique réactivée')
    return json(res, 200, { data: { maintenance: false } })
  }

  /* ---------- POST /api/orders (public) ---------- */
  if (method === 'POST' && (pathName === '/api/orders' || pathName === '/orders')) {
    const errors = validateOrder(body)
    if (Object.keys(errors).length > 0) {
      return json(res, 422, { message: 'Les données fournies sont invalides.', errors })
    }

    const lines = []
    let total = 0
    let lineId = 1
    for (const item of body.items) {
      const quantity = Number(item.quantity) || 1

      // Lot : prix du lot appliqué
      if (item.bundle_id !== undefined && item.bundle_id !== null) {
        const bundle = BUNDLES.find((b) => b.id === Number(item.bundle_id))
        if (!bundle) continue
        const lineTotal = bundle.price * quantity
        const resource = bundleResource(bundle)
        total += lineTotal
        lines.push({
          id: lineId++,
          name: bundle.name_fr,
          quantity,
          lineTotal,
          regularTotal: resource.regular_total * quantity,
        })
        continue
      }

      // Produit : promo « -X% dès N achetés » appliquée
      const product = PRODUCTS.find((p) => p.id === item.product_id)
      if (!product) continue
      const unitPrice = unitPriceFor(product, quantity)
      const lineTotal = unitPrice * quantity
      total += lineTotal
      lines.push({
        id: lineId++,
        product,
        name: product.name_fr,
        quantity,
        lineTotal,
        regularTotal: product.price * quantity,
      })
    }
    if (lines.length === 0) {
      return json(res, 422, { message: 'Aucun produit valide dans la commande.' })
    }

    const lang = body.lang === 'ar' ? 'ar' : 'fr'
    const order = {
      id: nextOrderId++,
      reference: 'DL-' + crypto.randomBytes(3).toString('hex').toUpperCase(),
      customer_name: body.customer_name.trim(),
      customer_phone: body.customer_phone.trim(),
      wilaya: body.wilaya.trim(),
      notes: (body.notes || '').toString().trim() || null,
      total,
      status: 'nouvelle',
      created_at: new Date().toISOString(),
      lines,
    }
    orders.push(order)

    const message = buildWhatsAppMessage(order, lines, lang)
    const waUrl = `https://wa.me/${SETTINGS.whatsapp_number}?text=${encodeURIComponent(message)}`

    console.log(`[order] ${order.reference} — ${order.customer_name} — ${formatDa(total)} DA (${lines.length} article·s)`)

    // 📧 notification e-mail au vendeur (voir App\Notifications\OrderPlaced côté Laravel)
    simulateSellerEmail(order)

    return json(res, 201, {
      data: {
        reference: order.reference,
        customer_name: order.customer_name,
        wilaya: order.wilaya,
        total: order.total,
        items_count: lines.reduce((s, l) => s + l.quantity, 0),
        status: order.status,
        whatsapp_message: message,
        whatsapp_url: waUrl,
      },
    })
  }

  /* ---------- Authentification (Sanctum simulé) ---------- */

  if (method === 'POST' && (pathName === '/api/auth/login' || pathName === '/auth/login')) {
    const email = String(body.email || '').trim().toLowerCase()
    const password = String(body.password || '')

    const errors = {}
    if (!email) errors.email = ['Le champ email est obligatoire.']
    if (!password) errors.password = ['Le champ mot de passe est obligatoire.']
    if (Object.keys(errors).length) return json(res, 422, { message: 'Les données fournies sont invalides.', errors })

    if (email !== ADMIN.email || password !== ADMIN.password) {
      return json(res, 422, {
        message: 'Les données fournies sont invalides.',
        errors: { email: ['Ces identifiants ne correspondent pas à nos enregistrements.'] },
      })
    }

    const token = crypto.randomBytes(20).toString('hex')
    tokens.set(token, ADMIN)

    const { password: _pw, ...safeUser } = ADMIN
    return json(res, 200, { data: { token, user: safeUser } })
  }

  if (pathName === '/api/auth/me' || pathName === '/auth/me') {
    const user = requireAuth(req, res)
    if (!user) return
    const { password: _pw, ...safeUser } = user
    return json(res, 200, { data: safeUser })
  }

  /* ---------- Admin : réglages de la boutique ---------- */
  if (pathName === '/api/admin/settings' && (method === 'GET' || effectiveMethod === 'PUT')) {
    if (!requireAuth(req, res)) return

    if (method === 'GET') {
      return json(res, 200, { data: SETTINGS })
    }

    // PUT : mise à jour
    const allowed = ['whatsapp_number','seller_email','shop_name_fr','shop_name_ar','shop_address_fr','shop_address_ar','shop_hours_fr','shop_hours_ar','shop_phone_display','shop_email','hero_image','maps_query','whatsapp_group_url','instagram_url','facebook_url','tiktok_url']
    for (const key of allowed) {
      if (body[key] !== undefined && body[key] !== null && body[key] !== '') {
        SETTINGS[key] = String(body[key])
      }
    }
    console.log('[admin] Réglages mis à jour ✓')
    return json(res, 200, { data: SETTINGS })
  }

  /* ---------- Admin : changement de mot de passe ---------- */
  if (pathName === '/api/admin/change-password' && method === 'POST') {
    if (!requireAuth(req, res)) return
    if (body.new_password !== body.new_password_confirmation) {
      return json(res, 422, { message: 'Les données fournies sont invalides.', errors: { new_password: ['La confirmation ne correspond pas.'] } })
    }
    if (String(body.new_password || '').length < 8) {
      return json(res, 422, { message: 'Les données fournies sont invalides.', errors: { new_password: ['Le mot de passe doit contenir au moins 8 caractères.'] } })
    }
    if (body.current_password !== ADMIN.password) {
      return json(res, 422, { message: 'Les données fournies sont invalides.', errors: { current_password: ['Le mot de passe actuel est incorrect.'] } })
    }
    ADMIN.password = body.new_password
    console.log('[admin] Mot de passe changé ✓')
    return json(res, 200, { data: { changed: true } })
  }

  /* ---------- Admin : suppression en masse produits ---------- */
  if (pathName === '/api/admin/products/bulk-delete' && method === 'POST') {
    if (!requireAuth(req, res)) return
    const ids = (body.ids || []).map(Number).filter(Number.isInteger)
    if (ids.length === 0) return json(res, 422, { message: 'Aucun identifiant fourni.' })
    const before = PRODUCTS.length
    for (let i = PRODUCTS.length - 1; i >= 0; i--) {
      if (ids.includes(PRODUCTS[i].id)) PRODUCTS.splice(i, 1)
    }
    const deleted = before - PRODUCTS.length
    console.log(`[admin] Suppression en masse : ${deleted} produit(s)`)
    return json(res, 200, { data: { deleted } })
  }

  /* ---------- Admin : suppression en masse lots ---------- */
  if (pathName === '/api/admin/bundles/bulk-delete' && method === 'POST') {
    if (!requireAuth(req, res)) return
    const ids = (body.ids || []).map(Number).filter(Number.isInteger)
    if (ids.length === 0) return json(res, 422, { message: 'Aucun identifiant fourni.' })
    const before = BUNDLES.length
    for (let i = BUNDLES.length - 1; i >= 0; i--) {
      if (ids.includes(BUNDLES[i].id)) BUNDLES.splice(i, 1)
    }
    const deleted = before - BUNDLES.length
    console.log(`[admin] Suppression en masse : ${deleted} lot(s)`)
    return json(res, 200, { data: { deleted } })
  }

  if (method === 'POST' && (pathName === '/api/auth/logout' || pathName === '/auth/logout')) {
    const user = requireAuth(req, res)
    if (!user) return
    const header = req.headers['authorization'] || ''
    const match = header.match(/^Bearer\s+(.+)$/i)
    if (match) tokens.delete(match[1])
    return json(res, 200, { data: { logged_out: true } })
  }

  /* ---------- Administration ---------- */

  // Capacités de l'instance (Laravel : Bunny configuré ou stockage local)
  if (pathName === '/api/admin/config' || pathName === '/admin/config') {
    if (!requireAuth(req, res)) return
    return json(res, 200, { data: { image_driver: 'local', webp: true } })
  }

  // Catégories côté admin (disponibles même pendant la maintenance)
  const adminCategoryMatch = pathName.match(/^\/(?:api\/)?admin\/categories(?:\/(\d+))?$/)

  if (adminCategoryMatch) {
    if (!requireAuth(req, res)) return
    const categoryId = adminCategoryMatch[1] ? Number(adminCategoryMatch[1]) : null

    if (method === 'GET' && !categoryId) {
      return json(res, 200, { data: orderedCategories().map(categoryResource) })
    }

    if (method === 'POST' && !categoryId) {
      const errors = {}
      if (!body.name_fr || !String(body.name_fr).trim()) errors.name_fr = ['Le nom (français) est obligatoire.']
      if (!body.name_ar || !String(body.name_ar).trim()) errors.name_ar = ['الاسم (عربي) مطلوب.']

      // Catégorie parent : null (principale) ou identifiant d'une principale.
      let parentId = null
      if (body.parent_id !== undefined && body.parent_id !== null && body.parent_id !== '') {
        parentId = Number(body.parent_id)
        const parent = CATEGORIES.find((c) => c.id === parentId)
        if (!parent) errors.parent_id = ['La catégorie parent est introuvable.']
        else if (parent.parent_id) errors.parent_id = ['Le parent est déjà une sous-catégorie (2 niveaux maximum).']
      }

      if (Object.keys(errors).length) return json(res, 422, { message: 'Les données fournies sont invalides.', errors })

      let slug = String(body.slug || '').trim() || slugifyCsv(body.name_fr)
      let n = 1
      while (CATEGORIES.some((c) => c.slug === slug)) slug = `${slugifyCsv(body.name_fr)}-${++n}`

      const category = {
        id: Math.max(...CATEGORIES.map((c) => c.id)) + 1,
        parent_id: parentId,
        slug,
        name_fr: String(body.name_fr).trim(),
        name_ar: String(body.name_ar).trim(),
        description_fr: String(body.description_fr || '').trim() || null,
        description_ar: String(body.description_ar || '').trim() || null,
        position: Number(body.position) || (CATEGORIES.length + 1) * 10,
      }
      CATEGORIES.push(category)
      console.log(`[admin] Catégorie créée : ${category.name_fr} (${category.slug})`)
      return json(res, 201, { data: categoryResource(category) })
    }

    if ((effectiveMethod === 'PUT' || effectiveMethod === 'PATCH') && categoryId) {
      const category = CATEGORIES.find((c) => c.id === categoryId)
      if (!category) return json(res, 404, { message: 'Catégorie introuvable.' })

      if (body.name_fr !== undefined) category.name_fr = String(body.name_fr).trim()
      if (body.name_ar !== undefined) category.name_ar = String(body.name_ar).trim()
      if (body.description_fr !== undefined) category.description_fr = String(body.description_fr).trim() || null
      if (body.description_ar !== undefined) category.description_ar = String(body.description_ar).trim() || null
      if (body.position !== undefined) category.position = Number(body.position) || category.position
      if (body.slug !== undefined && String(body.slug).trim()) {
        const wanted = String(body.slug).trim()
        if (!CATEGORIES.some((c) => c.slug === wanted && c.id !== categoryId)) category.slug = wanted
      }

      // Catégorie parent : null (devient principale) ou une principale.
      if (body.parent_id !== undefined) {
        let parentId = null
        if (body.parent_id !== null && body.parent_id !== '') {
          parentId = Number(body.parent_id)
          const parent = CATEGORIES.find((c) => c.id === parentId)
          if (!parent) {
            return json(res, 422, { message: 'La catégorie parent est introuvable.', errors: { parent_id: ['La catégorie parent est introuvable.'] } })
          }
          if (parent.parent_id) {
            return json(res, 422, { message: 'Le parent est déjà une sous-catégorie (2 niveaux maximum).', errors: { parent_id: ['Le parent est déjà une sous-catégorie (2 niveaux maximum).'] } })
          }
          if (parent.id === categoryId) {
            return json(res, 422, { message: 'Une catégorie ne peut pas être son propre parent.', errors: { parent_id: ['Une catégorie ne peut pas être son propre parent.'] } })
          }
        }
        category.parent_id = parentId
      }

      console.log(`[admin] Catégorie mise à jour : ${category.name_fr} (#${category.id})`)
      return json(res, 200, { data: categoryResource(category) })
    }

    if (effectiveMethod === 'DELETE' && categoryId) {
      const index = CATEGORIES.findIndex((c) => c.id === categoryId)
      if (index === -1) return json(res, 404, { message: 'Catégorie introuvable.' })

      const productCount = PRODUCTS.filter((p) => p.category_id === categoryId).length
      if (productCount > 0) {
        const name = CATEGORIES[index].name_fr
        return json(res, 422, {
          message: `Impossible de supprimer « ${name} » : ${productCount} produit(s) y sont rattachés. Déplacez ou supprimez d'abord ces produits.`,
        })
      }

      const childCount = CATEGORIES.filter((c) => c.parent_id === categoryId).length
      if (childCount > 0) {
        const name = CATEGORIES[index].name_fr
        return json(res, 422, {
          message: `Impossible de supprimer « ${name} » : elle possède ${childCount} sous-catégorie(s). Supprimez d'abord ses sous-catégories.`,
        })
      }

      const [removed] = CATEGORIES.splice(index, 1)
      console.log(`[admin] Catégorie supprimée : ${removed.name_fr} (#${removed.id})`)
      return json(res, 200, { data: { deleted: true, slug: removed.slug } })
    }
  }

  /* ---------- Admin : lots (bundles) ---------- */
  const adminBundleMatch = pathName.match(/^\/(?:api\/)?admin\/bundles(?:\/(\d+))?$/)

  if (adminBundleMatch) {
    if (!requireAuth(req, res)) return
    const bundleId = adminBundleMatch[1] ? Number(adminBundleMatch[1]) : null

    if (method === 'GET' && !bundleId) {
      let list = [...BUNDLES]
      const search = (query.get('search') || '').trim().toLowerCase()
      if (search) {
        list = list.filter((b) =>
          [b.name_fr, b.name_ar, b.slug].some((v) => (v || '').toLowerCase().includes(search))
        )
      }
      return json(res, 200, { data: list.map(bundleResource) })
    }

    if (method === 'POST' && !bundleId) {
      const errors = {}
      if (!body.name_fr || !String(body.name_fr).trim()) errors.name_fr = ['Le nom (français) est obligatoire.']
      if (!body.name_ar || !String(body.name_ar).trim()) errors.name_ar = ['الاسم (عربي) مطلوب.']
      if (!Number.isFinite(Number(body.price)) || Number(body.price) < 0) errors.price = ['Le prix du lot est obligatoire.']
      const items = Array.isArray(body.items) ? body.items.filter((i) => i && productById(Number(i.product_id))) : []
      if (items.length === 0) errors.items = ['Le lot doit contenir au moins un produit.']
      if (Object.keys(errors).length) return json(res, 422, { message: 'Les données fournies sont invalides.', errors })

      const slugBase = String(body.slug || '').trim() || slugifyCsv(body.name_fr)
      let slug = slugBase
      let n = 1
      while (BUNDLES.some((b) => b.slug === slug)) slug = `${slugBase}-${++n}`

      const bundle = {
        id: nextBundleId++,
        slug,
        name_fr: String(body.name_fr).trim(),
        name_ar: String(body.name_ar).trim(),
        description_fr: String(body.description_fr || '').trim() || null,
        description_ar: String(body.description_ar || '').trim() || null,
        price: Math.round(Number(body.price)),
        image: String(body.image || '').trim() || null,
        is_active: body.is_active === undefined ? true : ['1', 'true', true].includes(body.is_active),
        is_featured: ['1', 'true', true].includes(body.is_featured),
        position: BUNDLES.length * 10 + 10,
        items: items.map((i) => ({ product_id: Number(i.product_id), quantity: Math.max(1, Math.min(99, Number(i.quantity) || 1)) })),
      }
      BUNDLES.push(bundle)
      console.log(`[admin] Lot créé : ${bundle.name_fr} (${bundle.slug})`)
      return json(res, 201, { data: bundleResource(bundle) })
    }

    if ((effectiveMethod === 'PUT' || effectiveMethod === 'PATCH') && bundleId) {
      const bundle = BUNDLES.find((b) => b.id === bundleId)
      if (!bundle) return json(res, 404, { message: 'Lot introuvable.' })

      if (body.name_fr !== undefined) bundle.name_fr = String(body.name_fr).trim()
      if (body.name_ar !== undefined) bundle.name_ar = String(body.name_ar).trim()
      if (body.description_fr !== undefined) bundle.description_fr = String(body.description_fr).trim() || null
      if (body.description_ar !== undefined) bundle.description_ar = String(body.description_ar).trim() || null
      if (body.price !== undefined && Number.isFinite(Number(body.price))) bundle.price = Math.round(Number(body.price))
      if (body.image !== undefined) bundle.image = String(body.image).trim() || null
      if (body.is_active !== undefined) bundle.is_active = ['1', 'true', true].includes(body.is_active)
      if (body.is_featured !== undefined) bundle.is_featured = ['1', 'true', true].includes(body.is_featured)
      if (Array.isArray(body.items)) {
        bundle.items = body.items
          .filter((i) => i && productById(Number(i.product_id)))
          .map((i) => ({ product_id: Number(i.product_id), quantity: Math.max(1, Math.min(99, Number(i.quantity) || 1)) }))
      }

      console.log(`[admin] Lot mis à jour : ${bundle.name_fr} (#${bundle.id})`)
      return json(res, 200, { data: bundleResource(bundle) })
    }

    if (effectiveMethod === 'DELETE' && bundleId) {
      const index = BUNDLES.findIndex((b) => b.id === bundleId)
      if (index === -1) return json(res, 404, { message: 'Lot introuvable.' })
      const [removed] = BUNDLES.splice(index, 1)
      console.log(`[admin] Lot supprimé : ${removed.name_fr} (#${removed.id})`)
      return json(res, 200, { data: { deleted: true, slug: removed.slug } })
    }
  }

  /* ---------- Admin : import CSV en masse ---------- */
  if (/^\/(?:api\/)?admin\/products\/import$/.test(pathName) && method === 'POST') {
    if (!requireAuth(req, res)) return

    let csvText = null
    if (files && files.file) {
      csvText = files.file.data.toString('utf8')
    } else if (body.csv) {
      csvText = String(body.csv)
    }

    if (!csvText || !csvText.trim()) {
      return json(res, 422, { message: 'Le fichier CSV est vide ou illisible.' })
    }

    const rows = parseCsv(csvText)
    if (rows.length === 0) {
      return json(res, 422, { message: 'Le fichier CSV est vide ou illisible.' })
    }

    const toBool = (v) => ['1', 'true', 'vrai', 'oui', 'yes', 'actif'].includes(String(v ?? '').trim().toLowerCase())
    let created = 0
    let updated = 0
    const errors = []

    rows.forEach((row, index) => {
      const line = index + 2
      const nameFr = String(row.name_fr || '').trim()
      const nameAr = String(row.name_ar || '').trim()
      const price = Number(row.price)

      if (!nameFr || !nameAr) { errors.push(`Ligne ${line} : name_fr et name_ar sont obligatoires.`); return }
      if (!Number.isFinite(price) || price < 0) { errors.push(`Ligne ${line} : prix invalide (« ${row.price} »).`); return }

      const categoryKey = String(row.category || '').trim()
      const category = CATEGORIES.find((c) => c.slug === categoryKey || c.name_fr === categoryKey || c.name_ar === categoryKey) || CATEGORIES[0]

      let slug = String(row.slug || '').trim() || slugifyCsv(nameFr)

      const existing = PRODUCTS.find((p) => p.slug === slug)
      const payload = {
        category_id: category.id,
        name_fr: nameFr,
        name_ar: nameAr,
        description_fr: String(row.description_fr || '').trim(),
        description_ar: String(row.description_ar || '').trim(),
        price: Math.round(price),
        is_active: row.is_active === undefined || row.is_active === '' ? true : toBool(row.is_active),
        is_featured: toBool(row.is_featured || '0'),
      }
      const image = String(row.image || '').trim()
      if (image) payload.image = image

      if (existing) {
        Object.assign(existing, payload)
        updated++
      } else {
        let s = slug
        let n = 1
        while (PRODUCTS.some((p) => p.slug === s)) s = `${slug}-${++n}`
        slug = s
        PRODUCTS.push({
          id: nextProductId++,
          slug,
          ...payload,
          created_at: new Date().toISOString(),
        })
        created++
      }
    })

    console.log(`[admin] Import CSV : ${created} créé(s), ${updated} mis à jour, ${errors.length} erreur(s)`)
    return json(res, 200, { data: { created, updated, errors, rows: rows.length } })
  }

  /* ---------- Admin : export CSV ---------- */
  if (/^\/(?:api\/)?admin\/products\/export$/.test(pathName) && method === 'GET') {
    if (!requireAuth(req, res)) return

    const cell = (v) => {
      const s = String(v ?? '').replace(/"/g, '""')
      return /[;"\n]/.test(s) ? `"${s}"` : s
    }
    const lines = ['category;name_fr;name_ar;description_fr;description_ar;price;image;slug;is_active;is_featured']
    for (const p of PRODUCTS) {
      lines.push([
        categoryById(p.category_id)?.slug || '',
        cell(p.name_fr), cell(p.name_ar), cell(p.description_fr), cell(p.description_ar),
        p.price, cell(p.image), p.slug, p.is_active ? 1 : 0, p.is_featured ? 1 : 0,
      ].join(';'))
    }

    res.writeHead(200, {
      'Content-Type': 'text/csv; charset=UTF-8',
      'Content-Disposition': 'attachment; filename="darlila-produits.csv"',
      'Access-Control-Allow-Origin': '*',
    })
    return res.end(lines.join('\n'))
  }

  const adminProductsMatch = pathName.match(/^\/(?:api\/)?admin\/products(?:\/(\d+))?$/)

  if (adminProductsMatch) {
    if (!requireAuth(req, res)) return
    const productId = adminProductsMatch[1] ? Number(adminProductsMatch[1]) : null

    // GET : liste paginée (actifs + inactifs) + recherche serveur
    if (method === 'GET' && !productId) {
      let products = [...PRODUCTS]

      const category = query.get('category')
      if (category) {
        const cat = CATEGORIES.find((c) => c.slug === category)
        const ids = cat ? categoryFamilyIds(cat) : null
        products = ids ? products.filter((p) => ids.has(p.category_id)) : []
      }

      const search = (query.get('search') || '').trim().toLowerCase()
      if (search) {
        products = products.filter((p) =>
          [p.name_fr, p.name_ar, p.slug].some((v) => (v || '').toLowerCase().includes(search))
        )
      }

      const perPage = Math.min(Math.max(parseInt(query.get('per_page') || '20', 10), 5), 100)
      const page = Math.max(parseInt(query.get('page') || '1', 10), 1)
      const total = products.length
      const lastPage = Math.max(Math.ceil(total / perPage), 1)
      const current = Math.min(page, lastPage)
      const slice = products.slice((current - 1) * perPage, current * perPage)

      return json(res, 200, {
        data: slice.map(productResource),
        meta: {
          current_page: current,
          from: slice.length ? (current - 1) * perPage + 1 : null,
          last_page: lastPage,
          per_page: perPage,
          to: slice.length ? (current - 1) * perPage + slice.length : null,
          total,
        },
      })
    }

    // POST : création
    if (method === 'POST' && !productId) {
      const { payload, error, message } = productPayloadFrom(body, files)
      if (error) return json(res, 422, { message: 'Les données fournies sont invalides.', errors: { [error]: [message] } })

      const errors = validateProductPayload(payload, null)
      if (payload.image_url) { /* déjà validé */ }
      if (Object.keys(errors).length) {
        return json(res, 422, { message: 'Les données fournies sont invalides.', errors })
      }
      if (!payload.name_fr || !payload.name_ar || payload.price === undefined || payload.category_id === undefined) {
        const errors = {}
        if (!payload.name_fr) errors.name_fr = ['Le nom (français) est obligatoire.']
        if (!payload.name_ar) errors.name_ar = ['الاسم (عربي) مطلوب.']
        if (payload.price === undefined) errors.price = ['Le prix est obligatoire.']
        if (payload.category_id === undefined) errors.category_id = ['La catégorie est obligatoire.']
        return json(res, 422, { message: 'Les données fournies sont invalides.', errors })
      }
      if (!payload.image_path && !payload.image_url) {
        return json(res, 422, {
          message: 'Les données fournies sont invalides.',
          errors: { image: ['Une image (fichier ou URL) est requise.'] },
        })
      }

      const product = {
        id: nextProductId++,
        category_id: payload.category_id,
        slug: uniqueSlug(slugify(payload.slug || payload.name_fr), null),
        name_fr: payload.name_fr,
        name_ar: payload.name_ar,
        description_fr: payload.description_fr || '',
        description_ar: payload.description_ar || '',
        price: payload.price,
        image: payload.image_path || payload.image_url,
        is_featured: payload.is_featured === true,
        is_active: payload.is_active !== false,
        created_at: new Date().toISOString(),
      }
      PRODUCTS.push(product)
      console.log(`[admin] Produit créé : ${product.name_fr} (${product.slug})`)
      return json(res, 201, { data: productResource(product) })
    }

    // PUT/PATCH (avec spoof éventuel) : mise à jour
    if ((effectiveMethod === 'PUT' || effectiveMethod === 'PATCH') && productId) {
      const product = PRODUCTS.find((p) => p.id === productId)
      if (!product) return json(res, 404, { message: 'Produit introuvable.' })

      const { payload, error, message } = productPayloadFrom(body, files)
      if (error) return json(res, 422, { message: 'Les données fournies sont invalides.', errors: { [error]: [message] } })

      const errors = validateProductPayload(payload, productId)
      if (Object.keys(errors).length) {
        return json(res, 422, { message: 'Les données fournies sont invalides.', errors })
      }

      Object.assign(product, payload)
      if (payload.slug) product.slug = uniqueSlug(slugify(payload.slug), productId)
      if (payload.image_path) product.image = payload.image_path
      else if (payload.image_url) product.image = payload.image_url
      delete product.image_path
      delete product.image_url

      console.log(`[admin] Produit mis à jour : ${product.name_fr} (#${product.id})`)
      return json(res, 200, { data: productResource(product) })
    }

    // DELETE : suppression
    if (effectiveMethod === 'DELETE' && productId) {
      const index = PRODUCTS.findIndex((p) => p.id === productId)
      if (index === -1) return json(res, 404, { message: 'Produit introuvable.' })

      const [removed] = PRODUCTS.splice(index, 1)
      console.log(`[admin] Produit supprimé : ${removed.name_fr} (#${removed.id})`)
      return json(res, 200, { data: { deleted: true, slug: removed.slug } })
    }
  }

  /* ---------- Admin : commandes ---------- */

  if (pathName === '/api/admin/orders' || pathName === '/admin/orders') {
    if (!requireAuth(req, res)) return

    if (method === 'GET') {
      let list = [...orders].sort((a, b) => b.id - a.id)
      const status = query.get('status')
      if (status) list = list.filter((o) => o.status === status)
      return json(res, 200, { data: list.map(orderResource) })
    }
  }

  /* ---------- Admin : export CSV des commandes (comptabilité) ---------- */
  if (/^\/(?:api\/)?admin\/orders\/export$/.test(pathName) && method === 'GET') {
    if (!requireAuth(req, res)) return

    const status = query.get('status')
    let list = [...orders].sort((a, b) => a.id - b.id)
    if (status) list = list.filter((o) => o.status === status)

    const cell = (v) => {
      const s = String(v ?? '').replace(/"/g, '""')
      return /[;"\n\r]/.test(s) ? `"${s}"` : s
    }
    const formatDate = (iso) => {
      const d = new Date(iso)
      const p = (n) => String(n).padStart(2, '0')
      return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()} ${p(d.getHours())}:${p(d.getMinutes())}`
    }

    const lines = ['reference;date;client;telephone;wilaya;articles;detail_articles;total_da;statut']
    for (const o of list) {
      lines.push([
        o.reference,
        formatDate(o.created_at),
        cell(o.customer_name),
        o.customer_phone,
        cell(o.wilaya),
        o.lines.reduce((s, l) => s + l.quantity, 0),
        cell(o.lines.map((l) => `${l.product.name_fr} x${l.quantity}`).join(', ')),
        o.total,
        o.status,
      ].join(';'))
    }

    const now = new Date()
    const p = (n) => String(n).padStart(2, '0')
    const filename = `darlila-commandes-${now.getFullYear()}${p(now.getMonth() + 1)}${p(now.getDate())}-${p(now.getHours())}${p(now.getMinutes())}.csv`

    res.writeHead(200, {
      'Content-Type': 'text/csv; charset=UTF-8',
      'Content-Disposition': `attachment; filename="${filename}"`,
      'Access-Control-Allow-Origin': '*',
    })
    return res.end(lines.join('\n'))
  }

  const orderStatusMatch = pathName.match(/^\/(?:api\/)?admin\/orders\/(\d+)\/status$/)
  if (orderStatusMatch && (effectiveMethod === 'PATCH' || effectiveMethod === 'PUT')) {
    if (!requireAuth(req, res)) return

    const order = orders.find((o) => o.id === Number(orderStatusMatch[1]))
    if (!order) return json(res, 404, { message: 'Commande introuvable.' })

    const allowed = ['nouvelle', 'confirmee', 'expediee', 'livree', 'annulee']
    if (!allowed.includes(body.status)) {
      return json(res, 422, {
        message: 'Les données fournies sont invalides.',
        errors: { status: ['Statut invalide.'] },
      })
    }

    order.status = body.status
    console.log(`[admin] Commande ${order.reference} → ${order.status}`)
    return json(res, 200, { data: orderResource(order) })
  }

  return json(res, 404, { message: 'Not Found' })
})

server.listen(PORT, '0.0.0.0', () => {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true })
  console.log(`API de simulation Planet Kids démarrée sur http://127.0.0.1:${PORT}`)
  console.log(`Admin (Sanctum simulé) : ${ADMIN.email} / ${ADMIN.password}`)
  console.log('(Endpoints identiques à l\'API Laravel — voir backend-laravel/routes/api.php)')
})
