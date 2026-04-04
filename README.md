# Canvas → Notion Sync

Automatiza la sincronización de tareas de Canvas LMS a una base de datos de Notion. Filtra las tareas de la semana actual, evita duplicados, detecta si ya fueron entregadas y envía notificaciones por Telegram.

---

## Requisitos

- Python 3.11+
- Cuenta en Canvas LMS con acceso a la API
- Base de datos en Notion con las columnas correctas
- Bot de Telegram
- (Opcional) Cuenta en GitHub para automatización en la nube

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/AutomatizarNotionCanvas.git
cd AutomatizarNotionCanvas
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Copia el archivo de ejemplo y rellena con tus credenciales:

```bash
cp .env.example .env
```

Edita `.env`:

```env
CANVAS_API_TOKEN=tu_token_de_canvas
CANVAS_BASE_URL=https://tu-institucion.instructure.com/api/v1
NOTION_API_TOKEN=tu_token_de_notion
NOTION_DATABASE_ID=id_de_tu_base_de_datos
TELEGRAM_BOT_TOKEN=token_de_tu_bot
TELEGRAM_CHAT_ID=tu_chat_id
```

---

## Obtener las credenciales

### Canvas API Token
1. Entra a Canvas → **Cuenta** → **Configuración**
2. Baja hasta **Tokens de acceso aprobados**
3. Clic en **Generar nuevo token**

### Notion API Token y Database ID
1. Ve a [notion.so/my-integrations](https://www.notion.so/my-integrations) y crea una integración
2. Copia el **Internal Integration Token**
3. Abre tu base de datos en Notion → **...** → **Connections** → conecta tu integración
4. El Database ID está en la URL: `notion.so/{workspace}/{DATABASE_ID}?v=...`

### Telegram Bot Token y Chat ID
1. Abre **@BotFather** en Telegram → `/newbot` → sigue los pasos
2. BotFather te dará el token del bot
3. Escríbele al bot y abre en el navegador:
   ```
   https://api.telegram.org/bot{TOKEN}/getUpdates
   ```
4. Busca `"chat":{"id":...}` — ese es tu Chat ID

---

## Estructura de la base de datos en Notion

La base de datos debe tener exactamente estas columnas:

| Columna | Tipo |
|---|---|
| Descripción | Título |
| Materia | Select |
| Estado de tarea | Status |
| Fecha Limite | Date |

---

## Mapeo de cursos

En `config.py` define los substrings del nombre de tus cursos en Canvas y el nombre de la materia en Notion:

```python
COURSE_TO_MATERIA = {
    "ingenieria web": "Web 2",
    "estocastico":    "Modelo Estocastico",
    # agrega tus cursos aquí
}
```

Para ver los nombres exactos de tus cursos activos en Canvas puedes consultar:
```
GET /api/v1/courses?enrollment_state=active
```

---

## Uso local

```bash
python main.py
```

Al finalizar verás un reporte en consola y un log en `canvas_notion_sync.log`.

---

## Automatización con GitHub Actions

El workflow `.github/workflows/sync.yml` ejecuta el script automáticamente en la nube.

### Configurar secrets en GitHub

Ve a tu repositorio → **Settings** → **Secrets and variables** → **Actions** → **New repository secret** y agrega:

| Secret | Valor |
|---|---|
| `CANVAS_API_TOKEN` | Tu token de Canvas |
| `CANVAS_BASE_URL` | URL base de tu Canvas |
| `NOTION_API_TOKEN` | Tu token de Notion |
| `NOTION_DATABASE_ID` | ID de tu base de datos |
| `TELEGRAM_BOT_TOKEN` | Token de tu bot |
| `TELEGRAM_CHAT_ID` | Tu Chat ID |

### Horario de ejecución

- **Lunes a viernes**: cada 2 horas (12am, 2am, 4am... 10pm hora Colombia)
- **Domingo 10pm** hora Colombia
- **Sábado**: sin ejecución

También puedes ejecutarlo manualmente desde la pestaña **Actions** → **Run workflow**.

---

## Comportamiento

- Solo sincroniza tareas con fecha límite entre el lunes y el domingo de la semana en curso (hora Colombia UTC-5)
- No crea duplicados: compara por URL de la tarea en Canvas
- Si la tarea ya fue entregada en Canvas → se crea con estado **Listo**
- Si no ha sido entregada → se crea con estado **Sin empezar**
- Envía notificación por Telegram solo cuando se agregan tareas nuevas
