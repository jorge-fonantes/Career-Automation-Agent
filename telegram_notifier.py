import requests
import os
from dotenv import load_dotenv

# Carrega as variáveis do .env assim que o módulo é importado
load_dotenv()

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.token or not self.chat_id:
            print("⚠️ AVISO: Configurações do Telegram não encontradas no .env")
            self.base_url = None
        else:
            self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_report(self, message):
        if not self.base_url: return
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"}
            requests.post(url, json=payload)
        except Exception as e:
            print(f"⚠️ Erro Telegram: {e}")

    def send_file(self, file_path, caption=""):
        if not self.base_url: return
        try:
            url = f"{self.base_url}/sendDocument"
            with open(file_path, "rb") as f:
                files = {"document": f}
                data = {"chat_id": self.chat_id, "caption": caption}
                requests.post(url, data=data, files=files)
        except: pass