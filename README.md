# tech_job_market dbt Project

Medallion architecture dbt project for the `tech_job_market` PostgreSQL database.

## Architecture

| Layer | Models | Materialization | Purpose |
|---|---|---|---|
| **Bronze** | `stg_jobs`, `stg_hn_threads`, `stg_excluded_comments` | View | Raw source of truth — never modified |
| **Silver** | `jobs_silver` | Table | Cleaned, standardized, deduplicated |
| **Gold** | 12 mart tables | Table | Pre-aggregated analytics for specific use cases |

## Gold Marts (12 tables)

1. `gold_jobs_by_company` — Job counts & salary by company
2. `gold_jobs_by_location` — Job counts & salary by location
3. `gold_jobs_by_remote_policy` — Jobs & salary by remote policy
4. `gold_jobs_by_seniority` — Jobs & salary by seniority
5. `gold_jobs_over_time` — Monthly posting trends
6. `gold_salary_summary` — Overall salary statistics
7. `gold_skills_frequency` — Unique skill frequency
8. `gold_skill_cooccurrence` — Skill pairs that appear together
9. `gold_skill_salary` — Salary stats per individual skill
10. `gold_skill_by_seniority` — Skills by seniority level
11. `gold_remote_policy_analysis` — Remote policy deep-dive
12. `gold_seniority_analysis` — Seniority deep-dive

## Setup

### 1. Configure Profile

Edit `profiles.yml` with your PostgreSQL credentials:

```yaml
tech_job_market:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5432
      user: postgres
      password: <YOUR_PASSWORD>
      dbname: tech_job_market
      schema: jobmarket
```

### 2. Run dbt

```bash
cd ~/dbt_projects/tech_job_market

# Debug connection
dbt debug

# Run all models
dbt run

# Run specific layer
dbt run --select tag:silver
dbt run --select tag:gold

# Generate docs
dbt docs generate
dbt docs serve
```

## Data Lineage

```
jobmarket.jobs (bronze)
    │
    ▼
stg_jobs (staging view)
    │
    ▼
jobs_silver (silver table)
    ├──► gold_jobs_by_company
    ├──► gold_jobs_by_location
    ├──► gold_jobs_by_remote_policy
    ├──► gold_jobs_by_seniority
    ├──► gold_jobs_over_time
    ├──► gold_salary_summary
    ├──► gold_skills_frequency
    ├──► gold_skill_cooccurrence
    ├──► gold_skill_salary
    ├──► gold_skill_by_seniority
    ├──► gold_remote_policy_analysis
    └──► gold_seniority_analysis
```

## NVIDIA Auto-Ontology Preparation

Model descriptions in `models/schema.yml` are dbt-documented and ready for ontology ingestion. Key entities:

- **Job**: company, job_title, location, posted_at, salary_min, salary_max
- **Skill**: skill_std values (react, python, typescript, aws, etc.)
- **Seniority**: seniority_std values (Senior, Lead, Manager, Director, Staff, Principal)
- **Remote Policy**: remote_policy_std values (Remote, Onsite, Hybrid, Anywhere)

## Notes

- dbt-mcp server installation is blocked by network restrictions in this environment
- dbt-core 2.0.9 is installed at `/Users/roelsomido/.local/bin/dbt`
- To use dbt-mcp, install it once network access is available: `pip install dbt-mcp`
- All SQL models are compatible with dbt-mcp once installed
