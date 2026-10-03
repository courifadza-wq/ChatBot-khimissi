# ============================================================
#  Machine à états de commande
#  Collecte les informations de commande pas à pas, puis
#  renvoie un ordre structuré à envoyer par email.
# ============================================================
from __future__ import annotations

from dataclasses import dataclass, field

from .catalog import get_payment, find_product
from .database import save_order_session, load_order_session, delete_order_session


@dataclass
class Order:
    phone: str
    name: str = ""
    address: str = ""
    items: list = field(default_factory=list)
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

    def to_dict(self) -> dict:
        return {"phone": self.phone, "name": self.name, "address": self.address,
                "items": self.items, "payment": self.payment, "total": self.total}

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
        o = cls(phone=data.get("phone", ""))
        o.name = data.get("name", "")
        o.address = data.get("address", "")
        o.items = data.get("items", [])
        o.payment = data.get("payment", "")
        o.total = data.get("total", 0)
        return o

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


def get_session(phone: str) -> dict:
    data = load_order_session(phone)
    if data:
        return {"state": data["state"], "order": Order.from_dict(data["order"]), "client": data.get("client")}
    return {"state": ST_NEW, "order": Order(phone=phone), "client": None}


def _persist(phone: str, sess: dict) -> None:
    """Sauvegarde la session dans SQLite."""
    save_order_session(phone, sess["state"], sess["order"].to_dict(), sess.get("client"))


def reset_session(phone: str):
    delete_order_session(phone)


def _ask_name() -> str:
    return "Très bien 🛒 ! Pour enregistrer votre commande, quel est votre *nom complet* ?"


def _ask_address() -> str:
    return (
        "Merci ! Quelle est votre *adresse de livraison* (ville + adresse) ?\n\n"
        "🏪 Ou répondez *retrait magasin* si vous venez récupérer en boutique."
    )


def _ask_items() -> str:
    return (
        "Quel(s) produit(s) voulez-vous ?\n"
        "(ex : *2 SLIP GUAINE SBG/C*, *1 ROBE FIL SABY R301*)\n\n"
        "Vous pouvez en donner plusieurs."
    )



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
        client = None
        try:
            from .database import get_client
            client = get_client(phone)
        except Exception:
            pass
        sess["state"] = ST_NAME
        sess["client"] = client
        _persist(phone, sess)
        if client and client.get("name"):
            return (
                f"Parfait 🛒 ! Je vous reconnais, *{client['name']}* !\n\n"
                "Voulez-vous commander avec les mêmes informations qu'avant ?\n"
                f"• Nom : *{client['name']}*\n"
                f"• Adresse : *{client['address']}*\n\n"
                "Répondez *oui* pour confirmer, ou envoyez votre *nouveau nom* pour changer."
            )
        return _ask_name()

    client = sess.get("client")
    if state == ST_NAME:
        low = message.strip().lower()
        if client and client.get("name") and low in ("oui", "yes", "ok", "نعم", "اه", "ايوا"):
            order.name = client["name"]
            order.address = client["address"]
            sess["state"] = ST_ITEMS
            _persist(phone, sess)
            return (f"Parfait ! Utilisation de :\n👤 *{order.name}*  📍 *{order.address}*\n\n") + _ask_items()
        else:
            order.name = message.strip()
            sess["state"] = ST_ADDRESS
            _persist(phone, sess)
            return _ask_address()

    if state == ST_ADDRESS:
        _PICKUP_KEYWORDS = {"retrait", "magasin", "boutique", "recuperer", "récupérer",
                            "viens", "passage", "sur place"}
        low_addr = message.strip().lower()
        if any(kw in low_addr for kw in _PICKUP_KEYWORDS):
            order.address = "🏪 Retrait en magasin"
            sess["state"] = ST_ITEMS
            _persist(phone, sess)
            return "Super ! Commande à retirer en boutique 🏪\n\n" + _ask_items()
        order.address = message.strip()
        sess["state"] = ST_ITEMS
        _persist(phone, sess)
        return _ask_items()

    if state == ST_ITEMS:
        items = _parse_items(message)
        if not items:
            return "Je n'ai pas compris le produit 😕. Exemple : *2 SLIP GUAINE SBG/C*. Réessayez."
        for name, qty in items:
            order.add_item(name, qty)
        sess["state"] = ST_PAYMENT
        _persist(phone, sess)
        if client and client.get("preferred_payment"):
            return (
                f"Comment souhaitez-vous payer ?\n"
                f"(Vous avez utilisé *{client['preferred_payment']}* la dernière fois)\n\n"
            ) + "".join(f"• {p}\n" for p in get_payment()).rstrip()
        return _ask_payment()

    if state == ST_PAYMENT:
        order.payment = message.strip()
        sess["state"] = ST_CONFIRM
        _persist(phone, sess)
        return order.summary() + "\n\n" + _ask_confirm()

    if state == ST_CONFIRM:
        low = message.strip().lower()
        if low in ("oui", "yes", "ok", "confirmer", "نعم", "اه", "ايوا", "wa7ed") or low.startswith("نعم"):
            return "CONFIRMED"
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
            results.append((prod["designation"], qty))
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
