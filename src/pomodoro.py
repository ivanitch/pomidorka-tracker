#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import (
    Button,
    DataTable,
    Digits,
    Footer,
    Header,
    Label,
    TabbedContent,
    TabPane,
)

from src.storage import MODES, PeriodStats, SessionRecord, StatsStore


def notify_user(title: str, message: str) -> None:
    """Отправляет десктопное уведомление и проигрывает звук в LMDE/Linux."""
    if shutil.which("notify-send"):
        subprocess.Popen(
            ["notify-send", "-u", "normal", "-a", "Pomodoro", title, message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    sound_file = "/usr/share/sounds/freedesktop/stereo/complete.oga"
    if shutil.which("paplay"):
        subprocess.Popen(
            ["paplay", sound_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        print("\a", end="", flush=True)


class PomodoroApp(App[None]):
    CSS = """
    Screen {
        background: #1d2125;
    }

    TabbedContent {
        height: 1fr;
    }

    Tab {
        padding: 0 3;
    }

    Tab:hover {
        background: #2c333a;
        color: #ffffff;
    }

    TabPane {
        padding: 1 2;
        align: center middle;
    }

    #card {
        width: 80;
        height: auto;
        padding: 1 3;
        border: solid #38414a;
        background: #22272b;
    }

    #status {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: #579dff;
    }

    #status.break {
        color: #4bce97;
    }

    #tip {
        width: 100%;
        text-align: center;
        color: #8c9bab;
        margin-bottom: 1;
    }

    #timer {
        width: auto;
        margin: 1 0;
        color: #dee4ea;
    }

    #today-summary {
        width: 100%;
        text-align: center;
        color: #b6c2cf;
        margin-bottom: 1;
    }

    .row {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    Button {
        height: 3;
        margin: 0 1;
        min-width: 14;
    }

    .mode-btn {
        min-width: 21;
    }

    .util-btn {
        min-width: 20;
    }

    Button:hover {
        text-style: bold;
    }

    .stats-box {
        width: 100%;
        height: auto;
        padding: 1 2;
        margin-bottom: 1;
        border: solid #38414a;
        background: #22272b;
        color: #dee4ea;
    }

    DataTable {
        height: 1fr;
        border: solid #38414a;
        background: #22272b;
    }
    """

    BINDINGS = [
        Binding("space", "toggle_timer", "Старт/Пауза", priority=True),
        Binding("f", "complete_phase", "Зачесть", priority=True),
        Binding("r", "stop_timer", "Стоп", priority=True),
        Binding("s", "skip_phase", "Пропустить", priority=True),
        Binding("t", "switch_tab('tab-timer')", "Таймер", priority=True),
        Binding("d", "switch_tab('tab-today')", "Сегодня", priority=True),
        Binding("l", "switch_tab('tab-all')", "Весь лог", priority=True),
        Binding("n", "test_notify", "Тест сигнала", priority=True),
        Binding("q", "quit", "Выход", priority=True),
        # Поддержка русской раскладки
        Binding("а", "complete_phase", "", show=False, priority=True),
        Binding("к", "stop_timer", "", show=False, priority=True),
        Binding("ы", "skip_phase", "", show=False, priority=True),
        Binding("е", "switch_tab('tab-timer')", "", show=False, priority=True),
        Binding("в", "switch_tab('tab-today')", "", show=False, priority=True),
        Binding("д", "switch_tab('tab-all')", "", show=False, priority=True),
        Binding("т", "test_notify", "", show=False, priority=True),
        Binding("й", "quit", "", show=False, priority=True),
    ]

    mode_key: reactive[str] = reactive("dev")
    is_break: reactive[bool] = reactive(False)
    is_running: reactive[bool] = reactive(False)
    seconds_left: reactive[int] = reactive(MODES["dev"].work_min * 60)

    def __init__(self, store: StatsStore | None = None) -> None:
        super().__init__()
        self.store = store or StatsStore()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="tab-timer"):
            with TabPane("Таймер", id="tab-timer"):
                with Vertical(id="card"):
                    yield Label("", id="status")
                    yield Label("", id="tip")
                    with Center():
                        yield Digits("90:00", id="timer")
                    yield Label("", id="today-summary")

                    with Horizontal(classes="row"):
                        yield Button("Старт", id="start", variant="success")
                        yield Button("Пауза", id="pause", variant="warning", disabled=True)
                        yield Button("Зачесть", id="complete", variant="primary")
                        yield Button("Стоп", id="stop", variant="error")

                    with Horizontal(classes="row"):
                        yield Button("Dev 90/20", id="mode_dev", classes="mode-btn")
                        yield Button("Biz 50/10", id="mode_biz", classes="mode-btn")
                        yield Button("Classic 25/5", id="mode_classic", classes="mode-btn")

                    with Horizontal(classes="row"):
                        yield Button("Learn 45/15", id="mode_learn", classes="mode-btn")
                        yield Button("MVP 50/10", id="mode_mvp", classes="mode-btn")
                        yield Button("Docs 25/5", id="mode_docs", classes="mode-btn")

                    with Horizontal(classes="row"):
                        yield Button("Пропустить фазу", id="skip", classes="util-btn")
                        yield Button("Тест сигнала", id="test_notify", classes="util-btn")

            with TabPane("Сегодня", id="tab-today"):
                yield Label("", id="today-breakdown", classes="stats-box")
                yield DataTable(id="today-table")

            with TabPane("Весь лог", id="tab-all"):
                yield Label("", id="all-breakdown", classes="stats-box")
                yield DataTable(id="all-table")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "🍅 Pomodoro Tracker 🍅"
        self.set_interval(1.0, self._tick)

        today_table = self.query_one("#today-table", DataTable)
        today_table.can_focus = False
        today_table.add_columns("Время", "Режим", "Фаза", "Мин")

        all_table = self.query_one("#all-table", DataTable)
        all_table.can_focus = False
        all_table.add_columns("Дата", "Время", "Режим", "Фаза", "Мин")

        self._sync_ui()

    def on_tabbed_content_tab_activated(self) -> None:
        self._refresh_tables()

    def _tick(self) -> None:
        if not self.is_running:
            return
        if self.seconds_left > 0:
            self.seconds_left -= 1
            return
        self._finish_phase(completed=True)

    def _finish_phase(self, *, completed: bool) -> None:
        self.is_running = False
        mode = MODES[self.mode_key]

        if not self.is_break:
            if completed:
                self.store.record_session(self.mode_key, "work", mode.work_min)
                notify_user(
                    "🍅 Блок завершён!",
                    f"{mode.title} — пора отдохнуть {mode.break_min} мин.",
                )
            self.is_break = True
            self.seconds_left = mode.break_min * 60
        else:
            if completed:
                self.store.record_session(self.mode_key, "break", mode.break_min)
                notify_user(
                    "🍅 Отдых окончен!",
                    f"Возвращаемся к задаче: {mode.title}.",
                )
            self.is_break = False
            self.seconds_left = mode.work_min * 60

        self._sync_ui()

    @staticmethod
    def _format_breakdown(title: str, stats: PeriodStats) -> str:
        header = (
            f"{title}:  Фокус {stats.total_work_blocks} бл. ({stats.total_work_min} мин)  |  "
            f"Отдых {stats.total_break_blocks} ({stats.total_break_min} мин)"
        )
        modes_line = "  •  ".join(
            f"{m.short}: {stats.work_by_mode.get(k, 0)}"
            for k, m in MODES.items()
        )
        return f"{header}\n{modes_line}"

    def _refresh_tables(self) -> None:
        today_str = datetime.now().date().isoformat()
        today_stats = self.store.get_stats(today_str)
        all_stats = self.store.get_stats(None)

        self.query_one("#today-summary", Label).update(
            f"Сегодня: 🍅 {today_stats.total_work_blocks} бл. ({today_stats.total_work_min} мин фокуса)  |  "
            f"Отдых: {today_stats.total_break_min} мин"
        )
        self.query_one("#today-breakdown", Label).update(
            self._format_breakdown(f"Сегодня ({today_str})", today_stats)
        )
        self.query_one("#all-breakdown", Label).update(
            self._format_breakdown("За всё время", all_stats)
        )

        self._fill_table(
            self.query_one("#today-table", DataTable),
            self.store.get_sessions(today_str),
            include_date=False,
        )
        self._fill_table(
            self.query_one("#all-table", DataTable),
            self.store.get_sessions(None),
            include_date=True,
        )

    @staticmethod
    def _fill_table(
        table: DataTable[str],
        sessions: list[SessionRecord],
        *,
        include_date: bool,
    ) -> None:
        table.clear()
        for s in reversed(sessions):
            time_part = s.timestamp.split("T")[-1]
            mode_name = MODES[s.mode].short if s.mode in MODES else s.mode
            phase_label = "Фокус" if s.phase == "work" else "Отдых"
            if include_date:
                table.add_row(s.date, time_part, mode_name, phase_label, str(s.duration_min))
            else:
                table.add_row(time_part, mode_name, phase_label, str(s.duration_min))

    def _sync_ui(self) -> None:
        mode = MODES[self.mode_key]
        phase = "ОТДЫХ" if self.is_break else "ФОКУС"

        status = self.query_one("#status", Label)
        status.update(f"🍅 {mode.title}  •  {phase}")
        status.set_class(self.is_break, "break")

        self.query_one("#tip", Label).update(mode.tip)

        mins, secs = divmod(self.seconds_left, 60)
        self.query_one("#timer", Digits).update(f"{mins:02d}:{secs:02d}")

        self.query_one("#start", Button).disabled = self.is_running
        self.query_one("#pause", Button).disabled = not self.is_running

        for key in MODES:
            btn = self.query_one(f"#mode_{key}", Button)
            btn.variant = "primary" if key == self.mode_key else "default"

        self._refresh_tables()

    def watch_seconds_left(self) -> None:
        if self.is_mounted:
            mins, secs = divmod(self.seconds_left, 60)
            self.query_one("#timer", Digits).update(f"{mins:02d}:{secs:02d}")

    def action_toggle_timer(self) -> None:
        self.is_running = not self.is_running
        self._sync_ui()

    def action_complete_phase(self) -> None:
        self._finish_phase(completed=True)

    def action_stop_timer(self) -> None:
        self.is_running = False
        self.is_break = False
        self.seconds_left = MODES[self.mode_key].work_min * 60
        self._sync_ui()

    def action_skip_phase(self) -> None:
        self._finish_phase(completed=False)

    def action_switch_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id

    def action_set_mode(self, key: str) -> None:
        if key not in MODES:
            return
        self.mode_key = key
        self.is_running = False
        self.is_break = False
        self.seconds_left = MODES[key].work_min * 60
        self._sync_ui()

    def action_test_notify(self) -> None:
        notify_user("🍅 Тест сигнала", "Уведомления и звук работают!")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        self.set_focus(None)
        if btn_id == "start":
            self.is_running = True
            self._sync_ui()
        elif btn_id == "pause":
            self.is_running = False
            self._sync_ui()
        elif btn_id == "complete":
            self.action_complete_phase()
        elif btn_id == "stop":
            self.action_stop_timer()
        elif btn_id == "skip":
            self.action_skip_phase()
        elif btn_id == "test_notify":
            self.action_test_notify()
        elif btn_id and btn_id.startswith("mode_"):
            self.action_set_mode(btn_id.removeprefix("mode_"))


def main() -> None:
    PomodoroApp().run()


if __name__ == "__main__":
    main()
