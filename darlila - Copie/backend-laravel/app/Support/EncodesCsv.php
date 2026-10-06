<?php

namespace App\Support;

/**
 * Échappement CSV partagé (exports produits &amp; commandes).
 * Séparateur « ; » (convivial Excel français), guillemets gérés.
 */
trait EncodesCsv
{
    private function csvCell(?string $value): string
    {
        $value = str_replace('"', '""', (string) $value);

        return preg_match('/[;"\n\r]/', $value) ? '"'.$value.'"' : $value;
    }
}
