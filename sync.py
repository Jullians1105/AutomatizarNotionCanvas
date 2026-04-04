import html
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta

from canvas_client import CanvasClient
from notion_client import NotionClient

logger = logging.getLogger(__name__)

COLOMBIA_TZ = timezone(timedelta(hours=-5))


def get_current_week_range() -> tuple[datetime, datetime]:
    now = datetime.now(COLOMBIA_TZ)
    monday = now - timedelta(days=now.weekday())
    week_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return week_start, week_end


def is_due_this_week(due_at: str | None) -> bool:
    if not due_at:
        return False
    dt_utc = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
    dt_col = dt_utc.astimezone(COLOMBIA_TZ)
    now = datetime.now(COLOMBIA_TZ)
    week_start, week_end = get_current_week_range()
    return now <= dt_col <= week_end


@dataclass
class SyncReport:
    created: int = 0
    skipped: int = 0
    errors: int = 0
    skipped_courses: list[str] = field(default_factory=list)
    created_tasks: list[dict] = field(default_factory=list)


def extract_context(html_description: str) -> str:
    if not html_description:
        return ""
    unescaped = html.unescape(html_description)
    plain = re.sub(r"<[^<]+?>", "", unescaped).strip()
    last_gt = plain.rfind(">")
    if last_gt == -1 or last_gt == len(plain) - 1:
        return ""
    return plain[last_gt + 1:].strip()


def convert_utc_to_colombia(iso_str: str | None) -> str | None:
    if not iso_str:
        return None
    dt_utc = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    dt_col = dt_utc.astimezone(COLOMBIA_TZ)
    return dt_col.isoformat()


def map_course_to_materia(course_name: str, mapping: dict) -> str | None:
    lower = course_name.lower()
    for key, materia in mapping.items():
        if key in lower:
            return materia
    return None


def build_notion_properties(assignment: dict, materia: str, submitted: bool = False) -> dict:
    url = assignment.get("html_url", "").strip()
    name = assignment.get("name", "").strip() or url
    due_at = convert_utc_to_colombia(assignment.get("due_at"))
    estado = "Listo" if submitted else "Sin empezar"

    properties = {
        "Descripción": {"title": [{"text": {"content": name, "link": {"url": url}}}]},
        "Materia": {"select": {"name": materia}},
        "Estado de tarea": {"status": {"name": estado}},
    }

    if due_at:
        properties["Fecha Limite"] = {"date": {"start": due_at}}

    return properties


def run_sync(canvas: CanvasClient, notion: NotionClient, course_mapping: dict) -> SyncReport:
    report = SyncReport()

    existing_urls = notion.get_existing_titles()
    courses = canvas.get_active_courses()

    for course in courses:
        course_name = course.get("name", "")
        course_id = course.get("id")

        materia = map_course_to_materia(course_name, course_mapping)
        if not materia:
            logger.warning("Sin mapeo para curso: '%s' (id=%s) — saltando", course_name, course_id)
            report.skipped_courses.append(course_name)
            continue

        logger.info("Procesando curso: '%s' → '%s'", course_name, materia)
        assignments = canvas.get_assignments(course_id)

        for assignment in assignments:
            url = assignment.get("html_url", "").strip()
            name = assignment.get("name", "").strip()

            if not url:
                logger.warning("Asignacion sin URL en curso '%s', saltando", course_name)
                report.skipped += 1
                continue

            if not is_due_this_week(assignment.get("due_at")):
                logger.debug("Fuera de la semana actual: '%s' — saltando", name)
                report.skipped += 1
                continue

            if url in existing_urls:
                logger.debug("Ya existe en Notion: '%s' — saltando", url)
                report.skipped += 1
                continue

            try:
                submission_state = canvas.get_submission_state(course_id, assignment.get("id"))
                submitted = submission_state == "submitted"
                properties = build_notion_properties(assignment, materia, submitted)
                notion.create_page(properties)
                existing_urls.add(url)
                report.created += 1
                report.created_tasks.append({
                    "name": name,
                    "materia": materia,
                    "due_at": assignment.get("due_at"),
                })
                logger.info("Creada: '%s' (%s)", name, url)
            except Exception as e:
                logger.error("Error creando '%s': %s", url, e)
                report.errors += 1

    return report
