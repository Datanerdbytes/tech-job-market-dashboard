# Tech Job Market Dashboard

A [Dash](https://dash.plotly.com) + [Dash Mantine Components](https://www.dash-mantine-components.com)
dashboard for the `tech_job_market` project, styled after the
[Fox Stocks Dashboard](https://www.figma.com/community/file/1202866913852978897/fox-stocks-dashboard)
Figma template (Nickelfox, CC BY 4.0).

**Every number flows through the certified Auto-Ontology semantic layer** — the app
reads local snapshot JSONs (produced by querying the semantic layer's text-to-SQL
pipeline) and never touches Postgres directly.

## Run

```sh
cd dashboard
uv sync
uv run python app.py        # http://127.0.0.1:8050
```

Dash's built-in MCP server is enabled at `http://127.0.0.1:8050/_mcp`.

## Pages

| Page | Contents |
| --- | --- |
| Overview | KPI cards, salary envelope, postings trend (1Y/3Y/All), remote-policy donut, seniority dumbbell, top-companies watchlist |
| Skills | Most demanded skills, highest-paying skills, most common skill pairs |
| Companies & Locations | Company ranking toggle (postings / salary ceilings), consolidated locations |
| Data Notes | Per-dataset provenance (generated SQL) + data caveats |

## CI/CD

`.github/workflows/ci.yml` runs on every push and PR: ruff lint (same focused
rule set as the auto-ontology upstream) plus a production-mode smoke test that
loads the app and asserts all four pages and assets return 200 — with debug
and the MCP server disabled, exactly as they run in production.

Deploys are GitHub-driven: connect the repo to Vercel once, then every push
to `main` deploys production and every PR gets its own preview URL.

1. Push the repo to GitHub (done — `github.com/Datanerdbytes/tech-job-market-dashboard`).
2. In Vercel: **Add New → Project → Import** this repository.
3. Set **Root Directory** to `dashboard` (the `vercel.json` there carries the
   config). Framework Preset: Other.
4. Deploy — subsequent pushes to `main` redeploy automatically.

## Deploy

The app is read-only (snapshot JSONs committed to the repo, no secrets, no
server-side state), which makes it easy to host anywhere.

### Vercel (serverless — used for the portfolio deployment)

```sh
npm i -g vercel
cd dashboard
vercel            # first deploy: link the project, accept the defaults
vercel --prod     # promote to production
```

`vercel.json` routes everything to `api/index.py` (Dash is Flask under the
hood, served via Vercel's Python runtime) and bundles `data/snapshots/` into
the function. The MCP server and debug mode are disabled in production
(opt back in locally with `DASH_MCP=1` / `DASH_DEBUG=1`). Expect 1–3s cold
starts on the first visit after inactivity.

### Container hosts (Render / Railway / Cloud Run)

```sh
docker build -t tech-job-market-dashboard .
docker run -p 8050:8050 tech-job-market-dashboard
```

`Dockerfile` runs gunicorn on port 8050. On Render/Railway, point the service
at this directory; they detect the Dockerfile automatically.

### Refreshing deployed data

`refresh_data.py` needs to reach the auto-ontology stack, so it runs locally:

```sh
uv run python refresh_data.py        # re-query the semantic layer
git add data/snapshots && git commit -m "refresh snapshots" && git push
```

Pushing updated snapshots redeploys the Vercel site automatically (or restart
the container on other hosts).

## Refresh data

Snapshots live in `data/snapshots/*.json`. To re-query the semantic layer:

```sh
uv run python refresh_data.py                # all 13 datasets (~15–25 min; LLM-mediated)
uv run python refresh_data.py --only monthly companies
uv run python refresh_data.py --list         # show the fixed question per dataset
```

Requirements: the auto-ontology stack running (`docker compose up -d` from
`auto-ontology/`) and `AUTO_ONTOLOGY_API_TOKEN` present in `auto-ontology/.env`
(the token is read from there, never printed). Each dataset uses one fixed,
previously-validated question, so refresh results stay pinned to the certified
gold tables.

## Data caveats (also on the Data Notes page)

- Gold layer = 21,310 deduplicated postings (33,392 raw ingested).
- Only 9.5% of postings report salary — salary panels cover that subset.
- Salary-ceiling rankings favor small-sample outliers; location spellings are
  consolidated; intern-level salary rows are tiny samples.
