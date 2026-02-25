import smtplib
from email.message import EmailMessage
from email.utils import make_msgid, formatdate
import logging
import ssl

class MailSender:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def send_email(self, smtp_server, smtp_port, username, password, to_address, subject, content_html):
        """
        Sends an email using standard SMTP.
        
        Args:
            smtp_server (str): The SMTP server address.
            smtp_port (str): The SMTP server port.
            username (str): The user's email address.
            password (str): The user's application password.
            to_address (str): Recipient email address.
            subject (str): Subject line.
            content_html (str): The HTML content of the email body.
        """
        try:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = username
            msg['To'] = to_address
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid(domain=username.split('@')[1] if '@' in username else "localhost")
            
            # Text fallback is crucial for anti-spam
            # We strip HTML tags roughly for the text version
            import re
            text_content = re.sub('<[^<]+>', '', content_html).strip()
            if not text_content:
                text_content = "Veuillez activer l'affichage HTML pour voir cet email."
            
            msg.set_content(text_content)
            msg.add_alternative(content_html, subtype='html')

            context = ssl.create_default_context()
            
            port = int(smtp_port)
            if port == 465:
                # SSL connections
                with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                    server.login(username, password)
                    server.send_message(msg)
            else:
                # TLS connections (587, 25, etc.)
                with smtplib.SMTP(smtp_server, port) as server:
                    server.starttls(context=context)
                    server.login(username, password)
                    server.send_message(msg)
                    
            self.logger.info(f"Email sent successfully to {to_address} via {smtp_server}:{smtp_port}")
            return True, "Email envoyé avec succès"
            
        except smtplib.SMTPAuthenticationError:
            self.logger.error("Authentication failed. Check your email and app password.")
            return False, "Erreur d'authentification. Vérifiez le mot de passe d'application."
        except Exception as e:
            self.logger.error(f"Failed to send email to {to_address}: {e}")
            return False, str(e)
