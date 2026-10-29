"""Controlo de Erros de Encomendas — interface Streamlit."""

from datetime import timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import analise
from db import SqliteRepo, obter_repo
from horario import agora_local
from validacao import TIPOS_ERRO, ErroValidacao, validar

st.set_page_config(page_title="Controlo de Erros", page_icon="📦", layout="wide")

CORES = {"Troca": "#4C78A8", "Falta": "#E45756", "Excesso": "#F2A541"}
MSG_SEM_LIGACAO = "Sem ligação à base de dados, tente novamente."


def ler_secrets() -> dict:
    try:
        return dict(st.secrets)
    except Exception:  # sem ficheiro secrets.toml (uso local)
        return {}


SECRETS = ler_secrets()


@st.cache_resource
def repo():
    return obter_repo(SECRETS)


def login() -> bool:
    senha = SECRETS.get("APP_PASSWORD")
    if SECRETS.get("SUPABASE_URL") and not senha:
        # Na nuvem nunca abrir os dados sem palavra-passe.
        st.error("Falta definir APP_PASSWORD nos secrets do Streamlit. O app está bloqueado até lá.")
        return False
    if not senha or st.session_state.get("autenticado"):
        return True
    st.title("📦 Controlo de Erros de Encomendas")
    with st.form("login"):
        tentativa = st.text_input("Palavra-passe", type="password")
        if st.form_submit_button("Entrar"):
            if tentativa == senha:
                st.session_state["autenticado"] = True
                st.rerun()
            st.error("Palavra-passe incorreta.")
    return False


# ---------------------------------------------------------------- Registar erro

def pagina_registar():
    st.header("Registar erro")
    # Chaves novas a cada gravação bem-sucedida = formulário limpo; num erro mantêm-se os valores.
    n = st.session_state.setdefault("form_n", 0)
    if msg := st.session_state.pop("msg_sucesso", None):
        st.success(msg)

    try:
        operadores = repo().operadores()
    except Exception:
        operadores = []
        st.warning(MSG_SEM_LIGACAO)

    agora = agora_local().replace(second=0, microsecond=0, tzinfo=None)
    with st.form("registar"):
        c1, c2 = st.columns(2)
        data_ = c1.date_input("Data", value=agora.date(), format="DD/MM/YYYY", key=f"f_data_{n}")
        hora = c2.time_input("Hora do picking", value=agora.time(), step=60, key=f"f_hora_{n}")
        numero = st.text_input("N.º da encomenda *", key=f"f_numero_{n}")
        c1, c2 = st.columns(2)
        operador = c1.selectbox("Operador de picking *", operadores, index=None,
                                placeholder="Escolha um operador…", key=f"f_operador_{n}")
        novo = c2.text_input("…ou escreva um novo operador", key=f"f_novo_operador_{n}")
        tipo = st.radio("Tipo de erro *", TIPOS_ERRO, horizontal=True, key=f"f_tipo_{n}")
        c1, c2 = st.columns([3, 1])
        produto = c1.text_input("Produto (referência ou nome)", key=f"f_produto_{n}")
        quantidade = c2.number_input("Quantidade", min_value=0, step=1, value=0, key=f"f_quantidade_{n}",
                                     help="Deixe 0 se não se aplica.")
        obs = st.text_area("Observação", key=f"f_obs_{n}")
        gravar = st.form_submit_button("Gravar erro", type="primary")

    if not gravar:
        return
    try:
        registo = validar({
            "data": data_, "numero_encomenda": numero,
            "operador": novo if novo.strip() else operador,
            "hora_picking": hora, "tipo_erro": tipo, "produto": produto,
            "quantidade": quantidade or None, "observacao": obs,
        })
    except ErroValidacao as e:
        st.error(str(e))
        return
    try:
        repo().inserir(registo)
    except Exception:
        st.error(MSG_SEM_LIGACAO)
        return
    st.session_state["form_n"] += 1
    st.session_state["msg_sucesso"] = (
        f"Erro gravado: encomenda {registo['numero_encomenda']} — {registo['operador']} — {registo['tipo_erro']}.")
    st.rerun()


# ---------------------------------------------------------------- Painel

def carregar(inicio=None, fim=None) -> pd.DataFrame | None:
    try:
        return repo().listar(inicio, fim)
    except Exception:
        st.error(MSG_SEM_LIGACAO)
        return None


def pagina_painel():
    st.header("Painel de erros")
    hoje = agora_local().date()
    with st.sidebar:
        st.subheader("Filtros")
        periodo = st.date_input("Período", value=(hoje - timedelta(days=30), hoje), format="DD/MM/YYYY")
        inicio, fim = (periodo[0], periodo[-1]) if isinstance(periodo, (tuple, list)) and periodo else (None, None)

    df = carregar(inicio, fim)
    if df is None:
        return
    with st.sidebar:
        operadores = st.multiselect("Operador", sorted(df["operador"].unique()), placeholder="Todos")
        tipos = st.multiselect("Tipo de erro", TIPOS_ERRO, placeholder="Todos")
    df = analise.filtrar(df, operadores, tipos)

    if df.empty:
        st.info("Ainda não há registos para os filtros escolhidos.")
        return

    k = analise.kpis(df)
    cols = st.columns(4)
    cols[0].metric("Total de erros", k["total"])
    for col, t in zip(cols[1:], TIPOS_ERRO):
        col.metric(t, f"{k[t]}  ({k[t] / k['total']:.0%})")

    c1, c2 = st.columns(2)
    fig = px.bar(analise.por_tipo(df), x="tipo_erro", y="erros", color="tipo_erro",
                 color_discrete_map=CORES, title="Erros por tipo",
                 labels={"tipo_erro": "Tipo", "erros": "Erros"})
    c1.plotly_chart(fig.update_layout(showlegend=False), width="stretch")

    horas = analise.por_hora(df)
    fig = px.bar(horas, x="hora", y="erros", title="Erros por hora do picking",
                 labels={"hora": "Hora", "erros": "Erros"})
    fig.update_xaxes(tickmode="array", tickvals=horas["hora"], ticktext=[f"{h}h" for h in horas["hora"]])
    c2.plotly_chart(fig, width="stretch")

    c1, c2 = st.columns(2)
    fig = px.bar(analise.por_operador_tipo(df), x="operador", y="erros", color="tipo_erro",
                 color_discrete_map=CORES, title="Erros por operador",
                 labels={"operador": "Operador", "erros": "Erros", "tipo_erro": "Tipo"})
    c1.plotly_chart(fig, width="stretch")

    mapa = analise.mapa_operador_hora(df)
    fig = px.imshow(mapa, text_auto=True, aspect="auto", color_continuous_scale="Reds",
                    title="Mapa de calor: operador × hora",
                    labels={"x": "Hora", "y": "Operador", "color": "Erros"},
                    x=[f"{h}h" for h in mapa.columns])
    c2.plotly_chart(fig, width="stretch")

    fig = px.line(analise.evolucao_diaria(df), x="data", y="erros", markers=True,
                  title="Evolução diária", labels={"data": "Data", "erros": "Erros"})
    st.plotly_chart(fig, width="stretch")

    st.subheader("Registos")
    st.dataframe(df.drop(columns=["id", "criado_em"]), hide_index=True, width="stretch",
                 column_config=COLUNAS_TABELA)
    st.download_button("📥 Exportar Excel", analise.para_excel(df), "erros_encomendas.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


COLUNAS_TABELA = {
    "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
    "numero_encomenda": "Encomenda",
    "operador": "Operador",
    "hora_picking": st.column_config.TimeColumn("Hora", format="HH:mm"),
    "tipo_erro": "Tipo",
    "produto": "Produto",
    "quantidade": "Qtd.",
    "observacao": "Observação",
}


# ---------------------------------------------------------------- Gerir registos

def pagina_gerir():
    st.header("Gerir registos")
    df = carregar()
    if df is None:
        return
    if df.empty:
        st.info("Ainda não há registos.")
        return

    if msg := st.session_state.pop("msg_sucesso", None):
        st.success(msg)
    # Chaves novas após cada gravação: o editor e a caixa de apagar recomeçam limpos.
    n = st.session_state.setdefault("gerir_n", 0)
    st.caption("Edite diretamente na tabela e carregue em **Guardar alterações**.")
    editado = st.data_editor(
        df, hide_index=True, width="stretch", key=f"editor_{n}",
        disabled=["id", "criado_em"],
        column_config={**COLUNAS_TABELA,
                       "id": "N.º", "criado_em": None,
                       "tipo_erro": st.column_config.SelectboxColumn("Tipo", options=TIPOS_ERRO, required=True)},
    )
    if st.button("Guardar alterações", type="primary"):
        alterados, falhou = 0, False
        for posicao in st.session_state[f"editor_{n}"]["edited_rows"]:
            depois = editado.iloc[int(posicao)]
            try:
                repo().atualizar(int(depois["id"]), validar(depois.to_dict()))
                alterados += 1
            except ErroValidacao as e:
                st.error(f"Registo n.º {depois['id']}: {e}")
                falhou = True
            except Exception:
                st.error(MSG_SEM_LIGACAO)
                falhou = True
                break
        if falhou:
            # Sem recarregar: os erros ficam visíveis e as edições por corrigir mantêm-se na tabela.
            if alterados:
                st.success(f"{alterados} registo(s) atualizado(s); corrija os restantes e guarde de novo.")
        elif alterados:
            st.session_state["msg_sucesso"] = f"{alterados} registo(s) atualizado(s)."
            st.session_state["gerir_n"] += 1
            st.rerun()

    st.divider()
    st.subheader("Apagar registo")
    opcoes = {int(r.id): f"N.º {r.id} — {r.data:%d/%m/%Y} {r.hora_picking:%H:%M} — "
                         f"{r.numero_encomenda} — {r.operador} — {r.tipo_erro}"
              for r in df.itertuples()}
    escolhido = st.selectbox("Registo", list(opcoes), format_func=opcoes.get, index=None,
                             placeholder="Escolha o registo a apagar…", key=f"apagar_{n}")
    confirmar = st.checkbox("Confirmo que quero apagar este registo", key=f"confirmar_{n}")
    if st.button("Apagar", disabled=not (escolhido and confirmar)):
        try:
            repo().apagar(escolhido)
        except Exception:
            st.error(MSG_SEM_LIGACAO)
            return
        st.session_state["msg_sucesso"] = f"Registo n.º {escolhido} apagado."
        st.session_state["gerir_n"] += 1
        st.rerun()


# ---------------------------------------------------------------- Navegação

if login():
    with st.sidebar:
        st.title("📦 Controlo de Erros")
        pagina = st.radio("Menu", ["Registar erro", "Painel", "Gerir registos"], label_visibility="collapsed")
        if isinstance(repo(), SqliteRepo):
            st.caption("💾 Modo local: dados guardados em dados.db neste computador.")
        st.divider()
    {"Registar erro": pagina_registar, "Painel": pagina_painel, "Gerir registos": pagina_gerir}[pagina]()
