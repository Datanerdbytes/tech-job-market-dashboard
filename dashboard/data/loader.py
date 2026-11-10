"""Snapshot loader: every number in the dashboard comes from a snapshot JSON
produced by a query through the Auto-Ontology semantic layer (refresh_data.py,
or the validated bootstrap run). No direct database access anywhere."""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

SNAPSHOTS = Path(__file__).parent / "snapshots"


def load(name: str) -> dict:
    """Return a snapshot dict: {question, sql, rows, updated_at}."""
    with open(SNAPSHOTS / f"{name}.json") as f:
        return json.load(f)


def df(name: str) -> pd.DataFrame:
    return pd.DataFrame(load(name)["rows"])


def latest_update() -> str:
    stamps = [load(p.stem)["updated_at"] for p in SNAPSHOTS.glob("*.json")]
    return max(stamps)


def as_of_label() -> str:
    stamp = latest_update()
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).strftime("%b %d, %Y")


# ---------------------------------------------------------------------------
# Derived datasets (all computed from raw snapshots)
# ---------------------------------------------------------------------------

def monthly() -> pd.DataFrame:
    d = df("monthly").rename(columns={"month": "date", "job_count": "postings"})
    d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m")
    return d


def monthly_for_range(rng: str) -> pd.DataFrame:
    d = monthly()
    if rng == "1y":
        return d.tail(12)
    if rng == "3y":
        return d.tail(36)
    return d


def policy_summary() -> pd.DataFrame:
    """Single standardized values plus one 'combo policies' bucket."""
    d = df("policy")
    single = d[~d["remote_policy_std"].str.contains(";", na=False)].copy()
    combos = d[d["remote_policy_std"].str.contains(";", na=False)]["job_count"].sum()
    out = pd.concat(
        [single.rename(columns={"remote_policy_std": "policy"}),
         pd.DataFrame([{"policy": "Combo policies", "job_count": combos}])],
        ignore_index=True,
    ).sort_values("job_count", ascending=False, ignore_index=True)
    return out


def seniority_single() -> pd.DataFrame:
    """Pure single-level seniority rows (drops combo strings)."""
    d = df("seniority")
    return d[~d["seniority_std"].str.contains(";", na=False)].sort_values(
        "avg_salary_max", ascending=False, ignore_index=True
    )


def cooc_top(n: int = 10) -> pd.DataFrame:
    d = df("cooc").nlargest(n, "job_count").reset_index(drop=True)
    d["pair"] = d["skill_a"] + " + " + d["skill_b"]
    return d[["pair", "job_count"]]


def locations_consolidated() -> pd.DataFrame:
    """Merge extraction spelling variants into readable buckets."""
    d = df("locations")

    def bucket(loc) -> str:
        if loc is None or (isinstance(loc, float) and pd.isna(loc)):
            return "Unknown / not parsed"
        s = str(loc).lower()
        if "remote" in s:
            return "Remote (all variants)"
        if "san francisco" in s:
            return "San Francisco (variants)"
        if "london" in s:
            return "London, UK"
        if "berlin" in s:
            return "Berlin, Germany"
        if "onsite" in s:
            return "Onsite (label)"
        return str(loc)

    d["location"] = d["location"].map(bucket)
    return d.groupby("location", as_index=False)["job_count"].sum().sort_values(
        "job_count", ascending=False, ignore_index=True
    )


def kpis() -> dict:
    monthly_total = int(monthly()["postings"].sum())
    raw_total = int(df("postings_total")["count"].iloc[0])
    salary_count = int(df("salary_postings")["jobs_with_salary"].iloc[0])
    pol = policy_summary()
    remote = int(pol.loc[pol["policy"] == "Remote", "job_count"].iloc[0])
    overall = df("overall_salary").iloc[0]
    return {
        "unique_total": monthly_total,
        "raw_total": raw_total,
        "salary_count": salary_count,
        "salary_pct": salary_count / monthly_total,
        "remote_count": remote,
        "remote_pct": remote / monthly_total,
        "remote_pct_raw": float(load("remote_share_raw")["rows"][0]["remote_postings_share"]),
        "avg_salary_min": float(overall["avg_salary_min"]),
        "avg_salary_max": float(overall["avg_salary_max"]),
    }
