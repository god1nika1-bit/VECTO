"""Конфигурация бота — загрузка переменных окружения."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env из папки bot/
load_dotenv(Path(__file__).parent / ".env")

TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
OWNER_CHAT_ID: int = int(os.environ["OWNER_CHAT_ID"])
