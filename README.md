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
- `hover_item` - `json`, should describe `contents.show_item` as demonstrated [here](https://minecraft.fandom.com/wiki/Raw_JSON_text_format). Note that using this in code **SUCKS** so here's an example to help you out a bit:
    - In a python string: `[All](hover_item={"id": "minecraft:netherite_hoe", "tag": "{display: {Name: \\"\\\\\\"joe\\\\\\"\\"}}"})`
    - In a file: `[All](hover_item={"id": "minecraft:netherite_hoe", "tag": "{display: {Name: \"\\\"joe\\\"\"}}"})` 
- `hover_text` - `scope block`
- `color` - `color` or `hex_code`
- `link` - `url`
- `font` - `string`
- `copy` - `string`
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
- `translate` - `string`
- `with` - `json`
- `nbt` - `string`
- `block/entity/storage` - `string`, Selectors and coordinates should be put in strings as well (`"@s"` / `"88 72 239"`).
- `interpret` - `boolean`, follows the same rules as booleans in modifiers (`=true` is optional. Just `interpret` is valid.)
- `sep` or `separator` - `string`. Defines the string that should be inserted between entity/NBT selectors that target multiple values. Only used with `nbt` and `selector`.
- `score` - `string`. Must be followed by an arrow (`->`) and another string containing the objective name
- `key` - `keybind`

All standalone arguments are non-order specific, but components that are invalid in-game will not return an error. For instance, mixing `nbt` and `selector` will give unintended results in game, but will be seen as valid to the parser. Be careful not to mix invalid items.

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

Allay also supports text reuse in the form of **patterns** and **templates** (collectively referred to as **definitions**). All definitions must be included at the top of the file and separated by a delimiter (`#ALLAYDEFS\n` by default). Patterns can be identified by the `@` symbol, and templates can be defined by the `$` symbol. Both can be given custom names, but these names can only include letters, numbers, and underscores.

---
### Patterns
Patterns let you reuse modifiers.

An example of their usage is as follows:
```
@pattern_name = (color=#000000, bold, hover_text=<Basically /clone>)
Here is some [modified text](@pattern_name)
```
In this case, `[modified text](@pattern_name)` is equivalent to `[modified text](color=#000000, bold, hover_text=<Basically /clone>)`. 

However, merging patterns with other modifiers is valid:
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
### Using templates and patterns in your text
To use these definitions in your text, do the following:
```
@pattern = ()
$template = {}
#ALLAYDEFS

Okay, back to the show.
```

---
### Parenting
No, this isn't a guide on how to raise kids. Instead, it's an introduction on inheritance in your text components. You see, you might've noticed that in most components you generate with allay, that it's made of a list with the first element being `""`. This is because when a text-component is a list, all elements in the list inherit from the first element (so we set it to a blank string to avoid this inheritance). However, sometimes inheritance is useful. For example, if your entire component needs to be in bold, then you might want to set the parent to be `{"bold": true}` instead of wrapping your entire component inside a text isolator, but that can block certain features (nested modifier blocks isn't supported). Instead, you can do this:
```
PARENT = (bold)
#ALLAYDEFS
Hello, World!
```
This will output `[{"bold": true}, {"text": "Hello, World!"}]`. Note that parents persist (not across different parse calls though). Why is this persistence useful? Well, it lets you set the parent for a template, like so:
```
PARENT = (bold)
$template = {Hello, it's me}
#ALLAYDEFS
{$template}; I'm in California dreamin'...
```
However, this may not do what you expect. This will output the following:
```json
[{"bold": true}, [{"bold": true}, {"text": "Hello, it's me"}], {"text":"; I'm in California dreamin'..."}]
```
This set the parent for the rest of the text to, and not just our template! Is there any hope for this wretched error? 
Yup! You can nullify a parent, so the fixed version of the above should look like this:
```
PARENT = (bold)
$template = {Hello, it's me}
PARENT = NULL
#ALLAYDEFS
{$template}; I'm in California dreamin'...
```
This will now fix the output:
```json
["", [{"bold": true}, {"text": "Hello, it's me"}], {"text":"; I'm in California dreamin'..."}]
```
Note that either `NULL` or `null` is valid.

---
### Configuring the definition delimiter
The first blank line in-between the delimiter (`#ALLAYDEFS\n`) and the text body is ignored. The delimiter cannot be escaped, so using it in your text will result in the definitions being ended prematurely and likely a syntax error. However, if this becomes an issue, you can change the delimiter by setting `definition_delimeter` in `allay.Parser()`.

---
### Definitions via Code
Don't like in-lining definitions and having to fiddle with `#ALLAYDEFS`? Fear not! There's new sheriffs in town and they're names are `add_pattern`, `add_template`, and `set_parent`. 
These are methods on your parser object (`allay.Parser()`), so they need to be called on that. If you're adding a pattern or template, you need to pass in the name (not needed for parents), and then pass in a string containing your pattern, template, or parent, and voila! 
Note that patterns and parents do require the parenthesis inside your string (if you're not nullifying a parent that is, otherwise just pass `"null"`), but templates should not include the surrounding braces. 
Here's a quick example:
```py
parser.add_pattern("my_pattern", "(bold)") # parser.parse("[Hello, World!](@my_pattern)")
parser.add_pattern("my_template", "There once was a human named %0") # parser.parse("{$my_template, \"Jeff\"}")
parser.set_parent("(strikethrough)") or parser.set_parent("NULL")
```

---
## Parser Defaults
Do you want to output all your components as a dictionary instead of a string and are tired of setting `json_dump=False` for everything? With the power of **parser defaults**, this is easy!
There are two ways to set parser defaults, demonstrated below
```py
parser = allay.Parser(indent=2, json_dump=False)
# alternatively
parser.set_defaults(indent=2, json_dump=False)
```
Now every call to `parser.parse` will use these values. Note that values set in `parser.parse` will take precedence, so you could have JSON dumping off by default and then enable it explicitly in your function calls for those few special cases.
If defaults aren't set, then the default values of no indentation and JSON dumping will be set. 
Note that both arguments in `set_defaults` are optional, and you can set one, both, or neither (but why would you do that?).

--- 
## Notes
The package comes with a beet plugin (created by [rx](https://github.com/rx-modules)). It is not officially supported, and any issues should be directed to its creator.

If you have any questions, need any help, etc., feel free to make an issue with your question.

---

## Credits
* [fizzy/vberlier](https://github.com/vberlier) - Creator of TokenStream. Helped walk me through using it and any issues I had. 10/10 customer service.
* [rx](https://github.com/rx-modules) - Creator of the beet plugin, gave me a lot of feedback
* [AmberWat](https://github.com/AmberWat) - Helped with designing the Allay format, gave me the idea in the first place

