"""Skills page: demand, pay premium, co-occurrence."""

import dash_mantine_components as dmc
from dash import register_page

from data import loader
from pages.overview import provenance_link

register_page(__name__, path="/skills", name="Skills", title="Skills · Tech Job Market")

# Data is fetched inside the builder functions (called per page render), so a
# snapshot refresh shows up on the next page load without a server restart.


def demand_chart():
    skills = loader.df("skills")
    unique_total = int(loader.monthly()["postings"].sum())
    data = [{"skill": r["skill"], "postings": int(r["job_count"])} for _, r in skills.iterrows()]
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Group([dmc.Text("Most Demanded Skills", fw=700), provenance_link("skills")], justify="space-between"),
                dmc.Text(f"Skills extracted from {unique_total:,} unique postings",
                         size="xs", c="dimmed"),
                dmc.BarChart(
                    data=data,
                    dataKey="skill",
                    series=[{"name": "postings", "color": "brand.6"}],
                    orientation="vertical",
                    h=420,
                    withTooltip=True,
                    barProps={"radius": 6},
                    yAxisProps={"tickLine": False, "width": 135},
                ),
            ],
            gap="xs",
        ),
        p="lg",
    )


def pay_chart():
    skill_salary = loader.df("skill_salary")
    data = [{"skill": r["skill"], "ceiling": int(r["avg_salary_max"])}
            for _, r in skill_salary.iterrows()]
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Group(
                    [
                        dmc.Group([dmc.Text("Highest-Paying Skills", fw=700), provenance_link("skill_salary")], gap="sm"),
                        dmc.Badge("Avg Posted Ceiling", color="teal", variant="light"),
                    ],
                    justify="space-between",
                ),
                dmc.Text("Covers only the 9.5% of postings reporting salary",
                         size="xs", c="dimmed"),
                dmc.BarChart(
                    data=data,
                    dataKey="skill",
                    series=[{"name": "ceiling", "color": "brand.6"}],
                    orientation="vertical",
                    h=420,
                    withTooltip=True,
                    barProps={"radius": 6},
                    yAxisProps={"tickLine": False, "width": 135},
                ),
            ],
            gap="xs",
        ),
        p="lg",
    )


def cooc_chart():
    cooc = loader.cooc_top(10)
    data = [{"pair": r["pair"], "postings": int(r["job_count"])} for _, r in cooc.iterrows()]
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Group([dmc.Text("Most Common Skill Pairs", fw=700), provenance_link("cooc")], justify="space-between"),
                dmc.Text("Pairs appearing together in the same posting",
                         size="xs", c="dimmed"),
                dmc.BarChart(
                    data=data,
                    dataKey="pair",
                    series=[{"name": "postings", "color": "brand.6"}],
                    orientation="vertical",
                    h=420,
                    withTooltip=True,
                    barProps={"radius": 6},
                    yAxisProps={"tickLine": False, "width": 135},
                ),
            ],
            gap="xs",
        ),
        p="lg",
    )


def layout():
    return dmc.Stack(
        [
            dmc.Grid([dmc.GridCol(demand_chart(), span={"base": 12, "md": 6}),
                      dmc.GridCol(pay_chart(), span={"base": 12, "md": 6})],
                     gap="md"),
            cooc_chart(),
        ],
        gap="md",
    )
