import customtkinter as ctk
import os
import uuid
import threading
import socket
from datetime import datetime
from mail_handler import MailSender
from history_manager import HistoryManager
from reply_checker import ReplyChecker
from tracking_server import run_server

# Configuration
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Setup Managers
        self.mail_sender = MailSender()
        self.history_manager = HistoryManager()
        self.template_path = os.path.join(os.path.dirname(__file__), "templates", "email_template.html")

        # Tracking Server State
        self.server_thread = None
        self.server_running = False
        self.local_ip = self.get_local_ip()

        # Window Setup
        self.title("Mac Mass Mailer - Advanced")
        self.geometry("700x600")

        # Layout Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Tab View
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_send = self.tab_view.add("Envoi")
        self.tab_settings = self.tab_view.add("Paramètres IMAP")
        self.tab_history = self.tab_view.add("Historique & Suivi")

        # --- TAB 1: ENVOI ---
        self.setup_send_tab()

        # --- TAB 2: SETTINGS (IMAP) ---
        self.setup_settings_tab()

        # --- TAB 3: HISTORY ---
        self.setup_history_tab()
        
        # --- SERVER CONTROLS (IN SETTINGS) ---
        self.setup_server_controls()

        self.log("Application prête.")

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def setup_send_tab(self):
        self.tab_send.grid_columnconfigure(1, weight=1)
        
        # Title
        label_title = ctk.CTkLabel(self.tab_send, text="Nouvel Envoi", font=ctk.CTkFont(size=20, weight="bold"))
        label_title.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 20))

        # Inputs
        ctk.CTkLabel(self.tab_send, text="Email Destinataire:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_email = ctk.CTkEntry(self.tab_send, placeholder_text="exemple@domaine.com")
        self.entry_email.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.tab_send, text="Variable (Prénom):").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.entry_var = ctk.CTkEntry(self.tab_send, placeholder_text="Jean")
        self.entry_var.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.tab_send, text="Sujet:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.entry_subject = ctk.CTkEntry(self.tab_send, placeholder_text="Sujet de l'email")
        self.entry_subject.insert(0, "Votre invitation")
        self.entry_subject.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        self.checkbox_send = ctk.CTkCheckBox(self.tab_send, text="Confirmer l'envoi (Action irréversible)")
        self.checkbox_send.grid(row=4, column=0, columnspan=2, padx=20, pady=10)

        self.btn_send = ctk.CTkButton(self.tab_send, text="Générer & Envoyer", command=self.process_mail)
        self.btn_send.grid(row=5, column=0, columnspan=2, padx=20, pady=10, sticky="ew")

        # Logs Area
        self.textbox_log = ctk.CTkTextbox(self.tab_send, height=150)
        self.textbox_log.grid(row=6, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="nsew")

    def setup_settings_tab(self):
        self.tab_settings.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.tab_settings, text="Configuration Email (SMTP pour envoi, IMAP pour lecture)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=20)

        # SMTP Settings
        ctk.CTkLabel(self.tab_settings, text="Serveur SMTP (Envoi):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_smtp_server = ctk.CTkEntry(self.tab_settings, placeholder_text="smtp.gmail.com")
        self.entry_smtp_server.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.tab_settings, text="Port SMTP:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.entry_smtp_port = ctk.CTkEntry(self.tab_settings, placeholder_text="587")
        self.entry_smtp_port.insert(0, "587")
        self.entry_smtp_port.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # IMAP Settings
        ctk.CTkLabel(self.tab_settings, text="Serveur IMAP (Lecture):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.entry_imap = ctk.CTkEntry(self.tab_settings, placeholder_text="imap.gmail.com")
        self.entry_imap.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        # Credentials (Shared)
        ctk.CTkLabel(self.tab_settings, text="Email User:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.entry_user = ctk.CTkEntry(self.tab_settings)
        self.entry_user.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.tab_settings, text="Mot de passe (App Password):").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.entry_pass = ctk.CTkEntry(self.tab_settings, show="*")
        self.entry_pass.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        
        self.btn_save_settings = ctk.CTkButton(self.tab_settings, text="Sauvegarder (Simulation)", command=self.save_settings)
        self.btn_save_settings.grid(row=6, column=0, columnspan=2, padx=20, pady=20)
        
    def setup_server_controls(self):
        # Extend Settings Tab
        frame_server = ctk.CTkFrame(self.tab_settings)
        frame_server.grid(row=7, column=0, columnspan=2, padx=10, pady=20, sticky="ew")
        
        ctk.CTkLabel(frame_server, text="Serveur de Tracking (Local)", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        self.label_ip = ctk.CTkLabel(frame_server, text=f"IP Locale détectée: {self.local_ip}")
        self.label_ip.pack(pady=5)
        
        self.btn_server = ctk.CTkButton(frame_server, text="Démarrer le Serveur", command=self.toggle_server, fg_color="green")
        self.btn_server.pack(pady=10)
        
        ctk.CTkLabel(frame_server, text="Note: Le serveur doit être allumé pour que le lien 'Lu' fonctionne.\nLe destinataire doit être sur le même réseau (ou utilisez ngrok).", font=ctk.CTkFont(size=10)).pack(pady=5)

    def toggle_server(self):
        if not self.server_running:
            # Start
            self.server_thread = threading.Thread(target=run_server, kwargs={'port': 5000}, daemon=True)
            self.server_thread.start()
            self.server_running = True
            self.btn_server.configure(text="Serveur Actif (Port 5000)", fg_color="red", state="disabled") # Simple implementation: cannot easily stop flask thread without complexity
            self.log(f"Serveur de tracking démarré sur http://{self.local_ip}:5000")
        else:
            self.log("Le serveur est déjà en cours d'exécution.")
        
    def setup_history_tab(self):
        self.tab_history.grid_columnconfigure(0, weight=1)
        self.tab_history.grid_rowconfigure(1, weight=1)

        frame_ctrl = ctk.CTkFrame(self.tab_history)
        frame_ctrl.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.btn_refresh = ctk.CTkButton(frame_ctrl, text="🔍 Vérifier Réponses (IMAP)", command=self.check_replies_thread)
        self.btn_refresh.pack(side="left", padx=10, pady=10)

        self.btn_reload = ctk.CTkButton(frame_ctrl, text="🔄 Rafraîchir Liste", command=self.load_history_view)
        self.btn_reload.pack(side="left", padx=10, pady=10)
        
        # Scrollable Frame for rows
        self.scroll_history = ctk.CTkScrollableFrame(self.tab_history, label_text="Historique d'Envois")
        self.scroll_history.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.load_history_view()

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.textbox_log.insert("end", f"[{timestamp}] {message}\n")
        self.textbox_log.see("end")

    def load_template(self):
        if not os.path.exists(self.template_path):
            return None
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def process_mail(self):
        email = self.entry_email.get().strip()
        variable = self.entry_var.get().strip()
        subject = self.entry_subject.get().strip()
        send_immediately = self.checkbox_send.get() == 1

        if not email:
            self.log("Erreur: L'email est requis.")
            return

        self.log(f"Traitement pour: {email}...")

        tracking_id = str(uuid.uuid4())
        
        # Use detected local IP for the tracking URL
        # e.g., http://192.168.1.15:5000/track?id=...
        tracking_url = f"http://{self.local_ip}:5000/track?id={tracking_id}"
        tracking_pixel = f'<img src="{tracking_url}" width="1" height="1" style="display:none;">'

        template_content = self.load_template()
        if not template_content:
            self.log("Erreur: Template introuvable.")
            return

        final_content = template_content.replace("{variable}", variable)
        
        # Append pixel
        if "</body>" in final_content:
            final_content = final_content.replace("</body>", f"{tracking_pixel}</body>")
        else:
            final_content += tracking_pixel
            
        # Also add a visible link for debugging/testing transparency issues
        # final_content += f'<p style="font-size:10px; color:#ccc;">ID: {tracking_id}</p>'

        # Validate SMTP settings
        smtp_server = self.entry_smtp_server.get().strip()
        smtp_port = self.entry_smtp_port.get().strip()
        user = self.entry_user.get().strip()
        pwd = self.entry_pass.get().strip()

        if not all([smtp_server, smtp_port, user, pwd]):
            self.log("Erreur: Veuillez configurer le SMTP (Onglet Configuration Email).")
            return

        success, msg = self.mail_sender.send_email(
            smtp_server, smtp_port, user, pwd,
            email, subject, final_content
        )
        
        status = "Envoyé" if success else "Échec"
        self.history_manager.add_entry(email, variable, tracking_id, status)
        
        if success:
            self.log(f"Succès: Email envoyé à {email}. Pixel: {tracking_url}")
            self.load_history_view()
        else:
            self.log(f"Erreur SMTP: {msg}")

    def save_settings(self):
        # In a real app we would save to a config file
        self.log("Paramètres IMAP enregistrés en mémoire (pour cette session).")

    def check_replies_thread(self):
        threading.Thread(target=self.check_replies, daemon=True).start()

    def check_replies(self):
        host = self.entry_imap.get()
        user = self.entry_user.get()
        pwd = self.entry_pass.get()

        if not host or not user or not pwd:
            self.log("Erreur: Veuillez configurer l'IMAP dans l'onglet Paramètres.")
            return

        self.log("Connexion IMAP en cours pour vérifier les réponses...")
        checker = ReplyChecker(host, user, pwd)
        history = self.history_manager.get_history()
        
        replied_uuids = checker.check_replies(history)
        
        count = 0
        for uid in replied_uuids:
            if self.history_manager.update_status(uid, replied=True):
                count += 1
        
        self.log(f"Vérification terminée. {count} nouvelle(s) réponse(s) détectée(s).")
        
        # Updates GUI safely from main thread
        self.after(0, self.load_history_view)

    def load_history_view(self):
        # Clear existing
        for widget in self.scroll_history.winfo_children():
            widget.destroy()

        history = self.history_manager.get_history()
        
        # Header
        headers = ["Date", "Email", "Statut", "Lu?", "Répondu?"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.scroll_history, text=h, font=ctk.CTkFont(weight="bold")).grid(row=0, column=i, padx=5, pady=5)

        # Rows
        for i, entry in enumerate(reversed(history)):
            row = i + 1
            date_short = entry['date'].split("T")[0]
            ctk.CTkLabel(self.scroll_history, text=date_short).grid(row=row, column=0, padx=5, pady=2)
            ctk.CTkLabel(self.scroll_history, text=entry['email']).grid(row=row, column=1, padx=5, pady=2)
            ctk.CTkLabel(self.scroll_history, text=entry['status']).grid(row=row, column=2, padx=5, pady=2)
            
            # Read Checkbox (Manual toggle for now)
            # read_var = ctk.BooleanVar(value=entry.get('read', False))
            is_read = "✅" if entry.get('read') else "❌"
            ctk.CTkLabel(self.scroll_history, text=is_read).grid(row=row, column=3, padx=5, pady=2)
            # cb_read = ctk.CTkCheckBox(self.scroll_history, text="", variable=read_var, width=20, 
            #                           command=lambda u=entry['uuid'], v=read_var: self.history_manager.update_status(u, read=v.get()))
            # cb_read.grid(row=row, column=3, padx=5, pady=2)

            # Replied Label (Auto detected)
            is_replied = "✅" if entry.get('replied') else "❌"
            ctk.CTkLabel(self.scroll_history, text=is_replied).grid(row=row, column=4, padx=5, pady=2)

if __name__ == "__main__":
    app = App()
    app.mainloop()
