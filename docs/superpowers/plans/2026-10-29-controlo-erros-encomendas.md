# Controlo de Erros de Encomendas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** App Streamlit para o chefe registar erros de encomendas e analisá-los por tipo, hora do picking e operador.

**Architecture:** `validacao.py` e `analise.py` são funções puras; `db.py` expõe um repositório com duas implementações (SQLite local / Supabase) escolhidas por `obter_repo()`; `app.py` é só interface. Testes com pytest sobre as partes puras e o SQLite.

**Tech Stack:** Python 3.11+, Streamlit, pandas, plotly, supabase-py, openpyxl, pytest.

**Spec:** `docs/superpowers/specs/2026-10-29-controlo-erros-encomendas-design.md`

## Global Constraints

- Todo o texto visível ao utilizador em português de Portugal.
- Tipos de erro exatamente: `Troca`, `Falta`, `Excesso`.
- Tabela única `erros_encomendas` com as colunas da spec (`id, data, numero_encomenda, operador, hora_picking, tipo_erro, produto, quantidade, observacao, criado_em`).
- Supabase só é usado se `SUPABASE_URL` e `SUPABASE_KEY` existirem em `st.secrets`; caso contrário SQLite em `dados.db`.
- Palavra-passe em `st.secrets["APP_PASSWORD"]`; se não existir (uso local), o login é saltado.
- `dados.db` e `.streamlit/secrets.toml` nunca vão para o git.

## Review Focus

1. Operador escrito com espaços/maiúsculas diferentes ("  joão ", "JOÃO") → tem de contar como a mesma pessoa "João" (teste em Task 1).
2. Painel com filtros que não devolvem registos → mensagem "Ainda não há registos", sem exceções do plotly (teste em Task 3 sobre DataFrame vazio).
3. Quantidade 0 ou negativa → rejeitada com mensagem; vazia → aceite como `None` (teste em Task 1).
4. Hora/data vindas do Supabase chegam como texto (`"14:35:00"`, `"2026-10-29"`) → `listar()` devolve sempre `date`/`time` (teste em Task 2 sobre o conversor partilhado).
5. Falha de rede no Supabase ao gravar → mensagem amigável e o formulário mantém os valores (verificação manual em Task 4: `st.form(clear_on_submit=False)` e limpar só após sucesso).

---

### Task 1: Projeto base + validação

**Files:**
- Create: `requirements.txt`, `.gitignore`, `validacao.py`, `tests/test_validacao.py`

**Interfaces:**
- Produces: `TIPOS_ERRO: list[str] = ["Troca", "Falta", "Excesso"]`; `class ErroValidacao(ValueError)`; `normalizar_operador(nome: str) -> str`; `validar(dados: dict) -> dict` — devolve registo limpo (strings aparadas, opcionais vazios → `None`, `quantidade` int ou `None`) ou lança `ErroValidacao` com mensagem em português.

- [ ] **Step 1:** `git init`; `requirements.txt` com `streamlit`, `pandas`, `plotly`, `supabase`, `openpyxl`, `pytest`; `.gitignore` com `dados.db`, `.streamlit/secrets.toml`, `__pycache__/`, `.venv/`. Criar `.venv` e instalar.
- [ ] **Step 2: Testes que falham**

```python
def test_normaliza_operador():
    assert normalizar_operador("  joão ") == "João"
    assert normalizar_operador("JOÃO  silva") == "João Silva"

def test_valida_registo_minimo():
    r = validar({"data": date(2026,10,29), "numero_encomenda": " ENC-1 ", "operador": "ana",
                 "hora_picking": time(14,35), "tipo_erro": "Falta", "produto": "", "quantidade": None, "observacao": ""})
    assert r["numero_encomenda"] == "ENC-1" and r["operador"] == "Ana"
    assert r["produto"] is None and r["observacao"] is None and r["quantidade"] is None

@pytest.mark.parametrize("campo", ["numero_encomenda", "operador"])
def test_obrigatorio_vazio(campo): ...  # valor "  " -> ErroValidacao

def test_tipo_invalido(): ...           # "Outro" -> ErroValidacao
@pytest.mark.parametrize("q", [0, -2])
def test_quantidade_nao_positiva(q): ... # -> ErroValidacao
```

- [ ] **Step 3:** `pytest tests/test_validacao.py -v` → FAIL (import).
- [ ] **Step 4:** Implementar `validacao.py` (`normalizar_operador`: `" ".join(nome.split()).title()`).
- [ ] **Step 5:** `pytest tests/test_validacao.py -v` → PASS. Commit `feat: validação de registos`.

### Task 2: Camada de dados (SQLite + Supabase)

**Files:**
- Create: `db.py`, `schema.sql`, `tests/test_db.py`

**Interfaces:**
- Consumes: registo validado de `validar()`.
- Produces: classe base `Repo` com
  `inserir(registo: dict) -> int`, `listar(inicio: date | None = None, fim: date | None = None) -> pd.DataFrame` (colunas da tabela, `data` como `date`, `hora_picking` como `time`, ordenado por data e hora desc),
  `atualizar(id: int, campos: dict) -> None`, `apagar(id: int) -> None`, `operadores() -> list[str]` (distintos, ordenados).
  `SqliteRepo(caminho: str = "dados.db")`, `SupabaseRepo(url: str, key: str)`, `obter_repo(secrets: Mapping) -> Repo`, `_normalizar_df(df) -> pd.DataFrame` (converte texto → date/time; partilhado pelos dois repos).

- [ ] **Step 1: Testes que falham** (SqliteRepo com `":memory:"`, usar uma ligação persistente por instância)

```python
def test_inserir_e_listar(repo): id = repo.inserir(REG); df = repo.listar(); assert len(df)==1 and df.iloc[0]["id"]==id
def test_listar_filtra_datas(repo): ...   # registos 01/10 e 29/10; listar(date(2026,10,15), None) -> só 29/10
def test_atualizar(repo): ...             # tipo_erro -> "Excesso"
def test_apagar(repo): ...                # listar() vazio
def test_operadores_distintos(repo): ...  # ["Ana","João"]
def test_listar_vazio_tem_colunas(repo): assert list(repo.listar().columns) == COLUNAS
def test_normalizar_df_converte_texto():
    df = _normalizar_df(pd.DataFrame([{**REG_TEXTO, "data": "2026-10-29", "hora_picking": "14:35:00"}]))
    assert df.iloc[0]["data"] == date(2026,10,29) and df.iloc[0]["hora_picking"] == time(14,35)
def test_obter_repo_sem_chaves_usa_sqlite(): assert isinstance(obter_repo({}), SqliteRepo)
```

- [ ] **Step 2:** `pytest tests/test_db.py -v` → FAIL.
- [ ] **Step 3:** Implementar `SqliteRepo` (CREATE TABLE IF NOT EXISTS; datas/horas guardadas como ISO texto) e `_normalizar_df`.
- [ ] **Step 4:** Implementar `SupabaseRepo` com `supabase.create_client`; `.table("erros_encomendas")` com `.insert/.select().gte/.lte/.update/.delete().eq("id", id)`; serializar date/time com `isoformat()`. Sem teste automático (precisa de rede) — verificado manualmente no Task 5.
- [ ] **Step 5:** `schema.sql`: `create table erros_encomendas (id bigint generated always as identity primary key, data date not null, numero_encomenda text not null, operador text not null, hora_picking time not null, tipo_erro text not null check (tipo_erro in ('Troca','Falta','Excesso')), produto text, quantidade int check (quantidade > 0), observacao text, criado_em timestamptz not null default now());`
- [ ] **Step 6:** `pytest -v` → PASS. Commit `feat: repositório SQLite/Supabase`.

### Task 3: Análise

**Files:**
- Create: `analise.py`, `tests/test_analise.py`

**Interfaces:**
- Consumes: DataFrame de `Repo.listar()`.
- Produces:
  `filtrar(df, operadores: list[str], tipos: list[str]) -> DataFrame` (lista vazia = sem filtro);
  `kpis(df) -> dict` com chaves `total, Troca, Falta, Excesso`;
  `por_tipo(df) -> DataFrame[tipo_erro, erros]` (sempre os 3 tipos, 0 se ausente);
  `por_hora(df) -> DataFrame[hora, erros]` (hora inteira 0–23 a partir de `hora_picking`, só horas com dados);
  `por_operador_tipo(df) -> DataFrame[operador, tipo_erro, erros]`;
  `mapa_operador_hora(df) -> DataFrame` (índice operador, colunas horas, valores contagem, 0 nos vazios);
  `evolucao_diaria(df) -> DataFrame[data, erros]`;
  `para_excel(df) -> bytes` (openpyxl, folha "Erros").

- [ ] **Step 1: Testes que falham** com um DataFrame de 5 registos fixos (Ana 09:10 Troca, Ana 09:50 Falta, João 14:35 Falta, João 14:05 Falta, João 16:20 Excesso):

```python
assert kpis(df) == {"total":5,"Troca":1,"Falta":3,"Excesso":1}
assert por_hora(df).set_index("hora")["erros"].to_dict() == {9:2,14:2,16:1}
assert mapa_operador_hora(df).loc["Ana",14] == 0
assert por_tipo(df.iloc[0:1]).set_index("tipo_erro")["erros"].to_dict() == {"Troca":1,"Falta":0,"Excesso":0}
assert len(filtrar(df, ["Ana"], [])) == 2
# DataFrame vazio (colunas de COLUNAS): todas as funções correm sem exceção e kpis == {"total":0,"Troca":0,"Falta":0,"Excesso":0}
assert para_excel(df)[:2] == b"PK"
```

- [ ] **Step 2:** `pytest tests/test_analise.py -v` → FAIL.
- [ ] **Step 3:** Implementar com pandas `groupby`/`pivot_table(fill_value=0)`.
- [ ] **Step 4:** `pytest -v` → PASS. Commit `feat: funções de análise`.

### Task 4: Interface Streamlit + dados de exemplo

**Files:**
- Create: `app.py`, `seed.py`, `.streamlit/secrets.toml.example`

**Interfaces:**
- Consumes: `obter_repo`, `validar`, `ErroValidacao`, `TIPOS_ERRO`, todas as funções de `analise`.
- Produces: `seed.py` com `main(n: int = 100)` que insere `n` registos aleatórios (operadores Ana, João, Marta, Pedro, Rui; horas 07–19 com pico 11–12 e 17; últimos 30 dias) via `obter_repo({})`.

- [ ] **Step 1:** `app.py`: `st.set_page_config(page_title="Controlo de Erros", layout="wide")`; repo em `@st.cache_resource`; login se `APP_PASSWORD` em secrets (guardar em `st.session_state["autenticado"]`); `st.sidebar.radio` com "Registar erro", "Painel", "Gerir registos".
- [ ] **Step 2: Registar erro** — `st.form` com data (hoje), nº encomenda, operador (`st.selectbox` com `operadores()` + opção "➕ Novo operador" que mostra `text_input`), hora (agora), tipo (`st.radio` horizontal), produto, quantidade (`number_input` min 0, 0 = vazio), observação. Ao submeter: `validar` → `inserir` → `st.success`; `ErroValidacao` → `st.error(str(e))`; outra exceção do repo → `st.error("Sem ligação à base de dados, tente novamente.")` mantendo valores.
- [ ] **Step 3: Painel** — filtros na sidebar (intervalo de datas, últimos 30 dias por defeito; multiselect operador e tipo); se vazio → `st.info("Ainda não há registos")` e parar; 4 `st.metric`; gráficos plotly: barras por tipo, barras por hora, barras empilhadas operador×tipo, `px.imshow` do mapa, linha diária; `st.dataframe` e `st.download_button("Exportar Excel", para_excel(df), "erros_encomendas.xlsx")`. Cores fixas por tipo: Troca, Falta, Excesso.
- [ ] **Step 4: Gerir registos** — `st.data_editor` (coluna `tipo_erro` como `SelectboxColumn(TIPOS_ERRO)`, `id`/`criado_em` desativadas); botão "Guardar alterações" → validar cada linha alterada e `atualizar`; selectbox de id + checkbox de confirmação + botão "Apagar".
- [ ] **Step 5:** `seed.py` e `secrets.toml.example` (`APP_PASSWORD`, `SUPABASE_URL`, `SUPABASE_KEY` comentados).
- [ ] **Step 6: Verificação:** `python seed.py`; `streamlit run app.py`; no browser: registar um erro com operador " joão " (aparece "João"), registar com nº vazio (erro em português), painel mostra os 5 gráficos, filtro sem resultados mostra a mensagem, exportar abre no Excel, editar e apagar um registo. Commit `feat: interface Streamlit`.

### Task 5: Guia de publicação

**Files:**
- Create: `README.md`

- [ ] **Step 1:** README em português: (1) correr localmente (`python -m venv .venv`, instalar, `python seed.py` opcional, `streamlit run app.py`); (2) Supabase: criar projeto, SQL Editor → colar `schema.sql`, copiar URL e chave `service_role` (Settings → API); (3) GitHub: criar repositório privado e enviar código; (4) Streamlit Community Cloud: New app → `app.py` → Advanced settings → Secrets com `APP_PASSWORD`, `SUPABASE_URL`, `SUPABASE_KEY`; (5) partilhar o link com o chefe.
- [ ] **Step 2:** Verificação: com `.streamlit/secrets.toml` local contendo chaves Supabase reais (se o utilizador as fornecer), registar e listar um erro; caso contrário marcar como não verificado. Commit `docs: guia de utilização e publicação`.
