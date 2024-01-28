from rich import print
from rich.panel import Panel
from rich.table import Table

from . import __version__


def print_startup_info(base_url, route_prefix, api_key, fwd_key, /, style, **kwargs):
    """
    Prints the startup information of the application.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv(".env")
    except Exception:
        ...
    route_prefix = route_prefix or "/"
    if not isinstance(api_key, str):
        api_key = True if len(api_key) else False
    if not isinstance(fwd_key, str):
        fwd_key = True if len(fwd_key) else False
    table = Table(title="", box=None, width=61)

    metric = {
        "base url": {
            'value': base_url,
        },
        "route prefix": {
            'value': route_prefix,
        },
        "api keys": {
            'value': str(api_key),
        },
        "forward keys": {
            'value': str(fwd_key),
            'style': "#62E883" if fwd_key or not api_key else "red",
        },
    }
    table.add_column("", justify='left', width=12)
    table.add_column("", justify='left')
    for key, value in metric.items():
        if value['value']:
            table.add_row(key, value['value'], style=value.get('style', style))
    for key, value in kwargs.items():
        if value:
            table.add_row(key, str(value), style=style)

    print(
        Panel(
            table,
            title=f"🤗 openai-forward (v{__version__}) is ready to serve! ",
            expand=False,
        )
    )


def print_rate_limit_info(
    backend: str,
    strategy: str,
    global_req_rate_limit: str,
    req_rate_limit: dict,
    token_rate_limit: dict,
    **kwargs,
):
    """
    Print rate limit information.
    """
    table = Table(title="", box=None, width=61)
    table.add_column("")
    table.add_column("", justify='left')
    backend = backend or "memory"
    table.add_row("backend", backend, style='#7CD9FF')
    if strategy:
        table.add_row("strategy", strategy, style='#7CD9FF')

    if global_req_rate_limit:
        table.add_row(
            "global rate limit", f"{global_req_rate_limit} (req)", style='#C5FF95'
        )
    for key, value in req_rate_limit.items():
        table.add_row(key, f"{value} (req)", style='#C5FF95')

    for key, value in token_rate_limit.items():
        if isinstance(value, float):
            value = f"{value:.4f} s/token"
        table.add_row(key, f"{value} (token)", style='#C5FF95')

    for key, value in kwargs.items():
        table.add_row(key, str(value), style='#C5FF95')

    print(Panel(table, title="⏱️ Rate Limit configuration", expand=False))
