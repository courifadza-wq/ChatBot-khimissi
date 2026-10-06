<?php

use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        api: __DIR__.'/../routes/api.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware) {
        // Alias du middleware « admin » utilisé par routes/api.php
        // pour protéger l'espace d'administration.
        $middleware->alias([
            'admin' => \App\Http\Middleware\EnsureUserIsAdmin::class,
        ]);

        /*
         * Mode maintenance maison :
         *  - on retire le middleware par défaut (page 503 générique)
         *  - on ajoute le nôtre en fin de pile globale : JSON 503 pour l'API,
         *    admin toujours accessible, page HTML élégante sinon.
         *    (en fin de pile → la réponse repasse par HandleCors, ce qui
         *    conserve les en-têtes CORS pour le frontend cross-origine)
         */
        $middleware->remove(
            \Illuminate\Foundation\Http\Middleware\PreventRequestsDuringMaintenance::class
        );
        $middleware->append(\App\Http\Middleware\ShopMaintenance::class);
    })
    ->withExceptions(function (Exceptions $exceptions) {
        //
    })->create();
