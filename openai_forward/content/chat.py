import orjson
from orjson import JSONDecodeError
from loguru import logger
from httpx._decoders import LineDecoder

decoder = LineDecoder()


def _parse_iter_line_content(line: str):
    line = line[6:]
    try:
        line_dict = orjson.loads(line)
        return line_dict['choices'][0]['delta']['content']
    except JSONDecodeError:
        return ""
    except KeyError:
        return ""


def log_chat_completions(bytes_: bytes):
    txt_lines = decoder.decode(bytes_.decode('utf-8'))
    line0 = txt_lines[0]
    target_info = dict()
    if line0.startswith("data:"):
        line0 = orjson.loads(line0[6:])
        msg = line0['choices'][0]['delta']
    else:
        line0 = orjson.loads(line0)
        msg = line0['choices'][0]['message']

    target_info['created'] = line0['created']
    target_info['id'] = line0['id']
    target_info['model'] = line0['model']
    target_info['role'] = msg['role']
    target_info['content'] = msg.get("content", "")
    # loop for stream
    for line in txt_lines[1:]:
        if line in ("", "\n", "\n\n"):
            continue
        elif line.startswith("data: "):
            target_info['content'] += _parse_iter_line_content(line)
        else:
            logger.warning(f"line not startswith data: {line}")
    return target_info
