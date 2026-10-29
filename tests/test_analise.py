from datetime import date, time

import pandas as pd
import pytest

from analise import (evolucao_diaria, filtrar, kpis, mapa_operador_hora, para_excel,
                     por_hora, por_operador_tipo, por_tipo)
from db import COLUNAS, _normalizar_df


def linha(operador, hora, tipo, dia=29):
    return {"id": None, "data": date(2026, 10, dia), "numero_encomenda": "E", "operador": operador,
            "hora_picking": hora, "tipo_erro": tipo, "produto": None, "quantidade": None,
            "observacao": None, "criado_em": None}


@pytest.fixture
def df():
    return _normalizar_df(pd.DataFrame([
        linha("Ana", time(9, 10), "Troca", 28),
        linha("Ana", time(9, 50), "Falta"),
        linha("João", time(14, 35), "Falta"),
        linha("João", time(14, 5), "Falta"),
        linha("João", time(16, 20), "Excesso"),
    ]))


@pytest.fixture
def vazio():
    return _normalizar_df(pd.DataFrame(columns=COLUNAS))


def test_kpis(df):
    assert kpis(df) == {"total": 5, "Troca": 1, "Falta": 3, "Excesso": 1}


def test_por_hora(df):
    assert por_hora(df).set_index("hora")["erros"].to_dict() == {9: 2, 14: 2, 16: 1}


def test_mapa_operador_hora(df):
    mapa = mapa_operador_hora(df)
    assert mapa.loc["Ana", 14] == 0
    assert mapa.loc["João", 14] == 2


def test_por_tipo_inclui_tipos_ausentes(df):
    contagem = por_tipo(df.iloc[[df.index[df["tipo_erro"] == "Troca"][0]]])
    assert contagem.set_index("tipo_erro")["erros"].to_dict() == {"Troca": 1, "Falta": 0, "Excesso": 0}


def test_por_operador_tipo(df):
    r = por_operador_tipo(df).set_index(["operador", "tipo_erro"])["erros"]
    assert r[("João", "Falta")] == 2


def test_evolucao_diaria(df):
    assert evolucao_diaria(df).set_index("data")["erros"].to_dict() == {
        date(2026, 10, 28): 1, date(2026, 10, 29): 4}


def test_filtrar(df):
    assert len(filtrar(df, ["Ana"], [])) == 2
    assert len(filtrar(df, [], ["Falta"])) == 3
    assert len(filtrar(df, ["João"], ["Falta"])) == 2


def test_vazio_nao_rebenta(vazio):
    assert kpis(vazio) == {"total": 0, "Troca": 0, "Falta": 0, "Excesso": 0}
    for f in (por_tipo, por_hora, por_operador_tipo, mapa_operador_hora, evolucao_diaria):
        f(vazio)
    para_excel(vazio)


def test_para_excel(df):
    assert para_excel(df)[:2] == b"PK"
