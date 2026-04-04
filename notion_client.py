import logging
import time
import requests

logger = logging.getLogger(__name__)

NOTION_VERSION = "2022-06-28"
THROTTLE_SECONDS = 0.35


class NotionClient:
    def __init__(self, token: str, database_id: str):
        self.database_id = database_id
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        })
        self._last_request_time = 0.0

    def _throttle(self):
        elapsed = time.monotonic() - self._last_request_time
        wait = THROTTLE_SECONDS - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request_time = time.monotonic()

    def _request(self, method: str, endpoint: str, json: dict = None, max_retries: int = 5) -> requests.Response:
        url = f"https://api.notion.com/v1{endpoint}"
        delay = 1

        for attempt in range(1, max_retries + 1):
            self._throttle()
            response = self.session.request(method, url, json=json, timeout=30)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", delay))
                logger.warning(
                    "Notion rate limit (429), esperando %ds (intento %d/%d)...",
                    retry_after, attempt, max_retries,
                )
                time.sleep(retry_after)
                delay *= 2
                continue

            if response.status_code == 400:
                logger.error(
                    "Notion bad request (400): %s | body: %s",
                    response.text, json,
                )
                response.raise_for_status()

            response.raise_for_status()
            return response

        raise RuntimeError(f"Notion: máximo de reintentos alcanzado para {method} {endpoint}")

    def get_existing_titles(self) -> set[str]:
        titles = set()
        start_cursor = None

        while True:
            body = {"page_size": 100}
            if start_cursor:
                body["start_cursor"] = start_cursor

            response = self._request("POST", f"/databases/{self.database_id}/query", json=body)
            data = response.json()

            for page in data.get("results", []):
                title_prop = page.get("properties", {}).get("Descripción", {})
                title_parts = title_prop.get("title", [])
                if title_parts:
                    link = title_parts[0].get("text", {}).get("link")
                    if link:
                        titles.add(link["url"])
                    else:
                        titles.add(title_parts[0]["text"]["content"])

            if data.get("has_more"):
                start_cursor = data["next_cursor"]
            else:
                break

        logger.info("Notion: %d tareas existentes encontradas", len(titles))
        return titles

    def create_page(self, properties: dict) -> dict:
        body = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
        }
        response = self._request("POST", "/pages", json=body)
        logger.debug("Notion: página creada OK")
        return response.json()
