# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any, Callable

from .opcodeone_operands import RegisterOperand, operand_width_bits


def validate_constraints(
    constraints: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    values: dict[str, Any],
    *,
    error_factory: Callable[[str], Exception],
    symbolic_bit_index_types: tuple[type[Any], ...] = (),
) -> None:
    for constraint in constraints:
        constraint_type = constraint["type"]
        if constraint_type == "same_width":
            widths = {operand_width_bits(values[name]) for name in constraint["operands"]}
            widths.discard(None)
            if len(widths) != 1:
                raise error_factory("register width mismatch")
            continue

        if constraint_type == "same_width_when_present":
            widths = {operand_width_bits(values[name]) for name in constraint["operands"] if name in values}
            widths.discard(None)
            if len(widths) > 1:
                raise error_factory("register width mismatch")
            continue

        if constraint_type == "enum_or_absent":
            slot_name = constraint["slot"]
            slot_value = values.get(slot_name, "absent")
            if slot_value != "absent" and slot_value not in constraint["values"]:
                raise error_factory(f"invalid enum value for {slot_name}")
            continue

        if constraint_type == "keep_high_requires_width":
            if not values.get(constraint["slot"]):
                continue
            register_widths = [value.width_bits for value in values.values() if isinstance(value, RegisterOperand)]
            if not register_widths or register_widths[0] != constraint["width_bits"]:
                raise error_factory("TIMES keep high is only defined for reg16")
            continue

        if constraint_type == "bit_index_within_width":
            bit_index = values[constraint["bit_operand"]]
            if symbolic_bit_index_types and isinstance(bit_index, symbolic_bit_index_types):
                continue
            target = values[constraint["target_operand"]]
            target_width = operand_width_bits(target)
            if target_width is None:
                raise error_factory(f"slot '{constraint['target_operand']}' does not expose width_bits")
            if bit_index < 0 or bit_index >= target_width:
                target_kind = getattr(target, "kind", "target")
                raise error_factory(f"bit index {bit_index} out of range for {target_kind}")
            continue

        if constraint_type == "allowed_register_names":
            reg = values[constraint["slot"]]
            if reg.name not in constraint["names"]:
                names = ", ".join(constraint["names"])
                raise error_factory(f"register '{reg.name}' must be one of {names}")
            continue

        raise error_factory(f"unsupported constraint type '{constraint_type}' in JSON ISA")


__all__ = ["validate_constraints"]
