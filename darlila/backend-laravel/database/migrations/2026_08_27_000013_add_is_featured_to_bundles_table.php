<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Lots « en vedette » : affichés en tête de la section « Nos lots ».
     */
    public function up(): void
    {
        Schema::table('bundles', function (Blueprint $table) {
            $table->boolean('is_featured')->default(false)->after('is_active');
        });
    }

    public function down(): void
    {
        Schema::table('bundles', function (Blueprint $table) {
            $table->dropColumn('is_featured');
        });
    }
};
