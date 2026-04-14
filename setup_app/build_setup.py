"""
Genera el ejecutable setup_wizard.exe con PyInstaller.
Ejecutar desde la raíz del proyecto:  python setup_app/build_setup.py
"""
import subprocess
import sys
import os
from pathlib import Path

BASE = Path(__file__).parent
ROOT = BASE.parent

PYINSTALLER = [sys.executable, "-m", "PyInstaller"]

args = PYINSTALLER + [
    str(BASE / "setup_wizard.py"),
    "--name=CanvasNotionSetup",
    "--onefile",                         # Un solo .exe
    "--windowed",                        # Sin consola (GUI)
    "--clean",
    "--noconfirm",
    # Metadatos de versión (reduce falsos positivos en antivirus)
    "--version-file", str(BASE / "version_info.txt"),
    # Imports ocultos que PyInstaller puede no detectar sola
    "--hidden-import=tkinter",
    "--hidden-import=tkinter.ttk",
    "--hidden-import=tkinter.messagebox",
    "--hidden-import=tkinter.scrolledtext",
    "--hidden-import=docx",
    "--hidden-import=docx.shared",
    "--hidden-import=docx.enum.text",
    "--hidden-import=docx.oxml.ns",
    "--hidden-import=docx.oxml",
    "--hidden-import=requests",
    "--hidden-import=urllib3",
    "--hidden-import=charset_normalizer",
    "--hidden-import=certifi",
    "--hidden-import=idna",
    # Directorio de salida
    "--distpath", str(ROOT / "dist"),
    "--workpath", str(ROOT / "build"),
    "--specpath", str(BASE),
]

print("Construyendo CanvasNotionSetup.exe ...")
result = subprocess.run(args, cwd=str(ROOT))
if result.returncode == 0:
    exe = ROOT / "dist" / "CanvasNotionSetup.exe"
    print(f"\n✓ Ejecutable listo: {exe}")
else:
    print("\n✗ Build fallido")
    sys.exit(1)
