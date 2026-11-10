"""Fox Stocks-inspired theme for the Tech Job Market dashboard."""

# Brand scale anchored at the Fox Stocks purple #6425FE (index 6).
BRAND = [
    "#F3EFFE", "#E6DCFD", "#CBB6FB", "#B093FA", "#9570F8",
    "#7C4DF6", "#6425FE", "#5420D8", "#441AB2", "#34148C",
]

# Fox Stocks accent palette (template teal/beige/green cards and sparklines).
TEAL = "#A6F7E2"
BEIGE = "#FFE5A5"
GREEN = "#B9F5C8"
PINK = "#FFD6F5"
PURPLE = "#6425FE"
INK = "#2C2C2C"

# Ordered series colors for multi-series charts.
SERIES = [PURPLE, "#0EA5A0", BEIGE, "#3FA860", PINK, "#7C4DF6"]

THEME = {
    "colors": {"brand": BRAND},
    "primaryColor": "brand",
    "primaryShade": 6,
    "defaultRadius": "md",
    "fontFamily": "Inter, ui-sans-serif, system-ui, sans-serif",
    "headings": {"fontWeight": "600"},
    "components": {
        "Paper": {"defaultProps": {"radius": "lg", "withBorder": True}},
        "Card": {"defaultProps": {"radius": "lg", "withBorder": True}},
    },
}
