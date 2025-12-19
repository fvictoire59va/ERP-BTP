@echo off
REM Script pour construire et démarrer l'application ERP BTP avec Docker

echo ========================================
echo Construction de l'image Docker ERP BTP
echo ========================================
docker build -t erp-btp:latest .

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR: La construction de l'image a echoue
    echo Verifiez que Docker Desktop est demarre
    pause
    exit /b 1
)

echo.
echo ========================================
echo Demarrage du conteneur
echo ========================================
docker run -d ^
    --name erp-btp ^
    -p 8080:8080 ^
    -v "%cd%\data:/app/data" ^
    -v "%cd%\logs:/app/logs" ^
    --restart unless-stopped ^
    erp-btp:latest

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR: Le demarrage du conteneur a echoue
    echo Le conteneur existe peut-etre deja. Tentative de suppression et redemarrage...
    docker stop erp-btp 2>nul
    docker rm erp-btp 2>nul
    
    docker run -d ^
        --name erp-btp ^
        -p 8080:8080 ^
        -v "%cd%\data:/app/data" ^
        -v "%cd%\logs:/app/logs" ^
        --restart unless-stopped ^
        erp-btp:latest
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS: Application demarree !
    echo ========================================
    echo L'application est accessible a l'adresse : http://localhost:8080
    echo.
    echo Commandes utiles :
    echo   - Voir les logs : docker logs -f erp-btp
    echo   - Arreter : docker stop erp-btp
    echo   - Redemarrer : docker restart erp-btp
    echo   - Supprimer : docker stop erp-btp ^&^& docker rm erp-btp
    echo.
) else (
    echo.
    echo ERREUR: Impossible de demarrer le conteneur
    pause
    exit /b 1
)

pause
