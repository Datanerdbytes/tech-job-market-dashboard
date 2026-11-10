<!--
SPDX-FileCopyrightText: Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES.
All rights reserved.
SPDX-License-Identifier: Apache-2.0
-->

# AGENTS.md — tech_job_market Project Rules

This file consolidates agent guidance for the `tech_job_market` dbt project, its Auto-Ontology semantic layer, and the Next.js frontend.

---

## 1. Database & Semantic Layer Rules (Root)

- **Always use `auto-ontology` MCP first:** For any analytical question, business requirement, metric calculation, or data exploration on `tech_job_market`, you MUST query the `auto-ontology` MCP server and rely strictly on certified tables, columns, and semantic relationships.
- **Ensure `auto-ontology-mcp` is up before starting any task:** Before beginning work that touches the semantic layer, verify the `auto-ontology-mcp` server is running and reachable. If it is not, bring the stack up first — `docker compose up -d auto-ontology-mcp` from `auto-ontology/` — then confirm readiness via the MCP `check_readiness` tool. Do not start a task against a stopped server, and do not treat a stopped server as a reason to bypass the semantic layer.
- **Do not bypass the semantic layer:** Never use the direct `postgres` MCP server to answer business questions or write ad-hoc analytical queries from scratch when `auto-ontology` is available.
- **When to use direct `postgres` MCP:** Only use the direct `postgres` MCP for database administration, DDL inspection, or verifying raw connection health when explicitly requested.

---

## 2. Auto-Ontology Agent Entry Point

### Skills (in `auto-ontology/skills/`)

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `nvidia-ontology-setup` | Helm (official install), local Compose, developer `--dev` / `--ds`, MCP against an already-running instance, troubleshooting | Auto-Ontology is not up yet or something failed during bring-up |
| `nvidia-ontology-management` | Inspect, model, **modify**, and safely publish through glossary terms, SQL attributes, semantic relationships, model YAML import/export, and governed result definitions | You need to design concepts, mappings, relationships, measures, units, grain, policies; apply, verify, certify, publish, or roll back |
| `nvidia-ontology-query` | How an agent calls Auto-Ontology (MCP first, REST fallback), discovers meaning through the semantic layer, and validates SQL, rows, and answers | Auto-Ontology is already deployed; you need to ask descriptive/diagnostic questions and validate SQL, rows, and prose |

### Workflow Ownership

| User Action | Owning Skill |
|-------------|--------------|
| Install, configure, connect, ingest, compile, prove readiness | `nvidia-ontology-setup` |
| Inspect meaning and semantic relationships | `nvidia-ontology-management` |
| Design concepts, mappings, relationships, measures, units, grain, and policies | `nvidia-ontology-management` → `references/modeling.md` |
| Apply, verify, certify honestly, publish, and roll back | `nvidia-ontology-management` → `references/publication.md` |
| Ask descriptive or diagnostic questions and validate SQL, rows, and prose | `nvidia-ontology-query` → `references/query-validation.md` |

### Sources of Truth (Do Not Duplicate)

| Job | Owner | Skills Do |
|-----|-------|-----------|
| Install commands | `DEPLOYMENT.md` (Helm, official), `docker-compose.yml`; `dev_tools/setup_env.sh` for developer workflows | Invoke them; do not write a new installer |
| Live read tools | `mcp/auto_ontology_mcp/tools.py` (handshake tool list) | Prefer MCP; sequence reads; never copy the tool table |
| REST shapes and permissions | `docs/openapi/auto-ontology-api.json` | Name the operation and permission; link; do not paste schemas |

> **MCP is read-only by design.** Writes go through the Next.js `/api/...` surface.
> The live MCP tool list at handshake is the source of truth if it disagrees with anything in a skill.

---

## 3. Next.js Frontend Rules (`auto-ontology/frontend/`)

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

---

## 4. Project Structure Reference

```
tech_job_market/
├── AGENTS.md                          ← This file (consolidated)
├── dbt_project.yml
├── models/
├── seeds/
├── macros/
├── auto-ontology/
│   ├── AGENTS.md                      ← (Deprecated — see root AGENTS.md)
│   ├── CLAUDE.md                      ← Maintainer conventions (build, test, schema, frontend)
│   ├── DEPLOYMENT.md
│   ├── docker-compose.yml
│   ├── dev_tools/
│   ├── mcp/
│   ├── skills/
│   │   ├── nvidia-ontology-setup/
│   │   ├── nvidia-ontology-management/
│   │   └── nvidia-ontology-query/
│   ├── references/
│   │   ├── modeling.md
│   │   ├── publication.md
│   │   └── query-validation.md
│   └── frontend/
│       ├── AGENTS.md                  ← (Deprecated — see root AGENTS.md)
│       ├── package.json
│       ├── next.config.js
│       └── src/
└── ...
```

---

## 5. Quick Reference

- **Certified tables/columns only:** Always verify certification status before trusting semantic definitions.
- **MCP-first workflow:** `auto-ontology` MCP → validate → `postgres` MCP only for admin/DDL.
- **Pre-flight:** Confirm `auto-ontology-mcp` is up (and `check_readiness` is clean) before starting a task that uses the semantic layer.
- **Skills are in `auto-ontology/skills/`** under the `nvidia-ontology*` namespace.
- **Frontend code** lives in `auto-ontology/frontend/` — follow Next.js docs in `node_modules/next/dist/docs/`.
- **Never duplicate** `DEPLOYMENT.md`, `docker-compose.yml`, `mcp/auto_ontology_mcp/tools.py`, or `docs/openapi/auto-ontology-api.json` content in skills or agent instructions.