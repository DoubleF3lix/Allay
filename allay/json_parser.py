# Thanks fizzy <3 (https://github.com/vberlier/tokenstream/blob/main/examples/json.py)
import re

ESCAPE_REGEX = re.compile(r"\\.")
ESCAPE_SEQUENCES = {
    r"\n": "\n",
    r"\"": '"',
    r"\\": "\\",
}


def unquote_string(token):
    return ESCAPE_REGEX.sub(lambda match: ESCAPE_SEQUENCES[match[0]], token.value[1:-1])


def parse_json(stream):
    with stream.syntax(
        curly=r"\{|\}",
        bracket=r"\[|\]",
        string=r'"(?:\\.|[^"\\])*"',
        number=r"\d*\.?\d+",
        colon=r":",
        comma=r",",
        boolean=r"true|false",
    ):
        curly, bracket, string, number, boolean = stream.expect(
            ("curly", "{"), ("bracket", "["), "string", "number", "boolean"
        )

        if curly:
            result = {}

            for key in stream.collect("string"):
                stream.expect("colon")
                result[unquote_string(key)] = parse_json(stream)

                if not stream.get("comma"):
                    break

            stream.expect(("curly", "}"))
            return result

        elif bracket:
            if stream.get(("bracket", "]")):
                return []

            result = [parse_json(stream)]

            for _ in stream.collect("comma"):
                result.append(parse_json(stream))

            stream.expect(("bracket", "]"))
            return result

        elif string:
            return unquote_string(string)

        elif number:
            return float(number.value) if "." in number.value else int(number.value)

        elif boolean:
            return bool(boolean.value)
