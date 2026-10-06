<?php

namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;

/**
 * Authentification de l'espace d'administration (Sanctum, tokens Bearer).
 */
class AuthController extends Controller
{
    /**
     * POST /api/auth/login { email, password }
     * → { data: { token, user } }
     */
    public function login(Request $request): JsonResponse
    {
        $credentials = $request->validate([
            'email' => ['required', 'email'],
            'password' => ['required', 'string'],
        ]);

        $user = User::query()
            ->where('email', $credentials['email'])
            ->first();

        if (! $user || ! Hash::check($credentials['password'], $user->password)) {
            // protégé contre le brute-force par le middleware throttle:6,1
            throw ValidationException::withMessages([
                'email' => __('auth.failed'),
            ]);
        }

        if (! $user->is_admin) {
            throw ValidationException::withMessages([
                'email' => "Ce compte n'a pas accès à l'administration.",
            ]);
        }

        // Un seul token actif par appareil : on révoque les tokens précédents
        // portant le même nom, puis on en émet un nouveau.
        $user->tokens()->where('name', 'admin-spa')->delete();
        $token = $user->createToken('admin-spa')->plainTextToken;

        return response()->json([
            'data' => [
                'token' => $token,
                'user' => $user->toSafeArray(),
            ],
        ]);
    }

    /**
     * GET /api/auth/me — utilisateur courant (protégé par auth:sanctum).
     */
    public function me(Request $request): JsonResponse
    {
        return response()->json([
            'data' => $request->user()->toSafeArray(),
        ]);
    }

    /**
     * POST /api/admin/change-password — change le mot de passe admin.
     */
    public function changePassword(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'current_password' => ['required', 'string'],
            'new_password' => ['required', 'string', 'min:8', 'max:120', 'confirmed'],
        ]);

        $user = $request->user();

        if (! Hash::check($validated['current_password'], $user->password)) {
            throw ValidationException::withMessages([
                'current_password' => ['Le mot de passe actuel est incorrect.'],
            ]);
        }

        $user->update(['password' => Hash::make($validated['new_password'])]);

        return response()->json([
            'data' => ['changed' => true],
        ]);
    }

    /**
     * POST /api/auth/logout — révoque le token courant.
     */
    public function logout(Request $request): JsonResponse
    {
        $request->user()->currentAccessToken()?->delete();

        return response()->json([
            'data' => ['logged_out' => true],
        ]);
    }
}
