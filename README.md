# 📦 Controlo de Erros de Encomendas

App para registar erros de encomendas (**Troca**, **Falta**, **Excesso**) e analisar
quando e com quem acontecem: hora do picking, operador e evolução no tempo.

- **Registar erro** — formulário rápido (data, encomenda, operador, hora, tipo, produto, quantidade, observação).
- **Painel** — totais, erros por tipo, por hora do picking, por operador, mapa de calor operador × hora,
  evolução diária, tabela e exportação para Excel.
- **Gerir registos** — corrigir ou apagar registos.

---

## 1. Usar no próprio PC (sem contas)

Precisa do [Python 3.12+](https://www.python.org/downloads/) instalado.

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\streamlit run app.py
```

Depois da primeira instalação, basta fazer **duplo clique em `iniciar.bat`**.

Os dados ficam no ficheiro `dados.db`, nesta pasta. Faça cópias de segurança deste ficheiro.

Para ver o painel com dados fictícios: `.venv\Scripts\python seed.py`.
Apague o `dados.db` antes de começar a usar a sério.

---

## 2. Publicar na internet (acesso pelo link, no PC ou telemóvel)

Tudo gratuito. Faz-se uma única vez, em cerca de 20 minutos.

### 2.1 Supabase (base de dados)

1. Crie conta em <https://supabase.com> → **New project** (escolha a região *Europe*; guarde a palavra-passe da base de dados).
2. No menu lateral, **SQL Editor** → **New query** → cole o conteúdo de [`schema.sql`](schema.sql) → **Run**.
3. **Project Settings → API**: copie o **Project URL** e a chave **`service_role`** (secreta: nunca a partilhe nem a coloque no código).

### 2.2 GitHub (guardar o código)

1. Crie conta em <https://github.com> → **New repository** → marque **Private**.
2. Envie esta pasta para o repositório (por exemplo com o GitHub Desktop, ou `git remote add origin <url>` e `git push -u origin main`).
   Os ficheiros `dados.db` e `.streamlit/secrets.toml` não são enviados (estão no `.gitignore`).

### 2.3 Streamlit Community Cloud (alojamento)

1. Entre em <https://share.streamlit.io> com a conta do GitHub → **Create app** → escolha o repositório, branch `main`, ficheiro `app.py`.
2. Em **Advanced settings**: Python 3.12 e, em **Secrets**, cole (com os seus valores):

   ```toml
   APP_PASSWORD = "uma-palavra-passe-para-o-chefe"
   SUPABASE_URL = "https://xxxxxxxx.supabase.co"
   SUPABASE_KEY = "chave service_role"
   ```

3. **Deploy**. Em 1–2 minutos recebe um link `https://<nome>.streamlit.app` — envie-o ao chefe com a palavra-passe.

> Apps gratuitas do Streamlit "adormecem" após uns dias sem uso; ao abrir o link, basta carregar em
> *"Yes, get this app back up"* e esperar uns segundos. Os dados ficam no Supabase, não se perdem.
>
> No plano gratuito do Supabase, um projeto sem atividade durante 7 dias é pausado; reative-o no painel do Supabase.

---

## Para quem mantém o código

| Ficheiro | Função |
|---|---|
| `app.py` | Interface Streamlit (login, 3 páginas) |
| `db.py` | Acesso aos dados: Supabase se houver `SUPABASE_URL`/`SUPABASE_KEY` nos secrets, senão SQLite (`dados.db`) |
| `validacao.py` | Validação e normalização dos registos (ex.: `" joão "` → `"João"`) |
| `analise.py` | Cálculos do painel e exportação Excel |
| `schema.sql` | Criação da tabela no Supabase |
| `seed.py` | Dados fictícios para demonstração |

Testes: `.venv\Scripts\python -m pytest`
