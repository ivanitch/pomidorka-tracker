from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

Phase = Literal["work", "break"]

PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LOG_PATH = PROJECT_DIR / "tmp/stats.json"


@dataclass(frozen=True)
class Mode:
    key: str
    title: str
    short: str
    work_min: int
    break_min: int
    tip: str


@dataclass(frozen=True)
class SessionRecord:
    timestamp: str
    date: str
    mode: str
    phase: Phase
    duration_min: int


@dataclass(frozen=True)
class PeriodStats:
    work_by_mode: dict[str, int]
    work_min_by_mode: dict[str, int]
    total_work_blocks: int
    total_work_min: int
    total_break_blocks: int
    total_break_min: int


MODES: dict[str, Mode] = {
    "dev": Mode(
        "dev",
        "Разработка (90/20)",
        "Dev 90/20",
        90,
        20,
        "Глубокий фокус на сложной фиче/архитектуре. 2–3 блока в день.",
    ),
    "biz": Mode(
        "biz",
        "Бизнес (50/10)",
        "Biz 50/10",
        50,
        10,
        "Стратегия, аналитика, регламенты. 5 мин разминка + 5 мин чек-ин.",
    ),
    "classic": Mode(
        "classic",
        "Классика (25/5)",
        "Classic 25/5",
        25,
        5,
        "Рутина, мелкие баги, ревью, письма и согласования.",
    ),
    "learn": Mode(
        "learn",
        "Изучение стека (45/15)",
        "Learn 45/15",
        45,
        15,
        "Чередование: 1 блок теории -> 2 блока кода. Максимум практики руками.",
    ),
    "mvp": Mode(
        "mvp",
        "Гипотеза MVP/PoC (50/10)",
        "MVP 50/10",
        50,
        10,
        "Макс. 2–3 цикла. Жесткий фокус: работает или нет, без шлифовки.",
    ),
    "docs": Mode(
        "docs",
        "Чтение доков (25/5)",
        "Docs 25/5",
        25,
        5,
        "Короткие сессии для плотного текста, чтобы мозг не закипал.",
    ),
}


class StatsStore:
    """Хранилище истории сессий в JSON в папке проекта."""

    def __init__(self, path: Path = DEFAULT_LOG_PATH) -> None:
        self.path = path
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps({"sessions": []}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    def load_sessions(self) -> list[SessionRecord]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return [SessionRecord(**item) for item in raw.get("sessions", [])]
        except (json.JSONDecodeError, TypeError, KeyError):
            return []

    def record_session(
            self,
            mode: str,
            phase: Phase,
            duration_min: int,
            now: datetime | None = None,
    ) -> SessionRecord:
        dt = now or datetime.now()
        record = SessionRecord(
            timestamp=dt.isoformat(timespec="seconds"),
            date=dt.date().isoformat(),
            mode=mode,
            phase=phase,
            duration_min=duration_min,
        )
        sessions = self.load_sessions()
        sessions.append(record)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"sessions": [asdict(s) for s in sessions]}
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return record

    def get_sessions(self, target_date: str | None = None) -> list[SessionRecord]:
        sessions = self.load_sessions()
        if target_date is None:
            return sessions
        return [s for s in sessions if s.date == target_date]

    def get_stats(self, target_date: str | None = None) -> PeriodStats:
        sessions = self.get_sessions(target_date)
        work_by_mode = {key: 0 for key in MODES}
        work_min_by_mode = {key: 0 for key in MODES}
        total_work_blocks = 0
        total_work_min = 0
        total_break_blocks = 0
        total_break_min = 0

        for s in sessions:
            if s.phase == "work":
                work_by_mode[s.mode] = work_by_mode.get(s.mode, 0) + 1
                work_min_by_mode[s.mode] = work_min_by_mode.get(s.mode, 0) + s.duration_min
                total_work_blocks += 1
                total_work_min += s.duration_min
            elif s.phase == "break":
                total_break_blocks += 1
                total_break_min += s.duration_min

        return PeriodStats(
            work_by_mode=work_by_mode,
            work_min_by_mode=work_min_by_mode,
            total_work_blocks=total_work_blocks,
            total_work_min=total_work_min,
            total_break_blocks=total_break_blocks,
            total_break_min=total_break_min,
        )
