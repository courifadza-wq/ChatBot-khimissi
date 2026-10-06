<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Sous-catégories : une catégorie peut dépendre d'une catégorie
     * « parent » (2 niveaux maximum : Chaussures & Accessoires → Chaussures).
     *
     * parent_id NULL  → catégorie principale (affichée en haut des filtres)
     * parent_id <id>  → sous-catégorie de la catégorie indiquée
     */
    public function up(): void
    {
        Schema::table('categories', function (Blueprint $table) {
            $table->foreignId('parent_id')
                ->nullable()
                ->after('id')
                ->constrained('categories')
                ->nullOnDelete();
            $table->index(['parent_id', 'position']);
        });
    }

    public function down(): void
    {
        Schema::table('categories', function (Blueprint $table) {
            $table->dropConstrainedForeignId('parent_id');
            $table->dropIndex(['parent_id', 'position']);
        });
    }
};
