# Controlo de Erros de Encomendas — Design

Data: 2026-10-29

## Objetivo

Aplicação de uso exclusivo do chefe para registar manualmente erros de encomendas
e analisar quando e com quem acontecem: tipo de erro (troca, falta, excesso),
hora do picking e operador.

**Sucesso:** o chefe regista um erro em menos de 30 segundos e, no painel, vê de
imediato as horas críticas, os operadores com mais erros e a distribuição por tipo.

## Decisões

| Decisão | Escolha | Porquê |
|---|---|---|
| Interface | Streamlit (Python) | Um só programa com formulário e gráficos, sem frontend separado |
| Base de dados | Supabase (Postgres, plano gratuito) | Dados na nuvem, sem risco de perda local |
| Alternativa local | SQLite automático quando não há chaves do Supabase | Testar já no PC, sem contas |
| Alojamento | Streamlit Community Cloud (gratuito) | Link acessível no PC/telemóvel sem instalar nada |
| Acesso | Palavra-passe única (Streamlit secrets) | Uso de uma só pessoa; sem gestão de utilizadores |
| Gráficos | Plotly | Interativos (hover, zoom), nativos no Streamlit |

Fora do âmbito: vários utilizadores, importação de dados de ERP, registo de
pickings sem erro (taxa de erro), Power BI.

## Modelo de dados

Tabela única `erros_encomendas`:

| Coluna | Tipo | Obrigatório | Notas |
|---|---|---|---|
| id | inteiro, auto | sim | chave primária |
| data | date | sim | dia do picking |
| numero_encomenda | texto | sim | ex.: ENC-10452 |
| operador | texto | sim | normalizado: espaços aparados, "Título" (joão → João) |
| hora_picking | time | sim | HH:MM |
| tipo_erro | texto | sim | um de: `Troca`, `Falta`, `Excesso` |
| produto | texto | não | referência ou nome |
| quantidade | inteiro | não | ≥ 1 quando preenchido |
| observacao | texto | não | livre |
| criado_em | timestamp | sim | automático |

## Componentes

- **`db.py`** — camada de dados com interface única:
  `inserir(registo)`, `listar(filtros)`, `atualizar(id, campos)`, `apagar(id)`,
  `operadores()`. Duas implementações (`SupabaseRepo`, `SqliteRepo`); a função
  `obter_repo()` escolhe Supabase se existirem `SUPABASE_URL` e `SUPABASE_KEY`
  nos secrets, senão SQLite (`dados.db`).
- **`validacao.py`** — normalização e validação de um registo (campos
  obrigatórios, tipo de erro válido, quantidade positiva). Sem dependências de UI.
- **`analise.py`** — funções puras sobre um DataFrame: KPIs, erros por tipo,
  por hora, por operador×tipo, mapa de calor operador×hora, evolução diária.
- **`app.py`** — interface Streamlit: login, navegação lateral com 3 páginas.
- **`schema.sql`** — SQL para criar a tabela no Supabase.
- **`README.md`** — guia em português: correr localmente e publicar
  (Supabase → GitHub → Streamlit Cloud).

## Ecrãs

1. **Registar erro** — formulário com os campos acima; data e hora pré-preenchidas
   com o momento atual; operador com sugestões dos nomes já usados (ou novo nome);
   mensagem de confirmação e formulário limpo após gravar.
2. **Painel** — filtros (intervalo de datas, operador, tipo); KPIs (total, troca,
   falta, excesso); gráficos: barras por tipo, barras por hora do picking,
   barras empilhadas operador×tipo, mapa de calor operador×hora, linha diária;
   tabela de registos e botão "Exportar Excel".
3. **Gerir registos** — tabela editável (corrigir campos) e apagar com confirmação.

## Tratamento de erros

- Validação antes de gravar; mensagens claras em português no formulário.
- Falha de ligação ao Supabase: mensagem amigável ("Sem ligação à base de dados,
  tente novamente") sem perder o que foi escrito no formulário.
- Painel sem dados: mensagem "Ainda não há registos" em vez de gráficos vazios.

## Testes

- `pytest` para `validacao.py`, `analise.py` e `SqliteRepo` (base em memória).
- Verificação manual da interface localmente com dados de exemplo
  (`seed.py` gera ~100 registos fictícios para demonstrar o painel).
