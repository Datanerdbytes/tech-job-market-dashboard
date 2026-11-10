"""AppShell chrome: Fox-stocks-style sidebar + header."""

import dash_mantine_components as dmc
from dash_iconify import DashIconify

from data import loader

NAV_ITEMS = [
    {"label": "Overview", "icon": "solar:widget-4-bold", "href": "/"},
    {"label": "Skills", "icon": "solar:graph-up-bold", "href": "/skills"},
    {"label": "Companies & Locations", "icon": "solar:buildings-2-bold", "href": "/companies"},
    {"label": "Data Notes", "icon": "solar:document-text-bold", "href": "/notes"},
]


def _nav_link(item):
    return dmc.NavLink(
        label=item["label"],
        leftSection=DashIconify(icon=item["icon"], width=20),
        href=item["href"],
        id={"type": "nav-link", "index": item["href"]},
        active=False,
        color="brand",
        variant="light",
        mb=4,
    )


def navbar():
    return dmc.AppShellNavbar(
        p="md",
        children=[
            dmc.AppShellSection(
                dmc.Group(
                    [
                        dmc.ThemeIcon(
                            DashIconify(icon="solar:chart-square-bold", width=20),
                            color="brand",
                            radius="md",
                            size=36,
                        ),
                        dmc.Text("TechJob Market", fw=700, size="lg"),
                    ],
                    gap="xs",
                ),
                pb="lg",
            ),
            dmc.AppShellSection(
                dmc.Stack(
                    [
                        dmc.Text("ANALYTICS", c="dimmed", size="xs", fw=600, px="xs"),
                        *[_nav_link(item) for item in NAV_ITEMS],
                    ],
                    gap=2,
                ),
                grow=True,
            ),
            dmc.AppShellSection(
                dmc.Stack(
                    [
                        dmc.Paper(
                            dmc.Stack(
                                [
                                    dmc.ThemeIcon(
                                        DashIconify(icon="solar:lightbulb-bold", width=20),
                                        color="gray",
                                        variant="light",
                                        radius="xl",
                                    ),
                                    dmc.Text("Thoughts on the Data", size="sm", fw=600, ta="center"),
                                    dmc.Text(
                                        f"Only {loader.kpis()['salary_pct']:.1%} of postings "
                                        "report salary — every salary insight covers that "
                                        "subset, not the whole market.",
                                        size="xs",
                                        c="dimmed",
                                        ta="center",
                                    ),
                                ],
                                align="center",
                                gap=6,
                            ),
                            bg="var(--mantine-color-green-1)",
                            p="md",
                            radius="lg",
                        ),
                        dmc.Text(
                            f"Data as of {loader.as_of_label()}",
                            size="xs",
                            c="dimmed",
                            ta="center",
                            mt="sm",
                        ),
                    ],
                    gap="xs",
                ),
                pb="md",
            ),
        ],
    )


def header():
    kpis = loader.kpis()
    return dmc.AppShellHeader(
        h=72,
        px="lg",
        children=dmc.Group(
            [
                dmc.Stack(
                    [dmc.Text("Tech Job Market Insights", fw=700)],
                    gap=0,
                ),
                dmc.Group(
                    [
                        dmc.TextInput(
                            placeholder="Semantic-layer powered",
                            leftSection=DashIconify(icon="solar:magnifer-linear", width=18),
                            disabled=True,
                            w=260,
                            size="sm",
                        ),
                        dmc.Badge(
                            f"{kpis['unique_total']:,} unique postings",
                            color="brand",
                            variant="light",
                            size="lg",
                        ),
                        dmc.ActionIcon(
                            DashIconify(icon="solar:moon-stars-bold", width=20),
                            id="theme-toggle",
                            variant="default",
                            size="lg",
                            radius="md",
                            n_clicks=0,
                        ),
                    ],
                    gap="sm",
                ),
            ],
            justify="space-between",
            h="100%",
        ),
    )
