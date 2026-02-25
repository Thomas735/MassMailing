import json
import os

class ProfileManager:
    def __init__(self, filepath="profiles.json"):
        self.filepath = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                json.dump({}, f)

    def load_profiles(self):
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def save_profile(self, profile_name, smtp_server, smtp_port, imap_server, username, password):
        profiles = self.load_profiles()
        profiles[profile_name] = {
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "imap_server": imap_server,
            "username": username,
            "password": password
        }
        with open(self.filepath, 'w') as f:
            json.dump(profiles, f, indent=4)

    def get_profile(self, profile_name):
        profiles = self.load_profiles()
        return profiles.get(profile_name)

    def get_profile_names(self):
        return list(self.load_profiles().keys())
