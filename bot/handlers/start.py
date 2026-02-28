"""Хэндлер /start — точка входа с поддержкой deeplink."""

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from questions import (
    DEEPLINK_CONFIRM,
    DEEPLINK_CONFIRM_BUTTONS,
    SERVICE_CODES,
    WELCOME,
    WELCOME_BUTTONS,
)
from states import SurveyStates
from utils.deeplink import parse_deeplink

router = Router(name="start")


def _make_keyboard(buttons: list[tuple[str, str]], row_width: int = 2) -> InlineKeyboardMarkup:
    """Создаёт InlineKeyboardMarkup из списка (текст, callback_data)."""
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for text, data in buttons:
        row.append(InlineKeyboardButton(text=text, callback_data=data))
        if len(row) >= row_width:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _get_client_name(message: Message) -> str:
    """Имя клиента из профиля Telegram, fallback — «друг»."""
    if message.from_user and message.from_user.first_name:
        return message.from_user.first_name
    return "друг"


# === /start ===

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    """Обработка /start с опциональным deeplink payload."""
    # Извлекаем payload (до проверки состояния — понадобится при restart)
    payload = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""

    # Проверяем: есть ли незавершённый опрос
    current_state = await state.get_state()
    if current_state is not None:
        # Сохраняем payload для использования после решения клиента
        await state.update_data(_pending_payload=payload)
        kb = _make_keyboard(
            [("Начать заново", "restart_new"), ("Продолжить", "restart_continue")],
            row_width=2,
        )
        await message.answer(
            "У вас есть незавершённый опрос. Что хотите сделать?",
            reply_markup=kb,
        )
        await state.set_state(SurveyStates.restart_confirm)
        return

    # Нет активного состояния — обычный старт
    client_name = _get_client_name(message)
    await _do_start(message, state, payload, client_name)


@router.callback_query(SurveyStates.restart_confirm, F.data == "restart_new")
async def on_restart_new(callback: CallbackQuery, state: FSMContext) -> None:
    """Клиент выбрал «Начать заново»."""
    data = await state.get_data()
    payload = data.get("_pending_payload", "")
    await state.clear()
    await callback.answer()

    client_name = _get_client_name(callback.message)
    # Если имя недоступно из callback.message — берём из callback.from_user
    if client_name == "друг" and callback.from_user and callback.from_user.first_name:
        client_name = callback.from_user.first_name

    await _do_start(callback.message, state, payload, client_name)


@router.callback_query(SurveyStates.restart_confirm, F.data == "restart_continue")
async def on_restart_continue(callback: CallbackQuery, state: FSMContext) -> None:
    """Клиент выбрал «Продолжить» — убираем _pending_payload, возвращаемся."""
    data = await state.get_data()
    data.pop("_pending_payload", None)
    await state.set_data(data)
    await callback.answer("Продолжаем! Ответьте на последний вопрос выше ⬆️")


# === Логика старта ===

async def _do_start(message: Message, state: FSMContext, payload: str, client_name: str) -> None:
    """Запускает опрос — deeplink или прямой вход."""
    if payload:
        deeplink = parse_deeplink(payload)
        services = deeplink["services"]
        total = deeplink["total"]

        if not services:
            await _send_welcome(message, state, client_name)
            return

        # Сохраняем данные из deeplink в FSM
        await state.update_data(
            source="deeplink",
            client_name=client_name,
            preselected_services=services,
            preselected_total=total,
            services=services,
            message_log=[],
            files=[],
        )

        # Формируем список выбранных услуг
        services_list = "\n".join(
            f"✅ {SERVICE_CODES.get(s, s)}" for s in services
        )
        total_str = f"{total:,} ₽".replace(",", " ") if total else "не указано"

        text = DEEPLINK_CONFIRM.format(
            services_list=services_list,
            total=total_str,
        )
        kb = _make_keyboard(DEEPLINK_CONFIRM_BUTTONS, row_width=2)

        await message.answer(f"{client_name}, приветствую! 👋\n\n" + text[len("Привет! 👋\n\n"):], reply_markup=kb)
        await state.set_state(SurveyStates.confirm_deeplink)
    else:
        await _send_welcome(message, state, client_name)


async def _send_welcome(message: Message, state: FSMContext, client_name: str) -> None:
    """Отправляет приветствие для прямого входа (мультивыбор услуг)."""
    await state.update_data(
        source="direct",
        client_name=client_name,
        preselected_services=[],
        preselected_total=None,
        services=[],
        selected_welcome=[],
        message_log=[],
        files=[],
    )

    welcome_text = WELCOME.replace("Привет! 👋", f"{client_name}, привет! 👋")

    # Мультивыбор: сервисные кнопки с ⬜ + «Пока не знаю» + «Готово»
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for text, data in WELCOME_BUTTONS:
        if data == "svc_unknown":
            continue
        row.append(InlineKeyboardButton(text=f"⬜ {text}", callback_data=data))
        if len(row) >= 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(
        text="🤔 Пока не знаю — помогите разобраться", callback_data="svc_unknown",
    )])
    rows.append([InlineKeyboardButton(text="Готово ✓", callback_data="multi_done")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)

    await message.answer(welcome_text, reply_markup=kb)
    await state.set_state(SurveyStates.choose_services)
