# 🍅 Pomodoro Tracker 🍅

Терминальный (TUI) Pomodoro-трекер на Python и [Textual](https://textual.textualize.io/), заточенный под разработку,
бизнес-задачи, обучение и быстрые MVP-спринты.

Классический цикл «25/5» часто обрывает состояние потока при работе со сложным кодом или аналитикой, поэтому в трекер
зашиты 6 практических ритмов под разные типы нагрузки.

---

## Возможности

- **6 режимов работы** с подсказками по фокусу для каждого ритма.
- **Удобный TUI-интерфейс:** крупный таймер, кликабельные кнопки и управление с клавиатуры (включая русскую раскладку).
- **Вкладки со статистикой:**
    - **Таймер** — управление сессией, выбор режима и сводка за текущий день.
    - **Сегодня** — разбивка завершённых блоков по режимам и таблица сессий дня.
    - **Весь лог** — суммарная статистика и полная история за всё время.
- **Локальный JSON-лог:** все завершённые фазы (`work` / `break`) сохраняются в `stats.json` в директории `tmp/`.
- **Нативные уведомления Linux:** десктопные оповещения через `notify-send` и звуковой сигнал через `paplay` (с фолбэком
  на системный бип).

---

## Режимы работы

| Режим       |   Ритм    | Для каких задач                      | На что делать упор                                                   |
|:------------|:---------:|:-------------------------------------|:---------------------------------------------------------------------|
| **Dev**     | `90 / 20` | Разработка, архитектура, рефакторинг | Глубокое погружение без отвлечений. Оптимально 2–3 блока в день.     |
| **Biz**     | `50 / 10` | Аналитика, стратегия, регламенты     | Фокус на одной задаче; 5 мин разминки + 5 мин чек-ин в мессенджерах. |
| **Classic** | `25 / 5`  | Рутина, мелкие баги, ревью, почта    | Закрытие операционки во второй половине дня.                         |
| **Learn**   | `45 / 15` | Изучение нового стека / языка        | Чередование: 1 блок теории → 2 блока кода руками.                    |
| **MVP**     | `50 / 10` | Проверка гипотезы (MVP / PoC)        | Максимум 2–3 цикла. Фокус на «работает или нет», без шлифовки.       |
| **Docs**    | `25 / 5`  | Чтение сложной документации / статей | Короткие сессии, чтобы мозг не «закипал» от плотного текста.         |

---

## Установка и запуск

Требуется Python 3.15+ и [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/ivanitch/pomadoro-tracker pomadoro-tracker
cd pomadoro-tracker

# Установка зависимостей
uv sync

# Запуск трекера
pomodoro

# Запуск из директории проекта
uv run pomo
```

---

## Горячие клавиши

Все клавиши работают на английской и русской раскладках:

| Клавиша   | Действие                                                  |
|-----------|-----------------------------------------------------------|
| `Space`   | Старт / Пауза                                             |
| `f` (`а`) | Зачесть фазу досрочно (с записью в статистику и сигналом) |
| `r` (`к`) | Стоп (сброс текущей фазы)                                 |
| `s` (`ы`) | Пропустить фазу (без записи в статистику)                 |
| `t` (`е`) | Вкладка «Таймер»                                          |
| `d` (`в`) | Вкладка «Сегодня»                                         |
| `l` (`д`) | Вкладка «Весь лог»                                        |
| `n` (`т`) | Тест сигнала (уведомление и звук)                         |
| `q` (`й`) | Выход                                                     |

---

## Интеграция с Linux (Debian / LMDE / Cinnamon)

### 1. Скрипт-обёртка `~/.local/bin/pomodoro`

```bash
mkdir -p ~/.local/bin
cat << 'EOF' > ~/.local/bin/pomodoro
#!/usr/bin/env bash
cd /путь/к/проекту && exec ~/.local/bin/uv run pomo
EOF
chmod +x ~/.local/bin/pomodoro

```

*(Убедись, что путь к `uv` совпадает с выводом команды `which uv`.)*

### 2. Иконка помидора 🍅

```bash
mkdir -p ~/.local/share/icons/hicolor/scalable/apps
curl -s "[https://raw.githubusercontent.com/twitter/twemoji/master/assets/svg/1f345.svg](https://raw.githubusercontent.com/twitter/twemoji/master/assets/svg/1f345.svg)" \
  -o ~/.local/share/icons/hicolor/scalable/apps/pomodoro-tracker.svg
```

### 3. Ярлык в меню приложений

```bash
mkdir -p ~/.local/share/applications
cat << EOF > ~/.local/share/applications/pomodoro.desktop
[Desktop Entry]
Type=Application
Name=Pomodoro Tracker
Comment=Terminal Pomodoro timer for Dev and Business
Exec=$HOME/.local/bin/pomodoro
Icon=$HOME/.local/share/icons/hicolor/scalable/apps/pomodoro-tracker.svg
Terminal=true
Categories=Utility;
Keywords=pomodoro;timer;tracker;focus;
EOF
chmod +x ~/.local/share/applications/pomodoro.desktop
update-desktop-database ~/.local/share/applications

```

### 4. Автозагрузка при входе в систему

```bash
mkdir -p ~/.config/autostart
cp ~/.local/share/applications/pomodoro.desktop ~/.config/autostart/pomodoro.desktop

```

5. ### Автоактивация окна (опционально, Linux / X11)

Чтобы при завершении блока или отдыха окно терминала с трекером автоматически выводилось на передний план, установи
`wmctrl`:

```bash
sudo apt install wmctrl
```

*(Без `wmctrl` трекер продолжит работать, но окно придётся переключать вручную.)*

## Структура проекта и тесты

```text
├── src/
│   ├── __init__.py
│   ├── pomodoro.py        # TUI-приложение на Textual
│   └── storage.py         # Модели режимов и работа с JSON-логом
├── tests/
│   └── pomodoro_test.py   # Юнит-тесты хранилища и статистики
├── tmp/
│   └── stats.json         # История фокусов
├── pyproject.toml
├── uv.lock
└── README.md

```

Запуск тестов:

```bash
uv run pytest
```

> Файл `stats.json` создаётся автоматически при первом запуске в директории `tmp/` и хранится локально.

---

## UI

Трекер:

![Трекер](/docs/img/main.svg)

Статистика / Журнал событий (Сегодня / За все время):

![Статистика / Журнал событий](/docs/img/stats.svg)

Функции:

![Кастомизация](/docs/img/funcs.png)
