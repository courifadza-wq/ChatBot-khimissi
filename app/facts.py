"""
facts.py — Source de vérité unique pour les données du magasin.
Lit products.yaml (jamais de valeurs en dur ici).
is_open_now() calcule l'état en temps réel (fuseau Africa/Algiers).
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from .catalog import get_store

ALGIERS_TZ = ZoneInfo("Africa/Algiers")


def get_facts() -> dict:
    """Retourne les données du magasin depuis products.yaml."""
    return get_store()


def is_open_now() -> tuple[bool, str, str]:
    """
    Retourne (is_open, message_FR, message_AR) selon l'heure réelle Alger.
    Horaires : Sam–Jeu 09h–21h · Vendredi 14h30–21h
    """
    now = datetime.now(ALGIERS_TZ)
    weekday = now.weekday()  # 0=Lundi … 4=Vendredi … 6=Dimanche
    hour = now.hour + now.minute / 60.0

    s = get_facts()
    h = s.get("hours", {})

    if weekday == 4:  # Vendredi
        open_h, close_h = 14.5, 21.0
        days_fr = "Vendredi"
    else:
        open_h, close_h = 9.0, 21.0
        days_fr = h.get("weekday", {}).get("days_fr", "Sam–Jeu")

    is_open = open_h <= hour < close_h

    if is_open:
        rem_min = int((close_h - hour) * 60)
        if rem_min <= 60:
            msg_fr = f"✅ Oui, on est ouvert — on ferme dans {rem_min} min ⏰"
            msg_ar = f"✅ واه، المحل مفتوح — يسكر في {rem_min} دقيقة ⏰"
        else:
            close_str = f"{int(close_h)}h"
            msg_fr = f"✅ Oui, on est ouvert jusqu'à {close_str} 🟢"
            msg_ar = f"✅ واه، المحل مفتوح لحين الساعة {int(close_h)} 🟢"
    else:
        if weekday == 4 and hour < 14.5:
            msg_fr = "🕑 Aujourd'hui (vendredi) on ouvre à 14h30"
            msg_ar = "🕑 اليوم الجمعة، نفتحو من الساعة 2 ونص"
        elif hour >= 21.0:
            msg_fr = "🔒 Le magasin est fermé. On vous attend demain à 9h 😊"
            msg_ar = "🔒 المحل سكر الليلة. نستناوكم غدوة من الساعة 9 😊"
        else:
            msg_fr = "🔒 Le magasin est fermé. On ouvre à 9h 😊"
            msg_ar = "🔒 المحل مسكر. نفتحو من الساعة 9 😊"

    return is_open, msg_fr, msg_ar
