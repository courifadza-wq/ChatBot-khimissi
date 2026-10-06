<?php

namespace App\Http\Controllers;

use App\Models\Bundle;
use App\Models\Order;
use App\Models\OrderItem;
use App\Models\Product;
use App\Models\Setting;
use App\Notifications\OrderPlaced;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Notification;
use Illuminate\Support\Str;
use Illuminate\Validation\Rule;

class OrderController extends Controller
{
    /**
     * Enregistre une commande puis retourne le lien WhatsApp pré-rempli
     * permettant au client de la confirmer auprès de la boutique.
     *
     * POST /api/orders
     * {
     *   "customer_name": "Sarah B.",
     *   "customer_phone": "0555123456",
     *   "wilaya": "Alger",
     *   "notes": null,
     *   "lang": "fr",
     *   "items": [
     *     {"product_id": 1, "quantity": 2},          ← produit (promo « -X% dès N » appliquée)
     *     {"bundle_id": 3, "quantity": 1}            ← lot (prix du lot appliqué)
     *   ]
     * }
     */
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'customer_name' => ['required', 'string', 'min:2', 'max:120'],
            'customer_phone' => ['required', 'string', 'regex:/^[0-9+\s().\-]{9,20}$/'],
            'wilaya' => ['required', 'string', 'max:100'],
            'address' => ['nullable', 'string', 'max:255'],
            'notes' => ['nullable', 'string', 'max:1000'],
            'lang' => ['nullable', 'string', Rule::in(['fr', 'ar'])],
            'items' => ['required', 'array', 'min:1'],
            'items.*.quantity' => ['required', 'integer', 'min:1', 'max:99'],
        ]);

        $lang = $validated['lang'] ?? 'fr';

        /*
         * Chaque ligne est soit un produit, soit un lot. Les prix sont
         * TOUJOURS recalculés côté serveur : promos « -X % dès N achetés »
         * pour les produits, prix du lot pour les bundles.
         */
        $products = Product::query()
            ->whereIn('id', collect($validated['items'])->pluck('product_id')->filter())
            ->get()
            ->keyBy('id');

        $bundles = Bundle::query()
            ->with('items.product')
            ->whereIn('id', collect($validated['items'])->pluck('bundle_id')->filter())
            ->get()
            ->keyBy('id');

        $lines = [];
        $total = 0;
        $errors = [];

        foreach ($validated['items'] as $index => $item) {
            $quantity = (int) $item['quantity'];

            if (! empty($item['bundle_id'])) {
                $bundle = $bundles->get((int) $item['bundle_id']);

                if ($bundle === null) {
                    $errors["items.{$index}.bundle_id"] = ['Lot introuvable.'];
                    continue;
                }

                $unitPrice = $bundle->price;
                $lineTotal = $unitPrice * $quantity;
                $total += $lineTotal;

                $lines[] = [
                    'product_id' => null,
                    'product_name' => $bundle->localizedName($lang).' (lot)',
                    'unit_price' => $unitPrice,
                    'quantity' => $quantity,
                    'line_total' => $lineTotal,
                    'regular_total' => $bundle->regularTotal() * $quantity,
                ];

                continue;
            }

            if (empty($item['product_id'])) {
                $errors["items.{$index}.product_id"] = ['Article inconnu (product_id ou bundle_id requis).'];
                continue;
            }

            $product = $products->get((int) $item['product_id']);

            if ($product === null) {
                $errors["items.{$index}.product_id"] = ['Produit introuvable.'];
                continue;
            }

            $unitPrice = $product->unitPriceFor($quantity); // promo appliquée
            $lineTotal = $unitPrice * $quantity;
            $total += $lineTotal;

            $lines[] = [
                'product_id' => $product->id,
                'product_name' => $product->localizedName($lang),
                'unit_price' => $unitPrice,
                'quantity' => $quantity,
                'line_total' => $lineTotal,
                'regular_total' => $product->price * $quantity,
            ];
        }

        if ($errors !== []) {
            return response()->json([
                'message' => 'Les données fournies sont invalides.',
                'errors' => $errors,
            ], 422);
        }

        if ($lines === []) {
            return response()->json([
                'message' => __('Aucun produit valide dans la commande.'),
            ], 422);
        }

        $order = DB::transaction(function () use ($validated, $lines, $total) {
            $order = Order::create([
                'reference' => $this->uniqueReference(),
                'customer_name' => $validated['customer_name'],
                'customer_phone' => $validated['customer_phone'],
                'wilaya' => $validated['wilaya'],
                'address' => $validated['address'] ?? null,
                'notes' => $validated['notes'] ?? null,
                'total' => $total,
                'status' => Order::STATUS_NEW,
            ]);

            $order->items()->createMany(
                collect($lines)->map(fn (array $line) => [
                    'product_id' => $line['product_id'],
                    'product_name' => $line['product_name'],
                    'unit_price' => $line['unit_price'],
                    'quantity' => $line['quantity'],
                ])->all()
            );

            return $order->load('items');
        });

        $message = $this->buildWhatsAppMessage($order, $lines, $lang);
        $number = Setting::get(
            'whatsapp_number',
            config('services.whatsapp.number', '213555000000')
        );

        /*
         * Notification e-mail au vendeur (voir App\Notifications\OrderPlaced).
         * rescue() : une panne SMTP ne doit jamais faire échouer la commande
         * côté client — l'erreur est simplement journalisée.
         */
        rescue(function () use ($order) {
            $sellerEmail = Setting::get(
                'seller_email',
                config('mail.from.address', 'admin@darlila.dz')
            );

            Notification::route('mail', $sellerEmail)->notify(new OrderPlaced($order));
        });

        return response()->json([
            'data' => [
                'reference' => $order->reference,
                'customer_name' => $order->customer_name,
                'wilaya' => $order->wilaya,
                'total' => $order->total,
                'items_count' => $order->items->sum('quantity'),
                'status' => $order->status,
                'whatsapp_message' => $message,
                'whatsapp_url' => sprintf('https://wa.me/%s?text=%s', $number, rawurlencode($message)),
            ],
        ], 201);
    }

    /**
     * Génère une référence unique lisible, ex. « DL-4F7Q2A ».
     */
    private function uniqueReference(): string
    {
        do {
            $reference = 'DL-'.strtoupper(Str::random(6));
        } while (Order::query()->where('reference', $reference)->exists());

        return $reference;
    }

    /**
     * Construit le message WhatsApp récapitulatif de la commande
     * (remises promo et lots affichées, en français ou en arabe).
     */
    private function buildWhatsAppMessage(Order $order, array $lines, string $lang): string
    {
        $isArabic = $lang === 'ar';

        $intro = $isArabic
            ? 'مرحباً، أريد تأكيد طلبي:'
            : 'Bonjour, je souhaite confirmer ma commande :';

        $itemLines = collect($lines)
            ->map(function (array $line) use ($isArabic) {
                $total = number_format($line['line_total'], 0, '.', ' ');

                // Lot ou produit remisé → afficher le prix barré
                if ($line['regular_total'] > $line['line_total']) {
                    $regular = number_format($line['regular_total'], 0, '.', ' ');
                    $suffix = $isArabic ? ' دج' : ' DA';

                    return $isArabic
                        ? sprintf('- %s × %d = %s%s (بدل %s%s)', $line['product_name'], $line['quantity'], $total, $suffix, $regular, $suffix)
                        : sprintf('- %s × %d = %s DA (au lieu de %s DA)', $line['product_name'], $line['quantity'], $total, $regular);
                }

                return $isArabic
                    ? sprintf('- %s × %d = %s دج', $line['product_name'], $line['quantity'], $total)
                    : sprintf('- %s × %d = %s DA', $line['product_name'], $line['quantity'], $total);
            })
            ->implode("\n");

        $totalFormatted = number_format($order->total, 0, '.', ' ');
        $totalLabel = $isArabic ? 'المجموع' : 'Total';
        $refLabel = $isArabic ? 'المرجع' : 'Référence';
        $nameLabel = $isArabic ? 'الاسم' : 'Nom';
        $phoneLabel = $isArabic ? 'الهاتف' : 'Téléphone';
        $wilayaLabel = $isArabic ? 'الولاية' : 'Wilaya';

        $parts = [
            $intro,
            $itemLines,
            "{$totalLabel} : {$totalFormatted}".($isArabic ? ' دج' : ' DA'),
            "{$refLabel} : {$order->reference}",
            "{$nameLabel} : {$order->customer_name}",
            "{$phoneLabel} : {$order->customer_phone}",
            "{$wilayaLabel} : {$order->wilaya}",
        ];

        if ($order->notes) {
            $parts[] = ($isArabic ? 'ملاحظة' : 'Note').' : '.$order->notes;
        }

        return implode("\n", $parts);
    }
}
