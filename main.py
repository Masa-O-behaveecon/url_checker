import os
import copy
import tkinter as tk
from tkinter import messagebox
from urllib.parse import urlparse, parse_qsl
import customtkinter as ctk

from url_checker import URLChecker
from config_manager import ConfigManager
from icons import ICON_EDIT, ICON_DELETE, ICON_SAVE, ICON_CANCEL, IconButton
from util import safe_execute

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class URLCheckerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("URLチェッカー & エディタ")
        self.geometry("1050x700")
        self.minsize(800, 550)

        self.config_manager = ConfigManager()

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=15, pady=15)

        self.check_frame = None
        self.settings_frame = None

        self.show_check_view()

    def show_check_view(self):
        if self.settings_frame:
            self.settings_frame.pack_forget()
        if not self.check_frame:
            self.check_frame = URLCheckView(self.container, self)
        self.check_frame.pack(fill="both", expand=True)
        self.check_frame.refresh_config()

    def show_settings_view(self):
        if self.check_frame:
            self.check_frame.pack_forget()
        if not self.settings_frame:
            self.settings_frame = SettingsView(self.container, self)
        self.settings_frame.pack(fill="both", expand=True)
        self.settings_frame.refresh_list()


class URLCheckView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))

        title_label = ctk.CTkLabel(header_frame, text="URLチェッカー", font=ctk.CTkFont(size=22, weight="bold"))
        title_label.pack(side="left")

        settings_btn = ctk.CTkButton(header_frame, text="⚙ 設定", width=90, command=self.app.show_settings_view)
        settings_btn.pack(side="right")

        # URL Input Section
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", pady=(0, 10), padx=0)

        url_label = ctk.CTkLabel(input_frame, text="記事URL:", font=ctk.CTkFont(size=14, weight="bold"))
        url_label.pack(anchor="w", padx=10, pady=(10, 5))

        url_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        url_row.pack(fill="x", padx=10, pady=(0, 10))

        self.url_entry = ctk.CTkEntry(url_row, placeholder_text="https://example.com/category/2026-07-26?media=X&campaign=summer", height=38)
        self.url_entry.pack(fill="x", expand=True, padx=0)
        self.url_entry.bind("<KeyRelease>", self.on_url_change)

        # Main Split Content
        content_split = ctk.CTkFrame(self, fg_color="transparent")
        content_split.pack(fill="both", expand=True, pady=(0, 0))

        content_split.grid_columnconfigure(0, weight=3)
        content_split.grid_columnconfigure(1, weight=2)
        content_split.grid_rowconfigure(0, weight=1)

        # Left Column
        left_col = ctk.CTkFrame(content_split)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.status_box = ctk.CTkFrame(left_col, fg_color=("gray90", "gray20"))
        self.status_box.pack(fill="x", padx=10, pady=10)

        self.overall_status_label = ctk.CTkLabel(self.status_box, text="総合判定: -", font=ctk.CTkFont(size=14, weight="bold"))
        self.overall_status_label.pack(anchor="w", padx=10, pady=10)

        param_header_label = ctk.CTkLabel(left_col, text="クエリパラメータ設定・編集", font=ctk.CTkFont(size=14, weight="bold"))
        param_header_label.pack(anchor="w", padx=10, pady=(5, 5))

        self.param_table_frame = ctk.CTkScrollableFrame(left_col, height=280)
        self.param_table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Right Column
        right_col = ctk.CTkFrame(content_split)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        warn_header = ctk.CTkLabel(right_col, text="警告・エラー一覧", font=ctk.CTkFont(size=14, weight="bold"))
        warn_header.pack(anchor="w", padx=10, pady=(10, 5))

        self.warn_textbox = ctk.CTkTextbox(right_col, height=320)
        self.warn_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.warn_textbox.configure(state="disabled")

        self.configured_params = {}
        self.editing_param_name = None
        self.refresh_config()

    def refresh_config(self):
        self.configured_params = self.app.config_manager.get_parameters()
        self.run_check()

    def on_url_change(self, event=None):
        self.run_check()

    def run_check(self):
        url_str = self.url_entry.get()
        result = URLChecker.validate_url(url_str, self.configured_params)

        if result["is_valid"]:
            self.overall_status_label.configure(text="総合判定: OK (ルールに適合しています)", text_color=("green", "lightgreen"))
        else:
            self.overall_status_label.configure(text="総合判定: 要確認 (警告があります)", text_color=("red", "salmon"))

        self.warn_textbox.configure(state="normal")
        self.warn_textbox.delete("0.0", "end")
        warning_text = "\n".join(result["warnings"]) if result["warnings"] else "警告はありません。"
        self.warn_textbox.insert("0.0", warning_text)
        self.warn_textbox.configure(state="disabled")

        self.populate_param_table(result.get("parsed_params", []))

    def _on_combo_select(self, param_name, selected_val):
        current_url = self.url_entry.get()
        updated_url = URLChecker.update_query_param(current_url, param_name, selected_val)
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, updated_url)
        self.run_check()

    def populate_param_table(self, parsed_params):
        for widget in self.param_table_frame.winfo_children():
            widget.destroy()

        if not parsed_params:
            ctk.CTkLabel(self.param_table_frame, text="クエリパラメータはありません。", text_color="gray").pack(pady=20)
            return

        header_row = ctk.CTkFrame(self.param_table_frame, fg_color=("gray85", "gray25"))
        header_row.pack(fill="x", pady=2)
        ctk.CTkLabel(header_row, text="パラメータ名 (編集 / 削除)", font=ctk.CTkFont(weight="bold"), width=230).pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(header_row, text="値 (選択)", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5, pady=5, expand=True, fill="x")

        for param in parsed_params:
            name, val, valid_var = param["name"], param["value"], param["valid_var"]
            
            row = ctk.CTkFrame(self.param_table_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)

            var_col = ctk.CTkFrame(row, fg_color=("gray95", "gray22"), width=230, height=42)
            var_col.pack(side="left", padx=5, fill="y")
            var_col.pack_propagate(False)

            val_container = ctk.CTkFrame(row, fg_color="transparent")
            val_container.pack(side="left", fill="x", expand=True, padx=5)

            is_editing_name = (name == self.editing_param_name)

            if is_editing_name:
                name_var = ctk.StringVar(value=name)
                name_entry = ctk.CTkEntry(var_col, textvariable=name_var, width=115, height=28)
                name_entry.pack(side="left", padx=5, pady=7)
                name_entry.focus_set()

                def save_name(old_n=name, n_var=name_var):
                    new_n = n_var.get().strip()
                    if new_n and new_n != old_n:
                        current_url = self.url_entry.get()
                        updated_url = URLChecker.update_query_param_name(current_url, old_n, new_n)
                        self.url_entry.delete(0, "end")
                        self.url_entry.insert(0, updated_url)
                    self.editing_param_name = None
                    self.run_check()

                def cancel_name():
                    self.editing_param_name = None
                    self.run_check()

                name_entry.bind("<Return>", lambda e: save_name())

                IconButton(var_col, text=ICON_CANCEL, command=cancel_name).pack(side="right", padx=2)
                IconButton(var_col, text=ICON_SAVE, command=save_name).pack(side="right", padx=2)

            else:
                var_color = ("green", "lightgreen") if valid_var else ("red", "salmon")
                ctk.CTkLabel(var_col, text=name, anchor="w", justify="left", wraplength=120, text_color=var_color, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5, fill="y")
                
                IconButton(var_col, text=ICON_DELETE, command=lambda pn=name: self.url_entry.delete(0, "end") or self.url_entry.insert(0, URLChecker.remove_query_param(self.url_entry.get(), pn)) or self.run_check()).pack(side="right", padx=2)
                IconButton(var_col, text=ICON_EDIT, command=lambda pn=name: (setattr(self, 'editing_param_name', pn), self.run_check())).pack(side="right", padx=2)

            choices = list(self.configured_params.get(name, []))
            if val not in choices:
                choices.append(val)
            if not choices:
                choices = [val] if val else [""]

            combo = ctk.CTkComboBox(val_container, values=choices, variable=ctk.StringVar(value=val), command=lambda v, p=name: self._on_combo_select(p, v))
            combo.pack(side="left", fill="x", expand=True, padx=0)

            def make_commit_handler(target_combo, p_name, p_val):
                def on_commit(event=None):
                    widget = event.widget if event and hasattr(event.widget, "get") else target_combo
                    typed_val = widget.get().strip()
                    current_url = self.url_entry.get()
                    parsed = urlparse(current_url)
                    query_list = dict(parse_qsl(parsed.query))
                    if not typed_val or typed_val == query_list.get(p_name, ""):
                        return
                    updated_url = URLChecker.update_query_param(current_url, p_name, typed_val)
                    self.url_entry.delete(0, "end")
                    self.url_entry.insert(0, updated_url)
                    self.run_check()
                return on_commit

            handler = make_commit_handler(combo, name, val)
            if hasattr(combo, "_entry") and combo._entry:
                combo._entry.bind("<Return>", handler)
                combo._entry.bind("<FocusOut>", handler)
            combo.bind("<<ComboboxSelected>>", handler)


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.editing_states = {}  # {var_name: {"name_var": StringVar, "val_vars": [StringVar, ...], "values_list": list}}
        self.original_params = None

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(header_frame, text="← 戻る", width=80, command=self.app.show_check_view).pack(side="left")
        ctk.CTkLabel(header_frame, text="パラメータ設定管理", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left", padx=15)

        ctk.CTkLabel(self, text="URLのクエリパラメータおよび入力可能な値を管理します。", font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(0, 10))

        add_var_frame = ctk.CTkFrame(self)
        add_var_frame.pack(fill="x", pady=(0, 15), padx=0)

        ctk.CTkLabel(add_var_frame, text="新規パラメータの追加:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=10)
        self.new_var_entry = ctk.CTkEntry(add_var_frame, placeholder_text="パラメータ名 (例: platform)", width=200)
        self.new_var_entry.pack(side="left", padx=5, pady=10)
        ctk.CTkButton(add_var_frame, text="パラメータを追加", command=self.add_variable).pack(side="left", padx=5, pady=10)

        self.vars_scroll = ctk.CTkScrollableFrame(self, height=450)
        self.vars_scroll.pack(fill="both", expand=True, pady=(0, 10))

        self.refresh_list()

    def refresh_list(self):
        for widget in self.vars_scroll.winfo_children():
            widget.destroy()

        params = self.app.config_manager.get_parameters()
        if not params:
            ctk.CTkLabel(self.vars_scroll, text="登録されているパラメータはありません。", text_color="gray").pack(pady=20)
            return

        for var_name, values in params.items():
            self._build_var_card(var_name, values)

    def _build_var_card(self, var_name, values):
        is_editing = var_name in self.editing_states

        var_card = ctk.CTkFrame(self.vars_scroll, fg_color=("gray90", "gray20"))
        var_card.pack(fill="x", pady=8, padx=5)

        top_row = ctk.CTkFrame(var_card, fg_color="transparent")
        top_row.pack(fill="x", padx=10, pady=8)

        if is_editing:
            state = self.editing_states[var_name]
            IconButton(top_row, text=ICON_CANCEL, command=lambda v=var_name: self.cancel_edit(v)).pack(side="right", padx=2)
            IconButton(top_row, text=ICON_SAVE, command=lambda v=var_name: self.save_variable_edit(v)).pack(side="right", padx=2)
            
            ctk.CTkLabel(top_row, text="パラメータ名:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 5))
            ctk.CTkEntry(top_row, textvariable=state["name_var"], width=180, height=28).pack(side="left", padx=5)
        else:
            IconButton(top_row, text=ICON_DELETE, command=lambda v=var_name: self.delete_variable(v)).pack(side="right", padx=2)
            IconButton(top_row, text=ICON_EDIT, command=lambda v=var_name: self.start_edit(v, values)).pack(side="right", padx=2)
            ctk.CTkLabel(top_row, text=f"パラメータ名: {var_name}", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(5, 5))

        ctk.CTkLabel(var_card, text="許可される値一覧:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(8, 2))
        vals_container = ctk.CTkFrame(var_card, fg_color="transparent")
        vals_container.pack(fill="x", padx=10, pady=2)

        current_vals = self.editing_states[var_name]["values_list"] if is_editing else values

        if not current_vals:
            ctk.CTkLabel(vals_container, text="(値が登録されていません)", text_color="gray", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=5, pady=2)
            if is_editing:
                self.editing_states[var_name]["val_vars"] = []
        else:
            if is_editing:
                self.editing_states[var_name]["val_vars"] = []

            for idx, val in enumerate(current_vals):
                val_row = ctk.CTkFrame(vals_container, fg_color=("gray85", "gray25"))
                val_row.pack(fill="x", pady=2, padx=2)

                val_inner = ctk.CTkFrame(val_row, fg_color="transparent")
                val_inner.pack(side="left", fill="x", expand=True, padx=5, pady=2)

                if is_editing:
                    v_var = ctk.StringVar(value=val)
                    self.editing_states[var_name]["val_vars"].append(v_var)
                    ctk.CTkEntry(val_inner, textvariable=v_var, height=26).pack(side="left", fill="x", expand=True, padx=5)
                    
                    def make_del_cb(v_list, i):
                        return lambda: v_list.pop(i) and self.refresh_list() or self.refresh_list()
                    
                    IconButton(val_inner, text=ICON_DELETE, command=make_del_cb(current_vals, idx)).pack(side="right", padx=2)
                else:
                    ctk.CTkLabel(val_inner, text=val, font=ctk.CTkFont(size=12)).pack(side="left", padx=5)

        if is_editing:
            add_val_row = ctk.CTkFrame(var_card, fg_color="transparent")
            add_val_row.pack(fill="x", padx=10, pady=(5, 10))

            new_entry = ctk.CTkEntry(add_val_row, placeholder_text="新しい値を追加", width=180, height=28)
            new_entry.pack(side="left", padx=(0, 5))

            def add_val_action(v_list, entry, state):
                # Sync current state first
                v_list[:] = [var.get().strip() for var in state["val_vars"] if var.get().strip()]
                new_val = entry.get().strip()
                if new_val and new_val not in v_list:
                    v_list.append(new_val)
                self.refresh_list()

            ctk.CTkButton(add_val_row, text="値を追加", width=80, height=28, command=lambda: add_val_action(current_vals, new_entry, self.editing_states[var_name])).pack(side="left")

    def start_edit(self, var_name, values):
        if not self.editing_states:
            self.original_params = copy.deepcopy(self.app.config_manager.get_parameters())
        
        self.editing_states[var_name] = {
            "name_var": ctk.StringVar(value=var_name),
            "values_list": list(values),
            "val_vars": []
        }
        self.refresh_list()

    def cancel_edit(self, var_name):
        if self.original_params is not None:
            self.app.config_manager.set_parameters(copy.deepcopy(self.original_params))
            self.original_params = None
        if var_name in self.editing_states:
            del self.editing_states[var_name]
        self.refresh_list()

    def save_variable_edit(self, old_name):
        if old_name not in self.editing_states:
            return

        state = self.editing_states[old_name]
        new_name = state["name_var"].get().strip()
        if not new_name:
            messagebox.showwarning("入力エラー", "パラメータ名を入力してください。")
            return

        params = copy.deepcopy(self.app.config_manager.get_parameters())
        if new_name != old_name and new_name in params:
            messagebox.showerror("エラー", "既に存在するパラメータ名です。")
            return

        # Collect final values from string vars
        final_values = []
        for var in state["val_vars"]:
            val = var.get().strip()
            if val and val not in final_values:
                final_values.append(val)

        if not final_values:
            final_values = [v.strip() for v in state["values_list"] if v.strip()]

        # Rebuild params dict preserving original order
        updated_params = {}
        for k, v in params.items():
            if k == old_name:
                updated_params[new_name] = final_values
            else:
                updated_params[k] = v
        if new_name not in updated_params:
            updated_params[new_name] = final_values

        safe_execute(self.app.config_manager.set_parameters, copy.deepcopy(updated_params), error_message="設定の保存に失敗しました。")

        del self.editing_states[old_name]
        if new_name in self.editing_states:
            del self.editing_states[new_name]

        if not self.editing_states:
            self.original_params = None

        self.refresh_list()

    def add_variable(self):
        var_name = self.new_var_entry.get().strip()
        if not var_name:
            messagebox.showwarning("入力エラー", "パラメータ名を入力してください。")
            return
        
        success = safe_execute(self.app.config_manager.add_variable, var_name, error_message="パラメータの追加に失敗しました。", default=False)
        if success:
            self.new_var_entry.delete(0, "end")
            params = self.app.config_manager.get_parameters()
            self.start_edit(var_name, params.get(var_name, []))
            self.refresh_list()
        else:
            messagebox.showerror("エラー", "パラメータの追加に失敗しました（既に存在するか無効な名前です）。")

    def delete_variable(self, var_name):
        if not messagebox.askyesno("確認", f"パラメータ '{var_name}' を削除してもよろしいですか？"):
            return

        success = safe_execute(self.app.config_manager.remove_variable, var_name, error_message="パラメータの削除に失敗しました。", default=False)
        if success:
            if var_name in self.editing_states:
                del self.editing_states[var_name]
            if not self.editing_states:
                self.original_params = None
            self.refresh_list()


if __name__ == "__main__":
    app = URLCheckerApp()
    app.mainloop()
