<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

/**
 * Réserve les routes /api/admin/* aux comptes administrateurs.
 * (le champ is_admin est défini par le seeder ou manuellement en base)
 */
class EnsureUserIsAdmin
{
    public function handle(Request $request, Closure $next): Response
    {
        $user = $request->user();

        if (! $user instanceof \App\Models\User || ! $user->is_admin) {
            abort(403, 'Accès réservé aux administrateurs.');
        }

        return $next($request);
    }
}
