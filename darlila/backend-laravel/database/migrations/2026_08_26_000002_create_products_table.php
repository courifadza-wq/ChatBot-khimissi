<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('products', function (Blueprint $table) {
            $table->id();
            $table->foreignId('category_id')->constrained()->cascadeOnDelete();
            $table->string('slug', 180)->unique();
            $table->string('name_fr');
            $table->string('name_ar');
            $table->text('description_fr')->nullable();
            $table->text('description_ar')->nullable();
            $table->unsignedInteger('price'); // prix en dinars algériens (entier, pas de centimes)
            $table->string('image', 500); // URL externe ou chemin /storage/...
            $table->boolean('is_featured')->default(false);
            $table->boolean('is_active')->default(true); // visible dans la boutique publique
            $table->unsignedInteger('position')->default(0);
            $table->timestamps();

            $table->index('category_id');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('products');
    }
};
