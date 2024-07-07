import glob
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

SRC_PATH = os.path.join("server", "src")
struct_pattern = re.compile(r"type\s+(\w+)\s+struct\s+\{((.|\n)*?)[^{]}")
field_pattern = re.compile(r"\s*(\w*)\s*\*?(\[])*(\w*.?\w*)(\{})?\s*`json:\"(\w*|-)(,.*)?\"`.*")
# field_pattern = re.compile(r"\s*(\w*)\s*\*?(\[])*(\w*.?\w*)(\{})?\s*`json:\"(\w*|-)(,.*)?\"`.*")
STRUCT_FILTER = {
    "TableMessage",
    "Options",
    "Spectator",
    "CommandData",
    "GameJSON",
    "CardIdentity",
    "GameAction",
    "OptionsJSON",
    "CharacterAssignment",
    "GameActionListMessage",
    "UserMessage",
    "TableStartMessage",
    "GameActionMessage",
    "ActionClue",
    "ActionCardIdentity",
    "ActionDiscard",
    "ActionDraw",
    "ActionGameOver",
    "ActionPlay",
    "ActionPlayerTimes",
    "ActionStrike",
    "ActionStatus",
    "ActionTurn",
    "Clue",
    "InitMessage",
    "FinishOngoingGameMessage",
}

STRUCT_TEMPLATE = """
class {name}(HLModel):
{fields}"""

FIELD_TEMPLATE = "    {name}: Optional[{type}] = None"

TYPE_MAPPING = {
    "uint64": "int",
    "int": "int",
    "string": "str",
    "bool": "bool",
    "interface": "Any",
    "int64": "int",
    "time.Time": "datetime.datetime",
    "Spectator": "str",  # this is what we get in TableMessage.spectators
}


def iter_structs(path: str) -> Iterable[Tuple[str, List[str]]]:
    for src_file in glob.glob(os.path.join(path, "*.go")):
        src_content = Path(src_file).read_text("utf8")
        for match in struct_pattern.finditer(src_content):
            struct_name = match.group(1)
            lines = match.group(2).strip().splitlines(keepends=False)
            lines = [ln.split("//")[0].strip() for ln in lines]
            lines = [ln for ln in lines if ln]
            yield struct_name, lines


def parse_field_line(line: str) -> Tuple[Optional[str], Optional[str]]:
    match = field_pattern.match(line)
    if match is None:
        raise ValueError(f"Cannot parse line '{line}'")
    # name, array, type_, alias, omit = match.groups()
    name, array, type_, braces, alias, omit = match.groups()
    if alias == "-":
        return None, None
    type_ = type_.lstrip("*").strip()
    add_quotes = type_ not in TYPE_MAPPING

    type_ = TYPE_MAPPING.get(type_, type_)
    if add_quotes:
        type_ = f'"{type_}"'
    if array == "[]":
        type_ = f"List[{type_}]"
    return alias, type_


def struct_to_python(struct_name: str, lines: List[str]) -> str:
    fields = "\n".join(
        FIELD_TEMPLATE.format(name=name, type=type_)
        for line in lines
        for name, type_ in (parse_field_line(line),)
        if line.strip()
        if name is not None
    )
    if not fields:
        fields = "    pass"
    return STRUCT_TEMPLATE.format(name=struct_name, fields=fields)


def create_models(path: str, out: str):
    structs = []
    for name, lines in iter_structs(path):
        if name not in STRUCT_FILTER:
            continue
        structs.append(struct_to_python(name, lines))

    with open(out, "w", encoding="utf8") as f:
        f.write(
            """# ruff: noqa: A003
import datetime
from typing import Any, List, Optional

from msgspec import Struct


class HLModel(Struct, omit_defaults=True):
    pass

"""
        )
        f.write("\n\n".join(structs))
        f.write("\n")


def main():
    if len(sys.argv) != 3:
        print(f"Usege: python {__file__} <path to hanabi-live repo root>")
        return
    hanabi_live_path, out_path = sys.argv[1:]

    path = os.path.join(hanabi_live_path, SRC_PATH)
    create_models(path, out_path)


if __name__ == "__main__":
    main()
