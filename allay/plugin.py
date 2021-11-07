from beet import Context
from beet.core.container import Drop
from beet.core.file import TextFile
from beet.contrib.messages import Message
from beet.library.base import NamespaceFile
from beet.library.data_pack import DataPack

from .parser import Parser


class AllayMessage(TextFile, NamespaceFile):
    scope = ("messages",)
    extension = ".allay"

    def bind(self, pack: DataPack, path: str):
        json = Parser().parse(self.text)
        pack[path] = Message(json)

        raise Drop()


def beet_default(ctx: Context):
    ctx.data.extend_namespace.append(AllayMessage)
