from datetime import datetime
from zoneinfo import ZoneInfo


def get_brazil_time() -> str:
    """Get current time in São Paulo timezone (America/Sao_Paulo)

    Returns:
        str: Current time in São Paulo timezone (ISO format)
    """
    return datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()


def brazil_time_formatter(record: dict) -> str:
    """
    Patch function for Loguru to format the time field in Brazil timezone.
    Usage: logger.patch(lambda record: record.update(time=brazil_time(record)))
    """
    return record["time"].astimezone(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S %z")
