# 1. Image de base (Python léger)
FROM python:3.10-slim

# 2. Variables d'environnement pour Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 3. Dossier de travail dans le conteneur
WORKDIR /app

# 4. Copier les dépendances et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copier tout le code
COPY . .

# 6. Créer les dossiers nécessaires
RUN mkdir -p data/pdf logs static

# 7. Exposer le port 8080
EXPOSE 8080

# 8. La commande de démarrage
CMD ["python", "main.py"]
