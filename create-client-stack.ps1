# Script de création automatique d'une stack client dans Portainer
# Usage: .\create-client-stack.ps1 -ClientName "dupont" -PostgresPassword "motdepasse123" -SecretKey "cle-secrete-32-chars"

param(
    [Parameter(Mandatory=$true)]
    [string]$ClientName,
    
    [Parameter(Mandatory=$true)]
    [string]$PostgresPassword,
    
    [Parameter(Mandatory=$true)]
    [string]$SecretKey,
    
    [string]$InitialPassword = "",
    [string]$PortainerUrl = "https://localhost:9443",
    [string]$PortainerUser = "admin",
    [string]$PortainerPassword = "",
    [string]$EnvironmentId = "2",
    [int]$BasePort = 8080
)

# Désactiver la vérification SSL pour les certificats auto-signés
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
Add-Type @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(
            ServicePoint srvPoint, X509Certificate certificate,
            WebRequest request, int certificateProblem) {
            return true;
        }
    }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Création d'une stack client Portainer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Validation du mot de passe Portainer
if ([string]::IsNullOrWhiteSpace($PortainerPassword)) {
    $securePassword = Read-Host "Mot de passe Portainer" -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
    $PortainerPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
}

# Générer un mot de passe initial temporaire si non fourni
if ([string]::IsNullOrWhiteSpace($InitialPassword)) {
    # Générer un mot de passe aléatoire de 12 caractères
    $InitialPassword = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 12 | ForEach-Object {[char]$_})
    Write-Host "Mot de passe temporaire généré automatiquement" -ForegroundColor Cyan
}

try {
    # 1. Authentification à Portainer
    Write-Host "[1/4] Authentification à Portainer..." -ForegroundColor Yellow
    $authBody = @{
        username = $PortainerUser
        password = $PortainerPassword
    } | ConvertTo-Json

    $authResponse = Invoke-RestMethod -Uri "$PortainerUrl/api/auth" -Method Post -Body $authBody -ContentType "application/json"
    $token = $authResponse.jwt
    Write-Host "✓ Authentification réussie" -ForegroundColor Green

    # Headers pour les prochaines requêtes
    $headers = @{
        "X-API-Key" = $token
    }

    # 2. Récupérer la liste des stacks existantes
    Write-Host "[2/4] Récupération des stacks existantes..." -ForegroundColor Yellow
    $stacks = Invoke-RestMethod -Uri "$PortainerUrl/api/stacks" -Method Get -Headers $headers
    
    # Compter les stacks qui commencent par "client-"
    $clientStacks = $stacks | Where-Object { $_.Name -like "client-*" }
    $clientCount = $clientStacks.Count
    
    # Calculer le prochain port disponible
    $nextPort = $BasePort + $clientCount
    
    Write-Host "✓ Nombre de clients existants: $clientCount" -ForegroundColor Green
    Write-Host "✓ Port attribué: $nextPort" -ForegroundColor Green

    # 3. Vérifier si la stack existe déjà
    $existingStack = $stacks | Where-Object { $_.Name -eq "client-$ClientName" }
    if ($existingStack) {
        Write-Host "✗ Erreur: Une stack pour le client '$ClientName' existe déjà!" -ForegroundColor Red
        exit 1
    }

    # 4. Créer la nouvelle stack
    Write-Host "[3/4] Création de la stack client-$ClientName..." -ForegroundColor Yellow
    
    $stackBody = @{
        name = "client-$ClientName"
        repositoryURL = "https://github.com/fvictoire59va/ERP-BTP"
        repositoryReferenceName = "refs/heads/main"
        composeFile = "docker-compose.portainer.yml"
        repositoryAuthentication = $false
        env = @(
            @{ name = "CLIENT_NAME"; value = $ClientName }
            @{ name = "POSTGRES_PASSWORD"; value = $PostgresPassword }
            @{ name = "SECRET_KEY"; value = $SecretKey }
            @{ name = "APP_PORT"; value = $nextPort.ToString() }
            @{ name = "POSTGRES_DB"; value = "erp_btp" }
            @{ name = "POSTGRES_USER"; value = "erp_user" }
            @{ name = "POSTGRES_PORT"; value = (5432 + $clientCount).ToString() }
            @{ name = "INITIAL_USERNAME"; value = $ClientName }
            @{ name = "INITIAL_PASSWORD"; value = $InitialPassword }
        )
    } | ConvertTo-Json -Depth 10

    $createResponse = Invoke-RestMethod -Uri "$PortainerUrl/api/stacks?type=2&method=repository&endpointId=$EnvironmentId" `
        -Method Post `
        -Body $stackBody `
        -ContentType "application/json" `
        -Headers $headers

    Write-Host "✓ Stack créée avec succès (ID: $($createResponse.Id))" -ForegroundColor Green

    # 5. Afficher le résumé
    Write-Host ""
    Write-Host "[4/4] Résumé de la configuration:" -ForegroundColor Yellow
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host "Nom du client    : $ClientName" -ForegroundColor White
    Write-Host "Nom de la stack  : client-$ClientName" -ForegroundColor White
    Write-Host "Port application : $nextPort" -ForegroundColor White
    Write-Host "Port PostgreSQL  : $(5432 + $clientCount)" -ForegroundColor White
    Write-Host "URL accès        : http://votre-serveur:$nextPort" -ForegroundColor White
    Write-Host "Base de données  : erp_btp" -ForegroundColor White
    Write-Host "Utilisateur DB   : erp_user" -ForegroundColor White
    Write-Host ""
    Write-Host "Identifiants de connexion temporaires:" -ForegroundColor Yellow
    Write-Host "  Nom d'utilisateur : $ClientName" -ForegroundColor Green
    Write-Host "  Mot de passe      : $InitialPassword" -ForegroundColor Green
    Write-Host "  (À changer lors de la première connexion)" -ForegroundColor Gray
    Write-Host "=================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "✓ Stack déployée avec succès!" -ForegroundColor Green
    Write-Host "  Accédez à Portainer pour surveiller le déploiement." -ForegroundColor Gray

} catch {
    Write-Host ""
    Write-Host "✗ Erreur lors de la création de la stack:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host $_.ErrorDetails.Message -ForegroundColor Red
    }
    exit 1
}
