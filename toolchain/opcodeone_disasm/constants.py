# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import curses

try:
    from common.opcodeone_bundle_runtime import default_register_name_maps
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_bundle_runtime import default_register_name_maps


DISASSEMBLER_VERSION = "1.0"

REG16_BY_CODE, REG24_BY_CODE, REGSPECIAL_TOKENS = default_register_name_maps()
COND_TEXT = {1: "EQUAL", 2: "LESS than", 3: "BELOW", 4: "CHECK"}
LOGIC_TEXT = {0: "AND", 1: "OR", 2: "XOR"}
BIT_TEXT = {0: "TESTBIT", 1: "SETBIT", 2: "CLEARBIT", 3: "TOGGLEBIT"}
SHIFT_TEXT = {0: "LEFTSHIFT", 1: "RIGHTSHIFT", 2: "logical RIGHTSHIFT"}
MNEMONIC_TOKENS = {
    "PASS", "INTERRUPTIONS", "STOP", "PLACE", "LIFT", "LEAVE", "ENTER",
    "COPY", "MOVE", "SWAP", "PLUS", "MINUS", "TIMES", "DIV", "MODULE",
    "NEGATE", "ABSOLUTE", "SET", "NOT", "AND", "OR", "XOR", "TESTBIT",
    "SETBIT", "CLEARBIT", "TOGGLEBIT", "MIN", "MAX", "LEFTSHIFT",
    "RIGHTSHIFT", "LEFTROTATE", "RIGHTROTATE", "JUMP", "TAKE", "GIVE",
}
COMPACT_MNEMONIC_ROOTS = {
    "ABS", "BCLR", "BSET", "BTGL", "BTST", "GIVE", "INT", "JUMP", "LEAVE",
    "LSH", "LROT", "MAX", "MIN", "MINUS", "MOD", "NEG", "PLUS", "RROT",
    "RSH", "TAKE", "TIMES",
}
IMMEDIATE_MNEMONIC_ROOTS = {
    "AND", "BCLR", "BSET", "BTGL", "BTST", "DIV", "LSH", "MINUS", "MOD",
    "OR", "PLUS", "RSH", "SET", "TIMES", "XOR",
}
REG16_TOKENS = set(REG16_BY_CODE.values())
REG24_TOKENS = set(REG24_BY_CODE.values())
REGISTER_TOKENS = REG16_TOKENS | REG24_TOKENS
CONDITION_TOKENS = {"EQUAL", "LESS", "BELOW", "CHECK"}
KEYWORD_TOKENS = {"into", "to", "with", "of", "when", "from", "than"}
MODIFIER_TOKENS = {"on", "off", "logical", "unsigned"}
EXTENDER_TOKENS = {"byte", "keep", "use", "carry", "borrow", "high", "and", "interruption"}
THEME_TOKEN_KEYS = (
    "plain", "address", "mnemonic", "reg16", "reg24", "regspecial",
    "literal", "modifier", "extender", "keyword", "condition", "bracket", "segment",
)
CURSES_COLOR_NAMES = {
    "default": -1,
    "black": curses.COLOR_BLACK,
    "red": curses.COLOR_RED,
    "green": curses.COLOR_GREEN,
    "yellow": curses.COLOR_YELLOW,
    "blue": curses.COLOR_BLUE,
    "magenta": curses.COLOR_MAGENTA,
    "cyan": curses.COLOR_CYAN,
    "white": curses.COLOR_WHITE,
}
CURSES_ATTR_NAMES = {
    "bold": curses.A_BOLD,
    "dim": curses.A_DIM,
    "reverse": curses.A_REVERSE,
    "underline": curses.A_UNDERLINE,
}
DEFAULT_DISASM_THEME = {
    "tokens": {
        "plain": {},
        "address": {"fg": "cyan", "attrs": ["bold"]},
        "mnemonic": {"fg": "yellow", "attrs": ["bold"]},
        "reg16": {"fg": "green", "fg256": 76, "attrs": ["bold"]},
        "reg24": {"fg": "magenta", "fg256": 171, "attrs": ["bold"]},
        "regspecial": {"fg": "red", "fg256": 196, "attrs": ["bold"]},
        "literal": {"fg": "magenta"},
        "modifier": {"fg": "red", "attrs": ["bold"]},
        "extender": {"fg": "yellow"},
        "keyword": {"fg": "blue", "attrs": ["dim"]},
        "condition": {"fg": "cyan", "attrs": ["bold"]},
        "bracket": {"fg": "white", "attrs": ["dim"]},
        "segment": {"fg": "red", "attrs": ["bold"]},
    },
    "ui": {
        "current_line": {"bg256": 236},
        "status": {"fg": "cyan", "attrs": ["reverse"]},
    },
}
