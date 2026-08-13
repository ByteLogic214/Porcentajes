import os
import requests

class TelegramNotifier:
    """Envío inmediato de selecciones con EV+ a Telegram."""
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def send_pick(self, match: str, league: str, market: str, stat_prob: float, odds: float, ev: float, stake: int):
        if not self.token or not self.chat_id:
            print("Variables TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configuradas.")
            return

        message = (
            f"🎯 <b>SELECCIÓN EV+ DETECTADA</b>\n\n"
            f"⚽ <b>Partido:</b> {match}\n"
            f"🏆 <b>Liga:</b> {league}\n"
            f"📊 <b>Mercado:</b> {market}\n"
            f"📈 <b>Prob. Estadística:</b> {stat_prob}%\n"
            f"💰 <b>Cuota Actual:</b> {odds}\n"
            f"🔥 <b>EV:</b> +{ev}%\n"
            f"📌 <b>Stake:</b> {stake}/10"
        )
        
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            res = requests.post(url, json=payload, timeout=10)
            res.raise_for_status()
            print(f"Alerta enviada correctamente a Telegram para {match}")
        except Exception as e:
            print(f"Error al enviar la notificación a Telegram: {e}")
