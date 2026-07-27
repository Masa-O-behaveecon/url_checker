import unittest
import os
import customtkinter as ctk
from url_checker import URLChecker
from config_manager import ConfigManager

class TestURLChecker(unittest.TestCase):
    def setUp(self):
        self.config = {
            "media": ["X", "YouTube"],
            "campaign": ["summer"]
        }

    def test_valid_url(self):
        url = "https://example.com/posts/2026-07-26.html?media=X&campaign=summer"
        res = URLChecker.validate_url(url, self.config)
        self.assertTrue(res["is_valid"])
        self.assertTrue(res["date_valid"])
        self.assertEqual(res["date_str"], "2026-07-26")
        self.assertEqual(len(res["warnings"]), 0)

    def test_invalid_date(self):
        url = "https://example.com/posts/2026-07-32?media=X"
        res = URLChecker.validate_url(url, self.config)
        self.assertFalse(res["is_valid"])
        self.assertFalse(res["date_valid"])
        self.assertTrue(any("日付" in w for w in res["warnings"]))

    def test_invalid_param_value(self):
        url = "https://example.com/posts/2026-07-26?media=TikTok"
        res = URLChecker.validate_url(url, self.config)
        self.assertFalse(res["is_valid"])
        self.assertTrue(any("許可値" in w for w in res["warnings"]))

    def test_unknown_param(self):
        url = "https://example.com/posts/2026-07-26?unknown=123"
        res = URLChecker.validate_url(url, self.config)
        self.assertFalse(res["is_valid"])
        self.assertTrue(any("未登録" in w for w in res["warnings"]))

    def test_update_query_param(self):
        url = "https://example.com/posts/2026-07-26.html?media=X&campaign=summer"
        updated = URLChecker.update_query_param(url, "media", "YouTube")
        self.assertIn("media=YouTube", updated)
        self.assertIn("campaign=summer", updated)

    def test_update_query_param_name(self):
        url = "https://example.com/posts/2026-07-26.html?med=X&campaign=summer"
        updated = URLChecker.update_query_param_name(url, "med", "media")
        self.assertIn("media=X", updated)
        self.assertNotIn("med=X", updated)

    def test_remove_query_param(self):
        url = "https://example.com/posts/2026-07-26.html?media=X&campaign=summer"
        updated = URLChecker.remove_query_param(url, "campaign")
        self.assertIn("media=X", updated)
        self.assertNotIn("campaign=summer", updated)

class TestConfigManager(unittest.TestCase):
    def test_config_operations(self):
        test_file = "test_settings.json"
        if os.path.exists(test_file):
            os.remove(test_file)
        
        cm = ConfigManager(filepath=test_file)
        params = cm.get_parameters()
        self.assertIn("media", params)

        cm.add_variable("platform", ["iOS", "Android"])
        self.assertIn("platform", cm.get_parameters())

        cm.add_value_to_variable("platform", "Web")
        self.assertIn("Web", cm.get_parameters()["platform"])

        cm.edit_value_in_variable("platform", "Web", "Desktop")
        self.assertNotIn("Web", cm.get_parameters()["platform"])
        self.assertIn("Desktop", cm.get_parameters()["platform"])

        cm.rename_variable("platform", "os_type")
        self.assertNotIn("platform", cm.get_parameters())
        self.assertIn("os_type", cm.get_parameters())

        cm.remove_variable("os_type")
        self.assertNotIn("os_type", cm.get_parameters())

        if os.path.exists(test_file):
            os.remove(test_file)

class TestGUIIntegration(unittest.TestCase):
    def test_first_param_manual_edit_flow(self):
        # Test GUI event handling without showing window
        from main import URLCheckerApp
        app = URLCheckerApp()
        app.withdraw() # Hide window during test
        
        test_url = "https://example.com/posts/2026-07-26?media=X&campaign=summer"
        app.check_frame.url_entry.delete(0, "end")
        app.check_frame.url_entry.insert(0, test_url)
        app.check_frame.run_check()

        # Get the first param combo box (media)
        # Find the CTkComboBox widgets
        combos = []
        def find_combos(widget):
            if hasattr(widget, "get") and hasattr(widget, "_entry"):
                combos.append(widget)
            for child in widget.winfo_children():
                find_combos(child)

        find_combos(app.check_frame.param_table_frame)

        self.assertGreaterEqual(len(combos), 2)
        
        # Verify which is which
        print(f"DEBUG: Found {len(combos)} combos")
        for i, c in enumerate(combos):
            print(f"DEBUG: Combo {i}: {c.get()}")
            
        media_combo = combos[0]
        campaign_combo = combos[1]

        # Simulate user selecting/typing "Xa" into media combo box
        print(f"DEBUG: Media combo widget type: {type(media_combo)}")
        
        media_combo.set("Xa")
        media_combo._command("Xa")
        
        app.update_idletasks()
        app.update()
        
        print(f"DEBUG: After selection, URL: {app.check_frame.url_entry.get()}")
        
        # Check updated URL
        updated_url = app.check_frame.url_entry.get()
        self.assertIn("media=Xa", updated_url)
        self.assertIn("campaign=summer", updated_url)


        app.destroy()

    def test_settings_edit_and_save_flow(self):
        from main import URLCheckerApp
        app = URLCheckerApp()
        app.withdraw()

        # Switch to settings view
        app.show_settings_view()
        app.update_idletasks()
        app.update()

        settings_view = app.settings_frame
        
        # Start editing "media" variable
        settings_view.start_edit("media", ["X", "YouTube"])
        app.update_idletasks()
        app.update()

        # Simulate editing values using editing_states
        settings_view.editing_states["media"]["values_list"] = ["Xa", "YouTube", "added_data"]
        settings_view.editing_states["media"]["val_vars"] = [ctk.StringVar(value=v) for v in ["Xa", "YouTube", "added_data"]]

        # Save the edit
        settings_view.save_variable_edit("media")
        app.update_idletasks()
        app.update()

        # Assertion 1: Check config manager has the expected updated values
        updated_params = app.config_manager.get_parameters()
        self.assertEqual(updated_params["media"], ["Xa", "YouTube", "added_data"])

        # Assertion 2: Check screen display state / re-entering edit mode shows the updated values correctly
        settings_view.start_edit("media", updated_params["media"])
        app.update_idletasks()
        app.update()

        self.assertEqual(settings_view.editing_states["media"]["values_list"], ["Xa", "YouTube", "added_data"])

        app.destroy()

if __name__ == "__main__":
    unittest.main()
