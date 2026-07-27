import os
import sys
from util import load_json_file, save_json_file

# Determine base directory (script directory or executable directory)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "settings.json")

DEFAULT_CONFIG = {
    "parameters": {
        "media": ["X", "YouTube", "Facebook", "Note", "Instagram"],
        "campaign": ["summer", "winter", "spring", "autumn", "normal"]
    }
}

class ConfigManager:
    def __init__(self, filepath=CONFIG_FILE):
        self.filepath = os.path.abspath(filepath)
        self.config = load_json_file(self.filepath, DEFAULT_CONFIG.copy())
        if not os.path.exists(self.filepath):
            self.save_config()

    def save_config(self):
        return save_json_file(self.filepath, self.config)

    def get_parameters(self):
        return self.config.get("parameters", {})

    def set_parameters(self, params):
        self.config["parameters"] = params
        self.save_config()

    def add_variable(self, var_name, values=None):
        if not var_name:
            return False
        
        params = self.get_parameters()
        if var_name in params:
            return False

        params[var_name] = values or []
        self.set_parameters(params)
        return True

    def remove_variable(self, var_name):
        params = self.get_parameters()
        if var_name not in params:
            return False

        del params[var_name]
        self.set_parameters(params)
        return True

    def rename_variable(self, old_name, new_name):
        if not new_name or old_name == new_name:
            return False

        params = self.get_parameters()
        if old_name not in params or new_name in params:
            return False

        params[new_name] = params.pop(old_name)
        self.set_parameters(params)
        return True

    def add_value_to_variable(self, var_name, value):
        if not value:
            return False

        params = self.get_parameters()
        if var_name not in params:
            return False

        values = params[var_name]
        if value in values:
            return False

        values.append(value)
        self.set_parameters(params)
        return True

    def remove_value_from_variable(self, var_name, value):
        params = self.get_parameters()
        if var_name not in params:
            return False

        values = params[var_name]
        if value not in values:
            return False

        values.remove(value)
        self.set_parameters(params)
        return True

    def edit_value_in_variable(self, var_name, old_value, new_value):
        if not new_value:
            return False

        params = self.get_parameters()
        if var_name not in params:
            return False

        values = params[var_name]
        if old_value not in values or new_value in values:
            return False

        idx = values.index(old_value)
        values[idx] = new_value
        self.set_parameters(params)
        return True
