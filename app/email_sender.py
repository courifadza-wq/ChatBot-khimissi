# ============================================================
#  Envoi d'email au commerçant (SMTP) quand une commande est validée
#  Le message inclut : un résumé HTML + un fichier Excel (.xlsx) joint
# ============================================================
import logging
import smtplib
from email.message import EmailMessage

from .config import settings
from .excel_export import order_to_excel_bytes

logger = logging.getLogger("email")


def send_order_email(order) -> bool:
    """Envoie la commande formatée à STORE_EMAIL_TO (texte + HTML + Excel joint)."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD or not settings.STORE_EMAIL_TO:
        logger.error("SMTP non configuré — impossible d'envoyer l'email.")
        return False

    msg = EmailMessage()
    msg["Subject"] = f"🛒 Nouvelle commande — {order.name} ({order.phone})"
    msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"] = settings.STORE_EMAIL_TO

    # Corps texte (fallback)
    msg.set_content(order.summary())

    # Corps HTML enrichi (tableau des produits)
    items_html = "".join(
        f"<tr><td style='padding:6px;border:1px solid #ccc'>{it['name']}</td>"
        f"<td style='padding:6px;border:1px solid #ccc;text-align:center'>{it['qty']}</td></tr>"
        for it in order.items
    )
    html = f"""\
    <html><body style="font-family:Arial,sans-serif;color:#222">
      <h2 style="color:#1E3A5F">🛒 Nouvelle commande WhatsApp</h2>
      <p><strong>Client :</strong> {order.name}</p>
      <p><strong>Téléphone :</strong> {order.phone}</p>
      <p><strong>Adresse :</strong> {order.address}</p>
      <table cellspacing="0" style="border-collapse:collapse;margin:8px 0">
        <tr style="background:#1E3A5F;color:#fff">
          <th style="padding:6px;border:1px solid #ccc">Produit</th>
          <th style="padding:6px;border:1px solid #ccc">Qté</th>
        </tr>
        {items_html}
      </table>
      <p><strong>Total :</strong> {order.total} DZD</p>
      <p><strong>Paiement :</strong> {order.payment}</p>
      <p style="color:#888;font-size:12px">Le détail complet est dans le fichier Excel joint.</p>
    </body></html>
    """
    msg.add_alternative(html, subtype="html")

    # Joint le fichier Excel (.xlsx)
    try:
        xlsx_bytes = order_to_excel_bytes(order)
        filename = f"commande_{order.phone.replace('+', '')}.xlsx"
        msg.add_attachment(
            xlsx_bytes,
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename,
        )
        logger.info("Fichier Excel joint : %s (%d octets)", filename, len(xlsx_bytes))
    except Exception as e:  # noqa: BLE001
        logger.error("Erreur génération Excel: %s — envoi sans pièce jointe.", e)

    try:
        if settings.SMTP_USE_TLS:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20)
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info("Email de commande envoyé à %s", settings.STORE_EMAIL_TO)
        return True
    except Exception as e:  # noqa: BLE001
        logger.error("Erreur envoi email: %s", e)
        return False
