# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable, TypeVar

from .opcodeone_isa_bundle import load_default_bundle


T = TypeVar("T")


def opcode_map_from_bundle(bundle: dict[str, Any]) -> dict[str, int]:
    opcode_slots = bundle.get("opcode_slots", {}).get("slots")
    if not isinstance(opcode_slots, dict):
        raise ValueError("bundle opcode_slots.slots must be a mapping")

    opcode_map: dict[str, int] = {}
    for family in bundle["families"]:
        opcode_ref = family["opcode_ref"]
        value = opcode_slots.get(opcode_ref)
        if not isinstance(value, int):
            raise ValueError(f"bundle opcode slot '{opcode_ref}' must be an integer")
        opcode_map[opcode_ref] = value
    return opcode_map


def build_named_register_sets(
    register_sets: dict[str, Any],
    factory: Callable[[str, str, int, int], T],
) -> dict[str, dict[str, T]]:
    result: dict[str, dict[str, T]] = {}
    for set_name in ("reg16", "reg24"):
        members: dict[str, T] = {}
        width_bits = register_sets[set_name]["width_bits"]
        for member in register_sets[set_name]["members"]:
            members[member["name"]] = factory(set_name, member["name"], member["code"], width_bits)
        result[set_name] = members
    return result


def build_coded_register_sets(
    register_sets: dict[str, Any],
    factory: Callable[[str, str, int, int], T],
) -> dict[str, dict[int, T]]:
    result: dict[str, dict[int, T]] = {}
    for set_name in ("reg16", "reg24"):
        members: dict[int, T] = {}
        width_bits = register_sets[set_name]["width_bits"]
        for member in register_sets[set_name]["members"]:
            members[member["code"]] = factory(set_name, member["name"], member["code"], width_bits)
        result[set_name] = members
    return result


@lru_cache(maxsize=1)
def default_register_name_maps() -> tuple[dict[int, str], dict[int, str], frozenset[str]]:
    register_sets = load_default_bundle()["register_sets"]
    reg16_by_code = {member["code"]: member["name"] for member in register_sets["reg16"]["members"]}
    reg24_by_code = {member["code"]: member["name"] for member in register_sets["reg24"]["members"]}
    special_tokens = frozenset(member["name"] for member in register_sets.get("special", {}).get("members", []))
    return reg16_by_code, reg24_by_code, special_tokens


@lru_cache(maxsize=1)
def default_reserved_symbols() -> frozenset[str]:
    bundle = load_default_bundle()
    reserved: set[str] = set()

    for register_set in ("reg16", "reg24"):
        reserved.update(member["name"].upper() for member in bundle["register_sets"][register_set]["members"])
    reserved.update(member["name"].upper() for member in bundle["register_sets"].get("special", {}).get("members", []))

    for family in bundle["families"]:
        for form in family["forms"]:
            for pattern in form["syntax"]["patterns"]:
                for token in pattern["sequence"]:
                    if token["kind"] == "literal":
                        reserved.update(part.upper() for part in token["value"].split())
                        continue
                    if token["kind"] == "enum":
                        omit_keys = set(token.get("omit_keys", []))
                        reserved.update(
                            part.upper()
                            for enum_value in bundle["abstract_enums"][token["enum_ref"]]
                            if enum_value not in omit_keys
                            for part in enum_value.split()
                        )
                        continue
                    if token["kind"] == "keyword":
                        reserved.update(
                            part.upper()
                            for part in bundle["abstract_kinds"][token["keyword_ref"]]["literal"].split()
                        )

    reserved.update(
        {
            "IS",
            "IMPORT",
            "EXPORT",
            "BYTE",
            "WORD",
            "ADDR",
            "FILL",
            "FILE",
            "ALIGN",
        }
    )
    return frozenset(reserved)


__all__ = [
    "build_coded_register_sets",
    "build_named_register_sets",
    "default_reserved_symbols",
    "default_register_name_maps",
    "opcode_map_from_bundle",
]
