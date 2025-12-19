@echo off
REM Script pour vérifier l'état de PostgreSQL dans Docker

echo ========================================
echo Verification de PostgreSQL dans Docker
echo ========================================
echo.

echo 1. Etat des conteneurs :
echo ----------------------------------------
docker-compose ps
echo.

echo 2. Logs de l'application (dernieres lignes) :
echo ----------------------------------------
docker logs erp-btp --tail 20
echo.

echo 3. Test de connexion PostgreSQL :
echo ----------------------------------------
docker exec -it erp-btp-postgres psql -U fred -d client_erpbtp_victoire -c "\dt"
echo.

echo 4. Nombre de tables :
echo ----------------------------------------
docker exec -it erp-btp-postgres psql -U fred -d client_erpbtp_victoire -c "SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'public';"
echo.

pause
