"""Companies & Locations page: company ranking toggle + consolidated locations."""

import dash_mantine_components as dmc
from dash import register_page

from data import loader
from pages.overview import provenance_link
from dash_iconify import DashIconify

register_page(__name__, path="/companies", name="Companies & Locations",
              title="Companies · Tech Job Market")

# Data is fetched inside layout() (called per page render), so a snapshot
# refresh shows up on the next page load without a server restart.


def company_chart(data, measure):
    rows = [{"company": r["company"],
             "value": int(r["job_count"] if measure == "postings" else r["avg_salary_max"])}
            for _, r in data.iterrows()]
    return dmc.BarChart(
        id="company-chart",
        data=rows,
        dataKey="company",
        series=[{"name": "value", "color": "brand.6"}],
        orientation="vertical",
        h=430,
        withTooltip=True,
        barProps={"radius": 6},
        yAxisProps={"tickLine": False, "width": 135},
    )


def layout():
    companies = loader.df("companies")
    locations = loader.locations_consolidated()
    return dmc.Stack(
        [
            dmc.Paper(
                dmc.Stack(
                    [
                        dmc.Group(
                            [
                                dmc.Text("Top Companies", fw=700),
                                dmc.Anchor(
                                    dmc.ActionIcon(
                                        DashIconify(icon="solar:square-code-bold", width=16),
                                        variant="subtle", color="gray", size="sm",
                                        **{"aria-label": "View SQL and provenance",
                                           "data-tooltip": "View SQL & provenance"},
                                    ),
                                    href="/notes#note-companies",
                                    id="company-note-link",
                                ),
                                dmc.SegmentedControl(
                                    id="company-measure",
                                    data=[{"label": "By postings", "value": "postings"},
                                          {"label": "By salary ceiling", "value": "salary"}],
                                    value="postings",
                                    color="brand",
                                    size="xs",
                                ),
                            ],
                            justify="space-between",
                        ),
                        dmc.Text(id="company-chart-caption",
                                 size="xs", c="dimmed",
                                 children="Postings count across the gold layer."),
                        company_chart(companies, "postings"),
                    ],
                    gap="xs",
                ),
                p="lg",
            ),
            dmc.Paper(
                dmc.Stack(
                    [
                        dmc.Group([dmc.Text("Locations", fw=700), provenance_link("locations")], justify="space-between"),
                        dmc.Text("Extraction spelling variants consolidated; 15.6% of "
                                 "postings have no parsed location.", size="xs", c="dimmed"),
                        dmc.BarChart(
                            data=[{"location": r["location"], "postings": int(r["job_count"])}
                                  for _, r in locations.iterrows()],
                            dataKey="location",
                            series=[{"name": "postings", "color": "brand.6"}],
                            orientation="vertical",
                            h=320,
                            withTooltip=True,
                            barProps={"radius": 6},
                            yAxisProps={"tickLine": False, "width": 135},
                        ),
                    ],
                    gap="xs",
                ),
                p="lg",
            ),
        ],
        gap="md",
    )
