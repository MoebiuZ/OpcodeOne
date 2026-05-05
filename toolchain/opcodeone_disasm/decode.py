# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

from .json_decoder import default_disassembler
from .model import DisassembledLine, DisassemblerError


def words_from_binary(data: bytes) -> list[int]:
    if len(data) % 2:
        raise DisassemblerError("raw object size must be a multiple of 2 bytes")
    return [data[index] | (data[index + 1] << 8) for index in range(0, len(data), 2)]


def words_from_text(text: str) -> list[int]:
    words: list[int] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        raw = line.split(";", 1)[0].strip()
        if not raw:
            continue
        try:
            value = int(raw, 0)
        except ValueError as exc:
            raise DisassemblerError(f"line {line_no}: expected one numeric word per line, got '{raw}'") from exc
        if not 0 <= value <= 0xFFFF:
            raise DisassemblerError(f"line {line_no}: word out of range: {value}")
        words.append(value)
    return words


def auto_detect_words(data: bytes, source_name: str | None = None) -> list[int]:
    suffix = Path(source_name).suffix.lower() if source_name else ""
    if suffix in {".obj", ".bin"}:
        return words_from_binary(data)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return words_from_binary(data)
    try:
        return words_from_text(text)
    except DisassemblerError:
        return words_from_binary(data)


def disassemble_listing(words: list[int], *, base_address: int = 0, surface: str = "canonical") -> list[DisassembledLine]:
    return default_disassembler().disassemble_listing(words, base_address=base_address, surface=surface)


def disassemble_words(words: list[int], *, surface: str = "canonical") -> list[str]:
    return [entry.text for entry in disassemble_listing(words, surface=surface)]


def find_last_strict_prefix(words: list[int]) -> int:
    last_ok = 0
    for end in range(1, len(words) + 1):
        try:
            disassemble_listing(words[:end])
            last_ok = end
        except DisassemblerError:
            continue
    return last_ok
