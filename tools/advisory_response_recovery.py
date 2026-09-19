"""Offline, auditable recovery of invalid JSON string escapes only.

This does not alter model requests, valid JSON escapes, object structure, or
classifier fields. Callers must retain raw text, edits, and source hashes, then
run ordinary JSON parsing and the unchanged adjudicator validation.
"""


def repair_invalid_string_escapes(raw):
    output = []
    edits = []
    in_string = False
    index = 0
    while index < len(raw):
        char = raw[index]
        if char == '"':
            in_string = not in_string
        if in_string and char == '\\' and index + 1 < len(raw):
            following = raw[index + 1]
            if following not in '"\\/bfnrtu':
                output.append('\\')
                edits.append({'offset': index, 'escape': raw[index:index + 2],
                              'action': 'escape literal backslash'})
            output.extend((char, following))
            index += 2
            continue
        output.append(char)
        index += 1
    return ''.join(output), edits
