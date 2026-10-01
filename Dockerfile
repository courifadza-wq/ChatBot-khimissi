# ============================================================
#  Image de production pour déploiement Coolify / Docker
#  Volume persistant requis : /app/data  (mémoire SQLite)
# ============================================================
FROM python:3.13-slim

# Évite les logs bufférisés
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copie des dépendances (permet le cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code applicatif et des données initiales
COPY app ./app
COPY data ./data

# ── Répertoire de données persistant ──
# Coolify montera un volume sur /app/data pour que bot_memory.db
# survive aux redémarrages et aux mises à jour du conteneur.
RUN mkdir -p /app/data && chmod 777 /app/data

# Port exposé (Coolify peut le redéfinir via PORT env)
EXPOSE 8000

# Utilisateur non-root (sécurité)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Lancement uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
