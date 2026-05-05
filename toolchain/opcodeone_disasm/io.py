# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import sys
from pathlib import Path

try:
    from common.opcodeone_object import ObjectFile, ObjectFormatError, parse_object
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_object import ObjectFile, ObjectFormatError, parse_object

from .model import DisassemblerError


def read_bytes(path: str | None) -> tuple[bytes, str | None]:
    if path:
        data = Path(path).read_bytes()
        source_name = path
    else:
        data = sys.stdin.buffer.read()
        source_name = None
    return data, source_name


def read_legacy_input(path: str | None, input_format: str) -> list[int]:
    from .decode import auto_detect_words, words_from_binary, words_from_text

    data, source_name = read_bytes(path)
    if input_format == "raw":
        return words_from_binary(data)
    if input_format == "text":
        return words_from_text(data.decode("utf-8"))
    return auto_detect_words(data, source_name)


def read_object_input(path: str | None) -> ObjectFile:
    data, _ = read_bytes(path)
    try:
        return parse_object(data)
    except ObjectFormatError as exc:
        raise DisassemblerError(str(exc)) from exc


def read_interactive_input(binary_mode: bool, input_format: str) -> tuple[ObjectFile | list[int], str]:
    if not sys.stdin.isatty():
        if binary_mode:
            return read_legacy_input(None, input_format), "<stdin>"
        return read_object_input(None), "<stdin>"
    try:
        path = input("source path: ").strip()
    except EOFError as exc:
        raise DisassemblerError("interactive mode requires a source path or piped input") from exc
    if not path:
        raise DisassemblerError("interactive mode requires a source path")
    if binary_mode:
        return read_legacy_input(path, input_format), path
    return read_object_input(path), path
