from datetime import datetime
from agent.tools import ziva_tool


@ziva_tool
def get_current_datetime() -> str:
    """Get the current system date, time, and weekday. Returns a string like '2026-07-05 14:30:00 (Sunday)'."""
    now = datetime.now()
    return now.strftime('%Y-%m-%d %H:%M:%S') + f' ({now.strftime("%A")})'
