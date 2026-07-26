import os
import json
import logging
from tkinter import messagebox

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def safe_execute(func, *args, error_title="エラー", error_message="処理中にエラーが発生しました。", default=None, **kwargs):
    """
    Executes a function safely with standardized error handling and logging.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logging.error(f"Error in {func.__name__}: {e}", exc_info=True)
        if error_message:
            messagebox.showerror(error_title, f"{error_message}\n詳細: {e}")
        return default

def load_json_file(filepath, default_data):
    """
    Safely loads JSON from a file.
    """
    if not os.path.exists(filepath):
        return default_data
    
    def _read():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    return safe_execute(_read, error_title="読み込みエラー", error_message=f"設定ファイルの読み込みに失敗しました: {filepath}", default=default_data)

def save_json_file(filepath, data):
    """
    Safely saves data to a JSON file.
    """
    def _write():
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True

    return safe_execute(_write, error_title="保存エラー", error_message=f"設定ファイルの保存に失敗しました: {filepath}", default=False)
