# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .opcodeone_bundle_runtime import opcode_map_from_bundle


@dataclass(frozen=True)
class RuntimeSlotSpec:
    name: str
    slot_kind: str
    operand_kind_ref: str | None
    enum_ref: str | None
    keyword_ref: str | None
    optional: bool
    omit_keys: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeFixedField:
    word_index: int
    mask: int
    expected: int
    label: str


@dataclass(frozen=True)
class RuntimeSourceField:
    source: str
    word_index: int
    lsb: int
    width: int
    label: str


@dataclass(frozen=True)
class RuntimePattern:
    name: str
    sequence: tuple[dict[str, Any], ...]
    slot_tokens: tuple[dict[str, Any], ...]
    named_literals: dict[str, str]
    slot_names: frozenset[str]
    operand_slot_names: frozenset[str]


@dataclass(frozen=True)
class RuntimeForm:
    family_name: str
    opcode_ref: str
    opcode: int
    form_name: str
    syntax_patterns: tuple[RuntimePattern, ...]
    slot_specs: dict[str, RuntimeSlotSpec]
    defaults: dict[str, Any]
    constraints: tuple[dict[str, Any], ...]
    derived_fields: dict[str, dict[str, Any]]
    word_count: int
    encoding_words: tuple[tuple[dict[str, Any], ...], ...]
    fixed_fields: tuple[RuntimeFixedField, ...]
    source_fields: tuple[RuntimeSourceField, ...]


@dataclass(frozen=True)
class RuntimeFamily:
    name: str
    opcode_ref: str
    opcode: int
    forms: tuple[RuntimeForm, ...]


@dataclass(frozen=True)
class RuntimeBundle:
    families: tuple[RuntimeFamily, ...]
    forms_by_opcode: dict[int, tuple[str, tuple[RuntimeForm, ...]]]


def build_runtime_bundle(bundle: dict[str, Any]) -> RuntimeBundle:
    opcode_map = opcode_map_from_bundle(bundle)
    families: list[RuntimeFamily] = []
    forms_by_opcode: dict[int, tuple[str, tuple[RuntimeForm, ...]]] = {}

    for family in bundle["families"]:
        family_name = family["name"]
        opcode_ref = family["opcode_ref"]
        opcode = opcode_map[opcode_ref]
        compiled_forms = tuple(_compile_form(family_name, opcode_ref, opcode, form) for form in family["forms"])
        runtime_family = RuntimeFamily(name=family_name, opcode_ref=opcode_ref, opcode=opcode, forms=compiled_forms)
        families.append(runtime_family)
        forms_by_opcode[opcode] = (family_name, compiled_forms)

    return RuntimeBundle(families=tuple(families), forms_by_opcode=forms_by_opcode)


def _compile_form(
    family_name: str,
    opcode_ref: str,
    opcode: int,
    form: dict[str, Any],
) -> RuntimeForm:
    fixed_fields: list[RuntimeFixedField] = []
    source_fields: list[RuntimeSourceField] = []
    encoding_words = tuple(tuple(word_fields) for word_fields in form["encoding"]["words"])
    for word_index, word_fields in enumerate(encoding_words):
        for field in word_fields:
            width = field["msb"] - field["lsb"] + 1
            mask = ((1 << width) - 1) << field["lsb"]
            if field["kind"] == "fixed":
                fixed_fields.append(
                    RuntimeFixedField(
                        word_index=word_index,
                        mask=mask,
                        expected=field["value"] << field["lsb"],
                        label=f"{family_name}.{form['name']} {field['name']}",
                    )
                )
                continue
            source = field["source"]
            if source == "family_opcode":
                fixed_fields.append(
                    RuntimeFixedField(
                        word_index=word_index,
                        mask=mask,
                        expected=opcode << field["lsb"],
                        label=f"{family_name}.{form['name']} {field['name']}",
                    )
                )
                continue
            source_fields.append(
                RuntimeSourceField(
                    source=source,
                    word_index=word_index,
                    lsb=field["lsb"],
                    width=width,
                    label=f"{family_name}.{form['name']} {field['name']}",
                )
            )

    slot_specs: dict[str, RuntimeSlotSpec] = {}
    syntax_patterns = tuple(_compile_pattern(pattern) for pattern in form["syntax"]["patterns"])
    for pattern in syntax_patterns:
        for token in pattern.slot_tokens:
            spec = RuntimeSlotSpec(
                name=token["name"],
                slot_kind=token["slot_kind"],
                operand_kind_ref=token.get("operand_kind_ref"),
                enum_ref=token.get("enum_ref"),
                keyword_ref=token.get("keyword_ref"),
                optional=bool(token.get("optional", False)),
                omit_keys=tuple(token.get("omit_keys", [])),
            )
            existing = slot_specs.get(spec.name)
            if existing is not None and existing != spec:
                raise ValueError(f"{family_name}.{form['name']}: conflicting slot specs for '{spec.name}'")
            slot_specs[spec.name] = spec

    return RuntimeForm(
        family_name=family_name,
        opcode_ref=opcode_ref,
        opcode=opcode,
        form_name=form["name"],
        syntax_patterns=syntax_patterns,
        slot_specs=slot_specs,
        defaults=dict(form["defaults"]),
        constraints=tuple(form["constraints"]),
        derived_fields=form["derived_fields"],
        word_count=form["encoding"]["word_count"],
        encoding_words=encoding_words,
        fixed_fields=tuple(fixed_fields),
        source_fields=tuple(source_fields),
    )


def _compile_pattern(pattern: dict[str, Any]) -> RuntimePattern:
    sequence = tuple(pattern["sequence"])
    slot_tokens = tuple(token for token in sequence if token["kind"] == "slot")
    named_literals = {
        token["name"]: token["value"]
        for token in sequence
        if token["kind"] == "literal" and "name" in token
    }
    return RuntimePattern(
        name=pattern["name"],
        sequence=sequence,
        slot_tokens=slot_tokens,
        named_literals=named_literals,
        slot_names=frozenset(token["name"] for token in slot_tokens),
        operand_slot_names=frozenset(
            token["name"]
            for token in slot_tokens
            if token["slot_kind"] == "operand"
        ),
    )


__all__ = [
    "RuntimeBundle",
    "RuntimeFamily",
    "RuntimeFixedField",
    "RuntimeForm",
    "RuntimePattern",
    "RuntimeSlotSpec",
    "RuntimeSourceField",
    "build_runtime_bundle",
]
