"""Генерация .md + .pdf отчёта, пересылка файлов владельцу."""

import logging
import platform
from datetime import datetime
from pathlib import Path

from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from config import OWNER_CHAT_ID
from questions import FINISH_TEXT, SERVICE_CODES

logger = logging.getLogger(__name__)

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


def _build_report_sections(data: dict, user_id: int, username: str | None) -> dict:
    """Собирает все секции отчёта в словарь для переиспользования (.md и .pdf)."""
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
    files_count = len(files)

    # Блок 3
    service_answers = data.get("service_answers", {})

    # Блок 4
    budget = data.get("budget", "—")
    deadline = data.get("deadline", "—")

    # Свободное ТЗ
    free_tz = data.get("free_tz", "")

    # Блок 5
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

    return {
        "now": now,
        "niche": niche,
        "services_str": services_str,
        "ca_str": ca_str,
        "channels_str": channels_str,
        "pain": pain,
        "materials_str": materials_str,
        "style": style,
        "files_count": files_count,
        "service_answers": service_answers,
        "budget": budget,
        "deadline": deadline,
        "free_tz": free_tz,
        "client_name": client_name,
        "from_calc": from_calc,
        "log_str": log_str,
        "tg_str": tg_str,
        "user_id": user_id,
    }


def generate_md_report(data: dict, user_id: int, username: str | None) -> str:
    """Генерирует .md-отчёт без дублирования секций."""
    s = _build_report_sections(data, user_id, username)
    service_answers = s["service_answers"]

    report = f"""# ТЗ: {s['niche']} — {s['now']}

> {s['services_str']} | {s['budget']} | {s['deadline']} | {s['tg_str']}

## КЛИЕНТ
- **Ниша:** {s['niche']}
- **ЦА:** {s['ca_str']}
- **Каналы:** {s['channels_str']}
- **Боль:** {s['pain']}
- **С калькулятора:** {s['from_calc']}

## ПРОЕКТ
- **Материалы:** {s['materials_str']}
- **Файлы:** {s['files_count']} шт. (пересланы отдельно)
- **Стиль:** {s['style']}

## ДЕТАЛИ ПО УСЛУГАМ
"""
    if service_answers:
        for state_name, answer in service_answers.items():
            label = SERVICE_QUESTION_LABELS.get(state_name, state_name)
            report += f"- **{label}:** {answer}\n"
    else:
        report += "— нет доп. вопросов\n"

    report += f"""
## БЮДЖЕТ И СРОКИ
- **Бюджет:** {s['budget']}
- **Сроки:** {s['deadline']}
"""

    # Свободное ТЗ
    free_tz = s["free_tz"]
    if free_tz:
        report += f"""
## СВОБОДНОЕ ТЗ КЛИЕНТА
{free_tz}
"""

    report += f"""
## КОНТАКТ
- **Имя:** {s['client_name']}
- **Telegram:** {s['tg_str']} / {s['user_id']}

## ЛОГ СООБЩЕНИЙ
{s['log_str']}
"""
    return report


def _find_cyrillic_font() -> tuple[str, str] | None:
    """Ищет TTF-шрифт с поддержкой кириллицы. Возвращает (regular, bold) или None."""
    candidates = []

    if platform.system() == "Windows":
        fonts_dir = Path("C:/Windows/Fonts")
        candidates = [
            (fonts_dir / "arial.ttf", fonts_dir / "arialbd.ttf"),
            (fonts_dir / "calibri.ttf", fonts_dir / "calibrib.ttf"),
            (fonts_dir / "tahoma.ttf", fonts_dir / "tahomabd.ttf"),
        ]
    else:
        # Linux / Docker
        candidates = [
            (
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"),
            ),
            (
                Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
                Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
            ),
        ]

    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            return str(regular), str(bold)
    return None


def generate_pdf_report(data: dict, user_id: int, username: str | None) -> bytes:
    """Генерирует PDF-отчёт с кириллицей. Возвращает байты PDF-файла."""
    from fpdf import FPDF

    s = _build_report_sections(data, user_id, username)
    service_answers = s["service_answers"]

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Ищем шрифт с кириллицей
    font_paths = _find_cyrillic_font()
    if font_paths:
        regular_path, bold_path = font_paths
        pdf.add_font("CyrFont", "", regular_path, uni=True)
        pdf.add_font("CyrFont", "B", bold_path, uni=True)
        font = "CyrFont"
    else:
        raise RuntimeError("Не найден TTF-шрифт с поддержкой кириллицы")

    def heading(text: str) -> None:
        pdf.set_font(font, "B", 13)
        pdf.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    def field(label: str, value: str) -> None:
        pdf.set_font(font, "B", 10)
        pdf.cell(55, 7, f"{label}:", new_x="END")
        pdf.set_font(font, "", 10)
        pdf.multi_cell(0, 7, value)

    def paragraph(text: str) -> None:
        pdf.set_font(font, "", 10)
        pdf.multi_cell(0, 6, text)
        pdf.ln(2)

    # Заголовок
    pdf.set_font(font, "B", 16)
    pdf.cell(0, 12, f"ТЗ: {s['niche']}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font, "", 10)
    pdf.cell(0, 7, s["now"], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # Краткая строка
    pdf.set_font(font, "", 9)
    pdf.cell(0, 6,
             f"{s['services_str']}  |  {s['budget']}  |  {s['deadline']}  |  {s['tg_str']}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Клиент
    heading("КЛИЕНТ")
    field("Ниша", s["niche"])
    field("ЦА", s["ca_str"])
    field("Каналы", s["channels_str"])
    field("Боль", s["pain"])
    field("С калькулятора", s["from_calc"])
    pdf.ln(4)

    # Проект
    heading("ПРОЕКТ")
    field("Материалы", s["materials_str"])
    field("Файлы", f"{s['files_count']} шт. (пересланы отдельно)")
    field("Стиль", s["style"])
    pdf.ln(4)

    # Детали по услугам
    heading("ДЕТАЛИ ПО УСЛУГАМ")
    if service_answers:
        for state_name, answer in service_answers.items():
            label = SERVICE_QUESTION_LABELS.get(state_name, state_name)
            field(label, answer)
    else:
        paragraph("Нет доп. вопросов")
    pdf.ln(4)

    # Бюджет и сроки
    heading("БЮДЖЕТ И СРОКИ")
    field("Бюджет", s["budget"])
    field("Сроки", s["deadline"])
    pdf.ln(4)

    # Свободное ТЗ
    free_tz = s["free_tz"]
    if free_tz:
        heading("СВОБОДНОЕ ТЗ КЛИЕНТА")
        paragraph(free_tz)
        pdf.ln(4)

    # Контакт
    heading("КОНТАКТ")
    field("Имя", s["client_name"])
    field("Telegram", f"{s['tg_str']} / {s['user_id']}")

    return pdf.output()


async def _forward_client_files(bot, data: dict, chat_from_id: int) -> None:
    """Пересылает файлы клиента (фото, документы) владельцу по file_id."""
    files = data.get("files", [])
    if not files:
        return

    await bot.send_message(OWNER_CHAT_ID, f"📎 Файлы клиента ({len(files)} шт.):")

    for file_info in files:
        if not isinstance(file_info, dict):
            continue
        try:
            if file_info["type"] == "photo":
                await bot.send_photo(OWNER_CHAT_ID, file_info["file_id"])
            elif file_info["type"] == "document":
                await bot.send_document(OWNER_CHAT_ID, file_info["file_id"])
        except Exception as e:
            logger.warning("Не удалось переслать файл: %s", e)


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

    # --- Генерация и отправка отчётов владельцу ---
    bot = message.bot

    # Краткая сводка текстом
    summary = (
        f"📋 Новая заявка!\n\n"
        f"👤 {client_name} ({('@' + username) if username else user_id})\n"
        f"🏢 {data.get('niche', '—')}\n"
        f"🎯 {services_str}\n"
        f"💰 {data.get('budget', '—')}\n"
        f"⏰ {data.get('deadline', '—')}"
    )
    await bot.send_message(OWNER_CHAT_ID, summary)

    # Имя файла
    niche_short = data.get("niche", "заявка")[:30]
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    base_name = f"ТЗ_{niche_short}_{date_str}"

    # .md отчёт
    md_report = generate_md_report(data, user_id, username)
    md_bytes = md_report.encode("utf-8")
    md_file = BufferedInputFile(md_bytes, filename=f"{base_name}.md")
    await bot.send_document(OWNER_CHAT_ID, md_file)

    # .pdf отчёт
    try:
        pdf_bytes = generate_pdf_report(data, user_id, username)
        pdf_file = BufferedInputFile(pdf_bytes, filename=f"{base_name}.pdf")
        await bot.send_document(OWNER_CHAT_ID, pdf_file)
    except Exception as e:
        logger.error("Ошибка генерации PDF: %s", e)
        await bot.send_message(OWNER_CHAT_ID, f"⚠️ Не удалось сгенерировать PDF: {e}")

    # Пересылаем файлы клиента
    await _forward_client_files(bot, data, message.chat.id)

    # Очищаем состояние
    await state.clear()
