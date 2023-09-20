from typing import List

from rich.console import Console, Text

RoleColor = {
    "system": "#ea4335",
    "user": "#F5A88E",
    "assistant": "#BDADFF",
    "function": "#f79393",
    "preprompt": "#f7d97f",
    "other": "#4285f4",
}

#  ----------- console tools ------------

console = Console()


def print(text="", role: str = None, end="\n", **kwargs):
    style = RoleColor.get(role, None)
    console.print(text, style=style, end=end, **kwargs)


def markdown_print(text="", role: str = None, end="\n", **kwargs):
    from rich.markdown import Markdown

    style = RoleColor.get(role, None)
    console.print(Markdown(text), style=style, end=end, **kwargs)


# ------------- parse sse -------------


def parse_sse_buffer(buffer: bytearray) -> List[str]:
    """
    Parse SSE buffer into a list of SSE message list.

    Args:
        buffer (bytearray): The SSE buffer to parse.

    Returns:
        list: A list of SSE messages.
    """
    sse_str = buffer.decode("utf-8")

    events = sse_str.split("\n\n")
    events.pop()
    return events
