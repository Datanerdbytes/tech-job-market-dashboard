# Postgres MCP + dbt-mcp Setup — Reproduction Guide

Complete, verified steps to reproduce this environment from scratch on macOS.

**Verified:** 2026-11-08 — all commands below were run and confirmed working.

---

## 0. Summary of what gets installed

| Component | Location | Purpose |
|---|---|---|
| Docker container `postgres-dev` | localhost:5432 | PostgreSQL 16 + `tech_job_market` DB |
| postgres-mcp-server | `~/postgres-mcp-server` | MCP server for raw SQL over PostgreSQL |
| postgres venv (Python 3.15) | `~/postgres-mcp-server/venv` | Deps for postgres MCP server |
| dbt-mcp venv (Python 3.12) | `~/dbt-mcp-venv312` | dbt-mcp 0.10.3 + dbt-postgres 1.11.0 |
| dbt project | `~/dbt_projects/tech_job_market` | 16 models, bronze→silver→gold |
| MCP registrations | `~/.minimax/mcp.json` | Server definitions for the host |

**Key fact:** MCP server *installations* live on disk and are reusable. MCP server *registrations* are per-client (each harness has its own config file). To add these to another harness (e.g. Claude Desktop), copy the registration block — you do **not** reinstall anything.

---

## 1. PostgreSQL via Docker

```bash
docker run -d \
  --name postgres-dev \
  -e POSTGRES_PASSWORD='<POSTGRES_PASSWORD>' \
  -e POSTGRES_DB=tech_job_market \
  -p 5432:5432 \
  postgres:16
```

Verify:
```bash
docker ps --filter name=postgres-dev
```

> **Note:** If the container exists but is stopped, use `docker start postgres-dev` — do not recreate it, or the data is lost.

---

## 2. Postgres MCP server

### 2.1 Clone and create venv

```bash
cd ~
git clone https://github.com/aadarshjain/postgres-mcp-server.git
cd postgres-mcp-server
python3 -m venv venv
source venv/bin/activate
```

### 2.2 Install dependencies — **pin `mcp<2`**

```bash
pip install "mcp<2" fastmcp pg8000 SQLAlchemy
```

> ⚠️ **This pin is critical.** `mcp` 2.x renamed `FastMCP` → `MCPServer` and moved it to
> `mcp.server.mcpserver`. Installing unpinned `mcp` gives you 2.x, and `server.py`
> fails at import with:
>
> ```
> ModuleNotFoundError: No module named 'mcp.server.fastmcp'
> ```
>
> `fastmcp` 4.x also pulls in `mcp` 2.x as a dependency — install `mcp<2` **after**
> `fastmcp`, or reinstall to force the downgrade.
>
> `SQLAlchemy` is also required (`server.py` imports `sqlalchemy.engine.url.make_url`
> for DSN parsing) but is easy to forget since `requirements.txt` lists it.

Verify imports:
```bash
./venv/bin/python -c "import sqlalchemy, pg8000, mcp.server.fastmcp; print('OK')"
```

### 2.3 Confirm the server starts

```bash
./venv/bin/python server.py "postgresql://postgres:<PASSWORD>@localhost:5432/tech_job_market"
```

Expected output includes `Starting PostgreSQL Data Discovery MCP server...`.
Press Ctrl+C to exit — the server waits on stdin.

---

## 3. dbt-mcp server

### 3.1 Python version — **must be 3.9–3.12**

System Python is 3.15, which dbt-mcp does **not** support. Use a 3.12 interpreter.

```bash
# One-time: install Python 3.12 via uv (already present at ~/.local/bin/python3.12)
python3 -m venv ~/dbt-mcp-venv312
source ~/dbt-mcp-venv312/bin/activate
```

### 3.2 Install

```bash
pip install --no-deps dbt-mcp==0.10.3 dbt-postgres==1.11.0
pip install authlib==1.6.4 'requests==2.32.4' 'pyyaml==6.0.2' 'dbt-protos==1.0.382' \
            cryptography urllib3 idna charset-normalizer certifi \
            pydantic==2.7.4 pydantic-core==2.18.4
```

> `--no-deps` is used because a plain `pip install dbt-mcp` resolves to newer
> transitive versions that break on Python 3.12. Dependencies are then pinned
> explicitly to known-good versions.

### 3.3 Required environment variables

dbt-mcp runs `dbt` as a **subprocess**, so it inherits the MCP server's environment.
It needs:

| Variable | Value | Why |
|---|---|---|
| `POSTGRES_PASSWORD` | DB password | Passed through to `dbt` → `profiles.yml` `env_var()` |
| `DBT_PATH` | `/Users/roelsomido/dbt-mcp-venv312/bin/dbt` | Absolute path to the dbt binary. Defaults to bare `"dbt"`, which fails if the venv `bin` is not on `PATH` |
| `DBT_PROJECT_DIR` | `/Users/roelsomido/dbt_projects/tech_job_market` | Required when dbt CLI tools are enabled. Errors out otherwise |
| `DISABLE_SEMANTIC_LAYER` | `true` | See §3.4 |
| `DISABLE_DISCOVERY` | `true` | See §3.4 |
| `DISABLE_ADMIN_API` | `true` | See §3.4 |

### 3.4 Disable the dbt Cloud–dependent tools

**You are not using dbt Cloud.** The `semantic_layer`, `discovery`, and `admin_api`
tool groups are dbt Cloud APIs. When enabled, calling them triggers an OAuth flow
that **opens a browser to a login URL and then hangs** until the 120s MCP timeout.

Symptoms — the server logs:
```
INFO  Opening authorization URL  login.py:73
```
and the tool call never returns.

Setting the three `DISABLE_*` flags above avoids this entirely. The remaining
tools are the **dbt CLI tools**, which work purely locally:

```
build, compile, docs, list, parse, run, test, show
```

These are the tools to use for this project. `get_all_models`, `get_mart_models`,
`query_metrics`, `list_metrics`, `get_model_health`, etc. are dbt Cloud tools and
**will not work**.

### 3.5 Verify the server responds

```bash
export POSTGRES_PASSWORD='<PASSWORD>'
export DBT_PROJECT_DIR=/Users/roelsomido/dbt_projects/tech_job_market
export DBT_PATH=/Users/roelsomido/dbt-mcp-venv312/bin/dbt
export DISABLE_SEMANTIC_LAYER=true DISABLE_DISCOVERY=true DISABLE_ADMIN_API=true

~/dbt-mcp-venv312/bin/dbt-mcp
```

Confirm it starts without attempting OAuth. A `run` tool call should complete in
roughly 5–10 seconds.

---

## 4. dbt project — profiles.yml

The profile lives **inside the project directory** (not `~/.dbt/`), so dbt finds it
automatically when run from the project root.

```yaml
tech_job_market:
  target: dev
  outputs:
    dev:
      type: postgres
      host: 127.0.0.1          # NOT "localhost" — see below
      port: 5432
      user: postgres
      password: "{{ env_var('POSTGRES_PASSWORD') }}"
      dbname: tech_job_market
      schema: jobmarket
      threads: 4
      keepalives_idle: 240
```

### Two traps in this file

1. **`host` must be `127.0.0.1`, not `localhost`.**
   On macOS, `localhost` resolves to IPv6 `::1` first. The Docker container
   publishes `0.0.0.0:5432` and `[::]:5432`, but Postgres's `pg_hba.conf` rejects
   the IPv6 loopback for password auth. The failure looks like a wrong password:

   ```
   connection to server at "localhost" (::1), port 5432 failed:
   FATAL:  password authentication failed for user "postgres"
   ```

   `psql` may work while dbt fails, because psql falls back to IPv4. **When the
   error says "password authentication failed" but the password is correct,
   suspect IPv6.**

2. **`password` must use `env_var()`, not a literal placeholder.**
   Writing `password: <POSTGRES_PASSWORD>` makes dbt send the literal string
   `<POSTGRES_PASSWORD>` as the password, producing the same misleading
   "password authentication failed" error.

---

## 5. dbt project structure

```
~/dbt_projects/tech_job_market/
├── dbt_project.yml
├── profiles.yml
├── README.md
├── models/
│   ├── schema.yml
│   ├── staging/          # 3 views
│   │   ├── stg_jobs.sql
│   │   ├── stg_hn_threads.sql
│   │   └── stg_excluded_comments.sql
│   ├── silver/           # 1 table
│   │   └── jobs_silver.sql
│   └── gold/             # 12 tables
│       ├── gold_jobs_by_company.sql
│       ├── gold_jobs_by_location.sql
│       ├── gold_jobs_by_remote_policy.sql
│       ├── gold_jobs_by_seniority.sql
│       ├── gold_jobs_over_time.sql
│       ├── gold_salary_summary.sql
│       ├── gold_skills_frequency.sql
│       ├── gold_skill_cooccurrence.sql
│       ├── gold_skill_salary.sql
│       ├── gold_skill_by_seniority.sql
│       ├── gold_remote_policy_analysis.sql
│       └── gold_seniority_analysis.sql
├── analysis/  logs/  macros/  seeds/  snapshots/  target/  tests/
```

Medallion layout:
- **Bronze** `jobmarket.jobs` — raw source. **Never modified.**
- **Silver** `jobmarket.jobs_silver` — cleaned, standardized, deduplicated.
- **Gold** 12 marts — pre-aggregated for consumption.

Materializations are set per-directory in `dbt_project.yml`: staging → `view`,
silver and gold → `table`.

### 5.1 Column names must match the real tables

Two staging models were originally written against assumed column names that do not
exist. The actual schemas:

**`jobmarket.hn_threads`**
```
id, title, url, posted_at, points, num_comments, raw_text, fetched_at
```
→ no `author` column.

**`jobmarket.excluded_comments`**
```
id, thread_id, comment_id, raw_text, archived_at
```
→ no `reason` column, and no `fetched_at` (it is `archived_at`).

Always verify with `\d jobmarket.<table>` before writing a model.

### 5.2 NULL handling in gold marts

Silver keeps rows where only one of `company`/`location` is empty (only rows where
**both** are empty are dropped). Aggregating those produces a NULL group, which
fails a `not_null` test.

Filter explicitly in the gold models:
```sql
FROM {{ ref('jobs_silver') }}
WHERE company IS NOT NULL AND company <> ''
GROUP BY company
```

---

## 6. Running dbt

```bash
source ~/dbt-mcp-venv312/bin/activate
cd ~/dbt_projects/tech_job_market
export POSTGRES_PASSWORD='<PASSWORD>'

dbt debug     # expect "All checks passed!"
dbt run       # 16 models
dbt test      # 24 data tests
```

Expected results:
```
dbt run   → PASS=16 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=16
dbt test  → PASS=24 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=24
```

---

## 7. Registering with an MCP host

### 7.1 MiniMax Code

Registered via the `mavis` MCP tooling:

```bash
mavis mcp update --name postgres ...
mavis mcp update --name dbt-mcp ...
```

Resulting `~/.minimax/mcp.json`:

```json
{
  "mcpServers": {
    "postgres": {
      "type": "stdio",
      "enabled": true,
      "command": "/Users/roelsomido/postgres-mcp-server/venv/bin/python3",
      "args": [
        "/Users/roelsomido/postgres-mcp-server/server.py",
        "postgresql://postgres:<PASSWORD>@localhost:5432/tech_job_market"
      ],
      "env": {}
    },
    "dbt-mcp": {
      "type": "stdio",
      "enabled": true,
      "command": "/Users/roelsomido/dbt-mcp-venv312/bin/dbt-mcp",
      "args": [],
      "env": {
        "DBT_PATH": "/Users/roelsomido/dbt-mcp-venv312/bin/dbt",
        "DBT_PROJECT_DIR": "/Users/roelsomido/dbt_projects/tech_job_market",
        "DISABLE_ADMIN_API": "true",
        "DISABLE_DISCOVERY": "true",
        "DISABLE_SEMANTIC_LAYER": "true",
        "POSTGRES_PASSWORD": "<PASSWORD>"
      }
    }
  }
}
```

### 7.2 Claude Desktop (or any other harness)

**Nothing is reinstalled.** The venvs and dbt project already exist on disk — copy
the registration blocks into the target client's MCP config file.

macOS path:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

Add to the existing `mcpServers` object (do not overwrite other entries):

```json
{
  "mcpServers": {
    "postgres": {
      "command": "/Users/roelsomido/postgres-mcp-server/venv/bin/python3",
      "args": [
        "/Users/roelsomido/postgres-mcp-server/server.py",
        "postgresql://postgres:<PASSWORD>@localhost:5432/tech_job_market"
      ],
      "env": {}
    },
    "dbt-mcp": {
      "command": "/Users/roelsomido/dbt-mcp-venv312/bin/dbt-mcp",
      "args": [],
      "env": {
        "DBT_PATH": "/Users/roelsomido/dbt-mcp-venv312/bin/dbt",
        "DBT_PROJECT_DIR": "/Users/roelsomido/dbt_projects/tech_job_market",
        "DISABLE_ADMIN_API": "true",
        "DISABLE_DISCOVERY": "true",
        "DISABLE_SEMANTIC_LAYER": "true",
        "POSTGRES_PASSWORD": "<PASSWORD>"
      }
    }
  }
}
```

Then **fully quit and relaunch the client** so it re-reads the config.

> **Security note:** the password appears in plaintext in both config files.
> The config files are mode `600`. If you want to avoid this, move the postgres
> DSN into the server's `env` block if the server supports it, or use a
> `~/.pgpass`-style approach for the dbt side and set
> `password: "{{ env_var('POSTGRES_PASSWORD') }}"` as done here.

### 7.3 Claude Code

```bash
claude mcp add postgres \
  -- /Users/roelsomido/postgres-mcp-server/venv/bin/python3 \
     /Users/roelsomido/postgres-mcp-server/server.py \
     "postgresql://postgres:<PASSWORD>@localhost:5432/tech_job_market"

claude mcp add dbt-mcp \
  -e DBT_PATH=/Users/roelsomido/dbt-mcp-venv312/bin/dbt \
  -e DBT_PROJECT_DIR=/Users/roelsomido/dbt_projects/tech_job_market \
  -e DISABLE_SEMANTIC_LAYER=true \
  -e DISABLE_DISCOVERY=true \
  -e DISABLE_ADMIN_API=true \
  -e POSTGRES_PASSWORD='<PASSWORD>' \
  -- /Users/roelsomido/dbt-mcp-venv312/bin/dbt-mcp
```

---

## 8. Opening the project in VS Code

The VS Code file dialog can be flaky when a folder is already open in another
workspace. The CLI is more reliable:

```bash
code /Users/roelsomido/dbt_projects/tech_job_market
```

Verify the window title shows the project name (e.g. `Welcome — tech_job_market`)
and the Explorer shows `models/`, `dbt_project.yml`, `profiles.yml`.

---

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` | `mcp` 2.x installed | `pip install "mcp<2"` |
| `No module named 'sqlalchemy'` | Missing dep | `pip install SQLAlchemy` |
| `FATAL: password authentication failed` but password is right | `localhost` → IPv6 `::1` | Use `host: 127.0.0.1` |
| Same error, password genuinely wrong | Literal placeholder in `profiles.yml` | Use `{{ env_var('POSTGRES_PASSWORD') }}` |
| `DBT_PROJECT_DIR environment variable is required` | Env not set on MCP server | Set `DBT_PROJECT_DIR` in server `env` |
| `dbt` not found / CLI tools error | `dbt` not on PATH | Set `DBT_PATH` to absolute path |
| MCP tool hangs 120s, logs `Opening authorization URL` | dbt Cloud OAuth for semantic layer/discovery | Set the three `DISABLE_*` flags |
| `column "x" does not exist` | Model references non-existent column | `\d jobmarket.<table>` and fix |
| `not_null` test fails on a gold mart | NULL group from empty source field | Add `WHERE col IS NOT NULL AND col <> ''` |
| dbt-mcp install fails on Python 3.15 | Unsupported Python | Use Python 3.12 venv |

---

## 10. Current state

- PostgreSQL 16 container `postgres-dev` — up, port 5432
- Database `tech_job_market`, schema `jobmarket` — 16 tables
- `jobmarket.jobs` (bronze) — 33,392 rows, unmodified
- `jobmarket.jobs_silver` — 21,310 rows
- 12 gold marts — materialized
- dbt — 16 models pass, 24 data tests pass
- Both MCP servers registered and enabled in MiniMax Code
