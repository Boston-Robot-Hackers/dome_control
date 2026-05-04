---
version: "1.0"
generated: "2026-05-04"
---

# SimpleCommandParser

`simple_parser.py` converts free-form text input from the CLI into structured `ParsedCommand` objects. It also supports a set of abbreviations so the user can type `m fwd 1.5` instead of `move forward 1.5`.

## Output Types

```python
@dataclass
class ParsedCommand:
    command: str
    subcommand: Optional[str]
    arguments: List[Any]

@dataclass
class ParseError:
    message: str
    input_text: str
    position: Optional[int]
```

The parser returns `(ParsedCommand, None)` on success and `(None, ParseError)` on failure. Using a tuple rather than raising exceptions keeps the CLI's `execute_command` method clean — no try/except needed.

## Abbreviation Resolution

A global dict maps short tokens to their canonical forms:

```python
ABBREV_TO_FULL = {
    "m": "move",   "t": "turn",   "r": "robot",
    "fwd": "forward", "bak": "backward",
    "clk": "clockwise", "ccw": "counterclockwise",
    "q": "exit",   "x": "exit",
    ...
}
FULL_NAMES = set(ABBREV_TO_FULL.values())
```

`resolve_keyword` checks if a token is already a full name, then if it's a known abbreviation, otherwise returns it unchanged:

```python
def resolve_keyword(self, word: str) -> str:
    if word in self.full_names:
        return word
    if word in self.abbrev_to_full:
        return self.abbrev_to_full[word]
    return word
```

Unknown tokens pass through unchanged. The error surface is at execution time (unknown command in dispatcher), not parse time.

## Subcommand Detection

After resolving the first token (command), the parser checks whether the second token is a keyword or a plain argument:

```python
resolved_token = self.resolve_keyword(tokens[1])
is_keyword = resolved_token in self.full_names or resolved_token != tokens[1]

if is_keyword:
    subcommand = resolved_token
    arguments = [self.parse_value(arg) for arg in tokens[2:]]
else:
    arguments = [self.parse_value(arg) for arg in tokens[1:]]
```

`resolved_token != tokens[1]` is True when an abbreviation was expanded, which also counts as a keyword. If the second token is not a keyword, it and all subsequent tokens are treated as positional arguments to the command.

## Value Type Inference

```python
def parse_value(self, value_str: str) -> Any:
    if value_str.lower() in ("true", "yes", "1"):  return True
    if value_str.lower() in ("false", "no", "0"):  return False
    try:
        if "." not in value_str: return int(value_str)
    except ValueError: pass
    try:
        return float(value_str)
    except ValueError: pass
    return value_str
```

Values are parsed as: bool → int → float → string. The `int` branch skips values containing `.` to avoid converting `"1.0"` to `1` before the float branch sees it. This means `"1"` becomes `int(1)` but `"1.0"` becomes `float(1.0)`, which is the expected behaviour.

## Example Parse

```
input: "move forward 1.5"
tokens: ["move", "forward", "1.5"]
command: resolve("move") → "move"     (already full)
token[1]: resolve("forward") → "forward"  (already full, is_keyword=True)
subcommand: "forward"
arguments: [parse_value("1.5")] → [1.5]
result: ParsedCommand("move", "forward", [1.5])
```

`SimpleCLI._map_to_dispatcher_format` then converts this to `("move.forward", {"meters": 1.5})`.

## Observations

- Abbreviations for `intent` and `scene` groups are missing from `ABBREV_TO_FULL`. Users must type `intent describe_scene` in full.
- `ParseError.position` is never set to anything other than `None`. Position-aware error messages ("unexpected token at position 7") would help users fix malformed input.
- The parser has no concept of flags (`--flag value`). Optional parameters in `launch.start` (`--map`, `--use-sim-time`) cannot be passed through the parser — they would be misinterpreted as positional arguments.
