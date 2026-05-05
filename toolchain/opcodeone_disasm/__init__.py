# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from .constants import DISASSEMBLER_VERSION
from .cli import main
from .decode import disassemble_listing, disassemble_words, words_from_binary
from .formatting import (
    display_address_prefix,
    format_source,
    highlight_disassembly_text,
    normalize_space,
)
from .io import read_interactive_input, read_legacy_input, read_object_input
from .json_decoder import JsonDisassembler
from .listing import (
    data_listing_from_bytes,
    data_listing_from_words,
    disassemble_listing_relaxed,
    disassemble_object_listing,
    disassemble_segment,
)
from .theme import build_curses_theme, load_disasm_theme
from .viewer import interactive_disassembly_viewer

__all__ = [
    "DISASSEMBLER_VERSION",
    "build_curses_theme",
    "data_listing_from_bytes",
    "data_listing_from_words",
    "display_address_prefix",
    "disassemble_listing",
    "disassemble_listing_relaxed",
    "disassemble_object_listing",
    "disassemble_segment",
    "disassemble_words",
    "format_source",
    "highlight_disassembly_text",
    "interactive_disassembly_viewer",
    "JsonDisassembler",
    "load_disasm_theme",
    "main",
    "normalize_space",
    "read_interactive_input",
    "read_legacy_input",
    "read_object_input",
    "words_from_binary",
]
