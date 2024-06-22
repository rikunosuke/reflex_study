import os
from pathlib import Path

import reflex as rx
from dotenv import load_dotenv

load_dotenv()

config = rx.Config(
    app_name="reflex_study",
)

CONFIG_FILE_PATH = Path(os.getcwd()) / os.environ.get(
    "SETTINGS_FILE_PATH", ".config.json"
)
if not CONFIG_FILE_PATH.exists():
    CONFIG_FILE_PATH.touch()
