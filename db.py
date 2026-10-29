"""Acesso aos dados: SQLite local ou Supabase (na nuvem)."""

import sqlite3
from datetime import date, time
from typing import Mapping

import pandas as pd

TABELA = "erros_encomendas"
TABELA_OPERADOR = "operador"
COLUNAS = [
    "id", "data", "numero_encomenda", "operador", "hora_picking",
    "tipo_erro", "produto", "quantidade", "observacao", "criado_em",
]


def _para_texto(valor):
    """Datas e horas são guardadas/enviadas em formato ISO."""
    if isinstance(valor, time):
        return valor.strftime("%H:%M:%S")
    if isinstance(valor, date):
        return valor.isoformat()
    return valor


def _normalizar_df(df: pd.DataFrame) -> pd.DataFrame:
    """Garante as colunas da tabela, `data` como date e `hora_picking` como time."""
    df = df.reindex(columns=COLUNAS)
    if df.empty:
        return df
    df["data"] = pd.to_datetime(df["data"]).dt.date
    df["hora_picking"] = pd.to_datetime(df["hora_picking"].astype(str), format="mixed").dt.time
    df["quantidade"] = df["quantidade"].astype("Int64")
    return df.sort_values(["data", "hora_picking"], ascending=False).reset_index(drop=True)


def _ordenar(nomes) -> list[str]:
    return sorted(set(nomes), key=str.casefold)


class Repo:
    def adicionar_operador(self, nome: str) -> None:
        """Acrescenta o nome à tabela operador, se ainda não existir (sem distinguir maiúsculas)."""
        nome = " ".join(nome.split())
        if nome and nome.casefold() not in {o.casefold() for o in self.operadores()}:
            self._inserir_operador(nome)

    def _inserir_operador(self, nome: str) -> None: ...
    def inserir(self, registo: dict) -> int: ...
    def listar(self, inicio: date | None = None, fim: date | None = None) -> pd.DataFrame: ...
    def atualizar(self, id: int, campos: dict) -> None: ...
    def apagar(self, id: int) -> None: ...
    def operadores(self) -> list[str]: ...


class SqliteRepo(Repo):
    def __init__(self, caminho: str = "dados.db"):
        self.con = sqlite3.connect(caminho, check_same_thread=False)
        self.con.execute(f"""
            create table if not exists {TABELA} (
                id integer primary key autoincrement,
                data text not null,
                numero_encomenda text not null,
                operador text not null,
                hora_picking text not null,
                tipo_erro text not null check (tipo_erro in ('Troca','Falta','Excesso')),
                produto text,
                quantidade integer check (quantidade > 0),
                observacao text,
                criado_em text not null default current_timestamp
            )""")
        self.con.execute(f"create table if not exists {TABELA_OPERADOR} "
                         "(id integer primary key autoincrement, nome text not null)")
        self.con.commit()

    def inserir(self, registo: dict) -> int:
        campos = list(registo)
        cur = self.con.execute(
            f"insert into {TABELA} ({', '.join(campos)}) values ({', '.join('?' * len(campos))})",
            [_para_texto(registo[c]) for c in campos],
        )
        self.con.commit()
        return cur.lastrowid

    def listar(self, inicio=None, fim=None) -> pd.DataFrame:
        condicoes, params = [], []
        if inicio:
            condicoes.append("data >= ?")
            params.append(inicio.isoformat())
        if fim:
            condicoes.append("data <= ?")
            params.append(fim.isoformat())
        where = f" where {' and '.join(condicoes)}" if condicoes else ""
        df = pd.read_sql_query(f"select * from {TABELA}{where}", self.con, params=params)
        return _normalizar_df(df)

    def atualizar(self, id: int, campos: dict) -> None:
        sets = ", ".join(f"{c} = ?" for c in campos)
        self.con.execute(f"update {TABELA} set {sets} where id = ?",
                         [_para_texto(v) for v in campos.values()] + [id])
        self.con.commit()

    def apagar(self, id: int) -> None:
        self.con.execute(f"delete from {TABELA} where id = ?", [id])
        self.con.commit()

    def operadores(self) -> list[str]:
        linhas = self.con.execute(f"select operador from {TABELA} union select nome from {TABELA_OPERADOR}")
        return _ordenar(l[0] for l in linhas)

    def _inserir_operador(self, nome: str) -> None:
        self.con.execute(f"insert into {TABELA_OPERADOR} (nome) values (?)", [nome])
        self.con.commit()


class SupabaseRepo(Repo):
    def __init__(self, url: str, key: str):
        from supabase import create_client

        self.tabela = create_client(url, key).table

    def inserir(self, registo: dict) -> int:
        dados = {k: _para_texto(v) for k, v in registo.items()}
        return self.tabela(TABELA).insert(dados).execute().data[0]["id"]

    def _todas(self, colunas: str, inicio=None, fim=None, tabela: str = TABELA) -> list[dict]:
        """O Supabase devolve no máximo 1000 linhas por pedido: lê por páginas."""
        linhas, pagina = [], 1000
        while True:
            consulta = self.tabela(tabela).select(colunas)
            if inicio:
                consulta = consulta.gte("data", inicio.isoformat())
            if fim:
                consulta = consulta.lte("data", fim.isoformat())
            lote = consulta.order("id").range(len(linhas), len(linhas) + pagina - 1).execute().data
            linhas += lote
            if len(lote) < pagina:
                return linhas

    def listar(self, inicio=None, fim=None) -> pd.DataFrame:
        return _normalizar_df(pd.DataFrame(self._todas("*", inicio, fim)))

    def atualizar(self, id: int, campos: dict) -> None:
        dados = {k: _para_texto(v) for k, v in campos.items()}
        self.tabela(TABELA).update(dados).eq("id", id).execute()

    def apagar(self, id: int) -> None:
        self.tabela(TABELA).delete().eq("id", id).execute()

    def operadores(self) -> list[str]:
        usados = (l["operador"] for l in self._todas("operador"))
        da_tabela = (l["nome"] for l in self._todas("nome", tabela=TABELA_OPERADOR))
        return _ordenar([*usados, *da_tabela])

    def _inserir_operador(self, nome: str) -> None:
        self.tabela(TABELA_OPERADOR).insert({"nome": nome}).execute()


def obter_repo(secrets: Mapping) -> Repo:
    if secrets.get("SUPABASE_URL") and secrets.get("SUPABASE_KEY"):
        return SupabaseRepo(secrets["SUPABASE_URL"], secrets["SUPABASE_KEY"])
    return SqliteRepo()
