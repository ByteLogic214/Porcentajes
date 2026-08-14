import os
import requests
from typing import Optional
from datetime import datetime
from config.settings import settings

class TelegramNotifier:
    """Sistema de notificaciones vía Telegram."""
    
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else None
    
    def is_configured(self) -> bool:
        """Verifica si Telegram está correctamente configurado."""
        return bool(self.token and self.chat_id)
    
    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Envía un mensaje de texto a Telegram.
        
        Args:
            text: Mensaje a enviar
            parse_mode: Formato del mensaje (HTML o Markdown)
            
        Returns:
            True si se envió correctamente
        """
        if not self.is_configured():
            print("⚠️ Telegram no configurado. Mensaje no enviado.")
            return False
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ Error enviando mensaje a Telegram: {e}")
            return False
    
    def send_pick(self, 
                  match: str,
                  league: str,
                  market: str,
                  stat_prob: float,
                  odds: float,
                  ev: float,
                  stake: int,
                  bookmaker: str = "Media",
                  match_time: Optional[str] = None) -> bool:
        """
        Envía una selección de apuesta con EV+ a Telegram.
        
        Args:
            match: Nombre del partido (Ej: "Barcelona vs Real Madrid")
            league: Liga del partido
            market: Mercado de apuesta
            stat_prob: Probabilidad estadística calculada
            odds: Cuota de la casa de apuestas
            ev: Expected Value en porcentaje
            stake: Tamaño de apuesta recomendado (1-10)
            bookmaker: Casa de apuestas
            match_time: Hora del partido (opcional)
            
        Returns:
            True si se envió correctamente
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_info = f"\n🕒 <b>Hora partido:</b> {match_time}" if match_time else ""
        
        message = (
            f"🎯 <b>SELECCIÓN EV+ DETECTADA</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚽ <b>Partido:</b> {match}\n"
            f"🏆 <b>Liga:</b> {league}\n"
            f"📊 <b>Mercado:</b> {market}\n"
            f"{time_info}\n"
            f"\n📈 <b>ANÁLISIS:</b>\n"
            f"├─ Probabilidad Real: <b>{stat_prob}%</b>\n"
            f"├─ Cuota Casa: <b>{odds}</b>\n"
            f"├─ Casa de Apuestas: <b>{bookmaker}</b>\n"
            f"└─ Expected Value: <b>+{ev}%</b>\n"
            f"\n💰 <b>RECOMENDACIÓN:</b>\n"
            f"└─ Stake Kelly: <b>{stake}/10</b>\n"
            f"\n⏰ {timestamp}"
        )
        
        return self.send_message(message)
    
    def send_daily_summary(self, 
                          total_picks: int,
                          leagues_analyzed: int,
                          avg_ev: float,
                          best_pick: Optional[dict] = None) -> bool:
        """
        Envía un resumen diario del análisis.
        
        Args:
            total_picks: Total de picks encontrados
            leagues_analyzed: Número de ligas analizadas
            avg_ev: EV promedio de los picks
            best_pick: Mejor pick del día (opcional)
            
        Returns:
            True si se envió correctamente
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        best_pick_text = ""
        if best_pick:
            best_pick_text = (
                f"\n🏆 <b>MEJOR PICK DEL DÍA:</b>\n"
                f"├─ {best_pick['match']}\n"
                f"├─ Mercado: {best_pick['market']}\n"
                f"├─ EV: +{best_pick['ev']}%\n"
                f"└─ Stake: {best_pick['stake']}/10"
            )
        
        message = (
            f"📊 <b>RESUMEN DIARIO</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 {timestamp}\n\n"
            f"📈 <b>ESTADÍSTICAS:</b>\n"
            f"├─ Picks Detectados: <b>{total_picks}</b>\n"
            f"├─ Ligas Analizadas: <b>{leagues_analyzed}</b>\n"
            f"└─ EV Promedio: <b>+{avg_ev}%</b>\n"
            f"{best_pick_text}\n"
            f"\n✅ Análisis completado con éxito"
        )
        
        return self.send_message(message)
    
    def send_error(self, error_message: str) -> bool:
        """
        Envía un mensaje de error crítico.
        
        Args:
            error_message: Descripción del error
            
        Returns:
            True si se envió correctamente
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = (
            f"🚨 <b>ERROR EN EL SISTEMA</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ {timestamp}\n\n"
            f"❌ <b>Descripción:</b>\n"
            f"{error_message}\n\n"
            f"⚠️ Requiere atención inmediata"
        )
        
        return self.send_message(message)
