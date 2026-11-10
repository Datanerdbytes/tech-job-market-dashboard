"""Refresh dashboard snapshots through the Auto-Ontology semantic layer.

Each dataset has one fixed, previously-validated question. The script posts it
to the Next.js gateway (POST /api/chat/completions, SSE), parses the `result`
event (generated SQL + executed rows), and rewrites data/snapshots/<name>.json.
No direct database access — every number flows through the semantic layer.

Usage:
    uv run python refresh_data.py             # refresh all datasets
    uv run python refresh_data.py --only monthly companies
    uv run python refresh_data.py --list      # show dataset names + questions
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
import os

# Token lives in the stack's .env (never printed, never committed).
load_dotenv(Path(__file__).resolve().parent.parent / "auto-ontology" / ".env")
GATEWAY = os.environ.get("APP_URL", "http://localhost:3000").rstrip("/")
TOKEN = os.environ.get("AUTO_ONTOLOGY_API_TOKEN")

SNAPSHOTS = Path(__file__).resolve().parent / "data" / "snapshots"

# Question phrasings exactly as validated in the certification session.
# `evidence` pins ambiguous ones to the certified gold table: without it the
# LLM may answer from a different population (raw jobs vs gold layer) on a
# later run — e.g. 2,997 (raw, salary bounds non-null) vs 2,022 (gold summary).
DATASETS = {
    "postings_total": "How many job postings are there in total?",
    "salary_postings": "What is the jobs_with_salary value in the gold_salary_summary table?",
    "remote_share_raw": "What share of job postings are remote?",
    "policy": "Break down the number of job postings by remote work policy.",
    "monthly": "Show the number of job postings for each month over time.",
    "seniority": "What are the average minimum and maximum salaries for each seniority level?",
    "skills": "Which 10 skills appear most frequently in job postings?",
    "skill_salary": "Which 10 skills have the highest average maximum salary?",
    "companies": "Which 10 companies have the most job postings?",
    "company_salary": "Which 10 companies that report salary data have the highest average maximum salary?",
    "cooc": "Which pairs of skills most often appear together in the same job posting?",
    "locations": "Which 10 locations have the most job postings?",
    "overall_salary": "What are the overall average, lowest, and highest salaries across job postings?",
}

EVIDENCE = {
    "salary_postings": (
        "Use the certified gold table gold_salary_summary and return its "
        "jobs_with_salary column (job postings with salary data in the "
        "deduplicated gold layer). Do not count the raw jobs table."
    ),
    "overall_salary": (
        "Use the certified gold table gold_salary_summary and return its "
        "avg_salary_min, avg_salary_max, min_salary_min and max_salary_max columns."
    ),
}


def ask(question: str, evidence: str | None = None, timeout: int = 420) -> dict:
    """One semantic-layer question -> {sql, rows} from the SSE result event."""
    body = json.dumps({"question": question, "evidence": evidence, "stream": True}).encode()
    req = urllib.request.Request(
        f"{GATEWAY}/api/chat/completions",
        method="POST",
        data=body,
        headers={
            "x-api-key": TOKEN or "",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for raw in resp:
            line = raw.decode(errors="replace").strip()
            if line.startswith("data:") and '"result"' in line:
                answer = json.loads(line[5:].strip()).get("answer") or {}
                rows_raw = answer.get("sql_response_from_db") or []
                rows = []
                for chunk in rows_raw:
                    try:
                        rows.extend(json.loads(chunk))
                    except (TypeError, json.JSONDecodeError):
                        pass
                return {"sql": answer.get("sql_code"), "rows": rows}
    raise RuntimeError("no result event in SSE stream")


def refresh(name: str, attempts: int = 3) -> bool:
    question = DATASETS[name]
    for attempt in range(1, attempts + 1):
        try:
            out = ask(question, evidence=EVIDENCE.get(name))
            if not out["rows"]:
                raise RuntimeError("empty rows")
            payload = {
                "question": question,
                "sql": out["sql"],
                "rows": out["rows"],
                "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            path = SNAPSHOTS / f"{name}.json"
            if path.exists():  # keep the prior version for the notes-page diff line
                old = json.loads(path.read_text())
                payload["previous"] = {
                    "rows": old.get("rows"),
                    "sql": old.get("sql"),
                    "updated_at": old.get("updated_at"),
                }
            path.write_text(json.dumps(payload, indent=1))
            print(f"  {name:<18} OK   {len(out['rows'])} rows")
            return True
        except Exception as exc:  # transient NIM/Postgres pressure
            print(f"  {name:<18} attempt {attempt}/{attempts} failed: {str(exc)[:110]}")
            if attempt < attempts:
                time.sleep(20 * attempt)
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="*", choices=sorted(DATASETS), default=None)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list:
        for name, q in DATASETS.items():
            print(f"{name:<18} {q}")
        return

    if not TOKEN:
        sys.exit("AUTO_ONTOLOGY_API_TOKEN not found — check auto-ontology/.env")

    names = args.only or sorted(DATASETS)
    print(f"Refreshing {len(names)} dataset(s) via {GATEWAY}/api/chat/completions …")
    ok = 0
    for name in names:
        ok += refresh(name)
        time.sleep(3)  # spacing: rapid bursts exhaust Postgres connections
    print(f"\n{ok}/{len(names)} datasets refreshed.")
    if ok < len(names):
        sys.exit(1)


if __name__ == "__main__":
    main()
