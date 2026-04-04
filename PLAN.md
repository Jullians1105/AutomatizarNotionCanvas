# Plan: Canvas LMS → Notion Sync Script

## Context

Sincronizar automáticamente las tareas/asignaciones de Canvas LMS (universidad, 9no semestre) hacia la base de datos "Tareas 9no" en Notion. El script se ejecutará manualmente bajo demanda. El proyecto parte de cero (directorio vacío).

---

## Estructura del Proyecto

```
AutomatizarNotionCanvas/
├── .env                    # Credenciales (gitignored)
├── .env.example            # Template sin secretos
├── .gitignore
├── requirements.txt
├── config.py               # Configuración, mapeo de cursos
├── canvas_client.py        # Cliente API Canvas con paginación
├── notion_client.py        # Cliente API Notion con rate limiting
├── sync.py                 # Lógica de sincronización
└── main.py                 # Punto de entrada
```

---

## Schema Real de Notion (verificado via API)

| Campo Notion        | Tipo API   | Mapeo Canvas                          |
|---------------------|------------|---------------------------------------|
| Descripción         | title      | assignment.name                       |
| Fecha Limite        | date       | assignment.due_at (UTC → UTC-5)       |
| Fecha de inicio     | date       | OMITIR (vacío)                        |
| Materia             | select     | curso Canvas → mapeo por substring    |
| Contexto            | rich_text  | texto después del último ">" en description (HTML→texto) |
| Estado de tarea     | **status** | default: "Sin empezar"                |
| URL                 | url        | OMITIR (vacío)                        |
| Personas            | person     | OMITIR (vacío)                        |
| Archivos            | file       | OMITIR (vacío)                        |

**Opciones de Estado**: "Sin empezar", "En curso", "Listo"

**Opciones de Materia** (exactas, sin tildes):
- Desarrollo del software seguro
- Modelo Estocastico
- Diseño de interfaces
- Nuevas tecnologias
- Proyecto 2
- Web 2
- Sistemas Expertos
- Aplicabilidad de IA

---

## Diagrama de Flujo

```
main.py → Cargar .env → Validar tokens
  │
  ├─→ NotionClient.get_existing_titles() → set[str] (deduplicación)
  │
  ├─→ CanvasClient.get_active_courses() → list[curso]
  │     │
  │     └─→ Para cada curso:
  │           ├─ map_course_to_materia(curso.name) → materia o skip
  │           └─ CanvasClient.get_assignments(curso.id)
  │                 └─→ Para cada assignment (published):
  │                       ├─ ¿Ya existe en Notion? → skip
  │                       ├─ extract_context(description) → texto post-">"
  │                       ├─ convert_utc_to_colombia(due_at, lock_at)
  │                       └─ NotionClient.create_page(record)
  │
  └─→ Imprimir reporte + escribir log
```

---

## Mapeo de Cursos (config.py)

Diccionario de substrings (case-insensitive) → valor Materia en Notion:

```python
COURSE_TO_MATERIA = {
    "software seguro": "Desarrollo del software seguro",
    "estoc":           "Modelo Estocastico",
    "interfaces":      "Diseño de interfaces",
    "nuevas tecnolog": "Nuevas tecnologias",
    "proyecto 2":      "Proyecto 2",
    "web 2":           "Web 2",
    "sistemas expertos": "Sistemas Expertos",
    "aplicabilidad de ia": "Aplicabilidad de IA",
}
```

**Lógica**: iterar el dict, si `key in canvas_course_name.lower()` → retornar valor. Si no hay match → log warning, skip curso.

**Nota**: Los substrings exactos se ajustarán tras ver los nombres reales de Canvas en la primera ejecución.

---

## Módulos Principales

### `canvas_client.py`
- `CanvasClient(base_url, token)` — requests.Session con Bearer token
- `_get_paginated(url, params)` — sigue Link headers `rel="next"` automáticamente
- `get_active_courses()` — `GET /courses?enrollment_state=active&per_page=100`
- `get_assignments(course_id)` — `GET /courses/{id}/assignments?per_page=100`, filtra `workflow_state == "published"`

### `notion_client.py`
- `NotionClient(token, database_id)` — headers con Notion-Version 2022-06-28
- `_request(method, endpoint, json)` — throttle 0.35s entre calls, retry en 429
- `get_existing_titles()` — POST `/databases/{id}/query` con paginación (`has_more`/`start_cursor`), retorna `set[str]`
- `create_page(properties)` — POST `/pages` con parent database_id

### `sync.py`
- `extract_context(html_description)` — convierte HTML a texto plano (strip tags), busca último ">", retorna texto después (strip). Si no hay ">", retorna string vacío. Usa `re.sub('<[^<]+?>', '', html)` o `html.parser` para limpiar tags HTML
- `convert_utc_to_colombia(iso_str)` — parse UTC, aplica offset -5h, retorna ISO 8601
- `map_course_to_materia(name, mapping)` — substring match
- `build_assignment_record(assignment, materia)` — transforma a dict interno
- `run_sync(canvas, notion, config)` — orquesta todo, retorna SyncReport

### `main.py`
- Carga `.env` con python-dotenv
- Configura logging (archivo + stdout)
- Ejecuta `run_sync()`, imprime reporte

---

## Formato de Propiedades Notion (API)

```python
properties = {
    "Descripción": {"title": [{"text": {"content": "Quiz Teoría"}}]},
    "Fecha Limite": {"date": {"start": "2026-04-10T18:59:00-05:00"}},
    "Fecha de inicio": {"date": {"start": "2026-04-05T03:00:00-05:00"}},
    "Materia": {"select": {"name": "Sistemas Expertos"}},
    "Contexto": {"rich_text": [{"text": {"content": "Quiz Teoría"}}]},
    "Estado de tarea": {"status": {"name": "Sin empezar"}},
    "URL": {"url": "https://umb.instructure.com/courses/123/assignments/456"},
}
```

**Notas importantes del schema**:
- "Estado de tarea" usa `{"status": {...}}`, NO `{"select": {...}}` — usar el tipo incorrecto causa error 400
- "Fecha Limite" sin tilde en "Limite"
- "Personas" es tipo `person`, se omite del payload (no enviar array vacío)

---

## Dependencias

```
requests>=2.31.0
python-dotenv>=1.0.0
```

Solo stdlib adicional: `datetime`, `logging`, `re`, `html`.

---

## Manejo de Errores

| Escenario | Acción |
|-----------|--------|
| Canvas 401/403 | Fatal, abortar con mensaje claro |
| Canvas 5xx / timeout | Retry 3x con backoff exponencial |
| Notion 429 (rate limit) | Leer Retry-After, esperar, reintentar (max 5x) |
| Notion 400 (bad request) | Log error + request body, skip assignment |
| due_at null | Enviar date: null (Notion acepta fechas vacías) |
| lock_at null | Enviar date: null |
| Curso sin mapeo | Log warning, skip todas sus assignments |
| Nombre vacío | Skip assignment |

---

## Casos Edge

1. **Sin ">" en la descripción** → Contexto = string vacío
2. **Múltiples ">"** (ej: `A > B > C`) → Extraer solo lo después del último: `C`
3. **">" al final del texto** → Contexto = string vacío
4. **due_at / lock_at null** → Fecha vacía en Notion (aceptable)
5. **Mismo nombre en 2 cursos** → Dedup por título los trataría como duplicados. Aceptable por ahora; si es problema, cambiar a dedup por URL
6. **Asignaciones no publicadas** → Filtradas por `workflow_state`, no se sincronizan
7. **Rich text > 2000 chars** → No aplica (Contexto es solo el texto post-">", siempre corto)
8. **Re-ejecución del script** → Idempotente: las tareas ya existentes se saltan
9. **HTML con ">" como entidad (`&gt;`)** → `html.unescape()` antes de buscar el separador

---

## Variables de Configuración (.env)

```
CANVAS_API_TOKEN=<token>
CANVAS_BASE_URL=https://umb.instructure.com/api/v1
NOTION_API_TOKEN=<token>
NOTION_DATABASE_ID=2fb1a500b28980129474c1918da62d40
```

---

## Verificación (End-to-End)

1. Crear `.env` con tokens reales
2. `pip install -r requirements.txt`
3. `python main.py` — primera ejecución
4. Verificar en Notion que aparecen tareas nuevas con campos correctos
5. `python main.py` — segunda ejecución, debe reportar 0 nuevas (idempotencia)
6. Revisar `canvas_notion_sync.log` para confirmar logging correcto

---

## Decisiones Confirmadas

- **Extracción de Contexto**: El texto con ">" viene del campo `assignment.description` (HTML). Se parseará el HTML a texto plano, se buscará el último ">", y se extraerá lo que sigue. Si no hay ">", Contexto queda vacío.
- **Deduplicación**: Por título (`Descripción`) como clave única. URL de Canvas se guarda como referencia adicional.
- **Filtro de cursos**: `enrollment_state=active` para obtener solo cursos del semestre actual.
- **Timezone**: UTC → UTC-5 (Colombia) usando `datetime.timezone(timedelta(hours=-5))`.
