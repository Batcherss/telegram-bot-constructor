import os
import json

CONFIG_PATH = "config.json"
API_PATH = "api.json"

DEFAULT_ACTIONS = {
    "Any message": [],
    "Specific message": [["trigger_text", "Trigger text", "entry"]],
    "Timer": [["duration_slider", "Timer (slider, sec)", "slider", 1, 120]],
    "Subscription check": [["channel", "Channel (@username)", "entry"]],
    "Send message": [["text", "Message text", "entry"], ["file", "Attach file", "file"]],
    "Reply in private": [["text", "Private message text", "entry"]],
    "Send sticker": [["sticker_id", "Sticker ID", "entry"]],
    "Reply to command": [["command", "Command without /", "entry"]],
    "Send photo": [["photo", "Choose photo", "file"]],
    "Send voice message": [["voice", "Choose voice (ogg/mp3)", "file"]],
    "Inline button": [
        ["text", "Message text", "entry"],
        ["buttons", "Buttons (JSON)", "entry"],
    ],
    "Switch to": [["to", "Switch to DO", "entry"]]
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        data = {"api_keys": [], "DO1": []}
        save_config(data)
        return data
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "api_key" in data:
                data["api_keys"] = [data.pop("api_key")]
                save_config(data)
            if "api_keys" not in data:
                data["api_keys"] = []
            if "DO1" not in data:
                data["DO1"] = []
            return data
    except Exception as e:
        print(f"err cfg load: {e}")
        return {"api_keys": [], "DO1": []}

def save_config(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        print("Saved config [config.json]")

def load_actions():
    if not os.path.exists(API_PATH):
        with open(API_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_ACTIONS, f, indent=2, ensure_ascii=False)
        return DEFAULT_ACTIONS
    try:
        with open(API_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and data:
                return data
            raise ValueError("error format actions")
    except Exception:
        with open(API_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_ACTIONS, f, indent=2, ensure_ascii=False)
        print("Loaded default actions config.")
        return DEFAULT_ACTIONS
