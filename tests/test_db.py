from datetime import date, time

import pandas as pd
import pytest

from db import COLUNAS, SqliteRepo, _normalizar_df, obter_repo

REG = {
    "data": date(2026, 10, 29),
    "numero_encomenda": "ENC-1",
    "operador": "Ana",
    "hora_picking": time(14, 35),
    "tipo_erro": "Falta",
    "produto": None,
    "quantidade": None,
    "observacao": None,
}


@pytest.fixture
def repo():
    return SqliteRepo(":memory:")


def test_inserir_e_listar(repo):
    novo_id = repo.inserir(REG)
    df = repo.listar()
    assert len(df) == 1
    assert df.iloc[0]["id"] == novo_id
    assert df.iloc[0]["data"] == date(2026, 10, 29)
    assert df.iloc[0]["hora_picking"] == time(14, 35)


def test_listar_filtra_datas(repo):
    repo.inserir({**REG, "data": date(2026, 10, 1)})
    repo.inserir(REG)
    df = repo.listar(date(2026, 10, 15), None)
    assert list(df["data"]) == [date(2026, 10, 29)]
    df = repo.listar(None, date(2026, 10, 15))
    assert list(df["data"]) == [date(2026, 10, 1)]


def test_atualizar(repo):
    novo_id = repo.inserir(REG)
    repo.atualizar(novo_id, {"tipo_erro": "Excesso", "hora_picking": time(9, 5)})
    linha = repo.listar().iloc[0]
    assert linha["tipo_erro"] == "Excesso"
    assert linha["hora_picking"] == time(9, 5)


def test_apagar(repo):
    novo_id = repo.inserir(REG)
    repo.apagar(novo_id)
    assert repo.listar().empty


def test_operadores_distintos(repo):
    repo.inserir({**REG, "operador": "João"})
    repo.inserir(REG)
    repo.inserir(REG)
    assert repo.operadores() == ["Ana", "João"]


def test_listar_vazio_tem_colunas(repo):
    assert list(repo.listar().columns) == COLUNAS


def test_normalizar_df_converte_texto():
    df = _normalizar_df(pd.DataFrame([{**REG, "id": 1, "criado_em": "2026-10-29T10:00:00",
                                       "data": "2026-10-29", "hora_picking": "14:35:00"}]))
    assert df.iloc[0]["data"] == date(2026, 10, 29)
    assert df.iloc[0]["hora_picking"] == time(14, 35)


def test_obter_repo_sem_chaves_usa_sqlite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert isinstance(obter_repo({}), SqliteRepo)


def test_operadores_inclui_tabela_operador(repo):
    repo.adicionar_operador("Sara Rebelo")
    repo.inserir({**REG, "operador": "Ana"})
    assert repo.operadores() == ["Ana", "Sara Rebelo"]


def test_adicionar_operador_sem_duplicados(repo):
    repo.adicionar_operador("Tiago Pereira")
    repo.adicionar_operador("tiago pereira")
    repo.adicionar_operador("  Tiago Pereira ")
    assert repo.operadores() == ["Tiago Pereira"]
