import customtkinter as ctk
import tkinter.messagebox as mbox
from utils import load_config, save_config, load_actions
from tkinter import filedialog
from ui.bot import TelegramBotRunner
from net import validate_token
import time
import json
import platform
import os
import subprocess

ACTION_PARAMS = load_actions()
MAX_DOS = 6

class BotBuilderApp(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.config = load_config()
        self.current_do = "DO1"
        self.dos = [k for k in self.config if k.startswith("DO")]
        if not self.dos:
            self.dos = ["DO1"]
            self.config["DO1"] = []
        self.api_keys = self.config.get("api_keys", [])
        self.bot_runners = []

        self.build_ui()
        self.render_do_buttons()
        self.render_actions()
        self.build_status_labels()

        self.uptime_running = False
        self.uptime_seconds = 0

        print("Loaded configuration [config.json]")
        print("Loaded apikeys [api_keys]")
        print("Established connection to servers. ready to use")

    def build_status_labels(self):
        self.uptime_label = ctk.CTkLabel(self.sidebar, text="bot uptime: Not started")
        self.uptime_label.pack(side="bottom", pady=4, padx=10)

        self.active_bots_label = ctk.CTkLabel(self.sidebar, text="online bots: 0")
        self.active_bots_label.pack(side="bottom", pady=4, padx=10)

        self.ping_label = ctk.CTkLabel(self.sidebar, text="local ping: -- ms")
        self.ping_label.pack(side="bottom", pady=4, padx=10)

    def update_status_labels(self):
        if self.uptime_running:
            self.uptime_seconds = int(time.time() - self.bot_start_time)
            self.uptime_label.configure(text=f"bot uptime: {self.uptime_seconds} sec")

            active_bots = len(self.bot_runners)
            self.active_bots_label.configure(text=f"online bots: {active_bots}")

            ping = self.get_local_ping()
            if ping is not None:
                self.ping_label.configure(text=f"local ping: {ping} ms")
            else:
                self.ping_label.configure(text="local ping: error")

            self.after(3000, self.update_status_labels)

    def get_local_ping(self):
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', '8.8.8.8']

            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
            output = result.stdout
            import re
            match = re.search(r'time[=<]?\s*(\d+\.?\d*)\s*ms', output)
            if match:
                ping_ms = float(match.group(1))
                return ping_ms
            else:
                return None
        except Exception as e:
            print(f"Ping error: {e}")
            return None

    def build_ui(self):
        layout = ctk.CTkFrame(self)
        layout.pack(fill="both", expand=True, padx=10, pady=10)
        self.do_list_frame = ctk.CTkFrame(layout, width=100)
        self.do_list_frame.pack(side="left", fill="y")
        self.do_list_frame.pack_propagate(False)
        self.main_frame = ctk.CTkFrame(layout)
        self.main_frame.pack(side="left", fill="both", expand=True)

        self.actions_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.actions_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.sidebar = ctk.CTkFrame(layout, width=200)
        self.sidebar.pack(side="right", fill="y", padx=(10, 0))
        self.sidebar.pack_propagate(False)

        btn_pad = {"padx": 10, "pady": 10, "fill": "x"}
        self.btn_add = ctk.CTkButton(self.sidebar, text="➕ Add action", command=self.open_add_window)
        self.btn_add.pack(**btn_pad)
        self.btn_save = ctk.CTkButton(self.sidebar, text="💾 Save", command=self.save)
        self.btn_save.pack(**btn_pad)
        self.btn_start = ctk.CTkButton(self.sidebar, text="▶️ Start", command=self.start_all_bots)
        self.btn_start.pack(**btn_pad)
        self.btn_stop = ctk.CTkButton(self.sidebar, text="⏹️ Disable", command=self.stop_all_bots, state="disabled")
        self.btn_stop.pack(**btn_pad)

    def start_all_bots(self):
        self.bot_runners = []
        valid_keys = []

        for key in self.config.get("api_keys", []):
            if ":" not in key:
                print(f"[❌] Invalid token: {key}")
                continue
            if not validate_token(key):
                print(f"[❌] Token failed api check: {key}")
                continue

            try:
                runner = TelegramBotRunner(key, self.config, on_stop=self.on_bot_stopped)
                runner.start()
                self.bot_runners.append(runner)
            except Exception as e:
                print(f"[❌] error with starting bot with token {key[:10]}...: {e}")
        print(f"✅ active bots: {len(self.bot_runners)}")
        self.btn_add.configure(state="disabled")
        self.btn_save.configure(state="disabled")
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.start_uptime_counter()
        self.get_local_ping()



    def stop_all_bots(self):
        for runner in self.bot_runners:
            runner.stop()
        self.bot_runners.clear()

        self.btn_add.configure(state="normal")
        self.btn_save.configure(state="normal")
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")

        self.stop_uptime_counter()

    def start_uptime_counter(self):
        self.bot_start_time = time.time()
        self.uptime_seconds = 0
        self.uptime_running = True
        self.update_status_labels()

    def stop_uptime_counter(self):
        self.uptime_running = False

    def on_bot_stopped(self):
        pass  

    def render_do_buttons(self):
        for w in self.do_list_frame.winfo_children():
            w.destroy()

        for do_name in self.dos:
            b = ctk.CTkButton(self.do_list_frame, text=do_name, command=lambda n=do_name: self.switch_do(n))
            b.pack(pady=2, padx=5, fill="x")

        if len(self.dos) < MAX_DOS:
            ctk.CTkButton(self.do_list_frame, text="➕", command=self.add_do).pack(pady=(10, 0), padx=5, fill="x")

    def add_do(self):
        next_index = len(self.dos) + 1
        new_do = f"DO{next_index}"
        self.dos.append(new_do)
        self.config[new_do] = []
        self.switch_do(new_do)
        self.render_do_buttons()

    def switch_do(self, name):
        self.current_do = name
        self.render_actions()

    def render_actions(self):
        for w in self.actions_frame.winfo_children():
            w.destroy()
        actions = self.config.get(self.current_do, [])
        for i, act in enumerate(actions):
            fr = ctk.CTkFrame(self.actions_frame, corner_radius=5, fg_color="#222")
            fr.pack(fill="x", pady=5, padx=5)
            summary = f"{i+1}. {act['type']} " + ", ".join(f"{k}:{v}" for k, v in act.items() if k != "type")
            ctk.CTkLabel(fr, text=summary, wraplength=400).pack(side="left", padx=10, pady=5)
            fb = ctk.CTkFrame(fr)
            fb.pack(side="right", padx=5)
            ctk.CTkButton(fb, text="❌", width=30, command=lambda i=i: self.delete(i)).pack(side="left", padx=2)

    def delete(self, i):
        if self.current_do in self.config:
            del self.config[self.current_do][i]
        self.render_actions()

    def save(self):
        save_config(self.config)
        mbox.showinfo("✅ saved", "Config saved")
        print("Saved config [config.json]")

    def open_add_window(self):
        w = ctk.CTkToplevel(self)
        w.title("New action")
        w.geometry("400x350")
        w.grab_set()

        ctk.CTkLabel(w, text="Type of action:", font=("", 14)).pack(pady=10)
        combo = ctk.CTkOptionMenu(w, values=list(ACTION_PARAMS.keys()))
        combo.pack(fill="x", padx=20)
        combo.set(list(ACTION_PARAMS.keys())[0])

        params_frame = ctk.CTkScrollableFrame(w, height=200)
        params_frame.pack(fill="both", padx=20, pady=10)

        widgets = {}

        def on_type_change(choice):
            for ch in params_frame.winfo_children():
                ch.destroy()
            widgets.clear()
            for p in ACTION_PARAMS.get(choice, []):
                key, label, ptype = p[:3]
                ctk.CTkLabel(params_frame, text=label).pack(anchor="w", pady=5)
                if ptype == "entry":
                    ent = ctk.CTkEntry(params_frame)
                    ent.pack(fill="x", pady=2)
                    if key == "buttons":
                        ent.insert(0, '[{"text": "button 1", "callback_data": "btn1"}, {"text": "go", "url": "https://example.com"}]')
                    widgets[key] = ent
                elif ptype == "slider":
                    sl = ctk.CTkSlider(params_frame, from_=1, to=120, number_of_steps=119)
                    sl.set(10)
                    sl.pack(fill="x")
                    lbl = ctk.CTkLabel(params_frame, text="10 сек")
                    lbl.pack()
                    sl.configure(command=lambda v: lbl.configure(text=f"{int(float(v))} сек"))
                    widgets[key] = sl
                elif ptype == "file":
                    path = ctk.StringVar()
                    frf = ctk.CTkFrame(params_frame)
                    frf.pack(fill="x", pady=2)
                    ent = ctk.CTkEntry(frf, textvariable=path)
                    ent.pack(side="left", fill="x", expand=True)
                    btn = ctk.CTkButton(frf, text="📁", width=30, command=lambda v=path: v.set(filedialog.askopenfilename()))
                    btn.pack(side="right", padx=5)
                    widgets[key] = path

        combo.configure(command=on_type_change)
        on_type_change(combo.get())

        def add_action():
            act_type = combo.get()
            action = {"type": act_type}
            for key, wdg in widgets.items():
                if isinstance(wdg, ctk.CTkEntry):
                    v = wdg.get().strip()
                    if v:
                        action[key] = v
                elif isinstance(wdg, ctk.CTkSlider):
                    action["duration"] = int(wdg.get())
                elif isinstance(wdg, ctk.StringVar):
                    v = wdg.get().strip()
                    if v:
                        action[key] = v
            self.config[self.current_do].append(action)
            w.destroy()
            self.render_actions()

        ctk.CTkButton(w, text="Add ✅", command=add_action).pack(pady=10)
