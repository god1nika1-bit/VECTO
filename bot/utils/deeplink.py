"""Парсинг deeplink-параметров из калькулятора сайта.

Формат: ?start=landing_bot_40000
- Коды услуг: landing, bot, content, finmodel, copy, consult
- Последний элемент (если число) = сумма из калькулятора
"""

# Импорт от корня bot/ — работает т.к. точка входа bot.py
# добавляет bot/ в sys.path
from questions import SERVICE_CODES

VALID_CODES = set(SERVICE_CODES.keys())


def parse_deeplink(payload: str) -> dict[str, list[str] | int | None]:
    """Парсит payload из /start и возвращает услуги + сумму.

    Возвращает:
        {
            "services": ["landing", "bot"],
            "total": 40000  # или None если не указана
        }
    """
    if not payload:
        return {"services": [], "total": None}

    parts = payload.strip().split("_")
    total: int | None = None
    services: list[str] = []

    # Последний элемент может быть суммой
    if parts and parts[-1].isdigit():
        total = int(parts[-1])
        parts = parts[:-1]

    # Остальные — коды услуг
    for part in parts:
        if part in VALID_CODES:
            services.append(part)

    return {"services": services, "total": total}
