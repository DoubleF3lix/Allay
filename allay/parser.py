import json
from contextlib import contextmanager
from typing import Union

from tokenstream import TokenStream
from tokenstream.error import InvalidSyntax

from allay.json_parser import parse_json


class DefinitionAlreadyExists(Exception):
    ...


class Parser:
    """
    Parser - The base class for all allay parsers

    Args:
        indent (int, optional): Indentation level. Ignored if ``json_dump`` is False. Defaults to None.
        json_dump (bool, optional): Whether to dump the output as JSON in a string. Defaults to None.
        definition_delimeter (str, optional): The delimeter that should separate the definitions from the text. Defaults to "#ALLAYDEFS\n".
    """

    def __init__(
        self,
        indent: int = None,
        json_dump: bool = None,
        definition_delimeter: str = "#ALLAYDEFS\n",
    ) -> None:
        # Set default parser options
        self.indent = indent
        self.json_dump = json_dump
        self.set_defaults(indent, json_dump)

        self.definition_delimeter = definition_delimeter

        self.patterns = {}
        self.templates = {}
        self.parent = ""

    def parse(
        self, text: str, indent: int = None, json_dump: bool = None
    ) -> Union[str, dict]:
        """
        parse - Converts a string into a text-component using the Allay format

        Args:
            text (str): The text to parse, or a file path
            indent (int, optional): Indentation level. Ignored if ``json_dump`` is False. Defaults to None.
            json_dump (bool, optional): Whether to dump the output as JSON in a string. Defaults to None.

        Raises:
            InvalidSyntax: The syntax is invalid

        Returns:
            Union[str, dict]: The text-component
        """
        # Grab defaults (if neither defaults nor function-level config is set, then it should remain None and work fine)
        if not indent and self.indent:
            indent = self.indent

        if json_dump is None:
            json_dump = self.json_dump if self.json_dump is not None else True

        # Check if it's a file, and if it is, use the file contents as the input
        try:
            file = f'File "{text}"'  # File path
            with open(text, "r") as infile:
                text = infile.read()
        except OSError as error:
            file = '"src"'

        # Print errors but with pizzaz
        try:
            stream = TokenStream(self.pre_process(text))
            output = self.internal_parse(stream)

            self.parent = ""

            if json_dump:
                return json.dumps(output, indent=indent)
            return output

        except InvalidSyntax as error:
            error_line = error.location.lineno
            error_column = error.location.colno
            raise InvalidSyntax(
                f"Fatal error:\n\t{file}, line {error_line}\n\t\t{stream.source.split(chr(10))[error_line - 1]}\n\t\t{' ' * (error_column - 1)}^\nInvalidSyntax: {str(error)}".expandtabs(
                    2
                )
            )

    def set_defaults(self, indent: int = None, json_dump: bool = None) -> None:
        """
        set_defaults - Sets the default values for the parse function

        Args:
            indent (int, optional): Indentation level. Ignored if ``json_dump`` is False. Defaults to None.
            json_dump (bool, optional): Whether to dump the output as JSON in a string. Defaults to None.
        """
        if indent:
            self.indent = indent

        if json_dump:
            self.json_dump = json_dump

    def set_parent(
        self, stream: TokenStream, auto_generate_stream: bool = True
    ) -> dict:
        if auto_generate_stream and not isinstance(stream, TokenStream):
            stream = TokenStream(stream)

        with stream.syntax(paren=r"\(|\)", null=r"null|NULL"):
            if stream.get(("paren", "(")):
                with self.primary_syntax_definitions(stream):
                    contents = self.parse_modifiers(stream)
                stream.expect(("paren", ")"))

                self.parent = contents
                return contents

            elif stream.get("null"):
                self.parent = ""
                return ""
            else:
                raise InvalidSyntax(
                    "Expected either modifier or null for parent, got neither"
                )

    def pre_process(self, text: str) -> str:
        # Separate the special components (patterns and templates)
        defs_end_index = text.find(self.definition_delimeter)

        # The split token was found
        if defs_end_index != -1:
            stream = TokenStream(text[:defs_end_index].strip())
            self.parse_definitions(stream)

            # Remove #ALLAYDEFS (and the following newline) from the text
            text = text[defs_end_index + len(self.definition_delimeter) :]

        return text.strip()

    def get_string(self, stream: Union[str, TokenStream]) -> str:
        return stream.expect("string").value[1:-1].replace('\\"', '"')

    @contextmanager
    def primary_syntax_definitions(self, stream: TokenStream):
        with stream.syntax(
            # Symbols
            escape=r"\\.",
            sqrbr=r"\[|\]",
            brace=r"\{|\}",
            scope=r"<|>",
            equals=r"=",
            text=r"[^\[\]\{\}<>\\]+",
            arrow=r" ?[-=]> ?",
            # Types
            hex_code=r"#[0-9a-fA-F]{6}",
            url=r"http(s)?:\/\/[^(),]+\.[^(),]+",
            integer=r"[\d]+",
            color=r"black|dark_blue|dark_green|dark_aqua|dark_red|dark_purple|gold|gray|dark_gray|blue|green|aqua|red|light_purple|yellow|white|reset",
            keybind=r"advancements|attack|back|chat|command|drop|forward|fullscreen|hotbar|inventory|jump|left|loadToolbarActivator|pickItem|playerlist|right|saveToolbarActivator|screenshot|smoothCamera|sneak|socialInteractions|spectatorOutlines|sprint|swapOffhand|togglePerspective|use",
            selector=r"@[parse](\[.*\])?",
            boolean=r"true|false",
            string=r'"(?:\\.|[^"\\])*"',
            # Keywords sorted by type
            kw_json=r"hover_item",
            kw_scope=r"hover_text",
            kw_color=r"color",
            kw_link=r"link",
            kw_string=r"copy|suggest|run|insertion|font",
            kw_bool=r"bold|italic|obfuscated|strikethrough|underlined",
            kw_integer=r"page",
            kw_standalone=r"block|entity|storage|selector|translate|score|nbt|separator|interpret|sep|key|with",
        ):
            yield

    def add_definition(
        self,
        type: str,
        name: str,
        stream: Union[str, TokenStream],
        auto_generate_stream: bool,
    ) -> tuple:
        obj = self.patterns if type == "pattern" else self.templates

        name_prefix = "@" if type == "pattern" else "$"
        internal_name = name if name.startswith(name_prefix) else name_prefix + name

        if internal_name in obj:
            raise DefinitionAlreadyExists(
                f"{type.capitalize()} '{name}' has already been defined"
            )

        if auto_generate_stream and not isinstance(stream, TokenStream):
            stream = TokenStream(stream)

        return stream, internal_name

    def add_pattern(
        self,
        name: str,
        stream: Union[str, TokenStream],
        auto_generate_stream: bool = True,
    ) -> Union[str, dict]:
        """
        add_pattern - Adds a pattern to the parser.

        Args:
            name (str): The name of the template. The beginning ``@`` is optional.
            stream (Union[str, TokenStream]): The stream that contains the pattern. Make sure to enclose it in parenthesis. It can be a string or a ``TokenStream`` object. If a string, it will be converted to a ``TokenStream``.
            auto_generate_stream (bool, optional): Whether or not to wrap ``stream`` in a ``TokenStream`` object. Only set this to ``False`` if you're converting it manually. Defaults to True.

        Returns:
            dict: The parsed pattern
        """
        stream, name = self.add_definition(
            "pattern", name, stream, auto_generate_stream
        )

        # Despite being defined in the outer scope, this token needs to be defined in here also because parenthesis are required when using add_pattern directly. Without this token definition, calling this function directly will result in expecting a parenthesis and fail.
        with stream.syntax(paren=r"\(|\)"):
            # Parenthesis should be required in both add_pattern and in-text usage
            stream.expect(("paren", "("))
            with self.primary_syntax_definitions(stream):
                contents = self.parse_modifiers(stream)
            stream.expect(("paren", ")"))

        self.patterns[name] = contents

        return contents

    def add_template(
        self,
        name: str,
        stream: Union[str, TokenStream],
        auto_generate_stream: bool = True,
    ) -> dict:
        """
        add_template - Adds a template to the parser.

        Args:
            name (str): The name of the template. The beginning ``$`` is optional.
            stream (Union[str, TokenStream]): The stream that contains the template. Do not include the surrounding braces. It can be a string or a ``TokenStream`` object. If a string, it will be converted to a ``TokenStream``.
            auto_generate_stream (bool, optional): Whether or not to wrap ``stream`` in a ``TokenStream`` object. Only set this to ``False`` if you're converting it manually. Defaults to True.

        Returns:
            dict: The parsed template
        """
        stream, name = self.add_definition(
            "template", name, stream, auto_generate_stream
        )

        contents = self.internal_parse(stream)

        self.templates[name] = contents

        return contents

    def parse_definitions(self, stream: TokenStream) -> None:
        with stream.syntax(
            pattern=r"@\w+",
            template=r"\$\w+",
            parent=r"PARENT",
            equals=r"=",
            paren=r"\(|\)",
            brace=r"{|}",
        ), stream.intercept("newline"):

            try:
                pattern, template, parent = stream.expect(
                    "pattern", "template", "parent"
                )
                stream.expect("equals")

                if pattern:
                    self.add_pattern(pattern.value, stream, auto_generate_stream=False)

                elif template:
                    # Expected here and not in add_template because braces should NOT be added when add_template is used directly
                    stream.expect(("brace", "{"))
                    self.add_template(
                        template.value, stream, auto_generate_stream=False
                    )
                    stream.expect(("brace", "}"))

                elif parent:
                    self.set_parent(stream, auto_generate_stream=False)

                if stream.get("newline"):
                    # Handle new lines in-between arguments
                    while stream.get("newline"):
                        continue

                    self.parse_definitions(stream)

            except InvalidSyntax as error:
                # Check if there's no data left to parse. This handles there being extra newlines between any arguments and the #ALLAYDEFS keyword. If there's still data left, then there's a syntax error.
                if stream.source[stream.current.location.pos :].strip():
                    raise error

    def internal_parse(self, stream: TokenStream) -> list:
        output = []

        with self.primary_syntax_definitions(stream):
            for sqrbr, brace, escape, text in stream.collect(
                ("sqrbr", "["), ("brace", "{"), "escape", "text"
            ):
                if escape:
                    if escape.value[1] in {
                        "b",
                        "f",
                        "n",
                        "r",
                        "t",
                        "\\",
                        "[",
                        "]",
                        "(",
                        ")",
                        "{",
                        "}",
                        "<",
                        ">",
                    }:
                        output.append(escape.value[1])
                    else:
                        output.append(escape.value)

                elif sqrbr:
                    modified_text = self.internal_parse(stream)
                    stream.expect(("sqrbr", "]"))

                    with stream.syntax(paren=r"\(|\)"):
                        stream.expect(("paren", "("))
                        modifier_contents = self.parse_modifiers(stream)
                        stream.expect(("paren", ")"))

                    output.append(
                        {
                            "modified_text": modified_text,
                            "modifier_contents": modifier_contents,
                        }
                    )

                elif brace:
                    q = self.parse_standalone(stream)
                    output.append(q)

                elif text:
                    output.append(text.value)

            output = self.clean_ast(output)
            output = self.convert_ast_to_json(output)
            return output

    def error_if_scope(self, stream: TokenStream) -> None:
        if stream.data.get("scoped"):
            raise InvalidSyntax("Unexpected scope")

    def parse_non_template_standalone(self, stream: TokenStream) -> dict:
        standalone_contents = {}

        with stream.syntax(text=None, comma=r","):
            selector = stream.get("selector")
            kw_standalone = stream.get("kw_standalone")

            if selector:
                standalone_contents["selector"] = selector.value

            elif kw_standalone:
                if kw_standalone.value in {"sep", "separator"}:
                    stream.expect("equals")
                    standalone_contents["separator"] = self.get_string(stream)

                elif kw_standalone.value == "key":
                    stream.expect("equals")
                    standalone_contents["keybind"] = (
                        "key." + stream.expect("keybind").value
                    )

                elif kw_standalone.value == "translate":
                    stream.expect("equals")
                    standalone_contents["translate"] = self.get_string(stream)

                elif kw_standalone.value == "with":
                    stream.expect("equals")
                    standalone_contents["with"] = parse_json(stream)

                elif kw_standalone.value == "nbt":
                    stream.expect("equals")
                    standalone_contents["nbt"] = self.get_string(stream)

                elif kw_standalone.value in {"block", "entity", "storage"}:
                    stream.expect("equals")
                    standalone_contents[kw_standalone.value] = stream.expect(
                        "string"
                    ).value[1:-1]

                elif kw_standalone.value == "score":
                    stream.expect("equals")
                    player_name = self.get_string(stream)
                    stream.expect("arrow")
                    objective_name = self.get_string(stream)
                    standalone_contents["score"] = {
                        "name": player_name,
                        "objective": objective_name,
                    }

                elif kw_standalone.value == "interpret":
                    if stream.get("equals"):
                        boolean_value = stream.expect("boolean").value
                    else:
                        boolean_value = "true"

                    standalone_contents["interpret"] = boolean_value == "true"

            else:
                raise InvalidSyntax("Unknown standalone element input")

        if stream.get("comma"):
            standalone_contents |= self.parse_non_template_standalone(stream)

        return standalone_contents

    def parse_standalone(self, stream: TokenStream) -> dict:
        standalone_contents = {}

        with stream.syntax(text=None, comma=r",", template=r"\$\w+"):
            if token := stream.peek():
                if token.match("template"):
                    template = stream.expect("template")

                    if (q := template.value) not in self.templates:
                        raise InvalidSyntax(f"Unknown template '{q}'")

                    args = self.parse_template_args(stream)

                    # Turn the template into a string so we can use replace on it
                    template_value = json.dumps(self.templates[q])

                    # Replace all the tokens
                    for index, arg in enumerate(args):
                        template_value = template_value.replace(f"%{index}", arg)

                    # Convert it back into a dictionary
                    standalone_contents = json.loads(template_value)

                else:
                    standalone_contents = self.parse_non_template_standalone(stream)

            stream.expect(("brace", "}"))

            with stream.syntax(paren=r"\(|\)"):
                if stream.get(("paren", "(")):
                    modifier_contents = self.parse_modifiers(stream)
                    stream.expect(("paren", ")"))

                    try:
                        standalone_contents = standalone_contents | modifier_contents
                    except TypeError:
                        raise InvalidSyntax("Modifiers are not supported on templates")

        return standalone_contents

    def parse_template_args(self, stream: TokenStream) -> list:
        args = []
        if stream.get("comma"):
            # 1:-1 to remove quotes
            args.append(self.get_string(stream))
            # Add the previous argument to the list
            args.extend(self.parse_template_args(stream))

        return args

    def parse_modifiers(self, stream: TokenStream) -> dict:
        modifier_contents = {}
        with stream.syntax(
            text=None,
            comma=r",",
            pattern=r"@\w+",
        ):
            (
                kw_json,
                kw_scope,
                kw_string,
                kw_integer,
                kw_bool,
                kw_link,
                url,
                kw_color,
                hex_code,
                color,
                pattern,
            ) = stream.expect(
                "kw_json",
                "kw_scope",
                "kw_string",
                "kw_integer",
                "kw_bool",
                "kw_link",
                "url",
                "kw_color",
                "hex_code",
                "color",
                "pattern",
            )
            if kw_json:
                self.error_if_scope(stream)
                stream.expect("equals")
                json = parse_json(stream)
                if kw_json.value == "hover_item":
                    modifier_contents["hoverEvent"] = {
                        "action": "show_item",
                        "contents": json,
                    }
                else:
                    # Just "with" for now
                    modifier_contents[kw_json.value] = json

            elif kw_scope:  # Just "hover_text" for now
                self.error_if_scope(stream)
                stream.expect("equals")
                stream.expect(("scope", "<"))
                with stream.provide(scoped=True):
                    # Remove the existing parent for a bit
                    q = self.parent
                    self.parent = ""
                    modifier_contents["hoverEvent"] = {
                        "action": "show_text",
                        "contents": self.internal_parse(stream),
                    }
                    # Put the old parent back (even though we shouldn't need it for this parse)
                    self.parent = q
                stream.expect(("scope", ">"))

            elif kw_color or hex_code:
                if kw_color:
                    stream.expect("equals")
                    color, hex_code = stream.expect("color", "hex_code")
                    color = color.value if color else hex_code.value
                else:
                    color = hex_code.value

                modifier_contents["color"] = color

            elif color:
                modifier_contents["color"] = color.value

            elif url or kw_link:
                self.error_if_scope(stream)
                if url:
                    link = url.value
                elif kw_link:
                    stream.expect("equals")
                    link = self.get_string(stream)
                    if not link.startswith("http"):
                        link = f"https://{link}"
                modifier_contents["clickEvent"] = {"action": "open_url", "value": link}

            elif kw_string:
                # r"copy|suggest|run|insertion|font",
                if kw_string.value != "font":
                    self.error_if_scope(stream)
                stream.expect("equals")
                string_value = self.get_string(stream)
                if kw_string.value == "copy":
                    modifier_contents["clickEvent"] = {
                        "action": "copy_to_clipboard",
                        "value": string_value,
                    }
                elif kw_string.value == "suggest":
                    modifier_contents["clickEvent"] = {
                        "action": "suggest_command",
                        "value": string_value,
                    }
                elif kw_string.value == "run":
                    modifier_contents["clickEvent"] = {
                        "action": "run_command",
                        "value": string_value,
                    }
                elif kw_string.value in {"insertion", "font"}:
                    modifier_contents[kw_string.value] = string_value

            elif kw_integer:
                # Just page for now
                self.error_if_scope(stream)
                stream.expect("equals")
                integer_value = stream.expect("integer")
                modifier_contents["clickEvent"] = {
                    "action": "change_page",
                    "value": integer_value.value,
                }

            elif kw_bool:
                if stream.get("equals"):
                    boolean_value = stream.expect("boolean").value
                else:
                    boolean_value = "true"

                modifier_contents[kw_bool.value] = boolean_value == "true"

            elif pattern:
                if (q := pattern.value) not in self.patterns:
                    raise InvalidSyntax(f"Unknown pattern '{q}'")

                modifier_contents |= self.patterns[q]

            if stream.get("comma"):
                modifier_contents |= self.parse_modifiers(stream)

        return modifier_contents

    def clean_ast(self, ast: list) -> list:
        # Merges strings together into one string
        cleaned_ast = ast[:1]
        for elem in ast[1:]:
            if isinstance(elem, str) and isinstance(cleaned_ast[-1], str):
                cleaned_ast[-1] += elem
            else:
                cleaned_ast.append(elem)

        return cleaned_ast

    def convert_ast_to_json(self, ast: list) -> list:
        output = [self.parent or ""]
        for item in ast:
            if isinstance(item, str):
                output.append({"text": item})
            elif isinstance(item, dict):
                # Check if it's a modified block
                if "modifier_contents" in item:
                    if "modified_text" in item:
                        new_block = {"text": item["modified_text"][1]["text"]}
                    else:
                        # Standalone block
                        new_block = item["standalone_contents"]
                    output.append(new_block | item["modifier_contents"])
                # Otherwise it's a standalone
                else:
                    output.append(item)
            elif isinstance(item, list):
                output.append(item)

        return output
