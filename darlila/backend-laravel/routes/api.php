<?php

use App\Http\Controllers\Admin\BundleController as AdminBundleController;
use App\Http\Controllers\Admin\CategoryController as AdminCategoryController;
use App\Http\Controllers\Admin\ConfigController as AdminConfigController;
use App\Http\Controllers\Admin\OrderController as AdminOrderController;
use App\Http\Controllers\Admin\ProductController as AdminProductController;
use App\Http\Controllers\AuthController;
use App\Http\Controllers\BundleController;
use App\Http\Controllers\CategoryController;
use App\Http\Controllers\GalleryController;
use App\Http\Controllers\OrderController;
use App\Http\Controllers\ProductController;
use App\Http\Controllers\ReviewController;
use App\Http\Controllers\SettingController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| API Dar Lila — Boutique (parfums, cosmétiques & articles bébé)
|--------------------------------------------------------------------------
|
| Toutes les routes sont préfixées par /api (géré automatiquement par
| Laravel). Réponses JSON au format { "data": ... } grâce aux Resources.
|
*/

/* ---------- Public ---------- */

// Informations générales de la boutique (numéro WhatsApp, adresse, horaires…)
Route::get('/settings', SettingController::class)->name('settings.index');

// Catalogue (produits actifs uniquement)
Route::get('/categories', [CategoryController::class, 'index'])->name('categories.index');
Route::get('/products', [ProductController::class, 'index'])->name('products.index');
Route::get('/products/{slug}', [ProductController::class, 'show'])->name('products.show');

// Contenus
Route::get('/reviews', [ReviewController::class, 'index'])->name('reviews.index');
Route::get('/gallery', [GalleryController::class, 'index'])->name('gallery.index');

// Lots (bundles) : plusieurs produits à prix réduit
Route::get('/bundles', [BundleController::class, 'index'])->name('bundles.index');

// Commande : enregistrée en base puis confirmée via WhatsApp
// (+ notification e-mail au vendeur, voir OrderController)
Route::post('/orders', [OrderController::class, 'store'])->name('orders.store');

/* ---------- Authentification (Sanctum, tokens Bearer) ---------- */

Route::prefix('auth')->name('auth.')->group(function () {
    // throttle:6,1 → 6 tentatives par minute et par IP (anti brute-force)
    Route::post('/login', [AuthController::class, 'login'])
        ->middleware('throttle:6,1')->name('login');

    Route::middleware('auth:sanctum')->group(function () {
        Route::get('/me', [AuthController::class, 'me'])->name('me');
        Route::post('/logout', [AuthController::class, 'logout'])->name('logout');

    });
});

/* ---------- Espace d'administration (admin uniquement) ---------- */

Route::prefix('admin')
    ->name('admin.')
    ->middleware(['auth:sanctum', 'admin'])
    ->group(function () {
        // Capacités de l'instance (ex. stockage des images : Bunny ou local)
        Route::get('/config', AdminConfigController::class)->name('config');

        // Catégories (accessibles même pendant la maintenance, contrairement
        // à la route publique /api/categories)
        Route::get('/categories', [AdminCategoryController::class, 'index'])->name('categories.index');
        Route::post('/categories', [AdminCategoryController::class, 'store'])->name('categories.store');
        Route::match(['put', 'patch'], '/categories/{category}', [AdminCategoryController::class, 'update'])->name('categories.update');
        Route::delete('/categories/{category}', [AdminCategoryController::class, 'destroy'])->name('categories.destroy');

        // Produits
        Route::get('/products', [AdminProductController::class, 'index'])->name('products.index');
        Route::post('/products', [AdminProductController::class, 'store'])->name('products.store');
        Route::post('/products/import', [AdminProductController::class, 'import'])->name('products.import');
        Route::get('/products/export', [AdminProductController::class, 'export'])->name('products.export');
        Route::match(['put', 'patch'], '/products/{product}', [AdminProductController::class, 'update'])->name('products.update');
        Route::delete('/products/{product}', [AdminProductController::class, 'destroy'])->name('products.destroy');

        // Lots
        Route::get('/bundles', [AdminBundleController::class, 'index'])->name('bundles.index');
        Route::post('/bundles', [AdminBundleController::class, 'store'])->name('bundles.store');
        Route::match(['put', 'patch'], '/bundles/{bundle}', [AdminBundleController::class, 'update'])->name('bundles.update');
        Route::delete('/bundles/{bundle}', [AdminBundleController::class, 'destroy'])->name('bundles.destroy');

        // Réglages de la boutique (modifiables depuis l'admin)
        Route::get('/settings', [\App\Http\Controllers\Admin\SettingController::class, 'index'])->name('settings.index');
        Route::put('/settings', [\App\Http\Controllers\Admin\SettingController::class, 'update'])->name('settings.update');

        // Changement de mot de passe
        Route::post('/change-password', [AuthController::class, 'changePassword'])
            ->name('change-password');

        // Suppression en masse
        Route::post('/products/bulk-delete', [AdminProductController::class, 'bulkDelete'])
            ->name('products.bulk-delete');
        Route::post('/bundles/bulk-delete', [AdminBundleController::class, 'bulkDelete'])
            ->name('bundles.bulk-delete');

        // Commandes
        Route::get('/orders', [AdminOrderController::class, 'index'])->name('orders.index');
        Route::get('/orders/export', [AdminOrderController::class, 'export'])->name('orders.export');
        Route::patch('/orders/{order}/status', [AdminOrderController::class, 'updateStatus'])->name('orders.status');
    });
