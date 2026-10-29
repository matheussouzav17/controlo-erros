"""Hora local de Portugal (o servidor do Streamlit Cloud corre em UTC)."""

from datetime import datetime
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("Europe/Lisbon")


def agora_local() -> datetime:
    return datetime.now(FUSO)
