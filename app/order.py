# ============================================================
#  Machine à états de commande
#  Collecte les informations de commande pas à pas, puis
#  renvoie un ordre structuré à envoyer par email.
# ============================================================
from __future__ import annotations

from dataclasses import dataclass, field

from .catalog import get_payment, find_product


@dataclass
class Order:
    phone: str
    name: str = ""
    address: str = ""
    items: list = field(default_factory=list)  # [{name, qty, price}]
    payment: str = ""
    total: int = 0

    def add_item(self, name: str, qty: int):
        self.items.append({"name": name, "qty": qty})
        self._recompute_total()

    def _recompute_total(self):
        from .catalog import get_products
        total = 0
        for it in self.items:
            price = 0
            for p in get_products():
                if p["name"].lower() in it["name"].lower() or it["name"].lower() in p["name"].lower():
                    price = p["price"]
                    break
            total += price * it["qty"]
        self.total = total

    def summary(self) -> str:
        lines = ["📋 *Récapitulatif de votre commande* :", ""]
        for it in self.items:
            lines.append(f"• {it['name']} x {it['qty']}")
        lines.append("")
        lines.append(f"💰 Total : {self.total} DZD")
        lines.append(f"👤 Nom : {self.name}")
        lines.append(f"📍 Adresse : {self.address}")
        lines.append(f"💳 Paiement : {self.payment}")
        return "\n".join(lines)


# États possibles du dialogue
ST_NEW, ST_NAME, ST_ADDRESS, ST_ITEMS, ST_PAYMENT, ST_CONFIRM = range(6)

# Un état par numéro de téléphone (en mémoire).
# Pour la production multi-instance, remplacer par Redis.
_sessions: dict[str, dict] = {}


def get_session(phone: str) -> dict:
    if phone not in _sessions:
        _sessions[phone] = {"state": ST_NEW, "order": Order(phone=phone)}
    return _sessions[phone]


def reset_session(phone: str):
    _sessions.pop(phone, None)


def _ask_name() -> str:
    return "Très bien 🛒 ! Pour enregistrer votre commande, quel est votre *nom complet* ?"


def _ask_address() -> str:
    return "Merci ! Quelle est votre *adresse de livraison* (ville + adresse) ?"


def _ask_items() -> str:
    return "Quel(s) produit(s) voulez-vous ? (ex : *2 Casque Bluetooth Pro*, *1 T-shirt Premium*)\n\nVous pouvez en donner plusieurs."


def _ask_payment() -> str:
    return "Comment souhaitez-vous payer ?\n" + "\n".join(f"• {p}" for p in get_payment())


def _ask_confirm() -> str:
    return "Confirmez-vous cette commande ? Répondez *oui* ou *non*."


# -----------------------------------------------------------
# Fonction principale : avance la conversation d'un message
# Retourne la réponse texte à envoyer, ou None pour terminer
# -----------------------------------------------------------
def process(phone: str, message: str, intent: str) -> str | None:
    sess = get_session(phone)
    state = sess["state"]
    order: Order = sess["order"]

    # Démarrage d'une nouvelle commande
    if state == ST_NEW and intent == "order_start":
        sess["state"] = ST_NAME
        return _ask_name()

    # À chaque étape, on stocke l'info puis on pose la question suivante
    if state == ST_NAME:
        order.name = message.strip()
        sess["state"] = ST_ADDRESS
        return _ask_address()

    if state == ST_ADDRESS:
        order.address = message.strip()
        sess["state"] = ST_ITEMS
        return _ask_items()

    if state == ST_ITEMS:
        items = _parse_items(message)
        if not items:
            return "Je n'ai pas compris le produit 😕. Exemple : *2 Casque Bluetooth Pro*. Réessayez."
        for name, qty in items:
            order.add_item(name, qty)
        sess["state"] = ST_PAYMENT
        return _ask_payment()

    if state == ST_PAYMENT:
        order.payment = message.strip()
        sess["state"] = ST_CONFIRM
        return _ask_confirm()

    if state == ST_CONFIRM:
        low = message.strip().lower()
        if low in ("oui", "yes", "ok", "confirmer", "نعم", "اه", "ايوا", "wa7ed", "yes") or low.startswith("نعم"):
            return "CONFIRMED"  # signal : la commande est prête
        reset_session(phone)
        return "Commande annulée. À bientôt 👋"

    return None


def _parse_items(message: str) -> list[tuple[str, int]]:
    """Extrait une liste (produit, quantité) d'un message libre.
    Gère : '2 casque et 1 t-shirt', '1 كاسك و 2 تيشيرت', virgules, '+', 'et', 'و'."""
    import re
    # sépare sur les connecteurs (espaces autour de و pour ne pas casser بلوتوث)
    chunks = re.split(r"\s+et\s+|\s+و\s+|\s+and\s+|\s*[,;+]\s*", message.lower())
    results = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        qty = 1
        mq = re.match(r"^(\d+)\s*[xX]?\s*", chunk)
        if mq:
            qty = max(1, int(mq.group(1)))
            chunk = chunk[mq.end():].strip()
        if not chunk:
            continue
        prod = find_product(chunk)
        if prod:
            results.append((prod["name"], qty))
    return results


def build_email_body(order: Order) -> str:
    """Construit le corps de l'email HTML pour le commerçant."""
    items_html = "".join(
        f"<tr><td>{it['name']}</td><td>{it['qty']}</td></tr>" for it in order.items
    )
    return f"""
    <html><body style="font-family:Arial,sans-serif">
      <h2>🛒 Nouvelle commande WhatsApp</h2>
      <p><strong>Client :</strong> {order.name}</p>
      <p><strong>Téléphone :</strong> {order.phone}</p>
      <p><strong>Adresse :</strong> {order.address}</p>
      <table border="1" cellpadding="6" cellspacing="0">
        <tr><th>Produit</th><th>Qté</th></tr>
        {items_html}
      </table>
      <p><strong>Total :</strong> {order.total} DZD</p>
      <p><strong>Paiement :</strong> {order.payment}</p>
    </body></html>
    """
