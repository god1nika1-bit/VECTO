"""Генерация .md-отчёта и отправка владельцу."""

import io
from datetime import datetime

from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from config import OWNER_CHAT_ID
from questions import FINISH_TEXT, SERVICE_CODES


# Маппинг state_name → читаемое название вопроса для отчёта
SERVICE_QUESTION_LABELS: dict[str, str] = {
    "service_l1": "Тип сайта",
    "service_l2": "Реклама на сайт",
    "service_t1": "Функции бота",
    "service_t2": "Нагрузка (обращений/день)",
    "service_c1": "Площадки контента",
    "service_c2": "Тон общения",
    "service_f1": "Финмодель для кого",
    "service_f2": "Финансовые данные",
    "service_k1": "Тип текста",
}


def generate_report(data: dict, user_id: int, username: str | None) -> str:
    """Генерирует .md-отчёт по шаблону из спецификации."""
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    niche = data.get("niche", "—")
    services = data.get("services", [])
    services_str = ", ".join(SERVICE_CODES.get(s, s) for s in services)

    # Блок 1
    client_type = data.get("client_type", "—")
    client_age = data.get("client_age")
    ca_str = client_type
    if client_age:
        ca_str += f" ({client_age})"
    channels = data.get("channels", [])
    channels_str = ", ".join(channels) if channels else "—"
    pain = data.get("pain", "—")

    # Блок 2
    materials = data.get("materials", [])
    materials_str = ", ".join(materials) if materials else "—"
    style = data.get("style", "—")
    files = data.get("files", [])
    files_str = "\n".join(f"- {f}" for f in files) if files else "Нет"

    # Блок 3
    service_answers = data.get("service_answers", {})

    # Блок 4
    budget = data.get("budget", "—")
    deadline = data.get("deadline", "—")

    # Блок 5
    contact_method = data.get("contact_method", "—")
    contact_value = data.get("contact_value", "—")
    client_name = data.get("client_name", "—")

    # Deeplink
    source = data.get("source", "direct")
    preselected_total = data.get("preselected_total")
    from_calc = "Да" if source == "deeplink" else "Нет"
    if preselected_total:
        from_calc += f" (сумма: {preselected_total:,} ₽)".replace(",", " ")

    # Лог сообщений
    message_log = data.get("message_log", [])
    log_str = "\n".join(f"> {m}" for m in message_log) if message_log else "—"

    # Telegram
    tg_str = f"@{username}" if username else str(user_id)

    # Формируем .md
    report = f"""# ТЗ: {niche} — {now}

## 🔴 КЛЮЧЕВОЕ
- **Услуги:** {services_str}
- **Боль:** {pain}
- **Бюджет:** {budget}
- **Сроки:** {deadline}
- **С калькулятора:** {from_calc}
- **Контакт:** {contact_method} — {contact_value}

## 📋 БИЗНЕС
- **Ниша:** {niche}
- **ЦА:** {ca_str}
- **Каналы:** {channels_str}
- **Боль:** {pain}

## 🎯 ПРОЕКТ
- **Услуги:** {services_str}
- **Материалы:** {materials_str}
- **Файлы:** {files_str}
- **Стиль:** {style}

## 🔧 ДЕТАЛИ ПО УСЛУГАМ
"""
    if service_answers:
        for state_name, answer in service_answers.items():
            label = SERVICE_QUESTION_LABELS.get(state_name, state_name)
            report += f"- **{label}:** {answer}\n"
    else:
        report += "— нет доп. вопросов\n"

    report += f"""
## 💰 БЮДЖЕТ И СРОКИ
- **Бюджет:** {budget}
- **Сроки:** {deadline}

## 📞 КОНТАКТ
- **Имя:** {client_name}
- **Способ:** {contact_method}
- **Значение:** {contact_value}
- **Telegram:** {tg_str} / {user_id}

## 📝 ПОЛНЫЙ ЛОГ
{log_str}
"""
    return report


async def finish_survey(message: Message, state: FSMContext) -> None:
    """Завершение опроса: сообщение клиенту + отчёт владельцу."""
    data = await state.get_data()
    user = message.from_user
    user_id = user.id if user else 0
    username = user.username if user else None

    # --- Сообщение клиенту ---
    client_name = data.get("client_name", "друг")
    services_str = ", ".join(
        SERVICE_CODES.get(s, s) for s in data.get("services", [])
    )
    finish_text = FINISH_TEXT.format(
        name=client_name,
        niche=data.get("niche", "—"),
        services=services_str or "—",
        budget=data.get("budget", "—"),
        deadline=data.get("deadline", "—"),
    )
    await message.answer(finish_text)

    # --- Генерация и отправка .md-отчёта владельцу ---
    report = generate_report(data, user_id, username)

    # Краткая сводка текстом
    summary = (
        f"📋 Новая заявка!\n\n"
        f"👤 {client_name} ({('@' + username) if username else user_id})\n"
        f"🏢 {data.get('niche', '—')}\n"
        f"🎯 {services_str}\n"
        f"💰 {data.get('budget', '—')}\n"
        f"⏰ {data.get('deadline', '—')}"
    )

    # Отправляем текст + файл владельцу
    bot = message.bot
    await bot.send_message(OWNER_CHAT_ID, summary)

    # Отправляем .md как файл
    niche_short = data.get("niche", "заявка")[:30]
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"ТЗ_{niche_short}_{date_str}.md"

    file_bytes = report.encode("utf-8")
    input_file = BufferedInputFile(file_bytes, filename=filename)
    await bot.send_document(OWNER_CHAT_ID, input_file)

    # Очищаем состояние
    await state.clear()
