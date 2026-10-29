from datetime import datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from horario import FUSO, agora_local

APP = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture
def pasta_temp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # o SQLite local (dados.db) fica numa pasta temporária


def test_agora_local_em_lisboa():
    agora = agora_local()
    assert agora.tzinfo == FUSO and str(FUSO) == "Europe/Lisbon"
    assert abs((agora - datetime.now(FUSO)).total_seconds()) < 5


def test_supabase_sem_palavra_passe_bloqueia(pasta_temp):
    at = AppTest.from_file(APP, default_timeout=30)
    at.secrets["SUPABASE_URL"] = "https://exemplo.supabase.co"
    at.secrets["SUPABASE_KEY"] = "chave"
    at.run()
    assert any("APP_PASSWORD" in e.value for e in at.error)
    assert len(at.sidebar.radio) == 0


def test_modo_local_avisado(pasta_temp):
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert any("Modo local" in c.value for c in at.sidebar.caption)
