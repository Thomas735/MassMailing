import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import logging

class ReplyChecker:
    def __init__(self, imap_server, email_user, email_pass):
        self.imap_server = imap_server
        self.email_user = email_user
        self.email_pass = email_pass
        self.logger = logging.getLogger(__name__)

    def get_email_body(self, msg):
        import re
        import html
        
        body_plain = None
        body_html = None
        
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))

                # skip any text/plain (txt) attachments
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    body_plain = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif ctype == 'text/html' and 'attachment' not in cdispo:
                    body_html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            ctype = msg.get_content_type()
            payload = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            if ctype == 'text/plain':
                body_plain = payload
            elif ctype == 'text/html':
                body_html = payload
            else:
                body_plain = payload

        if body_plain:
            return body_plain.strip()
        elif body_html:
            # Basic HTML to text conversion for readability
            text = html.unescape(body_html)
            # Replace common block tags with newlines
            text = re.sub(r'<(br|p|div|h[1-6]|tr|li|blockquote)[^>]*>', '\n', text, flags=re.IGNORECASE)
            # Remove <style> and <script> blocks completely
            text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', text, flags=re.IGNORECASE | re.DOTALL)
            # Remove all remaining HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            # Remove extra blank lines and spaces
            text = re.sub(r'\n\s*\n', '\n\n', text)
            return text.strip()
            
        return "Contenu non lisible."

    def check_replies(self, history_entries):
        """
        Checks for replies in the INBOX for the given history entries.
        Returns a list of dicts with reply details.
        """
        replies_found = []
        
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_user, self.email_pass)
            mail.select("inbox")
        except Exception as e:
            self.logger.error(f"IMAP Connection Error: {e}")
            return []
        
        for entry in history_entries:
            # We skip drafts/failures. We don't skip if already replied, 
            # because there might be multiple replies or a newer one, 
            # though for simplicity we only checked unreplied previously.
            # Let's check all Sent emails to catch late replies or multiple replies 
            # (assuming we track which ones we already downloaded, but for now we'll just get the latest).
            if entry.get("status") != "Envoyé":
                continue

            recipient_email = entry.get("email")
            sent_date_str = entry.get("date")
            
            if not recipient_email or not sent_date_str:
                continue

            try:
                sent_date = datetime.fromisoformat(sent_date_str)
            except ValueError:
                continue

            try:
                status, messages = mail.search(None, f'(FROM "{recipient_email}")')
                if status != "OK":
                    continue
                
                msg_ids = messages[0].split()
                if not msg_ids:
                    continue
                
                # We need to find replies that we haven't already saved.
                # The history entry might have a list of 'replies'.
                existing_reply_dates = [r.get("date") for r in entry.get("replies", [])]
                
                for msg_id in reversed(msg_ids):
                    res, msg_data = mail.fetch(msg_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            if msg["Date"]:
                                date_tuple = email.utils.parsedate_tz(msg["Date"])
                                if date_tuple:
                                    msg_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                                    msg_date_iso = msg_date.isoformat()
                                    
                                    if msg_date > sent_date and msg_date_iso not in existing_reply_dates:
                                        # Decode Subject
                                        subject = ""
                                        if msg["Subject"]:
                                            for part_subj, part_enc in decode_header(msg["Subject"]):
                                                if isinstance(part_subj, bytes):
                                                    subject += part_subj.decode(part_enc or "utf-8", errors="ignore")
                                                else:
                                                    subject += str(part_subj)
                                        
                                        body = self.get_email_body(msg)
                                        
                                        reply_dict = {
                                            "uuid": entry.get("uuid"),
                                            "date": msg_date_iso,
                                            "email": recipient_email,
                                            "subject": subject,
                                            "content": body
                                        }
                                        replies_found.append(reply_dict)
                                        # We append it, but we continue processing other msg_ids to get ALL new replies
            except Exception as e:
                self.logger.error(f"Error checking {recipient_email}: {e}")
                continue

        try:
            mail.close()
            mail.logout()
        except:
            pass
            
        return replies_found
