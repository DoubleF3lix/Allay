import json

from tokenstream import TokenStream
from tokenstream.error import InvalidSyntax

from allay.json_parser import parse_json


class Parser:
    def parse(self, contents: str, indent: int = None) -> str:
        """
        parse - Converts a string into a text-component using the Allay format

        Args:
            contents (str): The string to parse
            indent (int, optional): Indentation level. Defaults to None.

        Returns:
            str: The text-component
        """
        try:
            if indent:
                return json.dumps(
                    self.internal_parse(TokenStream(contents)), indent=indent
                )
            else:
                return json.dumps(self.internal_parse(TokenStream(contents)))
        except InvalidSyntax as error:
            raise SyntaxError(error.format("src"))

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
                    output.append(self.parse_standalone(stream))

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
        with stream.syntax(text=None, comma=r","):
            selector, kw_standalone = stream.expect("selector", "kw_standalone")
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

        stream.expect(("brace", "}"))

        with stream.syntax(paren=r"\(|\)"):
            if stream.get(("paren", "(")):
                modifier_contents = self.parse_modifiers(stream)
                stream.expect(("paren", ")"))

                standalone_contents = standalone_contents | modifier_contents

        return standalone_contents

    def parse_modifiers(self, stream: TokenStream) -> dict:
        """
        parse_modifiers - Parses a modifier block

        Args:
            stream (TokenStream): The stream to parse

        Returns:
            dict: The modifier contents
        """
        modifier_contents = {}
        with stream.syntax(text=None, comma=r","):
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

        return output
