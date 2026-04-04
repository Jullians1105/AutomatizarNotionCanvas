import logging
import sys

from config import (
    CANVAS_API_TOKEN,
    CANVAS_BASE_URL,
    NOTION_API_TOKEN,
    NOTION_DATABASE_ID,
    COURSE_TO_MATERIA,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from canvas_client import CanvasClient
from notion_client import NotionClient
from sync import run_sync
from telegram_notifier import send_telegram_message, build_notification

LOG_FILE = "canvas_notion_sync.log"


def setup_logging():
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("=== Iniciando sincronización Canvas → Notion ===")

    canvas = CanvasClient(CANVAS_BASE_URL, CANVAS_API_TOKEN)
    notion = NotionClient(NOTION_API_TOKEN, NOTION_DATABASE_ID)

    report = run_sync(canvas, notion, COURSE_TO_MATERIA)

    message = build_notification(report)
    send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)

    print("\n--- Reporte de sincronización ---")
    print(f"  Tareas creadas:  {report.created}")
    print(f"  Tareas saltadas: {report.skipped}")
    print(f"  Errores:         {report.errors}")
    if report.skipped_courses:
        print(f"  Cursos sin mapeo ({len(report.skipped_courses)}):")
        for name in report.skipped_courses:
            print(f"    - {name}")
    print(f"\nLog guardado en: {LOG_FILE}")
    logger.info(
        "Sincronización completa — creadas: %d, saltadas: %d, errores: %d",
        report.created, report.skipped, report.errors,
    )


if __name__ == "__main__":
    main()
