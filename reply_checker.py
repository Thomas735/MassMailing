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

    def check_replies(self, history_entries):
        """
        Checks for replies in the INBOX for the given history entries.
        Returns a list of UUIDs that have received a reply.
        """
        replied_uuids = []
        
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_user, self.email_pass)
            mail.select("inbox")
        except Exception as e:
            self.logger.error(f"IMAP Connection Error: {e}")
            return []

        # Optimization: Get all messages from the last X days to avoid checking everything
        # For simplicity in this demo, we'll search by sender for each pending entry
        
        for entry in history_entries:
            # Skip if already replied or not sent
            if entry.get("replied") or entry.get("status") != "Envoyé":
                continue

            recipient_email = entry.get("email")
            sent_date_str = entry.get("date")
            
            if not recipient_email or not sent_date_str:
                continue

            try:
                sent_date = datetime.fromisoformat(sent_date_str)
            except ValueError:
                continue

            # Search for emails FROM this recipient
            # IMAP search is not very granular with time, so we fetch all from sender and filter by date
            try:
                status, messages = mail.search(None, f'(FROM "{recipient_email}")')
                if status != "OK":
                    continue
                
                msg_ids = messages[0].split()
                if not msg_ids:
                    continue
                
                # Check dates of specific messages
                for msg_id in reversed(msg_ids): # Check newest first
                    res, msg_data = mail.fetch(msg_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            # Parse Date
                            if msg["Date"]:
                                date_tuple = email.utils.parsedate_tz(msg["Date"])
                                if date_tuple:
                                    msg_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                                    
                                    # If message is newer than sent date, it's a reply
                                    if msg_date > sent_date:
                                        replied_uuids.append(entry.get("uuid"))
                                        break # Found a reply, move to next entry
            except Exception as e:
                self.logger.error(f"Error checking {recipient_email}: {e}")
                continue

        try:
            mail.close()
            mail.logout()
        except:
            pass
            
        return replied_uuids
