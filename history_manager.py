import json
import os
from datetime import datetime

class HistoryManager:
    def __init__(self, filepath="history.json"):
        self.filepath = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump([], f)

    def add_entry(self, email, variable, subject, uuid_str, status="Sent", content=""):
        entry = {
            "date": datetime.now().isoformat(),
            "email": email,
            "variable": variable,
            "subject": subject,
            "uuid": uuid_str,
            "status": status,
            "replied": False,
            "content": content,
            "replies": []
        }
        
        try:
            with open(self.filepath, 'r') as f:
                history = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            history = []
            
        history.append(entry)
        
        with open(self.filepath, 'w') as f:
            json.dump(history, f, indent=4)
            
    def get_history(self):
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, 'r') as f:
                history = json.load(f)
            # Migration/Normalization for old entries
            for entry in history:
                if "replied" not in entry: entry["replied"] = False
                if "subject" not in entry: entry["subject"] = ""
                if "content" not in entry: entry["content"] = "Contenu non disponible pour cet ancien email."
                if "replies" not in entry: entry["replies"] = []
                for reply in entry["replies"]:
                    if "read" not in reply:
                        reply["read"] = False
            return history
        except json.JSONDecodeError:
            return []

    def add_reply(self, uuid_str, reply_dict):
        history = self.get_history()
        updated = False
        if "read" not in reply_dict:
            reply_dict["read"] = False
            
        for entry in history:
            if entry.get("uuid") == uuid_str:
                entry["replied"] = True
                if "replies" not in entry:
                    entry["replies"] = []
                entry["replies"].append(reply_dict)
                updated = True
                break
        
        if updated:
            with open(self.filepath, 'w') as f:
                json.dump(history, f, indent=4)
        return updated

    def mark_reply_read(self, parent_uuid, reply_date):
        history = self.get_history()
        updated = False
        for entry in history:
            if entry.get("uuid") == parent_uuid:
                for reply in entry.get("replies", []):
                    if reply.get("date") == reply_date:
                        reply["read"] = True
                        updated = True
                        break
            if updated:
                break
        
        if updated:
            with open(self.filepath, 'w') as f:
                json.dump(history, f, indent=4)
        return updated

    def delete_entry(self, uuid_str):
        history = self.get_history()
        initial_len = len(history)
        history = [entry for entry in history if entry.get("uuid") != uuid_str]
        
        if len(history) < initial_len:
            with open(self.filepath, 'w') as f:
                json.dump(history, f, indent=4)
            return True
        return False

    def delete_by_email(self, email_target):
        history = self.get_history()
        initial_len = len(history)
        history = [entry for entry in history if entry.get("email") != email_target]
        
        if len(history) < initial_len:
            with open(self.filepath, 'w') as f:
                json.dump(history, f, indent=4)
            return True
        return False

    def clear_all(self):
        with open(self.filepath, 'w') as f:
            json.dump([], f)
        return True

    def clear_by_filter(self, active_filter):
        if active_filter == "Tous":
            return self.clear_all()
        
        history = self.get_history()
        initial_len = len(history)
        updated = False
        
        if active_filter == "Envoyés":
            history = [e for e in history if e.get("status") not in ("Envoyé", "Sent")]
            updated = len(history) < initial_len
            
        elif active_filter == "Échecs":
            history = [e for e in history if e.get("status") != "Échec"]
            updated = len(history) < initial_len
            
        elif active_filter == "Brouillons":
            history = [e for e in history if e.get("status") != "Brouillon"]
            updated = len(history) < initial_len
            
        elif active_filter == "Consultées":
            for entry in history:
                initial_replies = len(entry.get("replies", []))
                if initial_replies > 0:
                    entry["replies"] = [r for r in entry.get("replies", []) if not r.get("read")]
                    if len(entry["replies"]) < initial_replies:
                        updated = True

        elif active_filter == "Non consultées":
            for entry in history:
                initial_replies = len(entry.get("replies", []))
                if initial_replies > 0:
                    entry["replies"] = [r for r in entry.get("replies", []) if r.get("read")]
                    if len(entry["replies"]) < initial_replies:
                        updated = True
        
        if updated:
            with open(self.filepath, 'w') as f:
                json.dump(history, f, indent=4)
        return updated

