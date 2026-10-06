<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('orders', function (Blueprint $table) {
            $table->id();
            $table->string('reference')->unique(); // ex. DL-4F7Q2A
            $table->string('customer_name');
            $table->string('customer_phone');
            $table->string('wilaya');
            $table->string('address')->nullable();
            $table->text('notes')->nullable();
            $table->unsignedInteger('total')->default(0); // total en DA
            $table->string('status')->default('nouvelle'); // nouvelle|confirmee|expediee|livree|annulee
            $table->timestamps();

            $table->index('status');
            $table->index('created_at');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('orders');
    }
};
