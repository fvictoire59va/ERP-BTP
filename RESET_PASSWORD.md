# Réinitialisation de mot de passe - ERP BTP

## Fonctionnalité ajoutée

La fonctionnalité de réinitialisation de mot de passe a été implémentée avec les composants suivants :

## 1. Backend (AuthManager)

### Nouvelles méthodes dans `erp/core/auth.py` :

#### `SessionManager.create_reset_token(user_id: str) -> str`
- Crée un token de réinitialisation unique
- Durée de validité : 1 heure
- Retourne le token généré

#### `SessionManager.get_user_id_from_reset_token(reset_token: str) -> Optional[str]`
- Vérifie la validité du token
- Retourne l'ID utilisateur si le token est valide
- Supprime automatiquement les tokens expirés

#### `AuthManager.request_password_reset(email: str) -> Optional[str]`
- Demande une réinitialisation pour un email donné
- Vérifie que l'utilisateur existe et est actif
- Génère et retourne un token de réinitialisation
- Pour la sécurité : ne révèle pas si l'email existe ou non

#### `AuthManager.reset_password(reset_token: str, new_password: str) -> bool`
- Réinitialise le mot de passe avec un token valide
- Hash le nouveau mot de passe
- Met à jour l'utilisateur dans la base de données
- Supprime le token après utilisation

## 2. Interface utilisateur (AuthPanel)

### Nouvelles vues dans `erp/ui/panels/auth.py` :

#### Lien "Mot de passe oublié ?"
- Ajouté sur la page de connexion
- Redirige vers le formulaire de réinitialisation

#### Formulaire de demande de réinitialisation
- Champ : Email
- Valide le format de l'email
- Génère un token et affiche un message de succès
- Redirige automatiquement vers le formulaire de nouveau mot de passe après 2 secondes

#### Formulaire de nouveau mot de passe
- Champs : Nouveau mot de passe, Confirmation
- Validation :
  - Les deux mots de passe doivent correspondre
  - Minimum 6 caractères
  - Token valide et non expiré
- Affiche une notification de succès
- Redirige vers la page de connexion après réinitialisation

## 3. Flux d'utilisation

### Étape 1 : Demande de réinitialisation
1. Cliquer sur "Mot de passe oublié ?" sur la page de connexion
2. Entrer son adresse email
3. Cliquer sur "Envoyer"
4. Un token est généré (validité : 1 heure)

### Étape 2 : Définir le nouveau mot de passe
1. Automatiquement redirigé vers le formulaire (après 2 secondes)
2. Entrer le nouveau mot de passe (minimum 6 caractères)
3. Confirmer le nouveau mot de passe
4. Cliquer sur "Réinitialiser"

### Étape 3 : Connexion
1. Notification de succès affichée
2. Redirection automatique vers la page de connexion
3. Se connecter avec le nouveau mot de passe

## 4. Sécurité

### Mesures de sécurité implémentées :

- **Token à usage unique** : Le token est supprimé après utilisation
- **Expiration** : Les tokens expirent après 1 heure
- **Hash des mots de passe** : Les nouveaux mots de passe sont hashés avec salt
- **Validation** : Vérification du format email et longueur minimum du mot de passe
- **Messages génériques** : Ne révèle pas si un email existe dans le système
- **Logs** : Tous les événements sont enregistrés pour audit

## 5. Note sur l'envoi d'emails (Production)

### Version actuelle (Développement)
Le token est généré et l'utilisateur passe directement au formulaire de nouveau mot de passe.

### Pour la production
Il faudrait ajouter :
```python
# Exemple avec smtplib ou un service comme SendGrid
def send_reset_email(email: str, reset_token: str):
    reset_link = f"https://votre-domaine.com/reset-password?token={reset_token}"
    subject = "Réinitialisation de votre mot de passe"
    body = f"""
    Bonjour,
    
    Vous avez demandé la réinitialisation de votre mot de passe.
    Cliquez sur le lien ci-dessous pour définir un nouveau mot de passe :
    
    {reset_link}
    
    Ce lien expire dans 1 heure.
    
    Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.
    """
    # Envoi de l'email...
```

## 6. Tests recommandés

1. Demander une réinitialisation avec un email valide
2. Demander une réinitialisation avec un email invalide/inexistant
3. Tester l'expiration du token (après 1 heure)
4. Tenter d'utiliser le même token deux fois
5. Vérifier la validation des mots de passe (longueur, correspondance)
6. Se connecter avec le nouveau mot de passe

## 7. Améliorations futures possibles

- Envoi d'email avec lien de réinitialisation
- Limitation du nombre de demandes par période
- Historique des changements de mot de passe
- Politique de mot de passe fort (majuscules, chiffres, caractères spéciaux)
- Notification email après changement de mot de passe
- Interface admin pour réinitialiser les mots de passe utilisateurs
