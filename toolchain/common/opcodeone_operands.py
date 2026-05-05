# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RegisterOperand:
    kind: str
    name: str
    code: int
    width_bits: int


@dataclass(frozen=True)
class MemoryOperand:
    addressing: str
    base: RegisterOperand | None = None
    offset: Any | None = None
    addr: Any | None = None
    addr_hi8: Any | None = None
    addr_lo16: Any | None = None


def operand_width_bits(value: Any) -> int | None:
    if isinstance(value, RegisterOperand):
        return value.width_bits
    return None


def resolve_sequence_value(root: Any, path: str) -> Any:
    parts = path.split(".")
    if parts[0] not in root:
        return None

    value: Any = root[parts[0]]
    for part in parts[1:]:
        if isinstance(value, (RegisterOperand, MemoryOperand)):
            value = getattr(value, part, None)
            continue
        if isinstance(value, dict):
            value = value.get(part)
            continue
        return None
    return value


def scalarize_operand(value: Any) -> Any:
    if isinstance(value, RegisterOperand):
        return value.code
    return value


__all__ = [
    "MemoryOperand",
    "RegisterOperand",
    "operand_width_bits",
    "resolve_sequence_value",
    "scalarize_operand",
]
