# Installation de PostgreSQL client pour Windows

## Option 1 : Installer PostgreSQL complet

1. Téléchargez : https://www.postgresql.org/download/windows/
2. Installez (version 15 recommandée)
3. Ajoutez au PATH : `C:\Program Files\PostgreSQL\15\bin`

## Option 2 : Utiliser le script Docker (Recommandé)

Utilisez `migrate_to_cloud_sql_docker.bat` qui utilise Docker avec une image PostgreSQL temporaire.

**Avantages** :
- Pas besoin d'installer PostgreSQL
- Fonctionne immédiatement
- Version PostgreSQL contrôlée

**Utilisation** :
```bash
.\migrate_to_cloud_sql_docker.bat
```

## Option 3 : Ajouter PostgreSQL au PATH manuellement

Si PostgreSQL est déjà installé mais pas dans le PATH :

1. Recherchez l'installation :
   ```powershell
   Get-ChildItem -Path "C:\" -Filter "pg_dump.exe" -Recurse -ErrorAction SilentlyContinue
   ```

2. Ajoutez au PATH système :
   - Panneau de configuration > Système > Paramètres système avancés
   - Variables d'environnement
   - Variable système "Path"
   - Ajouter : `C:\Program Files\PostgreSQL\XX\bin`

3. Redémarrez PowerShell

## Vérification

```powershell
pg_dump --version
```

Devrait afficher : `pg_dump (PostgreSQL) 15.x`
