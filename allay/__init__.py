from .parser import Parser

__all__ = ["Parser"]

# Lets try to import beet if it exists
# This allows it to stay as an optional dep
try:
    import beet
    from .plugin import beet_default

    __all__.append("beet_default")
except ImportError:
    pass
