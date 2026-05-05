# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass


class DisassemblerError(Exception):
    pass


@dataclass(frozen=True)
class DisassembledLine:
    address: int
    word_count: int
    text: str
    raw_words: tuple[int, ...] = ()


@dataclass(frozen=True)
class HighlightToken:
    text: str
    kind: str
