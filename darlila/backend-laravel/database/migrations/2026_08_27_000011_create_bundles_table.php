<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Lots (bundles) : plusieurs produits regroupés à un prix réduit.
     */
    public function up(): void
    {
        Schema::create('bundles', function (Blueprint $table) {
            $table->id();
            $table->string('slug', 180)->unique();
            $table->string('name_fr');
            $table->string('name_ar');
            $table->text('description_fr')->nullable();
            $table->text('description_ar')->nullable();
            $table->unsignedInteger('price'); // prix du lot en DA (inférieur à la somme)
            $table->string('image', 500)->nullable(); // vide → image du premier article
            $table->boolean('is_active')->default(true);
            $table->unsignedInteger('position')->default(0);
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('bundles');
    }
};
