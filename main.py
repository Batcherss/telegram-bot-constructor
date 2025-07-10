import customtkinter as ctk
from utils import load_config
from net import validate_token
from ui.login import LoginWindow
from ui.builder import BotBuilderApp

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VreD 4.1")
        self.geometry("820x400")
        self.config = load_config()
        print("VreD 4.1 | Loading modules.")

        self.valid_token = None
        api_keys = self.config.get("api_keys", [])

        for key in api_keys:
            if validate_token(key):
                self.valid_token = key
                break

        if not self.valid_token:
            self.withdraw()
            LoginWindow(self, self.start_builder)
        else:
            print(f"Found valid telegram bot apikey: {self.valid_token[:6]}... Logging in.")
            self.start_builder()

    def start_builder(self):
        self.deiconify()
        app = BotBuilderApp(self)
        app.pack(fill="both", expand=True)
        print("Starting GUI Module..")

if __name__ == "__main__":
    MainApp().mainloop()
