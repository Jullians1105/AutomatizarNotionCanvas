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
    "soft seg":              "Desarrollo del software seguro",  # DESARROLLO SOFT SEG.
    "estocastico":           "Modelo Estocastico",             # MODELAMIENTO ESTOCASTICO
    "interfaces":            "Diseño de interfaces",           # DISEÑO DE INTERFACES
    "nuevas tec":            "Nuevas tecnologias",             # NUEVAS TEC DESARR
    "proyecto de inv":       "Proyecto 2",                     # PROYECTO DE INV. II
    "ingenieria web":        "Web 2",                          # INGENIERIA WEB II
    "sistemas expertos":     "Sistemas Expertos",              # SISTEMAS EXPERTOS
    "aplicabilidad":         "Aplicabilidad de IA",            # APLICABILIDAD DE LA INTEL
}
