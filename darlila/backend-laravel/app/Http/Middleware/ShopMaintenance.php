<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * Mode maintenance de la boutique Dar Lila.
 *
 * Activé par la présence du fichier storage/framework/down :
 *
 *   php artisan shop:down --message="…" --retry=600
 *   php artisan shop:up
 *
 * (les commandes natives `php artisan down/up` fonctionnent aussi)
 *
 * Comportement :
 *  - les routes API publiques répondent 503 JSON { maintenance: true, … },
 *    ce que le frontend Vue transforme en page d'attente élégante ;
 *  - l'administration (api/admin/*, api/auth/*) reste ACCESSIBLE afin de
 *    pouvoir gérer la boutique et réactiver le site ;
 *  - une page HTML 503 bilingue est rendue pour les visites directes
 *    de l'API dans un navigateur.
 */
class ShopMaintenance
{
    public function handle(Request $request, Closure $next): Response
    {
        $downFile = storage_path('framework/down');

        if (! is_file($downFile)) {
            return $next($request);
        }

        // L'admin et l'authentification restent joignables pendant la maintenance
        if ($request->is('api/admin', 'api/admin/*', 'api/auth', 'api/auth/*')) {
            return $next($request);
        }

        $data = json_decode((string) file_get_contents($downFile), true) ?: [];
        $retryAfter = max(30, (int) ($data['retry'] ?? 300));
        $message = $data['message']
            ?? 'La boutique Planet Kids est momentanément en maintenance. Nous revenons très vite !';

        if ($request->is('api/*') || $request->expectsJson()) {
            return response()->json([
                'message' => $message,
                'maintenance' => true,
                'retry_after' => $retryAfter,
            ], 503, ['Retry-After' => (string) $retryAfter]);
        }

        return response()
            ->view('errors.503', ['retryAfter' => $retryAfter, 'message' => $message], 503)
            ->header('Retry-After', (string) $retryAfter);
    }
}
