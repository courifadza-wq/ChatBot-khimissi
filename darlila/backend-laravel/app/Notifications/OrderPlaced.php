<?php

namespace App\Notifications;

use App\Models\Order;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Notifications\Notification;

/**
 * E-mail envoyé au vendeur à chaque nouvelle commande.
 *
 * - File d'attente : ShouldQueue (avec QUEUE_CONNECTION=sync, défaut ici,
 *   l'envoi est immédiat ; passez sur redis/database + queue:work en prod).
 * - Transport : MAIL_MAILER=log par défaut (le message est écrit dans
 *   storage/logs/laravel.log) — configurez un SMTP dans .env pour produire.
 */
class OrderPlaced extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(public Order $order)
    {
    }

    public function via(object $notifiable): array
    {
        return ['mail'];
    }

    public function toMail(object $notifiable): MailMessage
    {
        $order = $this->order->load('items');

        $rows = $order->items
            ->map(fn ($item) => [
                $item->product_name,
                $item->quantity,
                self::da($item->unit_price),
                self::da($item->unit_price * $item->quantity),
            ])
            ->all();

        return (new MailMessage)
            ->subject('🛍️ Nouvelle commande '.$order->reference.' — Planet Kids')
            ->greeting('Nouvelle commande reçue !')
            ->line('Un client vient de passer commande sur la boutique.')
            ->line('**Référence : '.$order->reference.'**')
            ->line('**Client :** '.$order->customer_name.' — '.$order->customer_phone)
            ->line('**Wilaya de livraison :** '.$order->wilaya)
            ->when($order->notes, fn (MailMessage $mail) => $mail->line('**Note du client :** '.$order->notes))
            ->table(
                ['Produit', 'Qté', 'Prix unitaire', 'Sous-total'],
                $rows
            )
            ->line('**Total de la commande : '.self::da($order->total).'** (paiement à la livraison)')
            ->action('Gérer la commande', rtrim(config('app.admin_url'), '/').'/admin/orders')
            ->line('Merci et bonne préparation ! 💛');
    }

    private static function da(int $amount): string
    {
        return number_format($amount, 0, '.', ' ').' DA';
    }
}
