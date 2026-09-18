from datetime import datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from loguru import Record


def get_brazil_time() -> str:
    """Get current time in São Paulo timezone (America/Sao_Paulo)

    Returns:
        str: Current time in São Paulo timezone (ISO format)
    """
    return datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()


def brazil_time_formatter(record: "Record") -> str:
    """Format a Loguru record with a timestamp in the São Paulo timezone."""
    timestamp = record["time"].astimezone(ZoneInfo("America/Sao_Paulo"))
    return f"[{{level}}] {timestamp:%Y-%m-%d %H:%M:%S %z} | {{message}}\n{{exception}}"
