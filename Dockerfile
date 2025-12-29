# 1. Image de base (Python léger)
FROM python:3.10-slim

# 2. Variables d'environnement pour Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 3. Dossier de travail dans le conteneur
WORKDIR /app

# 4. Installer curl pour le healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 5. Copier les dépendances et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copier tout le code
COPY . .

# 7. Créer les dossiers nécessaires
RUN mkdir -p data/pdf logs static

# 8. Exposer le port 8080
EXPOSE 8080

# 8. La commande de démarrage
CMD ["python", "main.py"]
