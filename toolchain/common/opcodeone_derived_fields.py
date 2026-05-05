# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any, Callable


def evaluate_derived_fields(
    derived_specs: dict[str, dict[str, Any]],
    *,
    resolve_source: Callable[[str, dict[str, Any]], Any],
    abstract_enums: dict[str, dict[str, int]],
    scalarize: Callable[[Any], Any],
    symbol_slice_factory: Callable[[Any, dict[str, Any]], Any],
    error_factory: Callable[[str], Exception],
) -> dict[str, Any]:
    derived: dict[str, Any] = {}
    for name, spec in derived_specs.items():
        derived[name] = evaluate_derived_field(
            spec,
            derived,
            resolve_source=resolve_source,
            abstract_enums=abstract_enums,
            scalarize=scalarize,
            symbol_slice_factory=symbol_slice_factory,
            error_factory=error_factory,
        )
    return derived


def evaluate_derived_field(
    spec: dict[str, Any],
    derived: dict[str, Any],
    *,
    resolve_source: Callable[[str, dict[str, Any]], Any],
    abstract_enums: dict[str, dict[str, int]],
    scalarize: Callable[[Any], Any],
    symbol_slice_factory: Callable[[Any, dict[str, Any]], Any],
    error_factory: Callable[[str], Exception],
) -> Any:
    field_type = spec["type"]
    if field_type == "enum_lookup":
        key = resolve_source(spec["source"], derived)
        if key is None:
            key = spec.get("default_key")
        if key is None:
            raise error_factory("missing enum input for derived field")
        return abstract_enums[spec["enum_ref"]][key]
    if field_type == "width_flag":
        reg = resolve_source(spec["source"], derived)
        return spec["mapping"][reg.kind]
    if field_type == "bit_slice":
        value = resolve_source(spec["source"], derived)
        if not isinstance(value, int):
            try:
                return symbol_slice_factory(value, spec)
            except Exception as exc:  # pragma: no cover - delegated factory failure
                raise error_factory(str(exc)) from exc
        scalar_value = scalarize(value)
        width = spec["msb"] - spec["lsb"] + 1
        return (scalar_value >> spec["lsb"]) & ((1 << width) - 1)
    if field_type == "keyword_presence_flag":
        value = resolve_source(spec["source"], derived)
        return spec["present_value"] if value else spec["absent_value"]
    if field_type == "keyword_combination_lookup":
        values = [bool(resolve_source(source, derived)) for source in spec["sources"]]
        for case in spec["cases"]:
            if case["when"] == values:
                return case["value"]
        raise error_factory("no derived-field case matches keyword combination")
    if field_type == "slot_or_constant":
        value = resolve_source(spec["source"], derived)
        if value is None:
            return spec["when_absent"]
        return scalarize(value)
    raise error_factory(f"unsupported derived field type '{field_type}' in JSON ISA")


def match_named_literal_derived_fields(
    derived_specs: dict[str, dict[str, Any]],
    named_literals: dict[str, str],
    source_values: dict[str, int],
    *,
    abstract_enums: dict[str, dict[str, int]],
    error_factory: Callable[[str], Exception],
) -> bool:
    for derived_name, spec in derived_specs.items():
        source = spec.get("source")
        if not isinstance(source, str) or not source.startswith("sequence."):
            continue
        input_name = source.split(".", 2)[1]
        if input_name not in named_literals:
            continue
        if spec["type"] != "enum_lookup":
            raise error_factory(
                f"named-literal derived field {derived_name} uses unsupported type {spec['type']!r}"
            )
        expected = abstract_enums[spec["enum_ref"]][named_literals[input_name]]
        if source_values.get(f"derived.{derived_name}") != expected:
            return False
    return True


def match_slot_or_constant_derived_fields(
    derived_specs: dict[str, dict[str, Any]],
    pattern_slots: set[str],
    source_values: dict[str, int],
    *,
    error_factory: Callable[[str], Exception],
) -> bool:
    for derived_name, spec in derived_specs.items():
        if spec["type"] != "slot_or_constant":
            continue
        source = spec["source"]
        if not isinstance(source, str) or not source.startswith("sequence."):
            raise error_factory(f"slot_or_constant source must be sequence.*, got {source!r}")
        slot_name = source.split(".", 2)[1]
        if slot_name in pattern_slots:
            continue
        if source_values.get(f"derived.{derived_name}") != spec["when_absent"]:
            return False
    return True


def invert_enum_value(
    enum_ref: str,
    value: int,
    *,
    abstract_enums: dict[str, dict[str, int]],
    error_factory: Callable[[str], Exception],
) -> str:
    inverse = {enum_value: key for key, enum_value in abstract_enums[enum_ref].items()}
    if value not in inverse:
        raise error_factory(f"value {value} is not valid for enum {enum_ref}")
    return inverse[value]


def invert_mapping_value(
    mapping: dict[str, int],
    value: int,
    *,
    error_factory: Callable[[str], Exception],
) -> str:
    inverse = {mapped: key for key, mapped in mapping.items()}
    if value not in inverse:
        raise error_factory(f"value {value} is not valid for mapping")
    return inverse[value]


def invert_keyword_case(
    cases: list[dict[str, Any]],
    value: int,
    *,
    error_factory: Callable[[str], Exception],
) -> dict[str, Any]:
    for case in cases:
        if case["value"] == value:
            return case
    raise error_factory(f"value {value} is not valid for keyword combination")


def merge_bit_slices(
    fragments: list[tuple[int, int, int]],
    *,
    error_factory: Callable[[str], Exception],
) -> int:
    value = 0
    covered = 0
    for lsb, msb, fragment in fragments:
        width = msb - lsb + 1
        mask = ((1 << width) - 1) << lsb
        if covered & mask:
            raise error_factory("overlapping bit slices")
        covered |= mask
        value |= (fragment & ((1 << width) - 1)) << lsb
    return value


__all__ = [
    "evaluate_derived_field",
    "evaluate_derived_fields",
    "invert_enum_value",
    "invert_keyword_case",
    "invert_mapping_value",
    "match_named_literal_derived_fields",
    "match_slot_or_constant_derived_fields",
    "merge_bit_slices",
]
