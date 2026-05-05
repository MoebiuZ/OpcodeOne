#!/usr/bin/env python3
# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0
"""Generate a textual catalog of canonical OpcodeOne instruction combinations."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from isa.tools.build_opcodeone_isa import DEFAULT_INDEX, build_bundle  # noqa: E402


@dataclass(frozen=True)
class SlotValue:
    text: str
    meta: dict[str, Any]


def build_register_values(bundle: dict[str, Any]) -> dict[str, list[SlotValue]]:
    result: dict[str, list[SlotValue]] = {}
    for set_name in ("reg16", "reg24"):
        values: list[SlotValue] = []
        width_bits = bundle["register_sets"][set_name]["width_bits"]
        for member in bundle["register_sets"][set_name]["members"]:
            values.append(
                SlotValue(
                    text=member["name"],
                    meta={
                        "kind": set_name,
                        "name": member["name"],
                        "code": member["code"],
                        "width_bits": width_bits,
                    },
                )
            )
        result[set_name] = values
    return result


def operand_values(bundle: dict[str, Any], register_values: dict[str, list[SlotValue]], operand_kind_ref: str) -> list[SlotValue]:
    spec = bundle["operand_kinds"][operand_kind_ref]
    kind = spec["type"]

    if kind == "register":
        return list(register_values[spec["register_set"]])
    if kind == "register_subset":
        return [value for value in register_values[spec["register_set"]] if value.meta["name"] in spec["members"]]
    if kind == "union":
        out: list[SlotValue] = []
        for member_ref in spec["members"]:
            out.extend(operand_values(bundle, register_values, member_ref))
        return out
    if kind == "immediate":
        return [SlotValue(f"<{operand_kind_ref}>", {"kind": "immediate", "operand_kind_ref": operand_kind_ref})]
    if kind == "address":
        return [SlotValue(f"<{operand_kind_ref}>", {"kind": "address", "operand_kind_ref": operand_kind_ref})]
    if kind == "relative_offset":
        return [SlotValue(f"<{operand_kind_ref}>", {"kind": "relative_offset", "operand_kind_ref": operand_kind_ref})]
    if kind == "memory":
        if spec["addressing"] == "[reg24]":
            return [
                SlotValue(f"[{reg.text}]", {"kind": "memory", "addressing": spec["addressing"], "base": reg.meta})
                for reg in register_values["reg24"]
            ]
        if spec["addressing"] == "[reg24+off16_signed]":
            return [
                SlotValue(
                    f"[{reg.text}+<off16_signed>]",
                    {"kind": "memory", "addressing": spec["addressing"], "base": reg.meta},
                )
                for reg in register_values["reg24"]
            ]
        if spec["addressing"] == "[addr24]":
            return [SlotValue("[<addr24>]", {"kind": "memory", "addressing": spec["addressing"]})]

    raise ValueError(f"Unsupported operand kind for catalog generation: {operand_kind_ref}")


def keyword_values(bundle: dict[str, Any], keyword_ref: str, optional: bool) -> list[SlotValue]:
    literal = bundle["abstract_kinds"][keyword_ref]["literal"]
    values = [SlotValue(literal, {"kind": "keyword", "present": True})]
    if optional:
        values.insert(0, SlotValue("", {"kind": "keyword", "present": False}))
    return values


def enum_values(bundle: dict[str, Any], enum_ref: str, omit_keys: list[str], optional: bool) -> list[SlotValue]:
    values = []
    for key in bundle["abstract_enums"][enum_ref]:
        if key in omit_keys:
            continue
        values.append(SlotValue(key, {"kind": "enum", "key": key}))
    if optional:
        values.insert(0, SlotValue("", {"kind": "enum", "key": "absent"}))
    return values


def constraint_ok(constraint: dict[str, Any], slots: dict[str, SlotValue]) -> bool:
    ctype = constraint["type"]
    if ctype == "same_width":
        widths = {slots[name].meta["width_bits"] for name in constraint["operands"]}
        return len(widths) == 1
    if ctype == "same_width_when_present":
        widths = {slots[name].meta["width_bits"] for name in constraint["operands"] if name in slots}
        return len(widths) <= 1
    if ctype == "enum_or_absent":
        if constraint["slot"] not in slots:
            return True
        key = slots[constraint["slot"]].meta["key"]
        return key == "absent" or key in constraint["values"]
    if ctype == "keep_high_requires_width":
        value = slots.get(constraint["slot"])
        if not value or not value.meta.get("present"):
            return True
        anchor = slots.get("dest") or slots.get("src")
        return bool(anchor and anchor.meta["width_bits"] == constraint["width_bits"])
    if ctype == "bit_index_within_width":
        bit_value = int(slots[constraint["bit_operand"]].text)
        target = slots[constraint["target_operand"]]
        return bit_value < target.meta["width_bits"]
    if ctype == "allowed_register_names":
        return slots[constraint["slot"]].meta["name"] in constraint["names"]
    raise ValueError(f"Unsupported constraint type in catalog generation: {ctype}")


def expand_pattern(bundle: dict[str, Any], register_values: dict[str, list[SlotValue]], form: dict[str, Any], pattern: dict[str, Any]) -> list[str]:
    slot_tokens = [token for token in pattern["sequence"] if token["kind"] == "slot"]
    generated: list[str] = []

    def backtrack(index: int, chosen: dict[str, SlotValue]) -> None:
        if index == len(slot_tokens):
            for constraint in form["constraints"]:
                if not constraint_ok(constraint, chosen):
                    return
            generated.append(render_instruction(pattern["sequence"], chosen))
            return

        token = slot_tokens[index]
        values: list[SlotValue]
        if token["slot_kind"] == "operand":
            values = operand_values(bundle, register_values, token["operand_kind_ref"])
            if token["operand_kind_ref"] == "bit_index_5":
                values = [SlotValue(str(i), {"kind": "immediate", "value": i}) for i in range(32)]
        elif token["slot_kind"] == "keyword":
            values = keyword_values(bundle, token["keyword_ref"], token.get("optional", False))
        elif token["slot_kind"] == "enum":
            values = enum_values(bundle, token["enum_ref"], token.get("omit_keys", []), token.get("optional", False))
        else:
            raise ValueError(f"Unsupported slot kind: {token['slot_kind']}")

        for value in values:
            chosen[token["name"]] = value
            backtrack(index + 1, chosen)
            chosen.pop(token["name"], None)

    backtrack(0, {})
    return generated


def render_instruction(sequence: list[dict[str, Any]], chosen: dict[str, SlotValue]) -> str:
    parts: list[str] = []
    for token in sequence:
        if token["kind"] == "literal":
            parts.append(token["value"])
            continue
        value = chosen[token["name"]]
        if value.text:
            parts.append(value.text)
    return " ".join(parts)


def build_catalog(bundle: dict[str, Any]) -> str:
    register_values = build_register_values(bundle)
    lines: list[str] = []
    for family in bundle["families"]:
        lines.append(f"# {family['name']}")
        for form in family["forms"]:
            lines.append(f"## {form['name']}")
            for pattern in form["syntax"]["patterns"]:
                lines.append(f"### {pattern['name']}")
                for instruction in expand_pattern(bundle, register_values, form, pattern):
                    lines.append(instruction)
                lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("isa/v0.9/instruction_catalog.txt"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle = build_bundle(DEFAULT_INDEX)
    args.output.write_text(build_catalog(bundle), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
