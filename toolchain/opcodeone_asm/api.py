# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from .assembler import (
    ASSEMBLER_VERSION,
    IMPLEMENTATION_NAME,
    JsonAssembler,
    assemble_exports,
    assemble_line,
    assemble_object,
    assemble_object_bytes,
    assemble_segments,
    assemble_source,
    default_output_path,
    format_payload_size,
    format_words,
)
from .constants import DEFAULT_OPCODE_MAP

__all__ = [
    "ASSEMBLER_VERSION",
    "IMPLEMENTATION_NAME",
    "DEFAULT_OPCODE_MAP",
    "JsonAssembler",
    "assemble_exports",
    "assemble_line",
    "assemble_object",
    "assemble_object_bytes",
    "assemble_segments",
    "assemble_source",
    "default_output_path",
    "format_payload_size",
    "format_words",
]
