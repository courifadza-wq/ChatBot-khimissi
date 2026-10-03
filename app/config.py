# ============================================================
#  Bot WhatsApp — Ventes + Commandes  (client)
#  Étape 1 : Configuration par variables d'environnement
# ============================================================
import os
from dataclasses import dataclass, field
from pathlib import Path
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    # ---- Serveur ----
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # ---- WhatsApp Cloud API (Meta) ----
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_ID: str = os.getenv("WHATSAPP_PHONE_ID", "")
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    # Version de l'API Graph de Meta (à adapter si besoin)
    GRAPH_API_VERSION: str = os.getenv("GRAPH_API_VERSION", "v21.0")
    # Numéro du propriétaire (format: 213XXXXXXXXX) pour les commandes secrètes
    OWNER_PHONE: str = os.getenv("OWNER_PHONE", "213554698746")

    # ---- Email du commerçant (SMTP) ----
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")  # mot de passe applicatif
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    STORE_EMAIL_TO: str = os.getenv("STORE_EMAIL_TO", "")  # qui reçoit les commandes
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "Mon Magasin")

    # ---- NLP / Intentions ----
    # "hybrid": règles + classifieur ML ; "rules": règles seules (0 dépendance IA)
    NL_MODE: str = os.getenv("NL_MODE", "hybrid")

    # ---- Store config ----
    PRODUCTS_FILE: Path = field(default_factory=lambda: BASE_DIR / "data" / "products.yaml")
    INTENTS_FILE: Path = field(default_factory=lambda: BASE_DIR / "data" / "intents.yaml")

    # ---- Base de conversation (état des commandes en cours) ----
    # mémoire simple : dict phone -> état. Pour la prod, remplacer par Redis.
    order_state: dict = field(default_factory=dict, repr=False)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
