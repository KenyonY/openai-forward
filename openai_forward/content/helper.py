from httpx._decoders import LineDecoder, TextChunker, TextDecoder
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


# ------------- parse bytes -------------


def iter_text(iter_tytes: list):
    decoder = TextDecoder("utf-8")
    chunker = TextChunker()
    for byte_content in iter_tytes:
        text_content = decoder.decode(byte_content)
        for chunk in chunker.decode(text_content):
            yield chunk
    text_content = decoder.flush()
    for chunk in chunker.decode(text_content):
        yield chunk
    for chunk in chunker.flush():
        yield chunk


def parse_to_lines(iter_bytes: list) -> list:
    decoder = LineDecoder()
    lines = []
    for text in iter_text(iter_bytes):
        lines.extend(decoder.decode(text))
    lines.extend(decoder.flush())
    return lines
