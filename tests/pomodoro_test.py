from datetime import datetime
from pathlib import Path

from src.storage import StatsStore, MODES, DEFAULT_LOG_PATH, PROJECT_DIR


def test_default_log_path_is_in_project_dir() -> None:
    assert PROJECT_DIR == Path(__file__).resolve().parent.parent
    assert DEFAULT_LOG_PATH == PROJECT_DIR / "tmp/stats.json"


def test_record_and_stats_by_day_and_all_time(tmp_path: Path) -> None:
    store = StatsStore(tmp_path / "stats.json")
    today = datetime(2026, 11, 18, 10, 0)
    yesterday = datetime(2026, 11, 17, 15, 0)

    store.record_session("learn", "work", 45, now=today)
    store.record_session("learn", "break", 15, now=today)
    store.record_session("mvp", "work", 50, now=today)
    store.record_session("docs", "work", 25, now=yesterday)

    today_stats = store.get_stats("2026-11-18")
    all_stats = store.get_stats(None)

    assert today_stats.work_by_mode["learn"] == 1
    assert today_stats.work_by_mode["mvp"] == 1
    assert today_stats.work_by_mode["docs"] == 0
    assert today_stats.total_work_blocks == 2
    assert today_stats.total_work_min == 95
    assert today_stats.total_break_min == 15

    assert all_stats.total_work_blocks == 3
    assert all_stats.total_work_min == 120
    assert set(MODES.keys()) == {"dev", "biz", "classic", "learn", "mvp", "docs"}


def test_corrupted_json_does_not_crash(tmp_path: Path) -> None:
    log_file = tmp_path / "stats.json"
    log_file.write_text("{broken json", encoding="utf-8")

    store = StatsStore(log_file)
    assert store.load_sessions() == []
    assert store.get_stats("2026-11-18").total_work_blocks == 0
