from rich.console import Console, Text

RoleColor = {
    "system": "#ea4335",
    "user": "#F5A88E",
    "assistant": "#BDADFF",
    "function": "#f79393",
    "preprompt": "#f7d97f",
    "other": "#4285f4",
}

console = Console()


def print(text="", role: str = None, end="\n", **kwargs):
    style = RoleColor.get(role, None)
    console.print(text, style=style, end=end, **kwargs)


def markdown_print(text="", role: str = None, end="\n", **kwargs):
    from rich.markdown import Markdown

    style = RoleColor.get(role, None)
    console.print(Markdown(text), style=style, end=end, **kwargs)
