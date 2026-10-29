"""Cálculos do painel sobre o DataFrame devolvido por Repo.listar()."""

from io import BytesIO

import pandas as pd

from validacao import TIPOS_ERRO


def filtrar(df: pd.DataFrame, operadores: list[str], tipos: list[str]) -> pd.DataFrame:
    if operadores:
        df = df[df["operador"].isin(operadores)]
    if tipos:
        df = df[df["tipo_erro"].isin(tipos)]
    return df


def kpis(df: pd.DataFrame) -> dict:
    contagem = df["tipo_erro"].value_counts()
    return {"total": len(df), **{t: int(contagem.get(t, 0)) for t in TIPOS_ERRO}}


def por_tipo(df: pd.DataFrame) -> pd.DataFrame:
    contagem = df["tipo_erro"].value_counts().reindex(TIPOS_ERRO, fill_value=0)
    return contagem.rename_axis("tipo_erro").reset_index(name="erros")


def _horas(df: pd.DataFrame) -> pd.Series:
    return df["hora_picking"].map(lambda h: h.hour).astype(int)


def por_hora(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame({"hora": pd.Series(dtype=int), "erros": pd.Series(dtype=int)})
    return _horas(df).value_counts().sort_index().rename_axis("hora").reset_index(name="erros")


def por_operador_tipo(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby(["operador", "tipo_erro"]).size().reset_index(name="erros")


def mapa_operador_hora(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    return pd.crosstab(df["operador"], _horas(df).rename("hora"))


def evolucao_diaria(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("data").size().reset_index(name="erros")


def para_excel(df: pd.DataFrame) -> bytes:
    saida = BytesIO()
    tabela = df.copy()
    tabela["hora_picking"] = tabela["hora_picking"].map(lambda h: h.strftime("%H:%M"))
    tabela.to_excel(saida, sheet_name="Erros", index=False)
    return saida.getvalue()
