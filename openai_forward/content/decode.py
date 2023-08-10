from httpx._decoders import LineDecoder, TextChunker, TextDecoder


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
