<?php

use Illuminate\Http\Request;

define('LARAVEL_START', microtime(true));

// Determine if the application is in maintenance mode...
if (file_exists($maintenance = __DIR__.'/../storage/framework/maintenance.php')) {
    require $maintenance;
}

// Register the Composer autoloader...
require __DIR__.'/../vendor/autoload.php';

// Bootstrap Laravel and handle the request...
$app = require_once __DIR__.'/../bootstrap/app.php';

/*
|--------------------------------------------------------------------------
| Compatibilité hébergement mutualisé (Hostinger…)
|--------------------------------------------------------------------------
| Sur un mutualisé, la racine web s'appelle souvent « public_html » au lieu
| de « public ». Cette ligne dit à Laravel que le dossier courant EST la
| racine publique, où qu'il soit renommé — indispensable pour que
| `php artisan storage:link` et public_path() restent corrects.
*/
$app->usePublicPath(__DIR__);

$app->handleRequest(Request::capture());
