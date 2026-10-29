"""Normalização e validação de um registo de erro de encomenda."""

import pandas as pd

TIPOS_ERRO = ["Troca", "Falta", "Excesso"]


class ErroValidacao(ValueError):
    pass


def normalizar_operador(nome: str) -> str:
    return " ".join(str(nome or "").split()).title()


def _vazio(valor) -> bool:
    """None, NaN e pd.NA (vindos da tabela editável) contam como vazios."""
    return valor is None or (pd.api.types.is_scalar(valor) and bool(pd.isna(valor)))


def _texto_opcional(valor):
    if _vazio(valor):
        return None
    texto = str(valor).strip()
    return texto or None


def validar(dados: dict) -> dict:
    numero = str(dados.get("numero_encomenda") or "").strip()
    operador = normalizar_operador(dados.get("operador"))
    tipo = dados.get("tipo_erro")

    if not numero:
        raise ErroValidacao("Indique o número da encomenda.")
    if not operador:
        raise ErroValidacao("Indique o operador de picking.")
    if dados.get("data") is None:
        raise ErroValidacao("Indique a data.")
    if dados.get("hora_picking") is None:
        raise ErroValidacao("Indique a hora do picking.")
    if tipo not in TIPOS_ERRO:
        raise ErroValidacao("Escolha o tipo de erro: Troca, Falta ou Excesso.")

    quantidade = dados.get("quantidade")
    if not _vazio(quantidade):
        quantidade = int(quantidade)
        if quantidade < 1:
            raise ErroValidacao("A quantidade tem de ser maior que zero.")
    else:
        quantidade = None

    return {
        "data": dados["data"],
        "numero_encomenda": numero,
        "operador": operador,
        "hora_picking": dados["hora_picking"],
        "tipo_erro": tipo,
        "produto": _texto_opcional(dados.get("produto")),
        "quantidade": quantidade,
        "observacao": _texto_opcional(dados.get("observacao")),
    }
