import requests
import os
import time
from dotenv import load_dotenv

# Carrega as variáveis do .env assim que o módulo é importado
load_dotenv()

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        # Aceita mais de um destinatário, separados por vírgula: "111,222"
        self.chat_ids = [c.strip() for c in (os.getenv("TELEGRAM_CHAT_ID") or "").split(",") if c.strip()]
        self.chat_id = self.chat_ids[0] if self.chat_ids else None

        if not self.token or not self.chat_ids:
            print("⚠️ AVISO: Configurações do Telegram não encontradas no .env")
            self.base_url = None
        else:
            self.base_url = f"https://api.telegram.org/bot{self.token}"

    def verificar(self):
        """ Testa token e chat ID sem mandar mensagem: só mostra "digitando..." por um instante. """
        if not self.base_url: return False
        for chat_id in self.chat_ids:
            try:
                resp = requests.post(f"{self.base_url}/sendChatAction",
                                     json={"chat_id": chat_id, "action": "typing"}, timeout=30)
            except requests.RequestException as e:
                print(f"⚠️ Erro Telegram: falha de conexão ({type(e).__name__})")
                return False
            if not resp.ok:
                print(f"⚠️ Erro Telegram: {resp.status_code} {resp.text[:200]}")
                return False
        return True

    def send_report(self, message):
        """ Envia texto em HTML do Telegram. Devolve True só se todos os destinatários receberam. """
        if not self.base_url: return False
        # all() pararia no primeiro erro e deixaria os outros sem a mensagem
        return all([self._enviar(chat_id, message) for chat_id in self.chat_ids])

    def _enviar(self, chat_id, message):
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        for _ in range(2):
            try:
                resp = requests.post(url, json=payload, timeout=30)
            except requests.RequestException as e:
                # A mensagem de erro pode conter a URL com o token, então não vai para o log
                print(f"⚠️ Erro Telegram: falha de conexão ({type(e).__name__})")
                return False
            if resp.status_code != 429:
                break
            # Limite de envio: o Telegram informa quanto tempo esperar
            time.sleep(resp.json().get("parameters", {}).get("retry_after", 5))
        if not resp.ok:
            print(f"⚠️ Erro Telegram: {resp.status_code} {resp.text[:200]}")
        return resp.ok

    def send_file(self, file_path, caption=""):
        if not self.base_url: return
        try:
            url = f"{self.base_url}/sendDocument"
            with open(file_path, "rb") as f:
                files = {"document": f}
                data = {"chat_id": self.chat_id, "caption": caption}
                requests.post(url, data=data, files=files)
        except: pass
