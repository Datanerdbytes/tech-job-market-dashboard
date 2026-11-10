"""Tech Job Market dashboard — Dash + Dash Mantine Components entry point."""

import os

import dash
import dash_mantine_components as dmc
from dash import dcc, page_container

# DMC 3.x requires React 19 (documented in the DMC getting-started guide).
dash._dash_renderer._set_react_version("19.2.4")

from callbacks import *  # noqa: F401,F403,E402  (registers callbacks)
from layout.shell import header, navbar  # noqa: E402
from theme import THEME  # noqa: E402

# The built-in MCP server is a local-dev convenience; never expose it on a
# public deployment (opt in with DASH_MCP=1 when running locally).
_ENABLE_MCP = os.environ.get("DASH_MCP", "0") == "1"
_DEBUG = os.environ.get("DASH_DEBUG", "0") == "1"

app = dash.Dash(
    __name__,
    use_pages=True,
    title="Tech Job Market Insights",
    suppress_callback_exceptions=True,
    enable_mcp=_ENABLE_MCP,
)

def serve_layout():
    """Built per request so shell chrome (freshness badge, nav) re-reads the
    snapshot cache on every full page load — a data refresh shows up after a
    browser reload, no server restart needed."""
    return dmc.MantineProvider(
        id="mantine-provider",
        theme=THEME,
        defaultColorScheme="light",
        forceColorScheme="light",
        children=dmc.AppShell(
            header={"height": 72},
            navbar={"width": 280, "breakpoint": "sm", "collapsed": {"mobile": True}},
            padding="xl",
            children=[
                dcc.Location(id="app-url", refresh=False),
                dcc.Store(id="note-scroll-dummy"),
                header(),
                navbar(),
                dmc.AppShellMain(
                    dmc.Container(page_container, size="1600", fluid=False)
                ),
            ],
        ),
    )


app.layout = serve_layout

server = app.server

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", "8050")), debug=_DEBUG)
