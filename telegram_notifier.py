import logging
import requests

logger = logging.getLogger(__name__)


def send_telegram_message(token: str, chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Notificación Telegram enviada")
    except Exception as e:
        logger.error("Error enviando notificación Telegram: %s", e)


def build_notification(report) -> str | None:
    if report.created == 0:
        return None
    lines = [f"*Canvas → Notion Sync*", f"✅ {report.created} tarea(s) nueva(s) agregada(s)"]
    return "\n".join(lines)
