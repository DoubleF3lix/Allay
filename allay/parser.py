import json

from tokenstream import TokenStream
from tokenstream.error import InvalidSyntax

from .json_parser import parse_json


class Parser:
    """
    Parser - The base class for all allay parsers

    Args:
        definition_delimeter (str, optional): The delimeter that should separate the definitions from the text. Defaults to "#ALLAYDEFS\n".
    """

    def __init__(self, definition_delimeter: str = "#ALLAYDEFS\n") -> None:
        self.definition_delimeter = definition_delimeter

    def parse(self, input: str, indent: int = None) -> str:
        """
        parse - Converts a string into a text-component using the Allay format

        Args:
            input (str): The string to parse, or a file path
            indent (int, optional): Indentation level. Defaults to None.

        Raises:
            InvalidSyntax: The syntax is invalid

        Returns:
            str: The text-component
        """
        # Check if it's a file, and if it is, use the file contents as the input
        try:
            file = f'File "{input}"'  # File path
            with open(input, "r") as infile:
                input = infile.read()
        except (FileNotFoundError, OSError) as error:
            file = '"src"'

        # Print errors but with pizzaz
        try:
            stream = TokenStream(self.pre_process(input))
            return json.dumps(self.internal_parse(stream), indent=indent)
        except InvalidSyntax as error:
            error_line = error.location.lineno
            error_column = error.location.colno
            raise InvalidSyntax(
                f"Fatal error:\n\t{file}, line {error_line}\n\t\t{stream.source.split(chr(10))[error_line - 1]}\n\t\t{' ' * (error_column - 1)}^\nInvalidSyntax: {str(error)}".expandtabs(
                    2
                )
            )

    def pre_process(self, text: str) -> str:
        """
        pre_process - Pre-processes the text to isolate any definitions and parse them, as well as clean up the text

        Returns:
            str: The pre-processed text
        """
        # Separate the special components (patterns and templates)
        defs_end_index = text.find(self.definition_delimeter)

        # The split token was found
        if defs_end_index != -1:
            stream = TokenStream(self.trim_newlines(text[:defs_end_index]))
            self.parse_definitions(stream)

            # Remove #ALLAYDEFS (and the following newline) from the text
            text = text[defs_end_index + len(self.definition_delimeter) :]

        return self.trim_newlines(text)

    def trim_newlines(self, text: str) -> str:
        """
        trim_newlines - Removes newlines from the start and end of the text

        Args:
            text (str): The text to trim the newlines of

        Returns:
            str: The trimmed text
        """
        if text.startswith("\n"):
            text = text[1:]
        if text.endswith("\n"):
            text = text[:-1]

        return text

    def parse_definitions(self, stream: TokenStream) -> None:
        """
        parse_definitions - Parses the definition block (anything above the delimeter) and adds them to class variables

        Args:
            stream (TokenStream): The stream to parse

        Raises:
            InvalidSyntax: Invalid syntax was found in a definition
        """
        with stream.syntax(
            pattern=r"@\w+",
            template=r"\$\w+",
            equals=r"=",
            paren=r"\(|\)",
            brace=r"{|}",
            semicolon=r";",
        ), stream.intercept("newline"):

            try:
                pattern, template = stream.expect("pattern", "template")
                stream.expect("equals")
                if pattern:
                    stream.expect(("paren", "("))

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
                        string=r"\"(?:\\.|[^\\\n])*?\"",
                        # Keywords sorted by type
                        kw_json=r"hover_item",
                        kw_scope=r"hover_text",
                        kw_color=r"color",
                        kw_link=r"link",
                        kw_string=r"copy|suggest|run|insertion|font",
                        kw_bool=r"bold|italic|obfuscated|strikethrough|underlined",
                        kw_integer=r"page",
                        kw_standalone=r"selector|translate|score|nbt|separator|sep|key",
                        kw_with=r"with",
                        nbt_location=r"block|entity|storage",
                    ):
                        pattern_contents = self.parse_modifiers(stream)

                    stream.expect(("paren", ")"))

                    self.patterns[pattern.value] = pattern_contents

                elif template:
                    stream.expect(("brace", "{"))
                    template_contents = self.internal_parse(stream)
                    stream.expect(("brace", "}"))

                    self.templates[template.value] = template_contents

                if stream.get("newline"):
                    # Handle new lines in-between arguments
                    while stream.get("newline"):
                        continue

                    self.parse_definitions(stream)

            except InvalidSyntax as error:
                # Check if there's no data left to parse. This handles there being extra newlines between any arguments and the #ALLAYDEFS keyword. If there's still data left, then there's a syntax error.
                if stream.source[
                    stream.current.location.pos : len(stream.source)
                ].strip():
                    raise error

    def internal_parse(self, stream: TokenStream) -> list:
        """
        internal_parse - Main parsing function. Wrapped by ``parse``.

        Args:
            stream (TokenStream): The stream to parse

        Returns:
            list: The parsed stream
        """
        output = []

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
            string=r"\"(?:\\.|[^\\\n])*?\"",
            # Keywords sorted by type
            kw_json=r"hover_item",
            kw_scope=r"hover_text",
            kw_color=r"color",
            kw_link=r"link",
            kw_string=r"copy|suggest|run|insertion|font",
            kw_bool=r"bold|italic|obfuscated|strikethrough|underlined",
            kw_integer=r"page",
            kw_standalone=r"selector|translate|score|nbt|separator|sep|key",
            kw_with=r"with",
            nbt_location=r"block|entity|storage",
        ):
            for sqrbr, brace, escape, text in stream.collect(
                ("sqrbr", "["), ("brace", "{"), "escape", "text"
            ):
                if escape:
                    output.append(escape.value[1])

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

    def parse_separator(self, stream: TokenStream) -> str:
        """
        parse_separator - Parses a separator. This is its own function since it's used several times.

        Args:
            stream (TokenStream): The stream to parse

        Returns:
            str: The separator value
        """
        stream.expect(("kw_standalone", "sep"), ("kw_standalone", "separator"))
        stream.expect("equals")  # equal sign
        return stream.expect("string").value[1:-1]

    def error_if_scope(self, stream: TokenStream) -> None:
        """
        error_if_scope - Raises an error if the stream is in a scope when it shouldn't be

        Args:
            stream (TokenStream): The stream to check the scope status of

        Raises:
            InvalidSyntax: Raised if the stream is in a scope
        """
        if stream.data.get("scoped"):
            raise InvalidSyntax("Unexpected scope")

    def parse_standalone(self, stream: TokenStream) -> dict:
        """
        parse_standalone - Parses a standalone block

        Args:
            stream (TokenStream): The stream to parse

        Returns:
            dict: The standalone block contents
        """
        standalone_contents = {}
        with stream.syntax(text=None, comma=r",", template=r"\$\w+"):
            selector, kw_standalone, template = stream.expect(
                "selector", "kw_standalone", "template"
            )
            if selector:
                separator = (
                    self.parse_separator(stream) if stream.get("comma") else None
                )
                standalone_contents["selector"] = selector.value
                if separator:
                    standalone_contents["separator"] = separator

            elif kw_standalone:
                if kw_standalone.value == "key":
                    stream.expect("equals")
                    keybind_value = stream.expect("keybind")
                    standalone_contents["keybind"] = "key." + keybind_value.value

                elif kw_standalone.value == "translate":
                    stream.expect("equals")
                    translation_key = stream.expect("string").value[1:-1]

                    with_value = None
                    if stream.get("comma"):
                        stream.expect("kw_with")
                        stream.expect("equals")
                        with_value = parse_json(stream)

                    standalone_contents["translate"] = translation_key
                    if with_value:
                        standalone_contents["with"] = with_value

                elif kw_standalone.value == "nbt":
                    stream.expect("equals")
                    nbt_path = stream.expect("string").value[1:-1]
                    stream.expect("comma")

                    nbt_type = stream.expect("nbt_location").value
                    stream.expect("equals")
                    nbt_location = stream.expect("string").value[1:-1]

                    separator = (
                        self.parse_separator(stream) if stream.get("comma") else None
                    )
                    standalone_contents["nbt"] = nbt_path
                    standalone_contents[nbt_type] = nbt_location
                    if separator:
                        standalone_contents["separator"] = separator

                elif kw_standalone.value == "score":
                    stream.expect("equals")
                    player_name = stream.expect("string").value[1:-1]
                    stream.expect("arrow")
                    objective_name = stream.expect("string").value[1:-1]
                    standalone_contents["score"] = {
                        "name": player_name,
                        "objective": objective_name,
                    }

            elif template:
                if (q := template.value) not in self.templates:
                    raise InvalidSyntax(f"Unknown template '{q}'")

                args = self.parse_template_args(stream)
                if args:
                    # Turn the template into a string so we can use replace on it
                    template_value = json.dumps(self.templates[q])
                    # Replace all the tokens
                    for index, arg in enumerate(args):
                        template_value = template_value.replace(f"%{index}", arg)

                    # Convert it back into a dictionary
                    standalone_contents = json.loads(template_value)

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
        """
        parse_template_args - Parses the arguments for a template

        Args:
            stream (TokenStream): The template call to parse the arguments for

        Returns:
            list: The list of parsed arguments
        """
        args = []
        if stream.get("comma"):
            # 1:-1 to remove quotes
            args.append(stream.expect("string").value[1:-1])
            # Add the previous argument to the list
            args.extend(self.parse_template_args(stream))

        return args

    def parse_modifiers(self, stream: TokenStream) -> dict:
        """
        parse_modifiers - Parses a modifier block

        Args:
            stream (TokenStream): The stream to parse

        Returns:
            dict: The modifier contents
        """
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

            elif kw_scope:
                # Just "hover_text" for now
                stream.expect("equals")
                stream.expect(("scope", "<"))
                with stream.provide(scoped=True):
                    modifier_contents["hoverEvent"] = {
                        "action": "show_text",
                        "contents": self.internal_parse(stream),
                    }
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
                    link = stream.expect("string").value[1:-1]
                    if not link.startswith("http"):
                        link = "https://" + link
                modifier_contents["clickEvent"] = {"action": "open_url", "value": link}

            elif kw_string:
                # r"copy|suggest|run|insertion|font",
                if kw_string.value != "font":
                    self.error_if_scope(stream)
                stream.expect("equals")
                string_value = stream.expect("string").value[1:-1]
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

                modifier_contents = modifier_contents | self.patterns[q]

            if stream.get("comma"):
                modifier_contents = modifier_contents | self.parse_modifiers(stream)

        return modifier_contents

    def clean_ast(self, ast: list) -> list:
        """
        clean_ast - Cleans up an AST by iterating through it and merging strings that are next to each other

        Args:
            ast (list): The AST to clean

        Returns:
            str: The cleaned AST
        """
        # Merges strings together into one string
        cleaned_ast = ast[:1]
        for elem in ast[1:]:
            if isinstance(elem, str) and isinstance(cleaned_ast[-1], str):
                cleaned_ast[-1] += elem
            else:
                cleaned_ast.append(elem)

        return cleaned_ast

    def convert_ast_to_json(self, ast: list) -> list:
        """
        convert_ast_to_json - Converts an AST to valid text-component JSON

        Args:
            ast (list): The AST to convert

        Returns:
            list: The text-component JSON
        """
        output = [""]
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
