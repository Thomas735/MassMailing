import customtkinter as ctk
import os
import uuid
import threading
import socket
import re
import tkinter.messagebox as messagebox
from datetime import datetime
from mail_handler import MailSender
from history_manager import HistoryManager
from reply_checker import ReplyChecker
from profile_manager import ProfileManager
from template_manager import TemplateManager
# Configuration
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Setup Managers
        self.mail_sender = MailSender()
        self.history_manager = HistoryManager()
        self.profile_manager = ProfileManager()
        self.template_manager = TemplateManager()

        # Pagination State
        self.current_page = 1
        self.items_per_page = 10

        # Window Setup
        self.title("Mac Mass Mailer - Advanced")
        self.geometry("700x600")

        # Layout Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Tab View
        self.tab_view = ctk.CTkTabview(self, command=self.on_tab_change)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_send = self.tab_view.add("Envoi")
        self.tab_model = self.tab_view.add("Modèle")
        self.tab_settings = self.tab_view.add("Paramètres IMAP")
        self.tab_history = self.tab_view.add("Historique & Suivi")

        # --- TAB 1: ENVOI ---
        self.setup_send_tab()

        # --- TAB 2: MODELE ---
        self.setup_model_tab()

        # --- TAB 3: SETTINGS (IMAP) ---
        self.setup_settings_tab()

        # --- TAB 4: HISTORY ---
        self.setup_history_tab()
        
        self.log("Application prête.")

    def setup_send_tab(self):
        self.tab_send.grid_columnconfigure(1, weight=1)
        
        # Title
        label_title = ctk.CTkLabel(self.tab_send, text="Nouvel Envoi", font=ctk.CTkFont(size=20, weight="bold"))
        label_title.grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 20))

        # Inputs
        ctk.CTkLabel(self.tab_send, text="Email Destinataire:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_email = ctk.CTkEntry(self.tab_send, placeholder_text="exemple@domaine.com")
        self.entry_email.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.tab_send, text="Modèle à utiliser:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.combo_send_template = ctk.CTkComboBox(self.tab_send, values=self.template_manager.get_template_names(), state="readonly", command=self.on_send_template_change)
        self.combo_send_template.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        templates = self.template_manager.get_template_names()
        if templates:
            self.combo_send_template.set(templates[0])

        # Dynamic Variables Frame
        self.frame_variables = ctk.CTkFrame(self.tab_send, fg_color="transparent")
        self.frame_variables.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.variable_entries = {}
        self.update_send_variables_ui()
        
        ctk.CTkLabel(self.tab_send, text="Sujet:").grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.entry_subject = ctk.CTkEntry(self.tab_send, placeholder_text="Sujet de l'email")
        self.entry_subject.insert(0, "Votre invitation")
        self.entry_subject.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

        self.checkbox_send = ctk.CTkCheckBox(self.tab_send, text="Confirmer l'envoi (Action irréversible)")
        self.checkbox_send.grid(row=5, column=0, columnspan=2, padx=20, pady=10)

        self.btn_send = ctk.CTkButton(self.tab_send, text="Générer & Envoyer", command=self.process_mail)
        self.btn_send.grid(row=6, column=0, columnspan=2, padx=20, pady=10, sticky="ew")

        # Logs Area
        self.textbox_log = ctk.CTkTextbox(self.tab_send, height=150)
        self.textbox_log.grid(row=7, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="nsew")

    def setup_settings_tab(self):
        self.tab_settings.grid_columnconfigure(1, weight=1)
        
        # Profile Selector
        ctk.CTkLabel(self.tab_settings, text="Profil Enregistré:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.combo_profiles = ctk.CTkComboBox(self.tab_settings, values=self.profile_manager.get_profile_names(), command=self.load_profile, state="readonly")
        self.combo_profiles.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Let's try to load the first profile if available
        profiles = self.profile_manager.get_profile_names()
        if profiles:
            self.combo_profiles.set(profiles[0])
            # Delay load to allow UI setup to finish but we need entries first.
            # We will call self.load_profile manually right after creating entries.

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
        
        # Save Profile Section
        frame_save = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        frame_save.grid(row=6, column=0, columnspan=2, pady=20, sticky="ew")
        frame_save.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(frame_save, text="Nom d'enregistrement:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_profile_name = ctk.CTkEntry(frame_save, placeholder_text="Ex: Gmail Pro")
        self.entry_profile_name.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        self.btn_save_settings = ctk.CTkButton(frame_save, text="💾 Enregistrer Profil", command=self.save_settings)
        self.btn_save_settings.grid(row=0, column=2, padx=10, pady=5)

        # Initial Load if profiles exist
        if profiles:
            self.load_profile(profiles[0])
        
    def setup_history_tab(self):
        self.tab_history.grid_columnconfigure(0, weight=1)
        self.tab_history.grid_rowconfigure(2, weight=1)

        frame_ctrl = ctk.CTkFrame(self.tab_history)
        frame_ctrl.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.btn_refresh = ctk.CTkButton(frame_ctrl, text="� Actualiser & Vérifier Réponses (IMAP)", command=self.check_replies_thread)
        self.btn_refresh.pack(side="left", padx=10, pady=10)
        
        self.btn_clear_all = ctk.CTkButton(frame_ctrl, text="🗑 Vider tout", fg_color="#c0392b", hover_color="#922b21", command=self.confirm_clear_all)
        self.btn_clear_all.pack(side="left", padx=5)

        self.btn_delete_email = ctk.CTkButton(frame_ctrl, text="🗑 Purger un contact...", fg_color="#d35400", hover_color="#a04000", command=self.confirm_delete_by_email)
        self.btn_delete_email.pack(side="left", padx=5)
        
        self.entry_search = ctk.CTkEntry(frame_ctrl, placeholder_text="Rechercher un email...", width=200)
        self.entry_search.pack(side="right", padx=10, pady=10)
        self.entry_search.bind("<KeyRelease>", self.on_search_change)
        
        self.filter_var = ctk.StringVar(value="Tous")
        self.seg_button = ctk.CTkSegmentedButton(self.tab_history, values=["Tous", "Envoyés", "Échecs", "Brouillons", "Non consultées", "Consultées"],
                                                 variable=self.filter_var, command=self.on_filter_change)
        self.seg_button.grid(row=1, column=0, padx=10, pady=(0, 10))
        
        # Scrollable Frame for rows
        self.scroll_history = ctk.CTkScrollableFrame(self.tab_history, label_text="Historique d'Envois")
        self.scroll_history.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        
        # Pagination Controls
        self.frame_pagination = ctk.CTkFrame(self.tab_history, fg_color="transparent")
        self.frame_pagination.grid(row=3, column=0, pady=5)
        
        self.btn_prev_page = ctk.CTkButton(self.frame_pagination, text="<", width=30, command=self.prev_page)
        self.btn_prev_page.pack(side="left", padx=5)
        
        self.lbl_page_info = ctk.CTkLabel(self.frame_pagination, text="Page 1 / 1")
        self.lbl_page_info.pack(side="left", padx=10)
        
        self.btn_next_page = ctk.CTkButton(self.frame_pagination, text=">", width=30, command=self.next_page)
        self.btn_next_page.pack(side="left", padx=5)

        self.load_history_view()

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_history_view()

    def next_page(self):
        # Upper bound checks are done in load_history_view
        self.current_page += 1
        self.load_history_view()

    def setup_model_tab(self):
        self.tab_model.grid_columnconfigure(0, weight=1)
        self.tab_model.grid_rowconfigure(3, weight=1)

        # Helper Text
        helper_text = "Modifiez le code HTML de votre email ci-dessous.\n" \
                      "Astuce : Utilisez {nom_de_la_variable} (ex: {variable}) pour vos variables."
        ctk.CTkLabel(self.tab_model, text=helper_text, justify="center", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=20, pady=10)

        # Top controls for Model Management
        frame_model_ctrl = ctk.CTkFrame(self.tab_model, fg_color="transparent")
        frame_model_ctrl.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        
        ctk.CTkLabel(frame_model_ctrl, text="Modèle:").pack(side="left", padx=(0, 10))
        self.combo_edit_template = ctk.CTkComboBox(frame_model_ctrl, values=self.template_manager.get_template_names(), command=self.on_edit_template_change, state="readonly")
        self.combo_edit_template.pack(side="left")
        templates = self.template_manager.get_template_names()
        if templates:
            self.combo_edit_template.set(templates[0])

        self.btn_new_template = ctk.CTkButton(frame_model_ctrl, text="➕ Nouveau", width=80, command=self.new_template_dialog)
        self.btn_new_template.pack(side="left", padx=5)

        self.btn_rename_template = ctk.CTkButton(frame_model_ctrl, text="✏️ Renommer", width=80, command=self.rename_template_dialog)
        self.btn_rename_template.pack(side="left", padx=5)

        self.btn_delete_template = ctk.CTkButton(frame_model_ctrl, text="🗑️ Supprimer", width=80, fg_color="red", hover_color="darkred", command=self.delete_current_template)
        self.btn_delete_template.pack(side="left", padx=5)

        # Variables Management Frame
        frame_var_ctrl = ctk.CTkFrame(self.tab_model, fg_color="transparent")
        frame_var_ctrl.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        
        ctk.CTkLabel(frame_var_ctrl, text="Variables:").pack(side="left", padx=(0, 10))
        self.combo_edit_variable = ctk.CTkComboBox(frame_var_ctrl, values=[], state="readonly")
        self.combo_edit_variable.pack(side="left")

        self.btn_add_var = ctk.CTkButton(frame_var_ctrl, text="➕ Ajouter", width=80, command=self.add_variable_dialog)
        self.btn_add_var.pack(side="left", padx=5)

        self.btn_rename_var = ctk.CTkButton(frame_var_ctrl, text="✏️ Renommer", width=80, command=self.rename_variable_dialog)
        self.btn_rename_var.pack(side="left", padx=5)

        self.btn_delete_var = ctk.CTkButton(frame_var_ctrl, text="🗑️ Supprimer", width=80, fg_color="red", hover_color="darkred", command=self.delete_current_variable)
        self.btn_delete_var.pack(side="left", padx=5)

        # Editor Frame
        frame_editor = ctk.CTkFrame(self.tab_model)
        frame_editor.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        frame_editor.grid_columnconfigure(0, weight=1)
        frame_editor.grid_rowconfigure(0, weight=1)

        self.textbox_template = ctk.CTkTextbox(frame_editor, font=ctk.CTkFont(family="Consolas", size=12))
        self.textbox_template.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Load Content Button
        frame_buttons = ctk.CTkFrame(self.tab_model, fg_color="transparent")
        frame_buttons.grid(row=4, column=0, pady=10)
        
        self.btn_load_template = ctk.CTkButton(frame_buttons, text="🔄 Recharger le modèle actuel", command=self.reload_template_to_editor)
        self.btn_load_template.pack(side="left", padx=10)

        self.btn_save_template = ctk.CTkButton(frame_buttons, text="💾 Enregistrer le modèle", command=self.save_template_from_editor, fg_color="green", hover_color="darkgreen")
        self.btn_save_template.pack(side="left", padx=10)

        # Load initial
        self.reload_template_to_editor()
        self.update_edit_variables_combo()

    def update_template_combos(self):
        names = self.template_manager.get_template_names()
        self.combo_edit_template.configure(values=names)
        self.combo_send_template.configure(values=names)
        
        if names and self.combo_edit_template.get() not in names:
            self.combo_edit_template.set(names[0])
            self.combo_send_template.set(names[0])
        self.update_edit_variables_combo()
        self.update_send_variables_ui()

    def new_template_dialog(self):
        dialog = ctk.CTkInputDialog(text="Nom du nouveau modèle:", title="Nouveau Modèle")
        name = dialog.get_input()
        if name:
            if name in self.template_manager.get_template_names():
                self.log(f"Erreur: Le modèle '{name}' existe déjà.")
                return
            self.template_manager.save_template(name, "<h1>Nouveau Modèle</h1>\n<p>Tapez votre message ici.</p>")
            self.update_template_combos()
            self.combo_edit_template.set(name)
            self.on_edit_template_change(name)

    def rename_template_dialog(self):
        old_name = self.combo_edit_template.get()
        if not old_name: return
        dialog = ctk.CTkInputDialog(text=f"Nouveau nom pour '{old_name}':", title="Renommer le modèle")
        new_name = dialog.get_input()
        if new_name:
            if self.template_manager.rename_template(old_name, new_name):
                self.update_template_combos()
                self.combo_edit_template.set(new_name)
                self.combo_send_template.set(new_name)
                self.log(f"Modèle renommé de '{old_name}' à '{new_name}'.")
            else:
                self.log("Erreur: Impossible de renommer le modèle. Peut-être que le nom existe déjà.")

    def delete_current_template(self):
        name = self.combo_edit_template.get()
        names = self.template_manager.get_template_names()
        if not name or len(names) <= 1:
            self.log("Action refusée: Vous devez conserver au moins un modèle.")
            return
        
        self.template_manager.delete_template(name)
        self.update_template_combos()
        remaining = self.template_manager.get_template_names()
        if remaining:
            self.combo_edit_template.set(remaining[0])
            self.combo_send_template.set(remaining[0])
            self.on_edit_template_change(remaining[0])
        self.log(f"Modèle '{name}' supprimé.")

    def on_edit_template_change(self, choice):
        self.reload_template_to_editor()
        self.update_edit_variables_combo()

    def update_edit_variables_combo(self):
        name = self.combo_edit_template.get()
        if not name: return
        variables = self.template_manager.get_template_variables(name)
        self.combo_edit_variable.configure(values=variables)
        if variables:
            self.combo_edit_variable.set(variables[0])
        else:
            self.combo_edit_variable.set("")

    def add_variable_dialog(self):
        name = self.combo_edit_template.get()
        if not name: return
        dialog = ctk.CTkInputDialog(text="Nouvelle variable (ex: nom_entreprise):", title="Ajouter Variable")
        var_name = dialog.get_input()
        if var_name:
            # Simple check to validate variable name (no spaces)
            var_name = var_name.strip().replace(" ", "_")
            if self.template_manager.add_variable(name, var_name):
                self.update_edit_variables_combo()
                self.update_send_variables_ui()
            else:
                self.log(f"La variable '{var_name}' existe déjà ou nom invalide.")

    def rename_variable_dialog(self):
        name = self.combo_edit_template.get()
        old_var = self.combo_edit_variable.get()
        if not name or not old_var: return
        dialog = ctk.CTkInputDialog(text=f"Nouveau nom pour la variable '{old_var}':", title="Renommer Variable")
        new_var = dialog.get_input()
        if new_var:
            new_var = new_var.strip().replace(" ", "_")
            if self.template_manager.rename_variable(name, old_var, new_var):
                self.update_edit_variables_combo()
                self.combo_edit_variable.set(new_var)
                self.update_send_variables_ui()
                self.log(f"Variable '{old_var}' renommée en '{new_var}'. N'oubliez pas de mettre à jour le HTML de votre modèle.")
            else:
                self.log("Erreur lors du renommage de la variable.")

    def delete_current_variable(self):
        name = self.combo_edit_template.get()
        var_name = self.combo_edit_variable.get()
        if not name or not var_name: return
        if self.template_manager.remove_variable(name, var_name):
            self.update_edit_variables_combo()
            self.update_send_variables_ui()
            self.log(f"Variable '{var_name}' supprimée.")

    def reload_template_to_editor(self):
        name = self.combo_edit_template.get()
        if not name: return
        content = self.template_manager.get_template_content(name)
        
        self.textbox_template.delete("0.0", "end")
        if content:
            self.textbox_template.insert("0.0", content)
            
    def save_template_from_editor(self):
        name = self.combo_edit_template.get()
        if not name: return
        content = self.textbox_template.get("0.0", "end").strip()
        
        # Validation : Check if HTML {tags} match registered variables
        registered_vars = self.template_manager.get_template_variables(name)
        # Find all {tags} inside the HTML content, excluding styling {} blocks by trying to match alphanumeric names only
        # We can loosely match {word}
        found_tags = re.findall(r'\{([A-Za-z0-9_]+)\}', content)
        
        missing_vars = []
        for tag in set(found_tags):
            if tag not in registered_vars:
                missing_vars.append(tag)
                
        if missing_vars:
            self.log(f"Erreur Enregistrement : Les variables suivantes sont utilisées dans le code HTML mais ne sont pas déclarées dans le menu déroulant : {', '.join(missing_vars)}")
            return
            
        try:
            self.template_manager.save_template(name, content)
            self.log(f"Modèle d'email '{name}' enregistré avec succès.")
            
            # Show a temporary success message
            success_label = ctk.CTkLabel(self.tab_model, text="Enregistré !", text_color="green")
            success_label.grid(row=5, column=0, pady=5)
            self.tab_model.after(3000, success_label.destroy)
        except Exception as e:
            self.log(f"Erreur lors de l'enregistrement du modèle: {e}")

    def on_send_template_change(self, choice):
        self.update_send_variables_ui()

    def update_send_variables_ui(self):
        # Clear existing entries
        for widget in self.frame_variables.winfo_children():
            widget.destroy()
        self.variable_entries.clear()
        
        template_name = self.combo_send_template.get()
        if not template_name: return
        
        variables = self.template_manager.get_template_variables(template_name)
        for i, var in enumerate(variables):
            ctk.CTkLabel(self.frame_variables, text=f"Variable ({var}):").grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = ctk.CTkEntry(self.frame_variables, placeholder_text=f"{var}")
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            self.variable_entries[var] = entry
            
        self.frame_variables.grid_columnconfigure(1, weight=1)

    def on_tab_change(self):
        if self.tab_view.get() == "Historique & Suivi":
            self.check_replies_thread()

    def on_search_change(self, event):
        self.current_page = 1
        self.load_history_view()

    def on_filter_change(self, value):
        self.current_page = 1
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
        subject = self.entry_subject.get().strip()
        send_immediately = self.checkbox_send.get() == 1
        
        # Get variables dictionary
        variables_data = {}
        for var_name, entry_widget in self.variable_entries.items():
            variables_data[var_name] = entry_widget.get().strip()

        # To keep backward compatibility with history (using 'variable' field), we encode the dict
        # or just fallback to listing the values
        variables_str = ", ".join([f"{k}:{v}" for k,v in variables_data.items()]) if variables_data else "Aucune"

        if not email:
            self.log("Erreur: L'email est requis.")
            return

        self.log(f"Traitement pour: {email}...")

        tracking_id = str(uuid.uuid4())
        
        template_name = self.combo_send_template.get()
        if not template_name:
            self.log("Erreur: Veuillez sélectionner un modèle.")
            return

        template_content = self.template_manager.get_template_content(template_name)
        if not template_content:
            self.log("Erreur: Modèle introuvable ou vide.")
            return

        final_content = template_content
        for var_name, var_value in variables_data.items():
            final_content = final_content.replace(f"{{{var_name}}}", var_value)
            
        if not send_immediately:
            self.history_manager.add_entry(email, variables_str, subject, tracking_id, "Brouillon", final_content)
            self.log(f"Brouillon sauvegardé pour {email} (envoi non confirmé).")
            self.load_history_view()
            return

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
        self.history_manager.add_entry(email, variables_str, subject, tracking_id, status, final_content)
        
        if success:
            self.log(f"Succès: Email envoyé à {email}.")
            self.load_history_view()
        else:
            self.log(f"Erreur SMTP: {msg}")

    def save_settings(self):
        profile_name = self.entry_profile_name.get().strip()
        smtp_var = self.entry_smtp_server.get().strip()
        port_var = self.entry_smtp_port.get().strip()
        imap_var = self.entry_imap.get().strip()
        user_var = self.entry_user.get().strip()
        pass_var = self.entry_pass.get().strip()

        if not profile_name:
            self.log("Erreur: Donnez un nom pour enregistrer ce profil.")
            return

        self.profile_manager.save_profile(profile_name, smtp_var, port_var, imap_var, user_var, pass_var)
        self.combo_profiles.configure(values=self.profile_manager.get_profile_names())
        self.combo_profiles.set(profile_name)
        self.log(f"Profil '{profile_name}' enregistré avec succès.")

    def load_profile(self, profile_name):
        profile = self.profile_manager.get_profile(profile_name)
        if profile:
            self.entry_smtp_server.delete(0, 'end')
            self.entry_smtp_server.insert(0, profile.get("smtp_server", ""))
            
            self.entry_smtp_port.delete(0, 'end')
            self.entry_smtp_port.insert(0, profile.get("smtp_port", "587"))
            
            self.entry_imap.delete(0, 'end')
            self.entry_imap.insert(0, profile.get("imap_server", ""))
            
            self.entry_user.delete(0, 'end')
            self.entry_user.insert(0, profile.get("username", ""))
            
            self.entry_pass.delete(0, 'end')
            self.entry_pass.insert(0, profile.get("password", ""))
            
            self.entry_profile_name.delete(0, 'end')
            self.entry_profile_name.insert(0, profile_name)
            self.log(f"Profil '{profile_name}' chargé.")

    def check_replies_thread(self):
        threading.Thread(target=self.check_replies, daemon=True).start()

    def check_replies(self):
        host = self.entry_imap.get()
        user = self.entry_user.get()
        pwd = self.entry_pass.get()

        if not host or not user or not pwd:
            self.log("Information: Configurez l'IMAP dans les paramètres pour vérifier les réponses automatiquement.")
            # We still load the view even if we can't check IMAP
            self.after(0, self.load_history_view)
            return

        self.log("Connexion IMAP en cours pour vérifier les réponses...")
        checker = ReplyChecker(host, user, pwd)
        history = self.history_manager.get_history()
        
        replies_found = checker.check_replies(history)
        
        count = 0
        for reply in replies_found:
            if self.history_manager.add_reply(reply["uuid"], reply):
                count += 1
        
        self.log(f"Vérification terminée. {count} nouvelle(s) réponse(s) détectée(s).")
        
        # Updates GUI safely from main thread
        self.after(0, self.load_history_view)

    def load_history_view(self):
        # Clear existing
        for widget in self.scroll_history.winfo_children():
            widget.destroy()

        history = self.history_manager.get_history()
        search_query = self.entry_search.get().strip().lower()
        active_filter = self.filter_var.get()
        
        if active_filter in ("Consultées", "Non consultées"):
            self.scroll_history.configure(label_text="Historique de Réception")
        else:
            self.scroll_history.configure(label_text="Historique d'Envois")

        if search_query:
            history = [entry for entry in history if search_query in entry.get('email', '').lower()]
            
        if active_filter == "Envoyés":
            history = [e for e in history if e.get("status") in ("Envoyé", "Sent")]
        elif active_filter == "Échecs":
            history = [e for e in history if e.get("status") == "Échec"]
        elif active_filter == "Brouillons":
            history = [e for e in history if e.get("status") == "Brouillon"]
            
        if active_filter in ("Non consultées", "Consultées"):
            # Extract all replies flat list
            replies_list = []
            for entry in self.history_manager.get_history():
                for r in entry.get("replies", []):
                    # Attach parent uuid to the reply dictionary so we can trace back deletions
                    r["_parent_uuid"] = entry.get("uuid")
                    if active_filter == "Consultées" and r.get("read"):
                        replies_list.append(r)
                    elif active_filter == "Non consultées" and not r.get("read"):
                        replies_list.append(r)
            
            if search_query:
                replies_list = [r for r in replies_list if search_query in r.get("email", "").lower() or search_query in r.get("subject", "").lower()]

            # Sort replies by date newest first
            replies_list.sort(key=lambda x: x.get("date", ""), reverse=True)
            
            # Pagination
            total_items = len(replies_list)
            total_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)
            if self.current_page > total_pages: self.current_page = total_pages
            
            start_idx = (self.current_page - 1) * self.items_per_page
            end_idx = start_idx + self.items_per_page
            
            paged_replies = replies_list[start_idx:end_idx]
            
            self.lbl_page_info.configure(text=f"Page {self.current_page} / {total_pages}")
            
            headers = ["Date", "Heure", "Expéditeur", "Sujet", "Statut", "Contenu", "Actions"]
            for i, h in enumerate(headers):
                ctk.CTkLabel(self.scroll_history, text=h, font=ctk.CTkFont(weight="bold")).grid(row=0, column=i, padx=5, pady=5)
            
            for i, reply in enumerate(paged_replies):
                row = i + 1
                try:
                    date_obj = datetime.fromisoformat(reply['date'])
                    date_short = date_obj.strftime("%Y-%m-%d")
                    time_short = date_obj.strftime("%H:%M:%S")
                except:
                    date_short = reply.get('date', '').split("T")[0] if reply.get('date') else ""
                    time_short = "--:--:--"

                ctk.CTkLabel(self.scroll_history, text=date_short).grid(row=row, column=0, padx=5, pady=2)
                ctk.CTkLabel(self.scroll_history, text=time_short).grid(row=row, column=1, padx=5, pady=2)
                ctk.CTkLabel(self.scroll_history, text=reply.get('email', '')).grid(row=row, column=2, padx=5, pady=2)
                
                subject_text = reply.get('subject', '')
                if len(subject_text) > 40: subject_text = subject_text[:37] + "..."
                ctk.CTkLabel(self.scroll_history, text=subject_text).grid(row=row, column=3, padx=5, pady=2)
                
                status_icon = "✅" if reply.get("read") else "❌"
                ctk.CTkLabel(self.scroll_history, text=status_icon).grid(row=row, column=4, padx=5, pady=2)
                
                content_str = reply.get('content', 'Contenu non disponible')
                parent_u = reply.get('_parent_uuid')
                reply_date = reply.get('date')
                btn_view = ctk.CTkButton(self.scroll_history, text="Consulter", width=60, 
                                         command=lambda u=parent_u, d=reply_date, c=content_str: self.open_reply(u, d, c))
                btn_view.grid(row=row, column=5, padx=5, pady=2)
                
                # Delete Parent Entry Button
                btn_del = ctk.CTkButton(self.scroll_history, text="🗑", width=30, fg_color="#c0392b", hover_color="#922b21",
                                        command=lambda u=parent_u: self.confirm_delete_entry(u))
                btn_del.grid(row=row, column=6, padx=5, pady=2)
            return

        # Pagination
        total_items = len(history)
        total_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)
        if self.current_page > total_pages: self.current_page = total_pages
        
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        
        # history is already reversed in logic, but wait, the original code used reversed(history).
        # We need to reverse it and then slice.
        history_reversed = list(reversed(history))
        paged_history = history_reversed[start_idx:end_idx]
        
        self.lbl_page_info.configure(text=f"Page {self.current_page} / {total_pages}")

        # Header for normal history
        headers = ["Date", "Heure", "Email", "Sujet", "Statut", "Répondu?", "Contenu", "Actions"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.scroll_history, text=h, font=ctk.CTkFont(weight="bold")).grid(row=0, column=i, padx=5, pady=5)

        # Rows for normal history
        for i, entry in enumerate(paged_history):
            row = i + 1
            try:
                date_obj = datetime.fromisoformat(entry['date'])
                date_short = date_obj.strftime("%Y-%m-%d")
                time_short = date_obj.strftime("%H:%M:%S")
            except:
                date_short = entry['date'].split("T")[0]
                time_short = "--:--:--"

            ctk.CTkLabel(self.scroll_history, text=date_short).grid(row=row, column=0, padx=5, pady=2)
            ctk.CTkLabel(self.scroll_history, text=time_short).grid(row=row, column=1, padx=5, pady=2)
            ctk.CTkLabel(self.scroll_history, text=entry['email']).grid(row=row, column=2, padx=5, pady=2)
            
            subject_text = entry.get('subject', '')
            if len(subject_text) > 20: subject_text = subject_text[:17] + "..."
            ctk.CTkLabel(self.scroll_history, text=subject_text).grid(row=row, column=3, padx=5, pady=2)
            
            ctk.CTkLabel(self.scroll_history, text=entry['status']).grid(row=row, column=4, padx=5, pady=2)

            # Replied Label (Auto detected)
            if entry.get('status') in ("Brouillon", "Échec"):
                is_replied = "-"
            else:
                is_replied = "✅" if entry.get('replied') else "❌"
            ctk.CTkLabel(self.scroll_history, text=is_replied).grid(row=row, column=5, padx=5, pady=2)
            
            # Content Button
            content_str = entry.get('content', 'Contenu non disponible')
            btn_view = ctk.CTkButton(self.scroll_history, text="Consulter", width=60, 
                                     command=lambda c=content_str: self.show_email_content_dialog(c))
            btn_view.grid(row=row, column=6, padx=5, pady=2)
            
            # Delete Button
            uuid_str = entry.get('uuid')
            btn_del = ctk.CTkButton(self.scroll_history, text="🗑", width=30, fg_color="#c0392b", hover_color="#922b21",
                                    command=lambda u=uuid_str: self.confirm_delete_entry(u))
            btn_del.grid(row=row, column=7, padx=5, pady=2)

    def confirm_clear_all(self):
        active_filter = self.filter_var.get()
        if active_filter == "Tous":
            msg = "Êtes-vous sûr de vouloir supprimer TOUT l'historique ?\nCette action est irréversible et supprimera tous les logs d'envoi et réponses sauvegardées."
        else:
            msg = f"Êtes-vous sûr de vouloir vider l'onglet '{active_filter}' ?\nCette action est irréversible."
            
        if messagebox.askyesno(f"Vider {active_filter}", msg):
            if self.history_manager.clear_by_filter(active_filter):
                self.log(f"Historique vidé pour l'onglet : {active_filter}.")
                self.load_history_view()
            else:
                self.log(f"Aucun élément à supprimer dans l'onglet : {active_filter}.")

    def confirm_delete_by_email(self):
        dialog = ctk.CTkInputDialog(text="Entrez l'adresse email exacte à purger de l'historique :", title="Purger un contact")
        email_target = dialog.get_input()
        if email_target:
            email_target = email_target.strip()
            if messagebox.askyesno("Confirmation de suppression", f"Voulez-vous vraiment supprimer TOUS les emails envoyés à et reçus de '{email_target}' ?"):
                if self.history_manager.delete_by_email(email_target):
                    self.log(f"Historique purgé pour le contact : {email_target}.")
                    self.load_history_view()
                else:
                    self.log(f"Aucun historique trouvé pour : {email_target}.")

    def confirm_delete_entry(self, uuid_str):
        if messagebox.askyesno("Supprimer l'email", "Êtes-vous sûr de vouloir supprimer cet email de l'historique ?"):
            if self.history_manager.delete_entry(uuid_str):
                self.log("Entrée d'historique supprimée.")
                self.load_history_view()

    def clean_html_for_display(self, text):
        import re
        import html
        
        # If it doesn't look like HTML, return as is
        if "<" not in text or ">" not in text:
            return text
            
        # Basic HTML to text conversion for readability
        cleaned = html.unescape(text)
        # Replace common block tags with newlines
        cleaned = re.sub(r'<(br|p|div|h[1-6]|tr|li|blockquote)[^>]*>', '\n', cleaned, flags=re.IGNORECASE)
        # Remove <style> and <script> blocks completely
        cleaned = re.sub(r'<(script|style|head)[^>]*>.*?</\1>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        # Remove all remaining HTML tags
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        # Remove extra blank lines and spaces
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
        return cleaned.strip()

    def open_reply(self, parent_uuid, reply_date, content):
        self.history_manager.mark_reply_read(parent_uuid, reply_date)
        self.show_email_content_dialog(content)
        self.load_history_view()

    def show_email_content_dialog(self, content):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Contenu de l'email")
        dialog.geometry("600x500")
        dialog.grid_rowconfigure(0, weight=1)
        dialog.grid_columnconfigure(0, weight=1)
        
        # Center in main window
        dialog.transient(self)
        dialog.focus()
        
        # Clean HTML if any (for old entries or messy replies)
        clean_content = self.clean_html_for_display(content)
        
        textbox = ctk.CTkTextbox(dialog, font=ctk.CTkFont(family="Consolas", size=12))
        textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        textbox.insert("0.0", clean_content)
        textbox.configure(state="disabled") # Readonly
        
        btn_close = ctk.CTkButton(dialog, text="Fermer", command=dialog.destroy)
        btn_close.grid(row=1, column=0, pady=10)

if __name__ == "__main__":
    app = App()
    app.mainloop()
