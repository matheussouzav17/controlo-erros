from datetime import date, time

import pytest

from validacao import ErroValidacao, normalizar_operador, validar


def registo(**alteracoes):
    base = {
        "data": date(2026, 10, 29),
        "numero_encomenda": " ENC-1 ",
        "operador": "ana",
        "hora_picking": time(14, 35),
        "tipo_erro": "Falta",
        "produto": "",
        "quantidade": None,
        "observacao": "",
    }
    base.update(alteracoes)
    return base


def test_normaliza_operador():
    assert normalizar_operador("  joão ") == "João"
    assert normalizar_operador("JOÃO  silva") == "João Silva"


def test_valida_registo_minimo():
    r = validar(registo())
    assert r["numero_encomenda"] == "ENC-1"
    assert r["operador"] == "Ana"
    assert r["produto"] is None and r["observacao"] is None and r["quantidade"] is None


def test_quantidade_valida_vira_int():
    assert validar(registo(quantidade=3.0))["quantidade"] == 3


@pytest.mark.parametrize("campo", ["numero_encomenda", "operador"])
def test_obrigatorio_vazio(campo):
    with pytest.raises(ErroValidacao):
        validar(registo(**{campo: "  "}))


@pytest.mark.parametrize("campo", ["data", "hora_picking"])
def test_data_hora_em_falta(campo):
    with pytest.raises(ErroValidacao):
        validar(registo(**{campo: None}))


def test_tipo_invalido():
    with pytest.raises(ErroValidacao):
        validar(registo(tipo_erro="Outro"))


@pytest.mark.parametrize("q", [0, -2])
def test_quantidade_nao_positiva(q):
    with pytest.raises(ErroValidacao):
        validar(registo(quantidade=q))


def test_vazios_do_pandas_viram_none():
    import pandas as pd

    r = validar(registo(produto=float("nan"), observacao=pd.NA, quantidade=pd.NA))
    assert r["produto"] is None and r["observacao"] is None and r["quantidade"] is None


@pytest.mark.parametrize("campo", ["numero_encomenda", "operador"])
def test_texto_obrigatorio_nan_rejeitado(campo):
    with pytest.raises(ErroValidacao):
        validar(registo(**{campo: float("nan")}))


@pytest.mark.parametrize("campo", ["data", "hora_picking"])
def test_data_hora_nat_rejeitada(campo):
    import pandas as pd

    with pytest.raises(ErroValidacao):
        validar(registo(**{campo: pd.NaT}))
