"""Основной flow опроса — блоки 1-5, мультивыбор, динамические вопросы."""

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from questions import (
    B1_NICHE_BUTTONS,
    B1_NICHE_MAP,
    B1_NICHE_TEXT,
    B2_CLIENT_AGE_BUTTONS,
    B2_CLIENT_AGE_MAP,
    B2_CLIENT_AGE_TEXT,
    B2_CLIENT_TYPE_BUTTONS,
    B2_CLIENT_TYPE_MAP,
    B2_CLIENT_TYPE_TEXT,
    B3_CHANNELS_BUTTONS,
    B3_CHANNELS_MAP,
    B3_CHANNELS_TEXT,
    B4_PAIN_BUTTONS,
    B4_PAIN_MAP,
    B4_PAIN_TEXT,
    BUDGET_BUTTONS,
    BUDGET_MAP,
    BUDGET_TEXT,
    CONFIRM_SUMMARY_BUTTONS,
    CONFIRM_SUMMARY_TEXT,
    CONTACT_INPUT_EMAIL_TEXT,
    CONTACT_INPUT_PHONE_TEXT,
    CONTACT_METHOD_BUTTONS,
    CONTACT_METHOD_MAP,
    CONTACT_METHOD_TEXT,
    CONTACT_NAME_TEXT,
    DEADLINE_BUTTONS,
    DEADLINE_MAP,
    DEADLINE_TEXT,
    MULTISELECT_DONE,
    P1_SERVICES_BUTTONS,
    P2_MATERIALS_BUTTONS,
    P2_MATERIALS_MAP,
    P2_MATERIALS_TEXT,
    P3_STYLE_BUTTONS,
    P3_STYLE_MAP,
    P3_STYLE_TEXT,
    SERVICE_CODES,
    SERVICE_QUESTIONS,
    WAITING_FILES_DONE,
    WELCOME_BUTTONS,
    WAITING_FILES_SKIP,
    WAITING_FILES_TEXT,
)
from states import SurveyStates

router = Router(name="survey")


# ==================== Утилиты ====================

def _kb(buttons: list[tuple[str, str]], row_width: int = 2) -> InlineKeyboardMarkup:
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


def _multiselect_kb(
    buttons: list[tuple[str, str]],
    selected: set[str],
    row_width: int = 2,
) -> InlineKeyboardMarkup:
    """Клавиатура мультивыбора с галочками ✅/⬜ + кнопка «Готово»."""
    toggled = []
    for text, data in buttons:
        prefix = "✅ " if data in selected else "⬜ "
        toggled.append((prefix + text.lstrip("✅⬜ "), data))
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for text, data in toggled:
        row.append(InlineKeyboardButton(text=text, callback_data=data))
        if len(row) >= row_width:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    # Кнопка «Готово»
    rows.append([InlineKeyboardButton(text=MULTISELECT_DONE[0], callback_data=MULTISELECT_DONE[1])])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _log_message(state: FSMContext, text: str) -> None:
    """Дописывает текстовое сообщение клиента в лог."""
    data = await state.get_data()
    log = data.get("message_log", [])
    log.append(text)
    await state.update_data(message_log=log)


async def _answer(callback: CallbackQuery, text: str, reply_markup=None) -> None:
    """Отвечает клиенту — редактирует или шлёт новое сообщение."""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        await callback.message.answer(text, reply_markup=reply_markup)


# ==================== ВХОД: подтверждение deeplink ====================

@router.callback_query(SurveyStates.confirm_deeplink, F.data == "deeplink_confirm")
async def on_deeplink_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    """Клиент подтвердил выбор с калькулятора → блок 1."""
    await callback.answer()
    await _ask_b1_niche(callback, state)


@router.callback_query(SurveyStates.confirm_deeplink, F.data == "deeplink_change")
async def on_deeplink_change(callback: CallbackQuery, state: FSMContext) -> None:
    """Клиент хочет изменить выбор → выбор услуг заново."""
    await callback.answer()
    await state.update_data(services=[], preselected_services=[], preselected_total=None)
    await _answer(callback, "Что из этого вам нужно? Можно выбрать несколько:",
                  reply_markup=_multiselect_kb(P1_SERVICES_BUTTONS, set(), row_width=2))
    await state.set_state(SurveyStates.p1_services)


# ==================== ВХОД: выбор услуг (прямой вход, мультивыбор) ====================

def _welcome_multiselect_kb(selected: set[str]) -> InlineKeyboardMarkup:
    """Клавиатура мультивыбора для приветствия (прямой вход)."""
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for text, data in WELCOME_BUTTONS:
        if data == "svc_unknown":
            continue
        prefix = "✅" if data in selected else "⬜"
        row.append(InlineKeyboardButton(text=f"{prefix} {text}", callback_data=data))
        if len(row) >= 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(
        text="🤔 Пока не знаю — помогите разобраться", callback_data="svc_unknown",
    )])
    rows.append([InlineKeyboardButton(text=MULTISELECT_DONE[0], callback_data=MULTISELECT_DONE[1])])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(SurveyStates.choose_services, F.data == "svc_unknown")
async def on_choose_unknown(callback: CallbackQuery, state: FSMContext) -> None:
    """«Пока не знаю» — консультация, переходим к блоку 1."""
    await callback.answer()
    await state.update_data(services=["consult"])
    await _ask_b1_niche(callback, state)


@router.callback_query(SurveyStates.choose_services, F.data == "multi_done")
async def on_choose_done(callback: CallbackQuery, state: FSMContext) -> None:
    """Завершение мультивыбора услуг при прямом входе."""
    await callback.answer()
    data = await state.get_data()
    selected = data.get("selected_welcome", [])
    services = [s.replace("svc_", "") for s in selected]
    if not services:
        services = ["consult"]
    await state.update_data(services=services)
    await _ask_b1_niche(callback, state)


@router.callback_query(SurveyStates.choose_services, F.data.startswith("svc_"))
async def on_choose_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    """Тогл услуги при прямом входе (мультивыбор)."""
    data = await state.get_data()
    selected = set(data.get("selected_welcome", []))
    if callback.data in selected:
        selected.discard(callback.data)
    else:
        selected.add(callback.data)
    await state.update_data(selected_welcome=list(selected))
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(
            reply_markup=_welcome_multiselect_kb(selected)
        )
    except Exception:
        pass


# ==================== БЛОК 1: О БИЗНЕСЕ ====================

async def _ask_b1_niche(callback: CallbackQuery, state: FSMContext) -> None:
    """Вопрос B1: ниша бизнеса."""
    await _answer(callback, B1_NICHE_TEXT, reply_markup=_kb(B1_NICHE_BUTTONS, row_width=2))
    await state.set_state(SurveyStates.b1_niche)


@router.callback_query(SurveyStates.b1_niche, F.data.startswith("niche_"))
async def on_b1_niche(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.data == "niche_custom":
        await _answer(callback, "Напишите, чем занимается ваш бизнес:")
        await state.set_state(SurveyStates.b1_niche_custom)
        return
    niche = B1_NICHE_MAP.get(callback.data, callback.data)
    await state.update_data(niche=niche)
    await _ask_b2_client_type(callback, state)


@router.message(SurveyStates.b1_niche_custom)
async def on_b1_niche_custom(message: Message, state: FSMContext) -> None:
    await _log_message(state, message.text)
    await state.update_data(niche=message.text)
    # Отправляем следующий вопрос как новое сообщение
    await message.answer(B2_CLIENT_TYPE_TEXT, reply_markup=_kb(B2_CLIENT_TYPE_BUTTONS, row_width=3))
    await state.set_state(SurveyStates.b2_client_type)


# --- B2: Целевой клиент ---

async def _ask_b2_client_type(callback: CallbackQuery, state: FSMContext) -> None:
    await _answer(callback, B2_CLIENT_TYPE_TEXT, reply_markup=_kb(B2_CLIENT_TYPE_BUTTONS, row_width=3))
    await state.set_state(SurveyStates.b2_client_type)


@router.callback_query(SurveyStates.b2_client_type, F.data.startswith("client_"))
async def on_b2_client_type(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    client_type = B2_CLIENT_TYPE_MAP.get(callback.data, callback.data)
    await state.update_data(client_type=client_type)

    # Если B2C или оба — доп. вопрос про возраст
    if callback.data in ("client_b2c", "client_both"):
        await _answer(callback, B2_CLIENT_AGE_TEXT, reply_markup=_kb(B2_CLIENT_AGE_BUTTONS, row_width=2))
        await state.set_state(SurveyStates.b2_client_age)
    else:
        await state.update_data(client_age=None)
        await _ask_b3_channels(callback, state)


@router.callback_query(SurveyStates.b2_client_age, F.data.startswith("age_"))
async def on_b2_client_age(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.data == "age_custom":
        await _answer(callback, "Опишите вашу аудиторию подробнее:")
        await state.set_state(SurveyStates.b2_client_age_custom)
        return
    age = B2_CLIENT_AGE_MAP.get(callback.data, callback.data)
    await state.update_data(client_age=age)
    await _ask_b3_channels(callback, state)


@router.message(SurveyStates.b2_client_age_custom)
async def on_b2_client_age_custom(message: Message, state: FSMContext) -> None:
    await _log_message(state, message.text)
    await state.update_data(client_age=message.text)
    await message.answer(B3_CHANNELS_TEXT,
                         reply_markup=_multiselect_kb(B3_CHANNELS_BUTTONS, set(), row_width=2))
    await state.set_state(SurveyStates.b3_channels)


# --- B3: Каналы привлечения (мультивыбор) ---

async def _ask_b3_channels(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(selected_channels=[], channels_custom=None)
    await _answer(callback, B3_CHANNELS_TEXT,
                  reply_markup=_multiselect_kb(B3_CHANNELS_BUTTONS, set(), row_width=2))
    await state.set_state(SurveyStates.b3_channels)


@router.callback_query(SurveyStates.b3_channels, F.data == "multi_done")
async def on_b3_channels_done(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    selected = data.get("selected_channels", [])
    channels = [B3_CHANNELS_MAP.get(s, s) for s in selected]
    await state.update_data(channels=channels)
    await _ask_b4_pain(callback, state)


@router.callback_query(SurveyStates.b3_channels, F.data.startswith("ch_"))
async def on_b3_channel_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    """Тогл канала в мультивыборе."""
    data = await state.get_data()
    selected = set(data.get("selected_channels", []))

    if callback.data == "ch_none":
        # «Пока нет клиентов» — сброс и завершение
        await callback.answer()
        await state.update_data(selected_channels=["ch_none"], channels=["Пока нет клиентов"])
        await _ask_b4_pain(callback, state)
        return

    if callback.data == "ch_custom":
        await callback.answer()
        await state.update_data(selected_channels=list(selected))
        # Запросить текст и после вернуться
        await _answer(callback, "Напишите, откуда приходят клиенты:")
        await state.set_state(SurveyStates.b3_channels)
        # Используем флаг чтобы отличить ввод текста от callback
        await state.update_data(_awaiting_channel_text=True)
        return

    # Тогл
    if callback.data in selected:
        selected.discard(callback.data)
    else:
        selected.discard("ch_none")  # убираем «нет клиентов» если выбрал канал
        selected.add(callback.data)

    await state.update_data(selected_channels=list(selected))
    await callback.answer()

    # Обновляем клавиатуру
    try:
        await callback.message.edit_reply_markup(
            reply_markup=_multiselect_kb(B3_CHANNELS_BUTTONS, selected, row_width=2)
        )
    except Exception:
        pass


@router.message(SurveyStates.b3_channels)
async def on_b3_channel_text(message: Message, state: FSMContext) -> None:
    """Текстовый ввод для 'Другое' в каналах."""
    data = await state.get_data()
    if not data.get("_awaiting_channel_text"):
        return
    await _log_message(state, message.text)
    selected = data.get("selected_channels", [])
    channels = [B3_CHANNELS_MAP.get(s, s) for s in selected]
    channels.append(message.text)
    await state.update_data(
        channels=channels,
        _awaiting_channel_text=False,
    )
    await _ask_b4_pain_msg(message, state)


# --- B4: Главная боль ---

async def _ask_b4_pain(callback: CallbackQuery, state: FSMContext) -> None:
    await _answer(callback, B4_PAIN_TEXT, reply_markup=_kb(B4_PAIN_BUTTONS, row_width=1))
    await state.set_state(SurveyStates.b4_pain)


async def _ask_b4_pain_msg(message: Message, state: FSMContext) -> None:
    """Версия для message (после текстового ввода)."""
    await message.answer(B4_PAIN_TEXT, reply_markup=_kb(B4_PAIN_BUTTONS, row_width=1))
    await state.set_state(SurveyStates.b4_pain)


@router.callback_query(SurveyStates.b4_pain, F.data.startswith("pain_"))
async def on_b4_pain(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.data == "pain_custom":
        await _answer(callback, "Опишите вашу проблему:")
        await state.set_state(SurveyStates.b4_pain_custom)
        return
    pain = B4_PAIN_MAP.get(callback.data, callback.data)
    await state.update_data(pain=pain)
    await _after_block1(callback, state)


@router.message(SurveyStates.b4_pain_custom)
async def on_b4_pain_custom(message: Message, state: FSMContext) -> None:
    await _log_message(state, message.text)
    await state.update_data(pain=message.text)
    await _after_block1_msg(message, state)


# ==================== БЛОК 2: О ПРОЕКТЕ ====================

async def _after_block1(callback: CallbackQuery, state: FSMContext) -> None:
    """После блока 1 — переходим к блоку 2 (или к сводке если редактирование)."""
    data = await state.get_data()
    # Если редактируем блок «Бизнес» — возвращаемся к сводке
    if data.get("_editing") == "business":
        await state.update_data(_editing=None)
        await _show_summary(callback, state)
        return
    # Если услуги уже определены (deeplink/вход) — пропускаем P1
    if data.get("services"):
        await _ask_p2_materials(callback, state)
    else:
        await _answer(callback, "Что из этого вам нужно? Можно выбрать несколько:",
                      reply_markup=_multiselect_kb(P1_SERVICES_BUTTONS, set(), row_width=2))
        await state.update_data(selected_p1=[])
        await state.set_state(SurveyStates.p1_services)


async def _after_block1_msg(message: Message, state: FSMContext) -> None:
    """После блока 1 (из текстового ввода)."""
    data = await state.get_data()
    if data.get("_editing") == "business":
        await state.update_data(_editing=None)
        # Для message-контекста нужно отправить сводку как новое сообщение
        await _show_summary_msg(message, state)
        return
    if data.get("services"):
        await message.answer(P2_MATERIALS_TEXT,
                             reply_markup=_multiselect_kb(P2_MATERIALS_BUTTONS, set(), row_width=2))
        await state.update_data(selected_materials=[])
        await state.set_state(SurveyStates.p2_materials)
    else:
        await message.answer("Что из этого вам нужно? Можно выбрать несколько:",
                             reply_markup=_multiselect_kb(P1_SERVICES_BUTTONS, set(), row_width=2))
        await state.update_data(selected_p1=[])
        await state.set_state(SurveyStates.p1_services)


# --- P1: Выбор услуг (мультивыбор, если не определены) ---

@router.callback_query(SurveyStates.p1_services, F.data == "multi_done")
async def on_p1_done(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    selected = data.get("selected_p1", [])
    services = [s.replace("svc_", "") for s in selected]
    if not services:
        services = ["consult"]
    await state.update_data(services=services)
    # Если редактируем услуги — возвращаемся к сводке
    if data.get("_editing") == "services":
        await state.update_data(_editing=None)
        await _show_summary(callback, state)
        return
    await _ask_p2_materials(callback, state)


@router.callback_query(SurveyStates.p1_services, F.data.startswith("svc_"))
async def on_p1_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected = set(data.get("selected_p1", []))
    if callback.data in selected:
        selected.discard(callback.data)
    else:
        selected.add(callback.data)
    await state.update_data(selected_p1=list(selected))
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(
            reply_markup=_multiselect_kb(P1_SERVICES_BUTTONS, selected, row_width=2)
        )
    except Exception:
        pass


# --- P2: Материалы (мультивыбор) ---

async def _ask_p2_materials(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(selected_materials=[])
    await _answer(callback, P2_MATERIALS_TEXT,
                  reply_markup=_multiselect_kb(P2_MATERIALS_BUTTONS, set(), row_width=2))
    await state.set_state(SurveyStates.p2_materials)


@router.callback_query(SurveyStates.p2_materials, F.data == "multi_done")
async def on_p2_done(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    data = await state.get_data()
    selected = data.get("selected_materials", [])
    materials = [P2_MATERIALS_MAP.get(s, s) for s in selected]
    await state.update_data(materials=materials)

    # Если есть материалы (не «ничего нет») → предложить скинуть файлы
    has_materials = selected and "mat_none" not in selected
    if has_materials:
        kb = _kb(
            [WAITING_FILES_SKIP, WAITING_FILES_DONE],
            row_width=2,
        )
        await _answer(callback, WAITING_FILES_TEXT, reply_markup=kb)
        await state.set_state(SurveyStates.waiting_files)
    else:
        await _ask_p3_style(callback, state)


@router.callback_query(SurveyStates.p2_materials, F.data.startswith("mat_"))
async def on_p2_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected = set(data.get("selected_materials", []))

    if callback.data == "mat_none":
        # «Ничего нет» — сброс + завершение мультивыбора
        await callback.answer()
        await state.update_data(
            selected_materials=["mat_none"],
            materials=["Ничего нет — с нуля"],
        )
        await _ask_p3_style(callback, state)
        return

    if callback.data in selected:
        selected.discard(callback.data)
    else:
        selected.discard("mat_none")
        selected.add(callback.data)
    await state.update_data(selected_materials=list(selected))
    await callback.answer()
    try:
        await callback.message.edit_reply_markup(
            reply_markup=_multiselect_kb(P2_MATERIALS_BUTTONS, selected, row_width=2)
        )
    except Exception:
        pass


# --- Ожидание файлов ---

@router.callback_query(SurveyStates.waiting_files, F.data.in_({"files_skip", "files_done"}))
async def on_files_done(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await _ask_p3_style(callback, state)


@router.message(SurveyStates.waiting_files)
async def on_file_received(message: Message, state: FSMContext) -> None:
    """Приём файлов/фото от клиента."""
    data = await state.get_data()
    files = data.get("files", [])

    file_info = None
    if message.document:
        file_info = f"📄 {message.document.file_name} ({message.document.file_id})"
    elif message.photo:
        # Берём фото в максимальном разрешении
        photo = message.photo[-1]
        file_info = f"🖼 Фото ({photo.file_id})"

    if file_info:
        files.append(file_info)
        await state.update_data(files=files)
        await message.answer(f"Принял! ({len(files)} файл(ов)). Ещё? Или нажмите кнопку выше.")
    elif message.text:
        await _log_message(state, message.text)
        await message.answer("Принял! Ещё файлы? Или нажмите кнопку выше.")


# --- P3: Стиль/референсы ---

async def _ask_p3_style(callback: CallbackQuery, state: FSMContext) -> None:
    await _answer(callback, P3_STYLE_TEXT, reply_markup=_kb(P3_STYLE_BUTTONS, row_width=2))
    await state.set_state(SurveyStates.p3_style)


@router.callback_query(SurveyStates.p3_style, F.data.startswith("style_"))
async def on_p3_style(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    style = P3_STYLE_MAP.get(callback.data, callback.data)
    await state.update_data(style=style)
    await _start_block3(callback, state)


@router.message(SurveyStates.p3_style)
async def on_p3_style_text(message: Message, state: FSMContext) -> None:
    """Клиент прислал ссылку на референс."""
    await _log_message(state, message.text)
    await state.update_data(style=f"Референс: {message.text}")
    await _start_block3_msg(message, state)


# ==================== БЛОК 3: ПО УСЛУГАМ ====================

async def _build_service_queue(state: FSMContext) -> list[tuple[str, str, list, dict]]:
    """Формирует очередь вопросов по выбранным услугам."""
    data = await state.get_data()
    services = data.get("services", [])
    queue = []
    for svc in services:
        if svc in SERVICE_QUESTIONS:
            queue.extend(SERVICE_QUESTIONS[svc])
    return queue


async def _start_block3(callback: CallbackQuery, state: FSMContext) -> None:
    """Запускает блок 3 — вопросы по услугам."""
    queue = await _build_service_queue(state)
    await state.update_data(service_queue=queue, service_answers={})
    await _next_service_question(callback, state)


async def _start_block3_msg(message: Message, state: FSMContext) -> None:
    """Запускает блок 3 из текстового контекста."""
    queue = await _build_service_queue(state)
    await state.update_data(service_queue=queue, service_answers={})
    await _next_service_question_msg(message, state)


async def _next_service_question(callback: CallbackQuery, state: FSMContext) -> None:
    """Показывает следующий вопрос из очереди или переходит к блоку 4."""
    data = await state.get_data()
    queue = data.get("service_queue", [])

    if not queue:
        await _ask_budget(callback, state)
        return

    state_name, text, buttons, _ = queue[0]
    await _answer(callback, text, reply_markup=_kb(buttons, row_width=2))

    # Устанавливаем соответствующее состояние
    target_state = getattr(SurveyStates, state_name, None)
    if target_state:
        await state.set_state(target_state)


async def _next_service_question_msg(message: Message, state: FSMContext) -> None:
    """Показывает следующий вопрос из message-контекста."""
    data = await state.get_data()
    queue = data.get("service_queue", [])

    if not queue:
        await message.answer(BUDGET_TEXT, reply_markup=_kb(BUDGET_BUTTONS, row_width=2))
        await state.set_state(SurveyStates.budget)
        return

    state_name, text, buttons, _ = queue[0]
    await message.answer(text, reply_markup=_kb(buttons, row_width=2))

    target_state = getattr(SurveyStates, state_name, None)
    if target_state:
        await state.set_state(target_state)


# --- Универсальный хэндлер для вопросов по услугам ---

SERVICE_STATES = [
    SurveyStates.service_l1,
    SurveyStates.service_l2,
    SurveyStates.service_t1,
    SurveyStates.service_t2,
    SurveyStates.service_c1,
    SurveyStates.service_c2,
    SurveyStates.service_f1,
    SurveyStates.service_f2,
    SurveyStates.service_k1,
]


@router.callback_query(StateFilter(*SERVICE_STATES))
async def on_service_answer(callback: CallbackQuery, state: FSMContext) -> None:
    """Универсальный обработчик ответов на вопросы по услугам."""
    await callback.answer()
    data = await state.get_data()
    queue = data.get("service_queue", [])
    answers = data.get("service_answers", {})

    if queue:
        state_name, _, _, mapping = queue[0]
        answer_text = mapping.get(callback.data, callback.data)
        answers[state_name] = answer_text
        queue = queue[1:]  # убираем отвеченный вопрос

    await state.update_data(service_queue=queue, service_answers=answers)
    await _next_service_question(callback, state)


@router.message(StateFilter(*SERVICE_STATES))
async def on_service_text(message: Message, state: FSMContext) -> None:
    """Текстовый ответ на вопрос по услуге (для кнопок «Другое»)."""
    await _log_message(state, message.text)
    data = await state.get_data()
    queue = data.get("service_queue", [])
    answers = data.get("service_answers", {})

    if queue:
        state_name = queue[0][0]
        answers[state_name] = message.text
        queue = queue[1:]

    await state.update_data(service_queue=queue, service_answers=answers)
    await _next_service_question_msg(message, state)


# ==================== БЛОК 4: БЮДЖЕТ И СРОКИ ====================

async def _ask_budget(callback: CallbackQuery, state: FSMContext) -> None:
    await _answer(callback, BUDGET_TEXT, reply_markup=_kb(BUDGET_BUTTONS, row_width=2))
    await state.set_state(SurveyStates.budget)


@router.callback_query(SurveyStates.budget, F.data.startswith("budget_"))
async def on_budget(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    budget = BUDGET_MAP.get(callback.data, callback.data)
    await state.update_data(budget=budget)
    await _answer(callback, DEADLINE_TEXT, reply_markup=_kb(DEADLINE_BUTTONS, row_width=2))
    await state.set_state(SurveyStates.deadline)


@router.callback_query(SurveyStates.deadline, F.data.startswith("dl_"))
async def on_deadline(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    deadline = DEADLINE_MAP.get(callback.data, callback.data)
    await state.update_data(deadline=deadline)
    await _show_summary(callback, state)


# ==================== СВОДКА ====================

async def _show_summary(callback: CallbackQuery, state: FSMContext) -> None:
    """Показывает сводку ответов перед контактом."""
    data = await state.get_data()

    services_str = ", ".join(SERVICE_CODES.get(s, s) for s in data.get("services", []))
    summary_parts = [
        f"🏢 Бизнес: {data.get('niche', '—')}",
        f"👥 ЦА: {data.get('client_type', '—')}",
        f"🎯 Нужно: {services_str or '—'}",
        f"💰 Бюджет: {data.get('budget', '—')}",
        f"⏰ Сроки: {data.get('deadline', '—')}",
    ]
    summary = "\n".join(summary_parts)
    text = CONFIRM_SUMMARY_TEXT.format(summary=summary)

    await _answer(callback, text, reply_markup=_kb(CONFIRM_SUMMARY_BUTTONS, row_width=2))
    await state.set_state(SurveyStates.confirm_summary)


async def _show_summary_msg(message: Message, state: FSMContext) -> None:
    """Сводка из message-контекста (после текстового ввода при редактировании)."""
    data = await state.get_data()
    services_str = ", ".join(SERVICE_CODES.get(s, s) for s in data.get("services", []))
    summary_parts = [
        f"🏢 Бизнес: {data.get('niche', '—')}",
        f"👥 ЦА: {data.get('client_type', '—')}",
        f"🎯 Нужно: {services_str or '—'}",
        f"💰 Бюджет: {data.get('budget', '—')}",
        f"⏰ Сроки: {data.get('deadline', '—')}",
    ]
    summary = "\n".join(summary_parts)
    text = CONFIRM_SUMMARY_TEXT.format(summary=summary)
    await message.answer(text, reply_markup=_kb(CONFIRM_SUMMARY_BUTTONS, row_width=2))
    await state.set_state(SurveyStates.confirm_summary)


@router.callback_query(SurveyStates.confirm_summary, F.data == "summary_ok")
async def on_summary_ok(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await _ask_contact(callback, state)


@router.callback_query(SurveyStates.confirm_summary, F.data == "summary_redo")
async def on_summary_redo(callback: CallbackQuery, state: FSMContext) -> None:
    """Клиент хочет изменить — показываем выбор что именно."""
    await callback.answer()
    edit_buttons = [
        ("🏢 Бизнес", "edit_business"),
        ("🎯 Услуги", "edit_services"),
        ("💰 Бюджет/сроки", "edit_budget"),
    ]
    await _answer(callback, "Что хотите изменить?", reply_markup=_kb(edit_buttons, row_width=3))


@router.callback_query(SurveyStates.confirm_summary, F.data.startswith("edit_"))
async def on_summary_edit_choice(callback: CallbackQuery, state: FSMContext) -> None:
    """Переход к редактированию конкретного блока."""
    await callback.answer()
    choice = callback.data.replace("edit_", "")
    await state.update_data(_editing=choice)

    if choice == "business":
        await _ask_b1_niche(callback, state)
    elif choice == "services":
        # Предзаполняем текущий выбор
        data = await state.get_data()
        current = [f"svc_{s}" for s in data.get("services", [])]
        await state.update_data(selected_p1=current)
        await _answer(
            callback,
            "Что из этого вам нужно? Можно выбрать несколько:",
            reply_markup=_multiselect_kb(P1_SERVICES_BUTTONS, set(current), row_width=2),
        )
        await state.set_state(SurveyStates.p1_services)
    elif choice == "budget":
        await _ask_budget(callback, state)


# ==================== БЛОК 5: КОНТАКТ ====================

async def _ask_contact(callback: CallbackQuery, state: FSMContext) -> None:
    await _answer(callback, CONTACT_METHOD_TEXT, reply_markup=_kb(CONTACT_METHOD_BUTTONS, row_width=1))
    await state.set_state(SurveyStates.contact_method)


@router.callback_query(SurveyStates.contact_method, F.data.startswith("contact_"))
async def on_contact_method(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    method = CONTACT_METHOD_MAP.get(callback.data, callback.data)
    await state.update_data(contact_method=method)

    if callback.data == "contact_tg":
        # Telegram — спрашиваем только имя
        await state.update_data(
            contact_value=f"@{callback.from_user.username}" if callback.from_user.username else str(callback.from_user.id),
        )
        await _answer(callback, CONTACT_NAME_TEXT)
        await state.set_state(SurveyStates.contact_name)
    elif callback.data == "contact_phone":
        await _answer(callback, CONTACT_INPUT_PHONE_TEXT)
        await state.set_state(SurveyStates.contact_input)
    elif callback.data == "contact_email":
        await _answer(callback, CONTACT_INPUT_EMAIL_TEXT)
        await state.set_state(SurveyStates.contact_input)


@router.message(SurveyStates.contact_input)
async def on_contact_input(message: Message, state: FSMContext) -> None:
    """Ввод телефона или email."""
    await _log_message(state, message.text)
    await state.update_data(contact_value=message.text)
    await message.answer(CONTACT_NAME_TEXT)
    await state.set_state(SurveyStates.contact_name)


@router.message(SurveyStates.contact_name)
async def on_contact_name(message: Message, state: FSMContext) -> None:
    """Имя клиента → завершение."""
    await _log_message(state, message.text)
    await state.update_data(client_name=message.text)

    # Переходим к генерации отчёта (импортируем здесь чтобы избежать circular)
    from handlers.report import finish_survey
    await finish_survey(message, state)
