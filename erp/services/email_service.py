"""
Service d'envoi d'emails pour l'application ERP BTP
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from erp.utils.logger import get_logger

logger = get_logger(__name__)


class EmailService:
    """Service d'envoi d'emails"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.smtp_from = os.getenv('SMTP_FROM', self.smtp_username)
        self.app_url = os.getenv('APP_URL', 'http://localhost:8080')
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Envoie un email
        
        Args:
            to_email: Adresse email du destinataire
            subject: Sujet de l'email
            html_content: Contenu HTML de l'email
            text_content: Contenu texte alternatif (optionnel)
            
        Returns:
            bool: True si envoyé avec succès, False sinon
        """
        if not self.smtp_username or not self.smtp_password:
            logger.warning("Configuration SMTP manquante, email non envoyé")
            return False
        
        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_from
            msg['To'] = to_email
            
            # Ajouter les contenus
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            # Connexion et envoi
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email envoyé avec succès à {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email à {to_email}: {e}")
            return False
    
    def send_password_reset_email(self, to_email: str, reset_token: str, username: str) -> bool:
        """
        Envoie un email de réinitialisation de mot de passe
        
        Args:
            to_email: Adresse email du destinataire
            reset_token: Token de réinitialisation
            username: Nom d'utilisateur
            
        Returns:
            bool: True si envoyé avec succès, False sinon
        """
        reset_link = f"{self.app_url}/reset-password?token={reset_token}"
        
        subject = "Réinitialisation de votre mot de passe - ERP BTP"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9fafb; padding: 30px; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 30px; 
                    background-color: #2563eb; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                .warning {{ background-color: #fef3c7; padding: 15px; border-left: 4px solid #f59e0b; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Réinitialisation de mot de passe</h1>
                </div>
                <div class="content">
                    <p>Bonjour <strong>{username}</strong>,</p>
                    
                    <p>Vous avez demandé la réinitialisation de votre mot de passe pour votre compte ERP BTP.</p>
                    
                    <p>Cliquez sur le bouton ci-dessous pour définir un nouveau mot de passe :</p>
                    
                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">Réinitialiser mon mot de passe</a>
                    </p>
                    
                    <p>Ou copiez ce lien dans votre navigateur :</p>
                    <p style="word-break: break-all; background-color: #e5e7eb; padding: 10px; border-radius: 5px;">
                        {reset_link}
                    </p>
                    
                    <div class="warning">
                        <strong>⚠️ Important :</strong>
                        <ul>
                            <li>Ce lien est valide pendant <strong>1 heure</strong></li>
                            <li>Si vous n'avez pas demandé cette réinitialisation, ignorez cet email</li>
                            <li>Ne partagez jamais ce lien avec personne</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
                    <p>&copy; 2025 ERP BTP - Tous droits réservés</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Bonjour {username},

Vous avez demandé la réinitialisation de votre mot de passe pour votre compte ERP BTP.

Cliquez sur le lien ci-dessous pour définir un nouveau mot de passe :
{reset_link}

⚠️ Important :
- Ce lien est valide pendant 1 heure
- Si vous n'avez pas demandé cette réinitialisation, ignorez cet email
- Ne partagez jamais ce lien avec personne

Cet email a été envoyé automatiquement, merci de ne pas y répondre.

© 2025 ERP BTP - Tous droits réservés
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_subscription_expired_email(self, to_email: str, username: str, client_id: str, renewal_link: str) -> bool:
        """
        Envoie un email d'avertissement d'expiration d'abonnement
        
        Args:
            to_email: Adresse email du destinataire
            username: Nom d'utilisateur
            client_id: ID du client
            renewal_link: Lien de prolongation d'abonnement
            
        Returns:
            bool: True si envoyé avec succès, False sinon
        """
        subject = "⚠️ Votre abonnement ERP BTP a expiré"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9fafb; padding: 30px; }}
                .button {{ 
                    display: inline-block; 
                    padding: 12px 30px; 
                    background-color: #16a34a; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                .warning {{ background-color: #fee2e2; padding: 15px; border-left: 4px solid #dc2626; margin: 20px 0; }}
                .info {{ background-color: #dbeafe; padding: 15px; border-left: 4px solid #0284c7; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ Abonnement expiré</h1>
                </div>
                <div class="content">
                    <p>Bonjour <strong>{username}</strong>,</p>
                    
                    <div class="warning">
                        <strong>Votre abonnement ERP BTP a expiré</strong>
                        <p>Vous ne pouvez plus accéder à l'application ERP BTP. Veuillez prolonger votre abonnement pour continuer.</p>
                    </div>
                    
                    <p>Nous vous proposons plusieurs options pour prolonger votre abonnement :</p>
                    
                    <p style="text-align: center;">
                        <a href="{renewal_link}" class="button">Prolonger mon abonnement</a>
                    </p>
                    
                    <div class="info">
                        <strong>ℹ️ À savoir :</strong>
                        <ul>
                            <li>Ce lien vous permettra de prolonger directement votre abonnement</li>
                            <li>Vous retrouverez toutes vos données après la prolongation</li>
                            <li>Le lien est valide pendant 24 heures</li>
                        </ul>
                    </div>
                    
                    <p><strong>Besoin d'aide ?</strong></p>
                    <p>Si vous avez des questions sur votre abonnement, veuillez <a href="mailto:support@erp-btp.com">contacter notre support</a>.</p>
                </div>
                <div class="footer">
                    <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
                    <p>&copy; 2025 ERP BTP - Tous droits réservés</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Bonjour {username},

⚠️ VOTRE ABONNEMENT ERP BTP A EXPIRÉ

Vous ne pouvez plus accéder à l'application ERP BTP. Veuillez prolonger votre abonnement pour continuer.

Cliquez sur le lien ci-dessous pour prolonger directement votre abonnement :
{renewal_link}

À savoir :
- Ce lien vous permettra de prolonger directement votre abonnement
- Vous retrouverez toutes vos données après la prolongation
- Le lien est valide pendant 24 heures

Besoin d'aide ? Contactez notre support : support@erp-btp.com

Cet email a été envoyé automatiquement, merci de ne pas y répondre.

© 2025 ERP BTP - Tous droits réservés
        """
        
        return self.send_email(to_email, subject, html_content, text_content)


# Instance singleton
_email_service = None

def get_email_service() -> EmailService:
    """Retourne l'instance singleton du service email"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
