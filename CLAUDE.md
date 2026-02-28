# VECTO — Проект цифровой студии

## О проекте

VECTO — коммерческий сайт-лендинг digital-студии. Хостинг: GitHub Pages.
- Прод: https://god1nika1-bit.github.io/VECTO/
- Стек: чистый HTML + CSS + JS (без фреймворков)
- Бот: Python 3.11+, aiogram 3.x
- ЦА: малый бизнес, стартапы, предприниматели в России

## Структура проекта

```
VECTO/
├── CLAUDE.md              ← ты сейчас здесь
├── index.html             ← главная (лендинг, 13 секций)
├── css/
│   └── styles.css         ← все стили, CSS-переменные
├── js/
│   └── main.js            ← canvas, reveal, аккордеон, калькулятор
├── docs/
│   └── bot-spec.md        ← спецификация Telegram-бота
└── bot/                   ← Telegram-бот (Python)
    ├── bot.py             ← точка входа
    ├── config.py          ← токены, ID владельца
    ├── states.py          ← FSM-состояния
    ├── questions.py       ← тексты вопросов и кнопок
    ├── handlers/
    │   ├── start.py       ← /start + deeplink парсинг
    │   ├── survey.py      ← основной flow опроса
    │   └── report.py      ← генерация .md + отправка
    ├── utils/
    │   └── deeplink.py    ← парсинг параметров калькулятора
    └── requirements.txt
```

## Дизайн-система

```css
--bg: #0a0a0a;
--bg-card: #111111;
--bg-card-hover: #161616;
--accent: #0066FF;
--text-primary: #f0f0f0;
--text-secondary: #8a8a8a;
--text-muted: #555555;
--border: #1e1e1e;
--font-display: 'Unbounded', sans-serif;
--font-body: 'Outfit', sans-serif;
--radius: 12px;
--radius-sm: 8px;
```

## Секции index.html

1. Navigation — фиксированная, blur, капсульная
2. Hero — canvas-анимация (сеть узлов), CTA
3. Problems (01) — 3 карточки + stats-bar
4. Process (02) — 6 шагов
5. Services (03) — 6 карточек с ценами
6. Packages (04) — 3 тарифа (Старт 35к / Рост 70к / Масштаб 120к)
7. Calculator (05) — выбор услуг → доп.опции → расчёт
8. Cases (06) — 3 кейса с CSS-превью
9. Education (07) — аккордеон возражений
10. About (08) — философия + ценности
11. FAQ (09) — аккордеон вопросов
12. Final CTA
13. Footer

## Ссылки

| Назначение | URL |
|------------|-----|
| Связь (все CTA) | `https://t.me/nika_archon` (временно → потом бот) |
| Канал ARCHON | `https://t.me/+1tiA7NMG_tcwMDZi` |
| Канал VECTO | `https://t.me/+Koi4i37OJXpmMTIy` |
| Канал ARDIS (только footer) | `https://t.me/+wy0FM4P7CDU5YzZi` |

## Архитектура сайт ↔ бот

```
Сайт → CTA / Калькулятор → t.me/vecto_studio_bot?start={params}
                                    │
                            Бот парсит deeplink
                            Знает выбранные услуги + сумму
                                    │
                            Ведёт по вопросам (FSM)
                                    │
                            Генерирует .md-отчёт
                                    │
                            Отправляет владельцу в ТГ
```

Формат deeplink: `?start=landing_bot_40000`
- Коды услуг: landing, bot, content, finmodel, copy, consult
- Последний элемент (если число) = сумма из калькулятора

## Правила кода

### HTML/CSS/JS (сайт)
- Чистый код, без фреймворков и конструкторов
- Mobile-first, адаптивность
- Семантическая разметка
- CSS-переменные из дизайн-системы
- Никаких inline-стилей
- Комментарии на русском
- Lighthouse 95+

### Python (бот)
- Python 3.11+, aiogram 3.x, asyncio
- Типизация (type hints)
- FSM через aiogram StatesGroup
- Тексты вопросов — отдельный файл questions.py
- Конфиг — через переменные окружения (.env)
- Комментарии на русском

## Текущие задачи (приоритет)

### 🔴 Активные
1. Telegram-бот MVP — шаблонные вопросы, inline-кнопки, deeplink, .md-отчёт
2. Интеграция калькулятора с deeplink бота
3. Скролл калькулятора к центру экрана при расчёте

### 🟡 Следующие
4. Промежуточный экран после расчёта (перед переходом в бота)
5. Meta-теги и OG-разметка
6. Социальное доказательство (отзывы)

### 🟢 Будущее
7. Секция блога
8. AI-обработка ответов бота
9. Рабочее ПО для просмотра .md-отчётов
