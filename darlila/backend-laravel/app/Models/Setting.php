<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\Facades\Cache;

class Setting extends Model
{
    protected $fillable = ['key', 'value'];

    /**
     * Retourne tous les réglages sous forme de tableau clé => valeur.
     * Le résultat est mis en cache 1 heure (vidé automatiquement à la sauvegarde).
     */
    public static function allAsArray(): array
    {
        return Cache::remember('darlila.settings', now()->addHour(), function () {
            return static::query()->pluck('value', 'key')->all();
        });
    }

    /**
     * Valeur d'un réglage donné (avec valeur par défaut).
     */
    public static function get(string $key, ?string $default = null): ?string
    {
        return static::allAsArray()[$key] ?? $default;
    }

    protected static function booted(): void
    {
        static::saved(fn () => Cache::forget('darlila.settings'));
        static::deleted(fn () => Cache::forget('darlila.settings'));
    }
}
