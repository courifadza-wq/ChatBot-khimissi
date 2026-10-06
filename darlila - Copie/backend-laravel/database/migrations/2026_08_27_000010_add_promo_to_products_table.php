<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Promotions quantité sur les produits :
     * « achetez N unités → X % de remise » (vide = pas de promo).
     */
    public function up(): void
    {
        Schema::table('products', function (Blueprint $table) {
            $table->unsignedTinyInteger('promo_quantity')->nullable()->after('is_featured'); // ex. 2 = dès 2 achetés
            $table->unsignedTinyInteger('promo_percent')->nullable()->after('promo_quantity'); // ex. 15 = -15 %
        });
    }

    public function down(): void
    {
        Schema::table('products', function (Blueprint $table) {
            $table->dropColumn(['promo_quantity', 'promo_percent']);
        });
    }
};
