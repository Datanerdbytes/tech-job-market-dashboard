"""Data Notes page: provenance and caveats for every panel."""

import dash_mantine_components as dmc
from dash import register_page
from dash_iconify import DashIconify

from data import loader

register_page(__name__, path="/notes", name="Data Notes", title="Data Notes · Tech Job Market")

DATASETS = [
    ("postings_total", "Raw ingested postings"),
    ("salary_postings", "Postings with salary data"),
    ("remote_share_raw", "Remote share (exact 'remote', raw policy)"),
    ("policy", "Remote work policy distribution"),
    ("monthly", "Postings per month"),
    ("seniority", "Salary by Seniority"),
    ("skills", "Most Demanded Skills"),
    ("skill_salary", "Highest-Paying Skills"),
    ("companies", "Top companies by postings"),
    ("company_salary", "Top companies by salary ceiling"),
    ("cooc", "Skill co-occurrence"),
    ("locations", "Locations"),
    ("overall_salary", "Overall salary statistics"),
]

CAVEATS = [
    "Gold-layer population is 21,310 deduplicated postings (33,392 raw ingested).",
    "Only 9.5% of postings (2,022) report salary data — every salary panel covers that subset.",
    "Salaries below $1,000 are parse noise (e.g. the $5 floor in overall min) and are excluded upstream.",
    "Salary-ceiling company rankings favor small-sample outliers (e.g. Meticulous at $900k).",
    "Location spellings are consolidated into variants; 15.6% of postings have no parsed location.",
    "Intern's $222k average ceiling reflects a tiny sample.",
]


def _fmt_val(v):
    if isinstance(v, float) and v > 1000:
        return f"{v:,.0f}"
    if isinstance(v, float):
        return f"{v:,.2f}"
    return f"{v:,}" if isinstance(v, int) else str(v)


def _diff_line(snap) -> dmc.Text | None:
    """Show what changed on the last refresh, if a previous version exists."""
    prev = snap.get("previous")
    if not prev:
        return None
    old_rows, new_rows = prev.get("rows") or [], snap.get("rows") or []
    old_date = (prev.get("updated_at") or "")[:10]
    if len(old_rows) == 1 and len(new_rows) == 1 and old_rows[0].keys() == new_rows[0].keys():
        changes = [
            f"{k}: {_fmt_val(old_rows[0].get(k))} → {_fmt_val(new_rows[0].get(k))}"
            for k in new_rows[0]
            if old_rows[0].get(k) != new_rows[0].get(k)
        ]
        summary = "; ".join(changes) if changes else "values unchanged"
    elif len(old_rows) == 1 and len(new_rows) == 1:
        old_s = ", ".join(f"{k}: {_fmt_val(v)}" for k, v in old_rows[0].items())
        new_s = ", ".join(f"{k}: {_fmt_val(v)}" for k, v in new_rows[0].items())
        summary = f"definition changed — was {old_s}, now {new_s}"
    else:
        summary = f"{len(old_rows)} rows → {len(new_rows)} rows"
    return dmc.Text(
        f"Last refresh ({old_date} → {snap['updated_at'][:10]}): {summary}",
        size="xs", c="brand", fw=500, className="tabular-nums",
    )


def _dataset_card(name, label):
    snap = loader.load(name)
    updated = snap["updated_at"][:10]
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Group(
                    [
                        dmc.Text(label, fw=600, size="sm"),
                        dmc.Badge(f"as of {updated}", color="gray", variant="light", size="sm"),
                    ],
                    justify="space-between",
                ),
                dmc.Text(snap["question"] or "—", size="xs", c="dimmed"),
                dmc.Text(f"{len(snap['rows'])} rows", size="xs", c="dimmed"),
                _diff_line(snap),
                dmc.Accordion(
                    dmc.AccordionItem(
                        [
                            dmc.AccordionControl("View generated SQL"),
                            dmc.AccordionPanel(
                                dmc.CodeHighlight(
                                    code=snap["sql"] or "-- derived in loader (no direct query)",
                                    language="sql",
                                )
                            ),
                        ],
                        value="sql",
                    ),
                ),
            ],
            gap=6,
        ),
        p="md",
        id=f"note-{name}",
    )


def layout():
    return dmc.Stack(
        [
            dmc.Paper(
                dmc.Stack(
                    [
                        dmc.Text("Where the Numbers Come From", fw=700),
                        dmc.Text(
                            "Every figure is queried through the certified Auto-Ontology "
                            "semantic layer (text-to-SQL over the certified gold tables), "
                            "then cached as a snapshot. No component reads Postgres directly.",
                            size="sm", c="dimmed",
                        ),
                        dmc.Text(
                            f"Snapshot freshness: {loader.as_of_label()} — refresh with "
                            "`python refresh_data.py` from the dashboard directory.",
                            size="sm",
                        ),
                    ],
                    gap="xs",
                ),
                p="lg",
            ),
            dmc.Paper(
                dmc.List(
                    [dmc.ListItem(c) for c in CAVEATS],
                    icon=dmc.ThemeIcon(
                        DashIconify(icon="solar:info-circle-bold", width=14),
                        color="gray", variant="light", radius="xl", size="sm",
                    ),
                    mt="md",
                ),
                p="lg",
            ),
            dmc.Stack([_dataset_card(n, lbl) for n, lbl in DATASETS], gap="sm"),
        ],
        gap="md",
    )
