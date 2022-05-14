import os

import allay

parser = allay.Parser()

parser.add_pattern("external_pattern", "(bold, blue)")
parser.add_template("external_template1", "arg 1: %0\narg 2: %1")
parser.add_template(
    "external_template2", "outside stuff. go away {@s}(@external_pattern)"
)

# TODO fix this jank and get the proper parser.parse("tests\\sample.allay") working
with open(
    os.path.join(
        os.path.dirname(os.path.dirname(allay.__file__)), "tests", "sample.allay"
    ),
    "r",
) as infile:
    file_contents = infile.read()

parsed_contents = parser.parse(file_contents)

# TODO invidiual tests instead of one large file
print(parsed_contents)

# Confirmed to work manually in game version 1.18.1
assert (
    parsed_contents
    == '["", {"text": "Formatting:\\nHere\'s some basic text. This is "}, {"text": "underlined", "underlined": true}, {"text": ".\\nThis is "}, {"text": "bold", "bold": true}, {"text": ". This is "}, {"text": "italic", "italic": true}, {"text": ". \\nThis is "}, {"text": "strikethrough", "strikethrough": true}, {"text": ". This is "}, {"text": "obfuscated", "obfuscated": true}, {"text": ". \\n"}, {"text": "Some text", "color": "#00aced"}, {"text": " with color. \\n"}, {"text": "Some text", "color": "blue"}, {"text": " with a different type of color.\\n"}, {"text": "Some", "font": "namespace:font/file/here"}, {"text": " text.\\n\\nInteractivity:\\n"}, {"text": "insertion", "insertion": "this text is appended into the chat box when the user shift clicks this"}, {"text": "\\n"}, {"text": "open url 1", "clickEvent": {"action": "open_url", "value": "https://example.com"}}, {"text": "\\n"}, {"text": "open url 2", "clickEvent": {"action": "open_url", "value": "https://example.com"}}, {"text": "\\n"}, {"text": "run cmd", "clickEvent": {"action": "run_command", "value": "say hello. It should support extra \\"quotes\\" too"}}, {"text": "\\n"}, {"text": "suggest cmd", "clickEvent": {"action": "suggest_command", "value": "/say Same as above"}}, {"text": "\\n"}, {"text": "change page", "clickEvent": {"action": "change_page", "value": "49"}}, {"text": "\\n"}, {"text": "copy2clipboard", "clickEvent": {"action": "copy_to_clipboard", "value": "voila, im inside your PC now! mwahahaha"}}, {"text": "\\n"}, {"text": "show text on hover", "hoverEvent": {"action": "show_text", "contents": ["", {"text": "The braces help to clarify scope so I can do "}, {"text": "this", "color": "#ff0000", "bold": true}]}}, {"text": "\\n"}, {"text": "show item on hover", "hoverEvent": {"action": "show_item", "contents": {"id": "minecraft:netherite_hoe", "count": 1, "tag": "{display: {Name: \\"\\\\\\"joe\\\\\\"\\"}}"}}}, {"text": "\\n\\nStandalone:\\n"}, {"selector": "@a", "separator": "\\""}, {"text": " \\n"}, {"translate": "translation_key"}, {"text": "\\n"}, {"translate": "text goes here", "with": ["raw", "json"]}, {"text": "\\n"}, {"score": {"name": "@s", "objective": "objective"}}, {"text": "\\n"}, {"score": {"name": "fake_player", "objective": "objective"}}, {"text": "\\n"}, {"nbt": "path", "block": "~ ~ ~", "separator": ", "}, {"text": "\\n"}, {"nbt": "path", "entity": "@s", "separator": " - "}, {"text": "\\n"}, {"nbt": "path", "storage": "storage:location", "separator": " -=- "}, {"text": "\\n"}, {"keybind": "key.inventory"}, {"text": "\\n\\nBut better yet... we can mix things!\\nThis right here is standard text, but with the power of "}, {"text": "formatting", "italic": true}, {"text": ", we can make it "}, {"text": "super", "underlined": true}, {"text": " "}, {"text": "pretty", "bold": true, "italic": true}, {"text": "!! Good luck with "}, {"text": "your adventures", "obfuscated": true}, {"text": ".\\nThings might get broken... isn\'t that right "}, {"selector": "@a[name=DoubleF3lix]"}, {"text": "? It looks like you\'re holding a \\""}, {"nbt": "SelectedItem.id", "entity": "@a"}, {"text": "\\".\\nThis text can also get "}, {"text": "colorful!", "color": "#00aced", "bold": true, "underlined": true}, {"text": ". Want to be sarcastic or just redact something? "}, {"text": "Stricken from the record... I guess?", "strikethrough": true}, {"text": "\\nHovering over "}, {"text": "this text", "hoverEvent": {"action": "show_text", "contents": ["", {"text": "will show this "}, {"text": "stuff!", "bold": true, "italic": true}, {"text": " Isn\'t that "}, {"text": "wild", "underlined": true}, {"text": "?"}]}, "insertion": "I\'m in your chat bar now... spooky, eh?"}, {"text": "\\nThis is a "}, {"text": "link", "clickEvent": {"action": "open_url", "value": "https://github.com/DoubleF3lix"}}, {"text": ", but so is "}, {"text": "this", "clickEvent": {"action": "open_url", "value": "https://example.com"}}, {"text": "\\n\\nHere\'s some token spam so we can make sure it isn\'t picked up by my crummy lexer/parser:\\nhelp:=(walrus operator????)pls\\"work\\"beans(test=text)w\\\\~\\\\~hich\\\\~\\\\~_isWHY!you\'re-[triggered].\\n\\nAnd here\'s hoping that escaping things also works:\\nSome basic "}, {"text": "hover text", "hoverEvent": {"action": "show_text", "contents": ["", {"text": "hover... hover... hover... :\\\\"}]}}, {"text": "\\n\\n\\nNow, let\'s test definitions. Some have been defined outside this file, but the rest are at the top of the file.\\n"}, {"text": "pattern usage 1", "italic": true, "color": "yellow"}, {"text": "\\n"}, {"text": "pattern usage 2", "italic": false, "color": "yellow"}, {"text": "\\n"}, ["", {"text": "inline stuff. hello "}, {"selector": "@s", "bold": true, "color": "blue"}], {"text": "\\n"}, ["", {"text": "arg 1: here comes arg 1!\\narg 2: phew, that was close"}], {"text": "\\nThis shouldn\'t error\\n"}, ["", {"text": "outside stuff. go away "}, {"selector": "@s", "bold": true, "color": "blue"}]]'
)
