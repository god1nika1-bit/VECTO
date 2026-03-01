"""FSM-состояния опроса."""

from aiogram.fsm.state import State, StatesGroup


class SurveyStates(StatesGroup):
    # --- Повторный /start ---
    restart_confirm = State()    # незавершённый опрос — начать заново или продолжить

    # --- Вход ---
    # Данные из deeplink сохраняются в FSM data:
    # source, preselected_services, preselected_total
    # Эти данные используются чтобы НЕ переспрашивать клиента
    confirm_deeplink = State()   # подтверждение выбора с калькулятора
    choose_services = State()    # выбор услуг (прямой вход)

    # --- Блок 1: О бизнесе ---
    b1_niche = State()           # ниша
    b1_niche_custom = State()    # ниша — свой вариант
    b2_client_type = State()     # тип клиента (B2C/B2B)
    b2_client_age = State()      # возраст ЦА (если B2C)
    b2_client_age_custom = State()
    b3_channels = State()        # каналы привлечения (мультивыбор)
    b4_pain = State()            # главная боль (мультивыбор)
    b4_pain_custom = State()     # боль — свой вариант (доп. текст)

    # --- Блок 2: О проекте ---
    p1_services = State()        # выбор услуг (если не определены)
    p2_materials = State()       # материалы (мультивыбор)
    waiting_files = State()      # приём файлов (фото, документы) от клиента
    p3_style = State()           # стиль/референсы
    p3_style_custom = State()    # ссылки на референсы

    # --- Блок 3: По услугам ---
    # Лендинг
    service_l1 = State()         # тип сайта
    service_l2 = State()         # реклама
    # Telegram-бот
    service_t1 = State()         # функции бота
    service_t2 = State()         # нагрузка
    # Контент
    service_c1 = State()         # площадки
    service_c2 = State()         # тон
    # Финмодель
    service_f1 = State()         # для кого
    service_f2 = State()         # данные
    # Копирайтинг
    service_k1 = State()         # тип текста

    # --- Блок 4: Бюджет и сроки ---
    budget = State()
    deadline = State()

    # --- Сводка ---
    confirm_summary = State()    # клиент видит сводку и подтверждает

    # --- Свободное ТЗ ---
    free_tz_input = State()      # клиент описывает задачу своими словами

    # --- Блок 5: Контакт ---
    contact_name = State()       # имя
