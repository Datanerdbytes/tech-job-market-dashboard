# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a `tech_job_market` dbt project implementing a medallion architecture (bronze→silver→gold) for PostgreSQL data analysis. The project contains 16 models: 3 staging views, 1 silver table, and 12 gold mart tables for pre-aggregated analytics.

## Commands

### Core dbt Commands
- `cd ~/dbt_projects/tech_job_market` - Enter project directory
- `dbt debug` - Verify PostgreSQL connection and configuration
- `dbt run` - Run all 16 models (bronze, silver, gold layers)
- `dbt run --select tag:silver` - Run only silver layer
- `dbt run --select tag:gold` - Run only gold layer
- `dbt docs generate` - Generate dbt documentation
- `dbt docs serve` - Serve documentation locally

### Quick Testing
- `dbt test` - Run 24 data quality tests (bronze: 0, silver: 4, gold: 20)
- `dbt compile` - Compile SQL from source to generated SQL (for debugging)

### Running a Single Model
```bash
# To run a specific model:
dbt run --select <model_name>

# Example:
dbt run --select gold_jobs_by_company
```

### Data Validation
- Check PostgreSQL tables before model development: `\d jobmarket.<table_name>`
- Verify column names match actual schema (see setup documentation for details)

## Architecture

The project follows a clear three-layer medallion architecture:

### Bronze Layer (Raw Sources)
- **Materialization**: Views (`view`)
- **Models**: `stg_jobs`, `stg_hn_threads`, `stg_excluded_comments`
- **Source**: Direct tables from `jobmarket.jobs` (33,392 rows, unmodified)

### Silver Layer (Cleaned Data)
- **Materialization**: Tables (`table`)
- **Model**: `jobs_silver` (21,310 rows, cleaned/standardized)
- **Purpose**: Deduplicated, standardized data

### Gold Layer (Analytics)
- **Materialization**: Tables (`table`)
- **Models**: 12 mart tables for specific analytics use cases:
  1. `gold_jobs_by_company` - Job counts & salary by company
  2. `gold_jobs_by_location` - Job counts & salary by location
  3. `gold_jobs_by_remote_policy` - Jobs & salary by remote policy
  4. `gold_jobs_by_seniority` - Jobs & salary by seniority
  5. `gold_jobs_over_time` - Monthly posting trends
  6. `gold_salary_summary` - Overall salary statistics
  7. `gold_skills_frequency` - Unique skill frequency
  8. `gold_skill_cooccurrence` - Skill pairs that appear together
  9. `gold_skill_salary` - Salary stats per individual skill
  10. `gold_skill_by_seniority` - Skills by seniority level
  11. `gold_remote_policy_analysis` - Remote policy deep-dive
  12. `gold_seniority_analysis` - Seniority deep-dive

## Setup Requirements

### PostgreSQL Connection
- Host: `127.0.0.1` (important: use `localhost` may cause IPv6 issues on macOS)
- Port: 5432
- User: `postgres`
- Database: `tech_job_market`
- Schema: `jobmarket`

### Environment Configuration
Required environment variables:
- `POSTGRES_PASSWORD` - Database password
- `DBT_PATH` - Absolute path to dbt binary (`/Users/roelsomido/dbt-mcp-venv312/bin/dbt`)
- `DBT_PROJECT_DIR` - Project directory (`/Users/roelsomido/dbt_projects/tech_job_market`)
- `DISABLE_SEMANTIC_LAYER=true` - Disable dbt Cloud semantic layer
- `DISABLE_DISCOVERY=true` - Disable dbt Cloud discovery
- `DISABLE_ADMIN_API=true` - Disable dbt Cloud admin API

### Key Files
- `profiles.yml` - Database connection configuration
- `dbt_project.yml` - dbt project configuration and model materialization settings
- `models/schema.yml` - Model schema documentation for NVIDIA Auto-Ontology
- `models/` directory structure:
  - `staging/` - Bronze layer views
  - `silver/` - Silver layer tables
  - `gold/` - Gold layer mart tables

## Development Workflow

1. **Setup**: Configure `profiles.yml` with PostgreSQL credentials
2. **Connect**: Run `dbt debug` to verify connection
3. **Run**: Execute models in dependency order (bronze → silver → gold)
4. **Test**: Validate data quality with `dbt test`
5. **Document**: Generate docs with `dbt docs generate`

## Important Notes

### Common Issues
1. **Password Authentication Failures**: Often caused by `localhost` vs `127.0.0.1` (use IPv4)
2. **Semantic Layer Hangs**: Enabled dbt Cloud tools cause OAuth browser redirects
3. **Python Version Mismatch**: dbt-mcp requires Python 3.9-3.12, not 3.15
4. **Column Name Mismatches**: Verify actual column names in PostgreSQL before model development

### Column Name Verifications
- `jobmarket.hn_threads`: No `author` column
- `jobmarket.excluded_comments`: No `reason` or `fetched_at` columns (use `archived_at` instead)

### NULL Handling in Gold Models
Silver layer filters rows where both `company` AND `location` are empty. Gold models must add explicit NULL filtering:
```sql
WHERE company IS NOT NULL AND company <> ''
```

## Quick Reference

```bash
# Full workflow
source ~/dbt-mcp-venv312/bin/activate
cd ~/dbt_projects/tech_job_market
export POSTGRES_PASSWORD='<PASSWORD>'

dbt debug     # Verify connection
dbt run       # Run all models (16 total)
dbt test      # Data quality (24 tests)
```

Expected results:
- dbt run → PASS=16 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=16
- dbt test → PASS=24 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=24