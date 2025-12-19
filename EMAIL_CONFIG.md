# Configuration de l'envoi d'emails

## Vue d'ensemble

La fonctionnalité de réinitialisation de mot de passe utilise l'envoi d'emails via SMTP.

## Configuration

### 1. Variables d'environnement

Ajoutez ces variables dans votre fichier `.env` :

```bash
# URL de l'application
APP_URL=http://localhost:8080

# Configuration SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=votre-email@gmail.com
SMTP_PASSWORD=votre-mot-de-passe-application
SMTP_FROM=votre-email@gmail.com
```

### 2. Configuration Gmail

Pour utiliser Gmail comme serveur SMTP :

1. **Activer la validation en deux étapes** sur votre compte Google
2. **Créer un mot de passe d'application** :
   - Allez sur https://myaccount.google.com/security
   - Recherchez "Mots de passe des applications"
   - Sélectionnez "Mail" et "Ordinateur Windows"
   - Copiez le mot de passe généré (16 caractères)
   - Utilisez-le dans `SMTP_PASSWORD`

### 3. Autres fournisseurs SMTP

#### Outlook/Hotmail
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=votre-email@outlook.com
```

#### SendGrid
```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=votre-api-key-sendgrid
```

#### OVH
```bash
SMTP_SERVER=ssl0.ovh.net
SMTP_PORT=587
SMTP_USERNAME=votre-email@domaine.fr
```

## Fonctionnement

1. L'utilisateur clique sur "Mot de passe oublié ?" sur la page de connexion
2. Il entre son adresse email
3. Le système génère un token de réinitialisation (valide 1 heure)
4. Un email est envoyé avec un lien : `http://localhost:8080/reset-password?token=xxx`
5. L'utilisateur clique sur le lien et entre son nouveau mot de passe
6. Le mot de passe est mis à jour et l'utilisateur est redirigé vers la page de connexion

## Mode de développement

Si la configuration SMTP n'est pas définie, le système affiche le lien de réinitialisation directement à l'écran au lieu d'envoyer un email.

## Test

Pour tester l'envoi d'emails :

1. Configurez les variables d'environnement dans `.env`
2. Redémarrez l'application
3. Cliquez sur "Mot de passe oublié ?"
4. Entrez une adresse email valide
5. Vérifiez votre boîte de réception

## Dépannage

### L'email n'est pas reçu

1. **Vérifiez les spams** : L'email peut être filtré
2. **Vérifiez les logs** : `docker logs erp-btp --tail 50`
3. **Testez la connexion SMTP** :
   ```python
   import smtplib
   server = smtplib.SMTP('smtp.gmail.com', 587)
   server.starttls()
   server.login('votre-email@gmail.com', 'votre-mot-de-passe')
   server.quit()
   ```

### Erreur d'authentification

- Gmail : Utilisez un mot de passe d'application, pas votre mot de passe principal
- Outlook : Vérifiez que SMTP est activé dans les paramètres
- Vérifiez que les identifiants sont corrects dans `.env`

### Le lien ne fonctionne pas

- Vérifiez que `APP_URL` correspond à l'URL réelle de votre application
- Le token expire après 1 heure
- Le token ne peut être utilisé qu'une seule fois

## Sécurité

- Les tokens de réinitialisation expirent après 1 heure
- Les tokens sont stockés en mémoire (perdus au redémarrage)
- Les liens de réinitialisation ne peuvent être utilisés qu'une fois
- Les mots de passe sont hashés avant stockage dans la base de données
