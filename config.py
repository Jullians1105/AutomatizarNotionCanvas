import os
from dotenv import load_dotenv

load_dotenv()

CANVAS_API_TOKEN = os.environ["CANVAS_API_TOKEN"]
CANVAS_BASE_URL = os.environ["CANVAS_BASE_URL"]
NOTION_API_TOKEN = os.environ["NOTION_API_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

COURSE_TO_MATERIA = {
    "mercadeo":              "Mercadeo",             # MERCADEO
    "cerebro":               "Cerebro",              # CEREBRO
    "ambiental":             "Edu. Ambiental",       # EDUCACION AMBIENTAL
    "gerencia":              "Gerencia",             # GERENCIA PROY SOFT
    "práctica":              "Practica",             # PRÁCTICA EMPRESARIAL
    "computacion":           "Computación",          # COMPUTACION MOVIL
    "proyecto de inv":       "Proyecto III",         # PROYECTO DE INV. III
    "inteligencia artificial": "IA",                 # INTELIGENCIA ARTIFICIAL
    "legislacion":           "Legislación",          # LEGISLACION INFORMATICA
}

# Orden de prioridad: se evalúa de arriba hacia abajo, la primera palabra
# clave que aparezca en el nombre de la tarea define el Tipo. Si ninguna
# coincide, se usa "Tarea" por defecto.
ASSIGNMENT_TIPO_KEYWORDS = {
    "sustentación":  "Sustentación",
    "sustentacion":  "Sustentación",
    "entrega":       "Entrega",
    "examen":        "Examen",
    "parcial":       "Parcial",
    "quiz":          "Quiz",
    "guía":          "Guía",
    "guia":          "Guía",
    "laboratorio":   "Guía",
    "tarea":         "Tarea",
}
ASSIGNMENT_TIPO_DEFAULT = "Tarea"
