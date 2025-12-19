@echo off
REM Script pour utiliser Docker Compose (plus simple)

echo ========================================
echo Demarrage avec Docker Compose
echo ========================================

docker-compose up --build -d

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS: Application demarree !
    echo ========================================
    echo L'application est accessible a l'adresse : http://localhost:8080
    echo.
    echo Commandes utiles :
    echo   - Voir les logs : docker-compose logs -f
    echo   - Arreter : docker-compose down
    echo   - Redemarrer : docker-compose restart
    echo.
) else (
    echo.
    echo ERREUR: Verifiez que Docker Desktop est demarre
    pause
    exit /b 1
)

pause
