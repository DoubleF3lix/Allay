# Allay
A parser to convert a descriptive text format into minecraft text components

## Getting Started
First, install the package with `pip install allay`.
Next, create a python script and import allay.

Usage is extremely simple:
```python
import allay 

parser = allay.Parser()
text_component = parser.parse(string)
```

---
## Format
Allay uses a markdown-inspired format. To start, we'll define our types.
- `string` - `"string"`
- `integer` - `49`
- `url/link` - `"https://example.com"`
- `boolean` - `true/false`
- `hex code` - `#ff0000`
- `color` - Any built in color such as `red`, `blue`, `black`, etc.
- `scope block` - `<text>`. Scope blocks are just like normal text, except any modifier that involves clicking or hovering cannot be used and will raise an error. They are only used in `hover_text`, and can use normal modifiers like `bold`, `color`, or `font`.
- `selector` - `@e[type=minecraft:allay]`
- `json` - `{"text": "Hello, World"}`
- `keybind` - Any valid keybind. Should not include the `key.`. `key.advancements` should be input as `advancements`.

Text is interpreted as exactly that, text. To format our text, we'll need to put it in what's called a **text isolator**, which is just text wrapped in square brackets. Then, we'll attach a modifier block to it. A **modifier block** is just a set of key value pairs (some exceptions apply) wrapped in parenthesis. For instance: `(color=blue, bold=true)` is a modifier block. Attaching a text isolator and a modifier block is as simple as putting them next to each other, like so: `[text](color=blue)`. 

If more than one modifier needs to be specified, they should be separated by commas: `(color=white, insertion="You shift clicked the chat")`

Modifiers should always be a set of key and value pairs separated by an equal sign. The only exceptions to this are:
- Links are automatically inferred if they begin with `https://` or `http://`
- Hex codes are automatically interpreted as colors
- `bold`, `italic`, `strikethrough`, `underlined`, and `obfuscated` do not require `=true`. Instead, you can just add the keywords. These two samples are equivalent: `[text](bold=true, italic=true)` - `[text](bold, italic)`.
- Built-in colors do not require a `color` keyword. `[text](black)` is valid.

Here's a full list of all valid modifiers and their expected types (not including the exceptions listed above):
- `hover_item` - `json`, should describe `contents.show_item` as demonstrated [here](https://minecraft.fandom.com/wiki/Raw_JSON_text_format).
- `hover_text` - `scope block`
- `color` - `color` or `hex_code`
- `link` - `url`
- `font` - `string`
- `copy` - `font`
- `suggest` - `string`
- `run` - `string`
- `insertion` - `string`
- `page` - `integer`
- `bold` - `boolean`
- `italic` - `boolean`
- `strikethrough` - `boolean`
- `underlined` - `boolean`
- `obfuscated` - `boolean`

Modifier blocks can also be applied to **standalone blocks**. Standalone blocks are used to show entity selectors, translation keys, keybinds, scoreboards, and NBT selectors. They are also given in key value pairs, however, unlike modifier blocks, multiple standalone blocks cannot be combined. Every individual component of a standalone block should be separated by commas.

Here is a list of all valid arguments in a standalone block:
- `selector` - `selector`
- `translate` - `string`, specifies the translation key
- `with` - `json`, optional. Only used with `translate` and must be used after `translate`.
- `nbt` - `string`, defines the NBT path on the location specified
- `block/entity/storage` - `string`, defines the location that the NBT path should be looked up in. Selectors and coordinates should be put in strings as well (`"@s"` / `"83 76 239"`) Must be included with `nbt`.
- `sep` or `separator` - Optional. Defines the string that should be inserted between entity/NBT selectors that target multiple values. Only used with `nbt` and `selector`. Must be specified last.
- `score` - `string`. Must be followed by an arrow (`->`) and another string containing the objective name
- `key` - `keybind`

And some examples:
- `{@s}`
- `{@s, sep=" - "}`
- `{@s, separator=" - "}`
- `{translate="k:ey"}`
- `{translate="k:ey", with=["raw", "json"]}`
- `{nbt="path", entity="@s"}`
- `{nbt="path", block="88 72 239", sep=" : "}`
- `{nbt="path", storage="store:age", sep="><"}`
- `{score="DoubleF3lix" -> "playerKills"}`
- `{score="@s"->"rightClick"}`
- `{key=advancements}`
- `{@s}(hover_text=<gone fancy>, #00aced)`

---
## Definitions

Allay also supports text reuse in the form of **patterns** and **templates** (collectively referred to as **definitions**). All definitions must be included at the top of the file and separated by a delimiter (`#ALLAYDEFS` by default). Patterns can be identified by the `@` symbol, and templates can be defined by the `$` symbol. Both can be given custom names, but these names can only include letters, numbers, and underscores.

---
### Patterns
Patterns let you reuse modifiers.

An example of their usage is as follows:
```
@pattern_name = (color=#000000, bold, hover_text=<Basically /clone>)
Here is some [modified text](@pattern_name)
```
In this case, `[modified text](@pattern_name)` is equivalent to `[modified text](color=#000000, bold, hover_text=<Basically /clone>)`. 

However, merging patterns wither other modifiers is valid:
```
@pattern1 = (bold, italic)
@pattern2 = (underlined, bold=false)

More [text](@pattern1, @pattern2, link="https://example.com")
```
Patterns are applied in order that they are listed in from left to right.
In this case, `[text](@pattern1, @pattern2, link="https://example.com")` is equivalent to `[text](italic, underlined, link="https://example.com")`, as the `bold` modifier in `@pattern1` is overridden by `@pattern2`.

---
### Templates
The primary attribute of templates is that they let you reuse blocks of text, and they can take arguments:
```
$template_name = {A template can use [modifiers](underlined) like normal. 
This template has %0 arguments. 
By the way, you owe me $%1.00.}
```

Usage is as follows:
```md
{$template_name, "2", "18,000"}
```
This would translate to 

```
A template can use [modifiers](underlined) like normal.
This template has 2 arguments. 
For instance, you owe me $18,000.00.
```

Arguments are done simply via find-replace, so take care to avoid using `%<num>` in your text. Currently, they cannot be escaped. Any missing arguments will not be replaced (and left as `%<num>`), and any extra arguments will be ignored. All arguments must be passed in as strings.

---
To use definitions in your text, do the following:
```
@pattern = ()
$template = {}
#ALLAYDEFS

Okay, back to the show.
```
The first blank line in-between the delimiter (`#ALLAYDEFS`) and the text body is ignored. The delimiter cannot be escaped, so using it in your text will result in the definitions being ended prematurely and likely a syntax error. However, if this becomes an issue, you can change the delimiter by setting `definition_delimeter` in `allay.Parser()`.

--- 
## Notes
The package comes with a beet plugin (created by [RitikShah](https://github.com/RitikShah)). It is not officially supported, and any issues should be directed to its creator.

If you have any questions, need any help, etc., feel free to make an issue with your question.

---

## Credits
* [fizzy/vberlier](https://github.com/vberlier) - Creator of TokenStream. Helped walk me through using it and any issues I had. 10/10 customer service.
* Amber - Helped with designing the Allay format, gave me the idea in the first place
* nphhpn, vdvman1, discohund, Repertor, miestrode, rx, Ravbug, Ersatz, and a bunch of others on the Minecraft Commands Discord - Helped walk me through the process (and grief) of creating a parser by hand before I started using TokenStream. 
