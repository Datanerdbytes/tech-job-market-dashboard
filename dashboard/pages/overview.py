"""Overview page: Foxstocks-style KPI strip, salary envelope, trend, remote
policy snapshot, seniority dumbbell, companies watchlist."""

import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, register_page
from dash_iconify import DashIconify

from data import loader
from theme import BEIGE, GREEN, INK, PURPLE, TEAL


def provenance_link(dataset: str) -> dmc.Anchor:
    """Small link to the dataset's provenance card on the Data Notes page."""
    return dmc.Anchor(
        dmc.ActionIcon(
            DashIconify(icon="solar:square-code-bold", width=16),
            variant="subtle",
            color="gray",
            size="sm",
            **{"aria-label": "View SQL and provenance", "data-tooltip": "View SQL & provenance"},
        ),
        href=f"/notes#note-{dataset}",
    )

register_page(__name__, path="/", name="Overview", title="Overview · Tech Job Market")

# Data is fetched inside the builder functions (called per page render), so a
# snapshot refresh shows up on the next page load without a server restart.


def kpi_card(bg, fg, label, value, sub, spark_color, spark_data):
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Text(label, size="sm", fw=600, c=fg),
                dmc.Text(value, fw=700, size="28px", c=fg, className="tabular-nums"),
                dmc.Group(
                    [
                        dmc.Text(sub, size="xs", c=fg, opacity=0.75),
                        dmc.Sparkline(
                            data=spark_data[-24:],
                            color=spark_color,
                            h=30,
                            w=78,
                            strokeWidth=2,
                        ),
                    ],
                    justify="space-between",
                    align="center",
                    wrap="nowrap",
                    gap="xs",
                ),
            ],
            gap=2,
        ),
        bg=bg,
        p="md",
        radius="lg",
        style={"flex": "1 1 200px", "minWidth": 200},
    )


def kpi_strip():
    kpis = loader.kpis()
    monthly_values = loader.monthly()["postings"].tolist()
    return dmc.Group(
        [
            kpi_card(TEAL, INK, "Unique Postings", f"{kpis['unique_total']:,}",
                     f"{kpis['raw_total']:,} raw ingested", "#0EA5A0", monthly_values),
            kpi_card(PURPLE, "white", "Remote (Standardized)", f"{kpis['remote_pct']:.1%}",
                     f"{kpis['remote_count']:,} postings", "#E9D5FF", monthly_values),
            kpi_card(BEIGE, INK, "With Salary Data", f"{kpis['salary_pct']:.1%}",
                     f"{kpis['salary_count']:,} of {kpis['unique_total']:,}", "#D97706", monthly_values),
            kpi_card(GREEN, INK, "Avg Salary Envelope",
                     f"${kpis['avg_salary_min']/1000:.0f}k–${kpis['avg_salary_max']/1000:.0f}k",
                     "avg floor → avg ceiling", "#16A34A", monthly_values),
        ],
        gap="md",
        align="stretch",
        wrap="wrap",
    )


def envelope_card():
    kpis = loader.kpis()
    skills = loader.df("skills")
    top_skill = skills.iloc[0]
    top_level = loader.seniority_single().iloc[0]
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Group([dmc.Text("Salary Envelope", fw=700), provenance_link("overall_salary")], justify="space-between"),
                dmc.Paper(
                    dmc.Group(
                        [
                            dmc.Stack(
                                [
                                    dmc.Text("Avg Ceiling", size="xs", c="rgba(255,255,255,0.8)"),
                                    dmc.Text(f"${kpis['avg_salary_max']/1000:.1f}k",
                                             c="white", fw=700, size="26px", className="tabular-nums"),
                                ],
                                gap=0,
                            ),
                            dmc.Badge(
                                f"+{top_level['seniority_std'].lower()} tops at "
                                f"${top_level['avg_salary_max']/1000:.0f}k",
                                color="teal", variant="light",
                            ),
                        ],
                        justify="space-between",
                    ),
                    bg=PURPLE,
                    p="md",
                    radius="lg",
                ),
                dmc.Paper(
                    dmc.Group(
                        [
                            dmc.Stack(
                                [
                                    dmc.Text("Avg Floor", size="xs", c="rgba(255,255,255,0.7)"),
                                    dmc.Text(f"${kpis['avg_salary_min']/1000:.1f}k",
                                             c="white", fw=700, size="20px", className="tabular-nums"),
                                ],
                                gap=0,
                            ),
                            dmc.ThemeIcon(
                                DashIconify(icon="solar:arrow-right-up-bold", width=20),
                                color="white", variant="light", radius="xl",
                            ),
                        ],
                        justify="space-between",
                    ),
                    bg=INK,
                    p="md",
                    radius="lg",
                ),
                dmc.Text("Top Demanded Skill", size="xs", c="dimmed", mt="xs"),
                dmc.Group(
                    [
                        dmc.Avatar(top_skill["skill"][:2].upper(), color="brand", radius="md"),
                        dmc.Text(top_skill["skill"], fw=600),
                        dmc.Text(f"{int(top_skill['job_count']):,} postings",
                                 c="dimmed", size="sm", ml="auto", className="tabular-nums"),
                    ],
                    gap="xs",
                ),
            ],
            gap="sm",
        ),
        p="lg",
        style={"flex": "1 1 300px"},
    )


def trend_card():
    d = loader.monthly_for_range("all")
    peak = d.loc[d["postings"].idxmax()]
    peak_label = pd.Timestamp(peak["date"]).strftime("%b %Y")
    stats = dmc.SimpleGrid(
        [
            _stat("Peak Month", peak_label, f"{int(peak['postings'])} postings"),
            _stat("Latest Month", d["date"].iloc[-1], f"{int(d['postings'].iloc[-1])} postings"),
            _stat("12-Mo Average", f"{int(d['postings'].tail(12).mean())}", "postings / month"),
            _stat("Coverage", f"{len(d)} months",
                  f"{d['date'].iloc[0]} – {d['date'].iloc[-1]}"),
        ],
        cols=2,
        spacing="xs",
        verticalSpacing="xs",
        mt="md",
    )
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Group(
                    [
                        dmc.Group([dmc.Text("Postings Over Time", fw=700), provenance_link("monthly")], gap="sm"),
                        dmc.SegmentedControl(
                            id="trend-range",
                            data=[{"label": "1Y", "value": "1y"},
                                  {"label": "3Y", "value": "3y"},
                                  {"label": "All", "value": "all"}],
                            value="all",
                            color="brand",
                            size="xs",
                        ),
                    ],
                    justify="space-between",
                ),
                dmc.AreaChart(
                    id="trend-chart",
                    data=d.to_dict("records"),
                    dataKey="date",
                    series=[{"name": "postings", "color": "brand.6"}],
                    h=250,
                    withGradient=True,
                    fillOpacity=0.25,
                    curveType="monotone",
                    withDots=False,
                    mt="sm",
                ),
                stats,
            ],
            gap="xs",
        ),
        p="lg",
        style={"flex": "2 1 480px"},
    )


def _stat(label, value, sub):
    return dmc.Stack(
        [
            dmc.Text(label, size="xs", c="dimmed"),
            dmc.Text(value, fw=700, size="lg", className="tabular-nums"),
            dmc.Text(sub, size="xs", c="dimmed"),
        ],
        gap=0,
    )


def policy_card():
    policy = loader.policy_summary()
    seg_colors = ["brand.6", "gray.5", "#0EA5A0", "gray.3", "#D9A514", "#F78AC0"]
    donut_data = [
        {"name": r["policy"], "value": int(r["job_count"]), "color": seg_colors[i]}
        for i, (_, r) in enumerate(policy.iterrows())
    ]
    total = policy["job_count"].sum()
    bars = dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Text(r["policy"], size="sm", style={"minWidth": 110}),
                    dmc.Progress(
                        value=r["job_count"] / total * 100,
                        color="brand" if i == 0 else "gray",
                        size="sm",
                        flex=1,
                    ),
                    dmc.Text(f"{r['job_count']/total:.1%}", size="sm", className="tabular-nums"),
                ],
                gap="sm",
            )
            for i, (_, r) in enumerate(policy.iterrows())
        ],
        gap="xs",
    )

    skills = loader.df("skills").head(5)
    smax = int(skills.iloc[0]["job_count"])
    skills_panel = dmc.Stack(
        [
            dmc.Group(
                [dmc.Text("Most Demanded Skills", fw=700), provenance_link("skills")],
                justify="space-between",
                wrap="nowrap",
            ),
            *[
                dmc.Group(
                    [
                        dmc.Text(r["skill"], size="sm", style={"minWidth": 74}),
                        dmc.Progress(
                            value=r["job_count"] / smax * 100,
                            color="brand",
                            size="sm",
                            flex=1,
                        ),
                        dmc.Text(f"{int(r['job_count']):,}", size="sm",
                                 className="tabular-nums", ta="right"),
                    ],
                    gap="xs",
                    wrap="nowrap",
                )
                for _, r in skills.iterrows()
            ],
            dmc.Anchor(
                dmc.Button("View all →", variant="light", color="brand", size="compact-xs"),
                href="/skills",
            ),
        ],
        gap="sm",
        style={
            "flex": "1 1 230px",
            "minWidth": 230,
            "borderLeft": "1px solid var(--mantine-color-default-border)",
            "paddingLeft": "var(--mantine-spacing-lg)",
        },
    )

    # Two titled columns: each column carries its own title at the top, so
    # "Remote Work Policy" and "Most Demanded Skills" share a baseline and the
    # columns wrap independently on narrow panes.
    policy_col = dmc.Stack(
        [
            dmc.Group([dmc.Text("Remote Work Policy", fw=700), provenance_link("policy")], justify="space-between"),
            dmc.Group(
                [
                    dmc.DonutChart(
                        data=donut_data,
                        size=150,
                        thickness=28,
                        withTooltip=True,
                        tooltipDataSource="segment",
                        chartLabel=f"{total:,}",
                        strokeColor="var(--mantine-color-body)",
                    ),
                    bars,
                ],
                gap="lg",
                align="center",
                wrap="wrap",
            ),
            dmc.Text("Standardized values; 20% of postings carry combo policies.",
                     size="xs", c="dimmed"),
        ],
        gap="sm",
        style={"flex": "3 1 420px", "minWidth": 320},
    )

    return dmc.Paper(
        dmc.Group(
            [policy_col, skills_panel],
            gap="lg",
            align="stretch",
            wrap="wrap",
        ),
        p="lg",
        style={"flex": "2 1 520px"},
    )


def dumbbell_fig(dark: bool = False):
    seniority = loader.seniority_single()
    ink = "#E9E9EE" if dark else INK
    grid = "#33334A" if dark else "#E5E4F2"
    connector = "#4A4A63" if dark else "#D6D3F5"
    fig = go.Figure()
    for _, r in seniority.iterrows():
        fig.add_trace(go.Scatter(
            x=[r["avg_salary_min"], r["avg_salary_max"]], y=[r["seniority_std"]] * 2,
            mode="lines", line={"color": connector, "width": 3},
            hoverinfo="skip", showlegend=False,
        ))
    fig.add_trace(go.Scatter(
        x=seniority["avg_salary_min"], y=seniority["seniority_std"], mode="markers",
        name="Avg Floor", marker={"color": "#0EA5A0", "size": 11},
        hovertemplate="%{y} avg floor: $%{x:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=seniority["avg_salary_max"], y=seniority["seniority_std"], mode="markers",
        name="Avg Ceiling", marker={"color": "#9B7BFF" if dark else PURPLE, "size": 11},
        hovertemplate="%{y} avg ceiling: $%{x:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, sans-serif", "color": ink, "size": 12},
        margin={"l": 10, "r": 20, "t": 10, "b": 10}, height=380,
        legend={"orientation": "h", "y": 1.06, "x": 0},
        xaxis={"tickformat": "$,.0f", "gridcolor": grid, "zeroline": False,
               "title": {"text": "USD per year"}},
        yaxis={"automargin": True},
    )
    return fig


def companies_watchlist():
    companies = loader.df("companies")
    rows = [
        dmc.Group(
            [
                dmc.Avatar(name[:2].upper(), color="brand", variant="light", radius="md"),
                dmc.Text(name, size="sm", fw=600, style={"flex": 1}),
                dmc.Text(f"{int(cnt):,} postings", size="sm", c="dimmed", className="tabular-nums"),
            ],
            gap="xs",
            wrap="nowrap",
        )
        for name, cnt in companies[["company", "job_count"]].itertuples(index=False)
    ]
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Group(
                    [
                        dmc.Group([dmc.Text("Top Companies", fw=700), provenance_link("companies")], gap="sm"),
                        dmc.Anchor(
                            dmc.Button("View all →", variant="light", color="brand", size="compact-xs"),
                            href="/companies",
                        ),
                    ],
                    justify="space-between",
                ),
                dmc.Stack(rows, gap="xs"),
            ],
            gap="sm",
        ),
        p="lg",
        style={"flex": "1 1 320px"},
    )


def layout():
    return dmc.Stack(
        [
            kpi_strip(),
            dmc.Group([envelope_card(), trend_card(), policy_card()],
                      gap="md", align="stretch", wrap="wrap"),
            dmc.Group([dumbbell_card(), companies_watchlist()],
                      gap="md", align="stretch", wrap="wrap"),
        ],
        gap="md",
    )


def dumbbell_card(dark: bool = False):
    return dmc.Paper(
        dmc.Stack(
            [
                dmc.Group([dmc.Text("Salary by Seniority", fw=700), provenance_link("seniority")], justify="space-between"),
                dcc.Graph(figure=dumbbell_fig(dark), id="seniority-dumbbell",
                          config={"displayModeBar": False}, style={"height": "380px"}),
                dmc.Text("Intern's $222k ceiling reflects a tiny sample — treat as noise.",
                         size="xs", c="dimmed"),
            ],
            gap="xs",
        ),
        p="lg",
        style={"flex": "2 1 480px"},
    )
