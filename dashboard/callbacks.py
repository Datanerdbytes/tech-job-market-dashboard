"""Global callbacks: trend range filter, company measure toggle, theme toggle."""

from dash import Input, MATCH, Output, State, clientside_callback, callback

from data import loader


@callback(
    Output({"type": "nav-link", "index": MATCH}, "active"),
    Input("app-url", "pathname"),
    State({"type": "nav-link", "index": MATCH}, "id"),
)
def set_active_nav(pathname, nav_id):
    href = nav_id["index"]
    if href == "/":
        return pathname == "/"
    return pathname.startswith(href)


@callback(
    Output("trend-chart", "data"),
    Input("trend-range", "value"),
    prevent_initial_call=True,
)
def update_trend(rng):
    return loader.monthly_for_range(rng or "all").to_dict("records")


@callback(
    Output("company-chart", "data"),
    Output("company-chart-caption", "children"),
    Output("company-note-link", "href"),
    Input("company-measure", "value"),
    prevent_initial_call=True,
)
def update_companies(measure):
    if measure == "salary":
        data = loader.df("company_salary")
        caption = ("Average posted salary ceiling per company — small-sample "
                   "outliers rank first (only 9.5% of postings report salary).")
        note = "/notes#note-company_salary"
    else:
        data = loader.df("companies")
        caption = "Postings count across the gold layer."
        note = "/notes#note-companies"
    rows = [{"company": r["company"],
             "value": int(r["job_count"] if measure == "postings" else r["avg_salary_max"])}
            for _, r in data.iterrows()]
    return rows, caption, note


# Jump-and-flash: when a provenance link lands on /notes#note-<dataset>,
# scroll to the card and flash it. The page content renders asynchronously,
# so poll briefly for the element.
clientside_callback(
    """
    function(hash) {
        if (!hash || hash.length < 2) return window.dash_clientside.no_update;
        const target = hash.slice(1);
        let tries = 0;
        const timer = setInterval(() => {
            const el = document.getElementById(target);
            tries += 1;
            if (el) {
                clearInterval(timer);
                el.scrollIntoView({behavior: 'smooth', block: 'center'});
                el.classList.remove('note-flash');
                void el.offsetWidth;  // restart the CSS animation
                el.classList.add('note-flash');
                setTimeout(() => el.classList.remove('note-flash'), 2400);
                // correct for late layout shifts (accordions, fonts, page swap)
                setTimeout(() => el.scrollIntoView({behavior: 'smooth', block: 'center'}), 900);
            } else if (tries > 20) {
                clearInterval(timer);
            }
        }, 150);
        return true;
    }
    """,
    Output("note-scroll-dummy", "data"),
    Input("app-url", "hash"),
    prevent_initial_call=True,
)


@callback(
    Output("mantine-provider", "forceColorScheme"),
    Output("seniority-dumbbell", "figure"),
    Input("theme-toggle", "n_clicks"),
    State("mantine-provider", "forceColorScheme"),
    prevent_initial_call=True,
)
def toggle_theme(n_clicks, current):
    dark = (current or "light") == "dark"
    from pages.overview import dumbbell_fig
    return ("light" if dark else "dark"), dumbbell_fig(dark=not dark)
