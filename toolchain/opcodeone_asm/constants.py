# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re

try:
    from common.opcodeone_bundle_runtime import default_reserved_symbols
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_bundle_runtime import default_reserved_symbols


DEFAULT_OPCODE_MAP = {
    "MEMREGOFF": 0,
    "MEMABS8": 1,
    "MEMABS16": 2,
    "MEMABS24": 3,
    "MOVECOPY": 4,
    "STACK": 5,
    "FLOW": 6,
    "SYSTEM": 7,
    "PLUS": 8,
    "MINUS": 9,
    "TIMES": 10,
    "DIV": 11,
    "UNARY": 12,
    "SET": 13,
    "LOGIC": 14,
    "BIT": 15,
    "MINMAX": 16,
    "SHIFT": 17,
    "ROTATE": 18,
    "JABS": 19,
    "JREG": 20,
    "JCOND": 21,
}

CONST_DEF_RE = re.compile(r"([a-z_][a-z0-9_]*)\s+IS\s+(.+)")
EXPORT_RE = re.compile(r"export\s+(\.?[a-z_][a-z0-9_]*)", flags=re.IGNORECASE)
IMPORT_RE = re.compile(r"import\s+([a-z_][a-z0-9_]*)", flags=re.IGNORECASE)
BYTE_DIRECTIVE_RE = re.compile(r"byte\s+(.+)", flags=re.IGNORECASE)
WORD_DIRECTIVE_RE = re.compile(r"word\s+(.+)", flags=re.IGNORECASE)
ADDR_DIRECTIVE_RE = re.compile(r"addr\s+(.+)", flags=re.IGNORECASE)
FILL_DIRECTIVE_RE = re.compile(r"fill\s+(\S+)\s+(\S+)", flags=re.IGNORECASE)
FILE_DIRECTIVE_RE = re.compile(r"file\s+(.+)", flags=re.IGNORECASE)
ALIGN_DIRECTIVE_RE = re.compile(r"align\s+(\S+)", flags=re.IGNORECASE)
SECTION_CODE_RE = re.compile(r"--code:", flags=re.IGNORECASE)
SECTION_DATA_RE = re.compile(r"--data:", flags=re.IGNORECASE)
LABEL_DEF_RE = re.compile(r"(\.[a-z_][a-z0-9_]*)\s*:", flags=re.IGNORECASE)
LABEL_REF_RE = re.compile(r"\.[a-z_][a-z0-9_]*", flags=re.IGNORECASE)
INVALID_LABEL_DEF_RE = re.compile(r"(\.[0-9][a-z0-9_]*)\s*:", flags=re.IGNORECASE)
INVALID_EXPORT_LABEL_RE = re.compile(r"export\s+(\.[0-9][a-z0-9_]*)", flags=re.IGNORECASE)
INVALID_IMPORT_LABEL_RE = re.compile(r"import\s+(\.[a-z0-9_]+)", flags=re.IGNORECASE)
INVALID_LABEL_REF_RE = re.compile(
    r"(?P<lead>[+-])?\s*(?P<label>\.[0-9][a-z0-9_]*)"
    r"(?:\s*(?P<op>[+-])\s*(?P<addend>0[xX][0-9A-Fa-f]+|\d+|%[A-Za-z_][A-Za-z0-9_]*))?",
    flags=re.IGNORECASE,
)

RESERVED_SYMBOLS = default_reserved_symbols()
