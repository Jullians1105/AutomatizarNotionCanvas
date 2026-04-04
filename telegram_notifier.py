import logging
import requests
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

COLOMBIA_TZ = timezone(timedelta(hours=-5))


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


def _format_due(due_at: str | None) -> str:
    if not due_at:
        return "Sin fecha"
    dt = datetime.fromisoformat(due_at.replace("Z", "+00:00")).astimezone(COLOMBIA_TZ)
    return dt.strftime("%d/%m/%Y %I:%M %p")


def build_notification(report) -> str | None:
    if report.created == 0:
        return None
    lines = [f"*Canvas → Notion Sync*", f"✅ {report.created} tarea(s) nueva(s):\n"]
    for task in report.created_tasks:
        lines.append(f"📚 *{task['materia']}*")
        lines.append(f"📝 {task['name']}")
        lines.append(f"📅 {_format_due(task['due_at'])}\n")
    return "\n".join(lines)
