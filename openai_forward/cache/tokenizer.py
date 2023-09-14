def encode_as_pieces(sentence):
    words = []

    # 定义分隔符集合
    # todo: replace with third-party library
    # delimiters = set(['：', '。', '，', '！', '？', ':', '.', ',', '!', '?'])
    delimiters = {
        '：',
        '。',
        '，',
        '、',
        '！',
        '？',
        ':',
        '.',
        ',',
        '!',
        '?',
        ' ',
        '\n',
        '\t',
        '\r',
        '\u3000',
        '\u202f',
        '\u2009',
    }

    buffer = ""
    for char in sentence:
        if '\u4e00' <= char <= '\u9fff' or char in delimiters:
            if buffer:
                words.append(buffer)
                buffer = ""
            words.append(char)
        elif char == ' ':  # 如果字符是空格
            if buffer:
                words.append(buffer)
                buffer = ""
            words.append(char)
        else:
            buffer += char

    if buffer:
        words.append(buffer)

    return words
