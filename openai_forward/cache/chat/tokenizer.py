try:
    import tiktoken

    TIKTOKEN_VALID = True

except ImportError:
    print("Warning: `tiktoken` not found. Install with `pip install tiktoken`.")
    TIKTOKEN_VALID = False


def encode_as_pieces(sentence):
    words = []

    delimiters = {'：', '。', '，', '、', '！', '？', ':', '.', ',', '!', '?'}

    buffer = ""
    for char in sentence:
        if '\u4e00' <= char <= '\u9fff' or char in delimiters:
            if buffer:
                words.append(buffer)
                buffer = ""
            words.append(char)
        elif char == ' ':
            if buffer:
                words.append(buffer)
                buffer = ""
            words.append(char)
        else:
            buffer += char

    if buffer:
        words.append(buffer)

    return words


def count_tokens(messages, assistant_content, model="gpt-3.5-turbo"):
    """Return the usage information of tokens in the messages list."""
    # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_format_inputs_to_ChatGPT_models.ipynb
    if not TIKTOKEN_VALID:
        print("Warning: `tiktoken` not found. Install with `pip install tiktoken`.")
        raise ImportError
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")

    count_name = 0
    messages_len = len(messages)
    content = ""
    for i in messages:
        content += i['content'] + i['role']
        name = i.get('name')
        if name:
            count_name += 1

    tokens_per_message = 3
    tokens_per_name = 1

    history_tokens = (
        len(encoding.encode(content))
        + (messages_len + 1) * tokens_per_message
        + count_name * tokens_per_name
    )

    assis_tokens = len(encoding.encode(assistant_content))

    total_tokens = history_tokens + assis_tokens
    return {
        "prompt_tokens": history_tokens,
        "completion_tokens": assis_tokens,
        "total_tokens": total_tokens,
    }
