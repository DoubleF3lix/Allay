import json
from typing import Union, cast

from beet import Context
from beet.contrib.messages import Message
from beet.core.container import Drop
from beet.core.file import TextFile
from beet.core.utils import JsonDict
from beet.library.base import NamespaceFile
from beet.library.data_pack import DataPack

from allay.parser import Parser

parser = Parser()


class AllayMessage(TextFile, NamespaceFile):
    scope = ("messages",)
    extension = ".allay"

    def bind(self, pack: DataPack, path: str):
        json = parser.parse(self.text)
        pack[path] = Message(json)

        raise Drop()


def register_pattern(name: str, raw: Union[JsonDict, str]):
    if isinstance(raw, str):
        raw = json.loads(parser.parse(f"@{name} = {raw}\n#ALLAYDEFS\n"))
    else:
        parser.patterns[f"@{name}"] = raw


def register_template(name: str, raw: Union[JsonDict, str]):
    if isinstance(raw, str):
        raw = json.loads(parser.parse(raw))

    parser.templates[f"${name}"] = raw


def beet_default(ctx: Context):
    if config := ctx.meta.get("allay", cast(JsonDict, {})):
        if patterns := config.get("patterns", cast(JsonDict, {})):
            for name, pattern in patterns.items():
                register_pattern(name, pattern)

        if templates := config.get("templates", cast(JsonDict, {})):
            for name, template in templates.items():
                register_template(name, template)

    ctx.data.extend_namespace.append(AllayMessage)
