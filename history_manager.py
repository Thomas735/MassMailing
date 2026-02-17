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

    def add_entry(self, email, variable, uuid_str, status="Sent"):
        entry = {
            "date": datetime.now().isoformat(),
            "email": email,
            "variable": variable,
            "uuid": uuid_str,
            "status": status,
            "read": False,
            "replied": False
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
                if "read" not in entry: entry["read"] = False
                if "replied" not in entry: entry["replied"] = False
            return history
        except json.JSONDecodeError:
            return []

    def update_status(self, uuid_str, replied=None, read=None):
        history = self.get_history()
        updated = False
        for entry in history:
            if entry.get("uuid") == uuid_str:
                if replied is not None:
                    entry["replied"] = replied
                if read is not None:
                    entry["read"] = read
                updated = True
                break
        
        if updated:
            with open(self.filepath, 'w') as f:
                json.dump(history, f, indent=4)
        return updated

