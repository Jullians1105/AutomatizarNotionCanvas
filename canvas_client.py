import logging
import time
import requests

logger = logging.getLogger(__name__)


class CanvasClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def _get_paginated(self, url: str, params: dict = None) -> list:
        results = []
        current_url = url
        current_params = params

        while current_url:
            response = self._request_with_retry(current_url, current_params)
            results.extend(response.json())

            next_url = self._parse_next_link(response.headers.get("Link", ""))
            current_url = next_url
            current_params = None  # params only on first request

        return results

    def _request_with_retry(self, url: str, params: dict = None, max_retries: int = 3) -> requests.Response:
        delay = 2
        for attempt in range(1, max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=30)

                if response.status_code in (401, 403):
                    raise SystemExit(
                        f"Canvas auth error {response.status_code}: verifica tu CANVAS_API_TOKEN"
                    )

                if response.status_code >= 500:
                    if attempt == max_retries:
                        response.raise_for_status()
                    logger.warning(
                        "Canvas %s en intento %d/%d, reintentando en %ds...",
                        response.status_code, attempt, max_retries, delay,
                    )
                    time.sleep(delay)
                    delay *= 2
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.Timeout:
                if attempt == max_retries:
                    raise
                logger.warning("Timeout en intento %d/%d, reintentando...", attempt, max_retries)
                time.sleep(delay)
                delay *= 2

    def _parse_next_link(self, link_header: str) -> str | None:
        for part in link_header.split(","):
            segments = part.strip().split(";")
            if len(segments) == 2 and segments[1].strip() == 'rel="next"':
                return segments[0].strip().strip("<>")
        return None

    def get_active_courses(self) -> list[dict]:
        url = f"{self.base_url}/courses"
        params = {"enrollment_state": "active", "per_page": 100}
        courses = self._get_paginated(url, params)
        logger.info("Canvas: %d cursos activos encontrados", len(courses))
        return courses

    def get_assignments(self, course_id: int) -> list[dict]:
        url = f"{self.base_url}/courses/{course_id}/assignments"
        params = {"per_page": 100}
        all_assignments = self._get_paginated(url, params)
        published = [a for a in all_assignments if a.get("workflow_state") == "published"]
        logger.debug(
            "Curso %s: %d asignaciones totales, %d publicadas",
            course_id, len(all_assignments), len(published),
        )
        return published

    def get_submission_state(self, course_id: int, assignment_id: int) -> str:
        url = f"{self.base_url}/courses/{course_id}/assignments/{assignment_id}/submissions/self"
        response = self._request_with_retry(url)
        return response.json().get("workflow_state", "unsubmitted")
