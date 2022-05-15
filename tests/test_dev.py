import allay
import pytest
from allay.parser import DefinitionAlreadyExists
from tokenstream.error import InvalidSyntax


def test_base_text():
    parser = allay.Parser()

    assert parser.parse("Hello, World", json_dump=False) == [
        "",
        {"text": "Hello, World"},
    ]


def test_escaping():
    parser = allay.Parser()

    assert parser.parse(
        'help:=(walrus operator????)pls"work"beans(test=text)w\\~\\~hich\\~\\~_isWHY!you\\\'re-\\[triggered\\].',
        json_dump=False,
    ) == [
        "",
        {
            "text": 'help:=(walrus operator????)pls"work"beans(test=text)w\\~\\~hich\\~\\~_isWHY!you\\\'re-[triggered].'
        },
    ]

    assert parser.parse(
        "oh my \\\\bean\\s\\\\n\u2009 \\[triggered\\](bold wowie) [pls](red)",
        json_dump=False,
    ) == [
        "",
        {"text": "oh my \\bean\\s\\n\u2009 [triggered](bold wowie) "},
        {"text": "pls", "color": "red"},
    ]

    assert (
        parser.parse("bacon\n\b\r\u2009beani\\e", json_dump=True)
        == '["", {"text": "bacon\\n\\b\\r\\u2009beani\\\\e"}]'
    )


def test_modifier_json_dumping():
    parser = allay.Parser()

    assert (
        parser.parse("[All](bold, italic, underlined, strikethrough)")
        == '["", {"text": "All", "bold": true, "italic": true, "underlined": true, "strikethrough": true}]'
    )


def test_modifier_booleans():
    parser = allay.Parser()

    assert parser.parse(
        "[All](bold, italic, underlined, strikethrough, obfuscated)", json_dump=False
    ) == [
        "",
        {
            "text": "All",
            "bold": True,
            "italic": True,
            "underlined": True,
            "strikethrough": True,
            "obfuscated": True,
        },
    ]

    assert parser.parse(
        "[All](bold, italic=false, underlined=true)", json_dump=False
    ) == [
        "",
        {
            "text": "All",
            "bold": True,
            "italic": False,
            "underlined": True,
        },
    ]


def test_modifier_integers():
    parser = allay.Parser()

    assert parser.parse("[All](page=3)", json_dump=False) == [
        "",
        {"text": "All", "clickEvent": {"action": "change_page", "value": "3"}},
    ]


def test_modifier_strings():
    parser = allay.Parser()

    assert parser.parse(
        '[All](font="my:font", copy="sus", insertion="I can think of")',
        json_dump=False,
    ) == [
        "",
        {
            "text": "All",
            "font": "my:font",
            "clickEvent": {
                "action": "copy_to_clipboard",
                "value": "sus",
            },
            "insertion": "I can think of",
        },
    ]

    assert parser.parse('[All](suggest="why is amogus")', json_dump=False) == [
        "",
        {
            "text": "All",
            "clickEvent": {
                "action": "suggest_command",
                "value": "why is amogus",
            },
        },
    ]

    assert parser.parse('[All](run="the only placeholder")', json_dump=False) == [
        "",
        {
            "text": "All",
            "clickEvent": {
                "action": "run_command",
                "value": "the only placeholder",
            },
        },
    ]


def test_modifier_urls():
    parser = allay.Parser()

    assert parser.parse('[All](link="https://example.com")', json_dump=False) == [
        "",
        {
            "text": "All",
            "clickEvent": {
                "action": "open_url",
                "value": "https://example.com",
            },
        },
    ]

    assert parser.parse('[All](link="http://example.com")', json_dump=False) == [
        "",
        {
            "text": "All",
            "clickEvent": {
                "action": "open_url",
                "value": "http://example.com",
            },
        },
    ]

    assert parser.parse('[All](link="example.com")', json_dump=False) == [
        "",
        {
            "text": "All",
            "clickEvent": {
                "action": "open_url",
                "value": "https://example.com",
            },
        },
    ]

    assert parser.parse("[All](https://example.com)", json_dump=False) == [
        "",
        {
            "text": "All",
            "clickEvent": {
                "action": "open_url",
                "value": "https://example.com",
            },
        },
    ]

    assert parser.parse("[All](http://example.com)", json_dump=False) == [
        "",
        {
            "text": "All",
            "clickEvent": {
                "action": "open_url",
                "value": "http://example.com",
            },
        },
    ]


def test_modifier_scope_blocks():
    parser = allay.Parser()

    assert parser.parse("[All](hover_text=<Hello, World!>)", json_dump=False) == [
        "",
        {
            "text": "All",
            "hoverEvent": {
                "action": "show_text",
                "contents": ["", {"text": "Hello, World!"}],
            },
        },
    ]

    assert parser.parse(
        '[All](hover_text=<[Hello, World!](bold, font="my:font")>)', json_dump=False
    ) == [
        "",
        {
            "text": "All",
            "hoverEvent": {
                "action": "show_text",
                "contents": [
                    "",
                    {"text": "Hello, World!", "bold": True, "font": "my:font"},
                ],
            },
        },
    ]


def test_modifier_json():
    parser = allay.Parser()

    assert parser.parse(
        '[All](hover_item={"id": "minecraft:netherite_hoe", "tag": "{display: {Name: \\"\\\\\\"joe\\\\\\"\\"}}"})',
        json_dump=False,
    ) == [
        "",
        {
            "text": "All",
            "hoverEvent": {
                "action": "show_item",
                "contents": {
                    "id": "minecraft:netherite_hoe",
                    "tag": '{display: {Name: "\\"joe\\""}}',
                },
            },
        },
    ]


def test_modifier_color():
    parser = allay.Parser()

    assert parser.parse("[Some](color=blue)", json_dump=False) == [
        "",
        {"text": "Some", "color": "blue"},
    ]

    assert parser.parse("[Some](blue)", json_dump=False) == [
        "",
        {"text": "Some", "color": "blue"},
    ]

    assert parser.parse("[Some](#47cdff)", json_dump=False) == [
        "",
        {"text": "Some", "color": "#47cdff"},
    ]

    assert parser.parse("[Some](color=#47cdff)", json_dump=False) == [
        "",
        {"text": "Some", "color": "#47cdff"},
    ]


def test_standalone():
    parser = allay.Parser()

    assert parser.parse(
        '{@s, translate="translation:key", with=["some", "json"], sep=" - ", key=advancements}',
        json_dump=False,
    ) == [
        "",
        {
            "selector": "@s",
            "translate": "translation:key",
            "with": ["some", "json"],
            "separator": " - ",
            "keybind": "key.advancements",
        },
    ]

    assert parser.parse('{score="imposter30"->"objective.main"}', json_dump=False) == [
        "",
        {"score": {"name": "imposter30", "objective": "objective.main"}},
    ]
    assert parser.parse('{score="@s" -> "objective.secondary"}', json_dump=False) == [
        "",
        {"score": {"name": "@s", "objective": "objective.secondary"}},
    ]

    assert parser.parse(
        '{nbt="key", block="88 76 239", interpret, sep=" - "}', json_dump=False
    ) == [
        "",
        {"nbt": "key", "block": "88 76 239", "interpret": True, "separator": " - "},
    ]

    assert parser.parse(
        '{nbt="key", entity="@s", interpret=false, separator="="}', json_dump=False
    ) == [
        "",
        {"nbt": "key", "entity": "@s", "interpret": False, "separator": "="},
    ]

    assert parser.parse(
        '{nbt="key", storage="in_our_midst", interpret=true}', json_dump=False
    ) == [
        "",
        {"nbt": "key", "storage": "in_our_midst", "interpret": True},
    ]

    assert parser.parse("{@s}(bold)", json_dump=False) == [
        "",
        {"selector": "@s", "bold": True},
    ]


def test_definitions():
    parser = allay.Parser()

    parser.add_pattern("extern_patt1", "(bold, italic, blue)")
    parser.add_pattern("extern_patt2", "(bold=false, obfuscated, blue)")
    parser.add_template("extern_temp1", "arg 1: %0\\\\narg 2: %1")
    parser.add_template("extern_temp2", "Go away, %0")

    assert parser.parse("[Many](@extern_patt1)", json_dump=False) == [
        "",
        {"text": "Many", "bold": True, "italic": True, "color": "blue"},
    ]

    assert parser.parse("[Many](@extern_patt1, @extern_patt2)", json_dump=False) == [
        "",
        {
            "text": "Many",
            "bold": False,
            "italic": True,
            "obfuscated": True,
            "color": "blue",
        },
    ]

    assert parser.parse(
        '[Before](strikethrough) {$extern_temp1, "ter", "nary"} [After](italic)',
        json_dump=False,
    ) == [
        "",
        {"text": "Before", "strikethrough": True},
        {"text": " "},
        ["", {"text": "arg 1: ter\\narg 2: nary"}],
        {"text": " "},
        {"text": "After", "italic": True},
    ]

    assert parser.parse(
        '{$extern_temp2, "Felix", "Discarded1", "Discarded2"}', json_dump=False
    ) == [
        "",
        ["", {"text": "Go away, Felix"}],
    ]

    assert parser.parse("{$extern_temp2}", json_dump=False) == [
        "",
        ["", {"text": "Go away, %0"}],
    ]

    parser.set_parent("(bold, blue)")
    assert parser.parse("Somebody", json_dump=False) == [
        {"bold": True, "color": "blue"},
        {"text": "Somebody"},
    ]

    assert parser.parse(
        "@intern_patt = (yellow)\n$intern_temp = {ABC}\nPARENT = (green, underlined)\n#ALLAYDEFS\n[Check](@intern_patt)\n{$intern_temp}",
        json_dump=False,
    ) == [
        {"color": "green", "underlined": True},
        {"text": "Check", "color": "yellow"},
        {"text": "\n"},
        ["", {"text": "ABC"}],
    ]

    # You can even set the parent of templates by doing this (yes this in intended):
    parser = allay.Parser()
    parser.set_parent("(italic)")
    parser.add_template("template", "Hello")
    parser.set_parent("(underlined)")
    assert parser.parse(
        "This is underlined, but this is both italics and underlined: {$template}",
        json_dump=False,
    ) == [
        {"underlined": True},
        {"text": "This is underlined, but this is both italics and underlined: "},
        [{"italic": True}, {"text": "Hello"}],
    ]

    # Or the in-text equivalent:
    parser = allay.Parser()
    assert parser.parse(
        "PARENT = (italic)\n$template = {Hello}\nPARENT = (underlined)\n#ALLAYDEFS\nThis is underlined, but this is both italics and underlined: {$template}",
        json_dump=False,
    ) == [
        {"underlined": True},
        {"text": "This is underlined, but this is both italics and underlined: "},
        [{"italic": True}, {"text": "Hello"}],
    ]

    # You can also set a parent to null, since parent persists
    parser = allay.Parser()
    assert parser.parse(
        "PARENT = (italic)\n$template = {Hello}\nPARENT = null\n#ALLAYDEFS\nThis is underlined, but this is both italics and underlined: {$template}",
        json_dump=False,
    ) == [
        "",
        {"text": "This is underlined, but this is both italics and underlined: "},
        [{"italic": True}, {"text": "Hello"}],
    ]


def test_file_io():
    import os

    parser = allay.Parser()

    assert parser.parse(
        os.path.join(os.getcwd(), "tests", "file.allay"), json_dump=False
    ) == [
        "",
        {"text": "Doobah Dabba Dee\n"},
        ["", {"text": "Never gonna give you up\nNever gonna let you down"}],
        {"text": "\n"},
        {"text": "A Few", "bold": True, "color": "blue"},
    ]

    parser = allay.Parser()

    with open(os.path.join(os.getcwd(), "tests", "file.allay"), "r") as infile:
        assert parser.parse(infile.read(), json_dump=False) == [
            "",
            {"text": "Doobah Dabba Dee\n"},
            ["", {"text": "Never gonna give you up\nNever gonna let you down"}],
            {"text": "\n"},
            {"text": "A Few", "bold": True, "color": "blue"},
        ]


def test_parser_defaults():
    parser = allay.Parser(json_dump=False)

    # Do the check twice to be sure it persists
    assert isinstance(parser.parse("Hello"), list)
    assert isinstance(parser.parse("World!"), list)

    parser.set_defaults(json_dump=True)

    assert isinstance(parser.parse("Hello"), str)
    assert isinstance(parser.parse("World!"), str)

    # Reset defaults
    parser = allay.Parser()
    assert isinstance(parser.parse("Hello"), str)


def test_syntax_errors():
    parser = allay.Parser()

    with pytest.raises(InvalidSyntax):
        parser.parse("[Hello](bold, italic, blue")

    with pytest.raises(InvalidSyntax):
        parser.parse("[Hello(bold, italic, blue)")

    with pytest.raises(InvalidSyntax):
        parser.parse("[Hello]")

    with pytest.raises(InvalidSyntax):
        parser.parse("[Hello\\]")

    with pytest.raises(InvalidSyntax):
        parser.parse('Python f-strings: f"{query}"')

    with pytest.raises(InvalidSyntax):
        parser.add_template("temporary_temp", "can't style this bum bum bum bum")
        parser.parse("{$temporary_temp}(bold)")

    with pytest.raises(InvalidSyntax):
        parser.parse("[Hello](@World)")

    with pytest.raises(InvalidSyntax):
        parser.parse("{$missingno}")

    with pytest.raises(InvalidSyntax):
        parser.parse("[Hello](what)")

    with pytest.raises(InvalidSyntax):
        parser.parse("{dooba_dooba_doo_doo_doo_doo__aaaaaah}")

    with pytest.raises(InvalidSyntax):
        parser.parse(
            "[A bit of a niche one](hover_text=<But we gotta check [these](page=12)>)"
        )

    with pytest.raises(InvalidSyntax):
        parser.parse(
            '[A bit of a niche one](hover_text=<But we gotta check [these](run="Explain to me how you\'re gonna have the user click a HOVER event")>)'
        )


def test_definition_errors():
    # Pattern defined twice internally
    with pytest.raises(DefinitionAlreadyExists):
        parser = allay.Parser()

        parser.add_pattern("extern_patt", "(bold, blue)")
        parser.add_pattern("extern_patt", "(red, obfuscated)")

    # Template defined twice internally
    with pytest.raises(DefinitionAlreadyExists):
        parser = allay.Parser()

        parser.add_template("extern_patt", "Reporting live from WKBN News: %0")
        parser.add_template(
            "extern_patt",
            "Pilot Sum Ting Wong and Wi Tu Lo found in the Pacific Ocean %0",
        )

    # Template already defined (external then internal)
    with pytest.raises(DefinitionAlreadyExists):
        parser = allay.Parser()

        parser.add_template("template", "Reporting live from WKBN News: %0")
        parser.parse("$template = {Q}\n#ALLAYDEFS\nRS")
