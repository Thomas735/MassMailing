import json
import os

class TemplateManager:
    def __init__(self, filepath="templates.json"):
        self.filepath = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filepath):
            # Check if old template file exists for migration
            old_template_path = os.path.join(os.path.dirname(__file__), "templates", "email_template.html")
            default_content = "<h1>Bonjour {variable},</h1>\n<p>Ceci est un test.</p>"
            if os.path.exists(old_template_path):
                with open(old_template_path, 'r', encoding='utf-8') as f:
                    default_content = f.read()
            
            initial_data = {
                "Défaut": {
                    "content": default_content,
                    "variables": ["variable"]
                }
            }
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=4)

    def load_templates(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Migration step for older formats where templates are just strings
            migrated = False
            for k, v in data.items():
                if isinstance(v, str):
                    data[k] = {
                        "content": v,
                        "variables": ["variable"]
                    }
                    migrated = True
                    
            if migrated:
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                    
            return data
            
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "Défaut": {
                    "content": "<h1>Bonjour {variable},</h1>\n<p>Ceci est un test.</p>",
                    "variables": ["variable"]
                }
            }

    def save_template(self, name, content, variables=None):
        templates = self.load_templates()
        if variables is None:
            if name in templates:
                variables = templates[name].get("variables", [])
            else:
                variables = ["variable"]
                
        templates[name] = {
            "content": content,
            "variables": variables
        }
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=4)

    def get_template_content(self, name):
        templates = self.load_templates()
        if name in templates:
            return templates[name].get("content", "")
        return None
        
    def get_template_variables(self, name):
        templates = self.load_templates()
        if name in templates:
            return templates[name].get("variables", [])
        return []

    def get_template_names(self):
        return list(self.load_templates().keys())
        
    def delete_template(self, name):
        templates = self.load_templates()
        if name in templates:
            del templates[name]
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(templates, f, indent=4)
                
    def rename_template(self, old_name, new_name):
        templates = self.load_templates()
        if old_name in templates and new_name and new_name not in templates:
            content = templates.pop(old_name)
            templates[new_name] = content
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(templates, f, indent=4)
            return True
        return False

    def add_variable(self, template_name, var_name):
        templates = self.load_templates()
        if template_name in templates:
            obj = templates[template_name]
            if "variables" not in obj:
                obj["variables"] = []
            if var_name and var_name not in obj["variables"]:
                obj["variables"].append(var_name)
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    json.dump(templates, f, indent=4)
                return True
        return False

    def remove_variable(self, template_name, var_name):
        templates = self.load_templates()
        if template_name in templates:
            obj = templates[template_name]
            if "variables" in obj and var_name in obj["variables"]:
                obj["variables"].remove(var_name)
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    json.dump(templates, f, indent=4)
                return True
        return False

    def rename_variable(self, template_name, old_var, new_var):
        templates = self.load_templates()
        if template_name in templates:
            obj = templates[template_name]
            if "variables" in obj and old_var in obj["variables"] and new_var:
                idx = obj["variables"].index(old_var)
                obj["variables"][idx] = new_var
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    json.dump(templates, f, indent=4)
                return True
        return False
