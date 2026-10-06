<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Http\Resources\OrderResource;
use App\Models\Order;
use App\Support\EncodesCsv;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Validation\Rule;

/**
 * Consultation et suivi des commandes (espace admin),
 * avec export CSV pour la comptabilité.
 */
class OrderController extends Controller
{
    use EncodesCsv;

    /**
     * GET /api/admin/orders?status=nouvelle — les plus récentes d'abord.
     */
    public function index(Request $request): AnonymousResourceCollection
    {
        $orders = $this->filteredQuery($request)
            ->with('items')
            ->latest('id')
            ->get();

        return OrderResource::collection($orders);
    }

    /**
     * PATCH /api/admin/orders/{order}/status { status }
     */
    public function updateStatus(Request $request, Order $order): OrderResource
    {
        $validated = $request->validate([
            'status' => ['required', 'string', Rule::in([
                Order::STATUS_NEW,
                Order::STATUS_CONFIRMED,
                Order::STATUS_SHIPPED,
                Order::STATUS_DELIVERED,
                Order::STATUS_CANCELLED,
            ])],
        ]);

        $order->update($validated);

        return new OrderResource($order->load('items'));
    }

    /**
     * GET /api/admin/orders/export?status=&from=&to=
     *
     * CSV comptable (séparateur « ; », ouvrable directement dans Excel) :
     * référence, date, client, téléphone, wilaya, nombre d'articles,
     * détail des articles, total en DA, statut.
     */
    public function export(Request $request)
    {
        $filename = sprintf('darlila-commandes-%s.csv', now()->format('Ymd-Hi'));

        $lines = [
            'reference;date;client;telephone;wilaya;articles;detail_articles;total_da;statut',
        ];

        $this->filteredQuery($request)
            ->with('items')
            ->orderBy('id')
            ->chunk(500, function ($orders) use (&$lines) {
                foreach ($orders as $order) {
                    $lines[] = implode(';', [
                        $order->reference,
                        $order->created_at?->format('d/m/Y H:i'),
                        $this->csvCell($order->customer_name),
                        $order->customer_phone,
                        $this->csvCell($order->wilaya),
                        $order->items->sum('quantity'),
                        $this->csvCell(
                            $order->items
                                ->map(fn ($item) => $item->product_name.' x'.$item->quantity)
                                ->implode(', ')
                        ),
                        $order->total,
                        $order->status,
                    ]);
                }
            });

        return response(implode("\n", $lines), 200, [
            'Content-Type' => 'text/csv; charset=UTF-8',
            'Content-Disposition' => 'attachment; filename="'.$filename.'"',
        ]);
    }

    /**
     * Filtres communs (statut, plage de dates) partagés par la liste
     * et l'export — l'export reflète exactement les filtres affichés.
     */
    private function filteredQuery(Request $request)
    {
        return Order::query()
            ->when(
                $request->filled('status'),
                fn ($query) => $query->where('status', $request->string('status')->toString())
            )
            ->when(
                $request->filled('from'),
                fn ($query) => $query->whereDate('created_at', '>=', $request->string('from')->toString())
            )
            ->when(
                $request->filled('to'),
                fn ($query) => $query->whereDate('created_at', '<=', $request->string('to')->toString())
            );
    }
}
