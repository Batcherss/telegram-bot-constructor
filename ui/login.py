import customtkinter as ctk
import tkinter.messagebox as mbox
from tkinter import filedialog
from net import validate_token
from utils import save_config

class LoginWindow(ctk.CTkToplevel):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.title("Token not found | VreD 4.1")
        self.geometry("450x250")
        self.resizable(False, False)
        self.on_success = on_success
        self.grab_set()

        ctk.CTkLabel(self, text="Bot tokens (separated by comma, space or new text):").pack(pady=10)
        self.entry = ctk.CTkTextbox(self, height=5)
        self.entry.pack(padx=20, pady=10, fill="x")

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=5)

        self.btn_check = ctk.CTkButton(btn_frame, text="Check", command=self.check_tokens)
        self.btn_check.grid(row=0, column=0, padx=10)

        self.btn_load_file = ctk.CTkButton(btn_frame, text="Load from file", command=self.load_from_file)
        self.btn_load_file.grid(row=0, column=1, padx=10)

    def load_from_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filepath:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            self.entry.delete("0.0", "end")
            self.entry.insert("0.0", content)
        except Exception as e:
            mbox.showerror("Error", f"Failed to read file:\n{e}")

    def check_tokens(self):
        raw_text = self.entry.get("0.0", "end").strip()
        if not raw_text:
            mbox.showerror("Error", "Please enter at least one token")
            return

        import re
        tokens = re.split(r"[\s,]+", raw_text)
        tokens = [t.strip() for t in tokens if t.strip()]

        valid_tokens = []
        for token in tokens:
            if ":" in token and validate_token(token):
                valid_tokens.append(token)

        if valid_tokens:
            save_config({
                "api_keys": valid_tokens,   
                "DO1": []                   
            })
            mbox.showinfo("✅", f"valid tokens: {len(valid_tokens)}")
            self.destroy()
            self.on_success()
            print("Starting main gui. gConstructor started.")
        else:
            mbox.showerror("❌", "No valid tokens")
