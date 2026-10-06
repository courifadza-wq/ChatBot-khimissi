const ExcelJS = require('./frontend-vue/node_modules/exceljs');

async function buildModelExcel() {
  const workbook = new ExcelJS.Workbook();
  workbook.creator = 'Planet Kids Admin';
  workbook.created = new Date();

  // =========================================================================
  // ONGLET 1 : MODÈLE PRODUITS (LE TABLEAU PRINCIPAL)
  // =========================================================================
  const sheet = workbook.addWorksheet('Modèle Produits', {
    views: [{ state: 'frozen', xSplit: 0, ySplit: 1 }]
  });

  sheet.columns = [
    { header: 'category_parent', key: 'category_parent', width: 28 },
    { header: 'category', key: 'category', width: 25 },
    { header: 'name_fr', key: 'name_fr', width: 35 },
    { header: 'name_ar', key: 'name_ar', width: 35 },
    { header: 'description_fr', key: 'description_fr', width: 45 },
    { header: 'description_ar', key: 'description_ar', width: 45 },
    { header: 'price', key: 'price', width: 15 },
    { header: 'image', key: 'image', width: 65 },
    { header: 'is_active', key: 'is_active', width: 12 },
    { header: 'is_featured', key: 'is_featured', width: 12 }
  ];

  // En-tête (Ligne 1)
  const headerRow = sheet.getRow(1);
  headerRow.height = 28;
  headerRow.eachCell((cell) => {
    cell.font = { name: 'Calibri', size: 11, bold: true, color: { argb: 'FFFFFF' } };
    cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: '2D3590' } };
    cell.alignment = { vertical: 'middle', horizontal: 'center' };
    cell.border = {
      top: { style: 'thin', color: { argb: '1E2360' } },
      left: { style: 'thin', color: { argb: '1E2360' } },
      bottom: { style: 'medium', color: { argb: 'EA2F90' } },
      right: { style: 'thin', color: { argb: '1E2360' } }
    };
  });

  // Exemples pré-remplis
  const sampleProducts = [
    { category_parent: 'Chaussures_Accessoires', category: 'chaussures', name_fr: 'Baskets Bébé Cuir Souple', name_ar: 'حذاء رضع من الجلد الناعم', description_fr: 'Baskets confortables en cuir souple pour premiers pas.', description_ar: 'حذاء مريح من الجلد الناعم للخطوات الأولى.', price: 2800, image: 'https://khemicishop.b-cdn.net/produits/baskets-bebe.jpg', is_active: 1, is_featured: 1 },
    { category_parent: 'Puericulture', category: 'repas-biberons', name_fr: 'Biberon Anti-Colique 260ml', name_ar: 'رضّاعة مضادة للمغص 260 مل', description_fr: 'Biberon avec tétine en silicone médicale sans BPA.', description_ar: 'رضّاعة مع حلمة سيليكون طبية خالية من BPA.', price: 1450, image: 'https://khemicishop.b-cdn.net/produits/biberon-260ml.jpg', is_active: 1, is_featured: 0 },
    { category_parent: 'Jouets_Eveil', category: 'jouets', name_fr: 'Ours en Peluche Doux 30cm', name_ar: 'دب من القطيفة الناعمة 30 سم', description_fr: 'Peluche douce hypoallergénique lavable en machine.', description_ar: 'دمية قطيفة ناعمة قابلة للغسل في الغسالة.', price: 3200, image: 'https://khemicishop.b-cdn.net/produits/ours-peluche.jpg', is_active: 1, is_featured: 1 },
    { category_parent: 'Cadeaux', category: 'naissance', name_fr: 'Coffret Cadeau Naissance 5 Pièces', name_ar: 'طقم هدية مولود جديد 5 قطع', description_fr: 'Contient bonnet, pyjama, bavette, doudou et chaussons.', description_ar: 'يحتوي على طاقية، بيجامة، مريلة، لعبة وحذاء.', price: 5900, image: 'https://khemicishop.b-cdn.net/produits/coffret-naissance.jpg', is_active: 1, is_featured: 1 },
    { category_parent: 'Chaussures_Accessoires', category: 'sacs', name_fr: 'Sac à Langer Multifonction', name_ar: 'حقيبة حفاضات متعددة الوظائف', description_fr: 'Sac grand volume avec compartiments isothermes pour biberons.', description_ar: 'حقيبة واسعة مع أقسام عازلة للحرارة للرضّاعات.', price: 4800, image: 'https://khemicishop.b-cdn.net/produits/sac-langer.jpg', is_active: 1, is_featured: 0 }
  ];

  sampleProducts.forEach((p) => sheet.addRow(p));

  // =========================================================================
  // ONGLET 2 : SOURCE DES CATÉGORIES (Alimente les listes déroulantes)
  // =========================================================================
  const sourceSheet = workbook.addWorksheet('Source Catégories');

  sourceSheet.columns = [
    { header: 'Catégories Mères', key: 'parents', width: 28 },
    { header: '', key: 'spacer', width: 3 },
    { header: 'Chaussures_Accessoires', key: 'chaussures', width: 25 },
    { header: 'Puericulture', key: 'puericulture', width: 25 },
    { header: 'Jouets_Eveil', key: 'jouets', width: 25 },
    { header: 'Cadeaux', key: 'cadeaux', width: 25 }
  ];

  // En-tête stylisé
  const sHeader = sourceSheet.getRow(1);
  sHeader.height = 26;
  sHeader.eachCell((cell, colNumber) => {
    if (colNumber === 2) return;
    cell.font = { name: 'Calibri', size: 11, bold: true, color: { argb: 'FFFFFF' } };
    cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'EA2F90' } };
    cell.alignment = { vertical: 'middle', horizontal: 'center' };
  });

  const parents = ['Chaussures_Accessoires', 'Puericulture', 'Jouets_Eveil', 'Cadeaux'];
  const subChaussures = ['chaussures', 'sacs', 'bonnets-chapeaux', 'chaussettes', 'accessoires-cheveux'];
  const subPuericulture = ['repas-biberons', 'sommeil', 'toilette-soins', 'promenade-sorties', 'equipement-bebe'];
  const subJouets = ['jouets', 'eveil', 'peluches'];
  const subCadeaux = ['naissance', 'anniversaire', 'coffrets-cadeaux'];

  const maxRows = Math.max(parents.length, subChaussures.length, subPuericulture.length, subJouets.length, subCadeaux.length);

  for (let i = 0; i < maxRows; i++) {
    sourceSheet.addRow({
      parents: parents[i] || '',
      spacer: '',
      chaussures: subChaussures[i] || '',
      puericulture: subPuericulture[i] || '',
      jouets: subJouets[i] || '',
      cadeaux: subCadeaux[i] || ''
    });
  }

  sourceSheet.eachRow((row, rn) => {
    if (rn > 1) {
      row.eachCell((cell) => {
        cell.border = {
          top: { style: 'thin', color: { argb: 'E0E0E0' } },
          left: { style: 'thin', color: { argb: 'E0E0E0' } },
          bottom: { style: 'thin', color: { argb: 'E0E0E0' } },
          right: { style: 'thin', color: { argb: 'E0E0E0' } }
        };
      });
    }
  });

  // =========================================================================
  // PLAGES NOMMÉES (Named Ranges) — CLÉ du système de cascade
  // =========================================================================
  workbook.definedNames.add("'Source Catégories'!$A$2:$A$5", 'Categories_Meres');
  workbook.definedNames.add("'Source Catégories'!$C$2:$C$6", 'Chaussures_Accessoires');
  workbook.definedNames.add("'Source Catégories'!$D$2:$D$6", 'Puericulture');
  workbook.definedNames.add("'Source Catégories'!$E$2:$E$4", 'Jouets_Eveil');
  workbook.definedNames.add("'Source Catégories'!$F$2:$F$4", 'Cadeaux');

  // =========================================================================
  // ONGLET 3 : LÉGENDE
  // =========================================================================
  const legendSheet = workbook.addWorksheet('Légende & Instructions');

  legendSheet.columns = [
    { header: 'Catégorie Mère', key: 'parent', width: 28 },
    { header: 'Code dans le fichier', key: 'code_parent', width: 25 },
    { header: 'Sous-catégorie', key: 'sub_name', width: 25 },
    { header: 'Code sous-catégorie', key: 'code_sub', width: 22 },
    { header: 'الاسم بالعربية', key: 'name_ar', width: 22 }
  ];

  const lHeader = legendSheet.getRow(1);
  lHeader.height = 26;
  lHeader.eachCell((cell) => {
    cell.font = { name: 'Calibri', size: 11, bold: true, color: { argb: 'FFFFFF' } };
    cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: '2D3590' } };
    cell.alignment = { vertical: 'middle', horizontal: 'center' };
  });

  const legendRows = [
    { parent: 'CHAUSSURES & ACCESSOIRES', code_parent: 'Chaussures_Accessoires', sub_name: 'Chaussures', code_sub: 'chaussures', name_ar: 'أحذية' },
    { parent: '', code_parent: '', sub_name: 'Sacs', code_sub: 'sacs', name_ar: 'حقائب' },
    { parent: '', code_parent: '', sub_name: 'Bonnets & Chapeaux', code_sub: 'bonnets-chapeaux', name_ar: 'طواقي وقبعات' },
    { parent: '', code_parent: '', sub_name: 'Chaussettes', code_sub: 'chaussettes', name_ar: 'جوارب' },
    { parent: '', code_parent: '', sub_name: 'Accessoires cheveux', code_sub: 'accessoires-cheveux', name_ar: 'إكسسوارات الشعر' },
    { parent: 'PUÉRICULTURE', code_parent: 'Puericulture', sub_name: 'Repas & Biberons', code_sub: 'repas-biberons', name_ar: 'الوجبات والرضّاعات' },
    { parent: '', code_parent: '', sub_name: 'Sommeil', code_sub: 'sommeil', name_ar: 'النوم' },
    { parent: '', code_parent: '', sub_name: 'Toilette & Soins', code_sub: 'toilette-soins', name_ar: 'الاستحمام والعناية' },
    { parent: '', code_parent: '', sub_name: 'Promenade & Sorties', code_sub: 'promenade-sorties', name_ar: 'التنزه والخروج' },
    { parent: '', code_parent: '', sub_name: 'Équipement bébé', code_sub: 'equipement-bebe', name_ar: 'تجهيزات الرضيع' },
    { parent: 'JOUETS & ÉVEIL', code_parent: 'Jouets_Eveil', sub_name: 'Jouets', code_sub: 'jouets', name_ar: 'ألعاب' },
    { parent: '', code_parent: '', sub_name: 'Éveil', code_sub: 'eveil', name_ar: 'تنمية مهارات' },
    { parent: '', code_parent: '', sub_name: 'Peluches', code_sub: 'peluches', name_ar: 'دمى قطيفة' },
    { parent: 'CADEAUX', code_parent: 'Cadeaux', sub_name: 'Naissance', code_sub: 'naissance', name_ar: 'مولود جديد' },
    { parent: '', code_parent: '', sub_name: 'Anniversaire', code_sub: 'anniversaire', name_ar: 'عيد ميلاد' },
    { parent: '', code_parent: '', sub_name: 'Coffrets cadeaux', code_sub: 'coffrets-cadeaux', name_ar: 'صناديق هدايا' }
  ];

  legendRows.forEach((r) => {
    const row = legendSheet.addRow(r);
    if (r.parent !== '') {
      row.getCell(1).font = { bold: true, color: { argb: 'EA2F90' } };
      row.getCell(2).font = { bold: true };
    }
  });

  // =========================================================================
  // VALIDATION DES DONNÉES + LISTES DÉROULANTES CASCADE (Lignes 2 à 500)
  // =========================================================================
  for (let r = 2; r <= 500; r++) {
    const row = sheet.getRow(r);
    row.height = 22;

    // COL A : Catégorie Mère — Liste déroulante alimentée par la plage nommée Categories_Meres
    row.getCell(1).dataValidation = {
      type: 'list',
      allowBlank: false,
      formulae: ['Categories_Meres'],
      showInputMessage: true,
      inputTitle: '① Catégorie Mère',
      inputMessage: 'Sélectionnez d\'abord la catégorie principale. La sous-catégorie se chargera automatiquement.',
      showErrorMessage: true,
      errorStyle: 'stop',
      errorTitle: 'Catégorie Mère Invalide !',
      error: 'Sélectionnez une catégorie principale valide dans la liste.'
    };

    // COL B : Sous-catégorie — INDIRECT(A2) → charge dynamiquement les filles de la mère sélectionnée
    row.getCell(2).dataValidation = {
      type: 'list',
      allowBlank: false,
      formulae: [`INDIRECT($A$${r})`],
      showInputMessage: true,
      inputTitle: '② Sous-catégorie',
      inputMessage: 'Choisissez la sous-catégorie fille (liste chargée automatiquement selon la catégorie mère).',
      showErrorMessage: true,
      errorStyle: 'stop',
      errorTitle: 'Sous-catégorie Invalide !',
      error: 'Choisissez une sous-catégorie valide de la catégorie mère sélectionnée.'
    };

    // COL C : name_fr — Obligatoire
    row.getCell(3).dataValidation = {
      type: 'textLength', operator: 'greaterThan', allowBlank: false, formulae: [0],
      showInputMessage: true, inputTitle: 'Nom FR (Obligatoire)', inputMessage: 'Nom du produit en français.',
      showErrorMessage: true, errorStyle: 'stop', errorTitle: 'Nom FR Manquant !', error: 'Le nom en français est obligatoire.'
    };

    // COL D : name_ar — Obligatoire
    const cellAr = row.getCell(4);
    cellAr.alignment = { readingOrder: 'rtl', horizontal: 'right' };
    cellAr.dataValidation = {
      type: 'textLength', operator: 'greaterThan', allowBlank: false, formulae: [0],
      showInputMessage: true, inputTitle: 'الاسم بالعربية (إجباري)', inputMessage: 'أدخل اسم المنتج بالعربية.',
      showErrorMessage: true, errorStyle: 'stop', errorTitle: 'الاسم مفقود !', error: 'الاسم بالعربية إجباري.'
    };

    // COL E : description_fr — Obligatoire
    row.getCell(5).dataValidation = {
      type: 'textLength', operator: 'greaterThan', allowBlank: false, formulae: [0],
      showInputMessage: true, inputTitle: 'Description FR (Obligatoire)', inputMessage: 'Description du produit en français.',
      showErrorMessage: true, errorStyle: 'stop', errorTitle: 'Description FR Manquante !', error: 'La description en français est obligatoire.'
    };

    // COL F : description_ar — Obligatoire
    const cellDescAr = row.getCell(6);
    cellDescAr.alignment = { readingOrder: 'rtl', horizontal: 'right' };
    cellDescAr.dataValidation = {
      type: 'textLength', operator: 'greaterThan', allowBlank: false, formulae: [0],
      showInputMessage: true, inputTitle: 'الوصف بالعربية (إجباري)', inputMessage: 'أدخل وصف المنتج بالعربية.',
      showErrorMessage: true, errorStyle: 'stop', errorTitle: 'الوصف مفقود !', error: 'الوصف بالعربية إجباري.'
    };

    // COL G : price — Nombre entier > 0
    const cellPrice = row.getCell(7);
    cellPrice.numFmt = '#,##0 "DA"';
    cellPrice.dataValidation = {
      type: 'whole', operator: 'greaterThan', allowBlank: false, formulae: [0],
      showInputMessage: true, inputTitle: 'Prix en DA', inputMessage: 'Nombre entier > 0 (ex. 2800).',
      showErrorMessage: true, errorStyle: 'stop', errorTitle: 'Prix Invalide !', error: 'Le prix doit être un nombre entier supérieur à 0.'
    };

    // COL H : image — URL Bunny CDN OBLIGATOIRE
    row.getCell(8).dataValidation = {
      type: 'textLength', operator: 'greaterThan', allowBlank: false, formulae: [0],
      showInputMessage: true, inputTitle: 'URL Image (Obligatoire)', inputMessage: 'Collez l\'URL Bunny.net de l\'image du produit.',
      showErrorMessage: true, errorStyle: 'stop', errorTitle: 'Image Manquante !', error: 'L\'URL de l\'image Bunny CDN est obligatoire.'
    };

    // COL I : is_active — 1/0
    row.getCell(9).dataValidation = {
      type: 'list', allowBlank: true, formulae: ['"1,0"'],
      showInputMessage: true, inputTitle: 'Actif ?', inputMessage: '1 = Visible / 0 = Masqué.'
    };

    // COL J : is_featured — 1/0
    row.getCell(10).dataValidation = {
      type: 'list', allowBlank: true, formulae: ['"1,0"'],
      showInputMessage: true, inputTitle: 'En Vedette ?', inputMessage: '1 = Vedette / 0 = Normal.'
    };

    // Bordures
    row.eachCell((cell) => {
      cell.border = {
        top: { style: 'thin', color: { argb: 'E0E0E0' } },
        left: { style: 'thin', color: { argb: 'E0E0E0' } },
        bottom: { style: 'thin', color: { argb: 'E0E0E0' } },
        right: { style: 'thin', color: { argb: 'E0E0E0' } }
      };
    });
  }

  // Sauvegarde (avec fallback si fichier ouvert dans Excel)
  const primaryPath = 'c:/Users/Fujitsu/Downloads/APP/darlila/modele_import_produits.xlsx';
  try {
    await workbook.xlsx.writeFile(primaryPath);
    console.log('✅ MODELE_PARFAIT_CASSETTE: modele_import_produits.xlsx généré avec succès !');
  } catch (err) {
    const altPath = 'c:/Users/Fujitsu/Downloads/APP/darlila/modele_import_produits_cascading.xlsx';
    await workbook.xlsx.writeFile(altPath);
    console.log('✅ MODELE_PARFAIT_CASSETTE: modele_import_produits_cascading.xlsx généré avec succès !');
  }
}

buildModelExcel().catch(console.error);
