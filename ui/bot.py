import telebot
import threading
import time
import os
import json
import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

class TelegramBotRunner:
    def __init__(self, api_key, config, on_stop=None):
        self.api_key = api_key
        self.config = config
        self.bot = telebot.TeleBot(self.api_key)
        self.running = False
        self.thread = None
        self.on_stop = on_stop
        self.timers = {}
        self.delay_ms = 0  # 🆕 добавлено для отслеживания задержки

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        print("Started bot. Running on telebot service.")
        print("Log file created. Logging into console.")
        print("--------------------=LOG=--------------------")

    def stop(self):
        self.running = False
        try:
            self.bot.stop_polling()
        except Exception as e:
            print(f"[stop error] {e}")

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.2)
        if self.on_stop:
            self.on_stop()

    def run(self):
        bot = self.bot

        try:
            bot.delete_webhook()  
            print(f"[{self.api_key[:10]}...] Webhook удалён")
        except Exception as e:
            print(f"[{self.api_key[:10]}...] Не удалось удалить webhook: {e}")

        def log_message(msg):
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            username = msg.from_user.first_name or "Unknown"
            if msg.from_user.last_name:
                username += " " + msg.from_user.last_name
            text = msg.text or "<non-text message>"
            log_line = f"{now} - {text} - {username}\n"
            print(log_line)
            with open("bot_messages.log", "a", encoding="utf-8") as f:
                f.write(log_line)

        @bot.message_handler(func=lambda m: True)
        def handle(msg):
            if not self.running:
                return
            log_message(msg)
            chat_id = msg.chat.id
            self.execute_do_block("DO1", msg, chat_id)

        while self.running:
            try:
                bot.polling(non_stop=False, timeout=60)
            except Exception as e:
                print(f"[polling error] {e}")
                time.sleep(3)

    def execute_do_block(self, do_name, msg, chat_id):
        if do_name not in self.config:
            print(f"[warn] DO-блок {do_name} не найден.")
            return

        actions = self.config[do_name]

        for idx, act in enumerate(actions):
            t = act.get("type")

            def send(text):
                self.bot.send_message(chat_id, text)

            def send_f(path, cap=None):
                if not os.path.isfile(path):
                    return
                ext = os.path.splitext(path)[1].lower()
                with open(path, "rb") as f:
                    if ext in [".jpg", ".png"]:
                        self.bot.send_photo(chat_id, f, caption=cap)
                    elif ext in [".ogg", ".mp3"]:
                        self.bot.send_voice(chat_id, f, caption=cap)
                    else:
                        self.bot.send_document(chat_id, f)

            if t == "Любое сообщение" and "text" in act:
                send(act["text"])

            elif t == "Конкретное сообщение" and msg.text and msg.text.lower() == act.get("trigger_text", "").lower():
                send(act.get("text", ""))

            elif t == "Проверка подписки":
                try:
                    st = self.bot.get_chat_member(act.get("channel"), msg.from_user.id).status
                    if st in ["member", "administrator", "creator"]:
                        send(act.get("text", ""))
                except Exception:
                    pass

            elif t == "Таймер":
                key = f"{chat_id}_{do_name}_{idx}"
                if key in self.timers:
                    continue
                self.timers[key] = True

                def ti():
                    duration = min(int(act.get("duration", 1)), 120)
                    time.sleep(duration)
                    send(act.get("text", ""))
                    self.timers.pop(key, None)

                threading.Thread(target=ti, daemon=True).start()

            elif t == "Вывод сообщения":
                if act.get("file"):
                    send_f(act["file"], cap=act.get("text", ""))
                else:
                    send(act.get("text", ""))

            elif t == "Ответить в приват":
                try:
                    self.bot.send_message(msg.from_user.id, act.get("text", ""))
                except Exception:
                    pass

            elif t == "Отправить стикер":
                self.bot.send_sticker(chat_id, act.get("sticker_id"))

            elif t == "Ответить на команду" and msg.text and msg.text.startswith("/" + act.get("command", "")):
                send(act.get("text", ""))

            elif t == "Отправить фото":
                send_f(act.get("photo"))

            elif t == "Отправить голосовое сообщение":
                send_f(act.get("voice"))

            elif t == "Переход":
                target = act.get("to")
                if target in self.config:
                    self.execute_do_block(target, msg, chat_id)
                else:
                    print(f"[warn] DO-блок для перехода {target} не найден.")

            elif t == "Inline кнопка":
                text = act.get("text", "")
                buttons_json = act.get("buttons", "[]")
                try:
                    buttons_data = json.loads(buttons_json)
                    markup = InlineKeyboardMarkup()
                    for btn in buttons_data:
                        if "url" in btn:
                            markup.add(InlineKeyboardButton(btn["text"], url=btn["url"]))
                        elif "callback_data" in btn:
                            markup.add(InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"]))
                        else:
                            markup.add(InlineKeyboardButton(btn["text"], callback_data="noop"))
                    send(text, markup=markup)
                except Exception as e:
                    print(f"[inline button parse error] {e}")
                    send(text)  

