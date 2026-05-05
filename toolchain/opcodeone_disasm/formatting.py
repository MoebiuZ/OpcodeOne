# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re

from .constants import (
    COMPACT_MNEMONIC_ROOTS,
    CONDITION_TOKENS,
    EXTENDER_TOKENS,
    IMMEDIATE_MNEMONIC_ROOTS,
    KEYWORD_TOKENS,
    MNEMONIC_TOKENS,
    MODIFIER_TOKENS,
    REG16_BY_CODE,
    REG16_TOKENS,
    REG24_BY_CODE,
    REG24_TOKENS,
    REGSPECIAL_TOKENS,
)
from .model import DisassembledLine, DisassemblerError, HighlightToken


def sign_extend(value: int, bits: int) -> int:
    sign_bit = 1 << (bits - 1)
    mask = (1 << bits) - 1
    value &= mask
    return (value ^ sign_bit) - sign_bit


def format_signed(value: int) -> str:
    return f"{value:+d}"


def format_hex(value: int, digits: int) -> str:
    return f"0x{value:0{digits}X}"


def format_addr(value: int, digits: int) -> str:
    return f"{value:0{digits}X}"


def display_address_prefix(address: int) -> str:
    return f"{format_addr(address, 6)}: "


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def mnemonic_root(token: str) -> str:
    return token.split(".", 1)[0].upper()


def classify_token(token: str) -> str:
    if not token or token.isspace():
        return "plain"
    if token in {"[", "]"}:
        return "bracket"
    if re.fullmatch(r"0x[0-9A-Fa-f]+|[+-]?\d+", token):
        return "literal"
    upper = token.upper()
    if token in REG16_TOKENS:
        return "reg16"
    if token in REGSPECIAL_TOKENS:
        return "regspecial"
    if token in REG24_TOKENS:
        return "reg24"
    if token in MODIFIER_TOKENS or upper in MODIFIER_TOKENS:
        return "modifier"
    if token in EXTENDER_TOKENS:
        return "extender"
    if upper in MNEMONIC_TOKENS or mnemonic_root(token) in MNEMONIC_TOKENS or mnemonic_root(token) in COMPACT_MNEMONIC_ROOTS:
        return "mnemonic"
    if token in CONDITION_TOKENS or upper in CONDITION_TOKENS:
        return "condition"
    if token in KEYWORD_TOKENS or upper in KEYWORD_TOKENS:
        return "keyword"
    return "plain"


def _is_immediate_literal_context(parts: list[str], index: int) -> bool:
    token = parts[index]
    if not re.fullmatch(r"0x[0-9A-Fa-f]+|[+-]?\d+", token):
        return False

    prev_meaningful: str | None = None
    last_mnemonic: str | None = None
    bracket_depth = 0
    for part in parts[:index]:
        if part == "[":
            bracket_depth += 1
        elif part == "]":
            bracket_depth = max(0, bracket_depth - 1)
        elif not part.isspace():
            prev_meaningful = part
            if classify_token(part) == "mnemonic":
                last_mnemonic = mnemonic_root(part)

    prev_upper = prev_meaningful.upper() if prev_meaningful else ""
    if bracket_depth > 0 or token.startswith("+") or token.startswith("-"):
        return False
    if prev_upper == "TO" and last_mnemonic == "SET":
        return True
    if prev_upper == "," and last_mnemonic in IMMEDIATE_MNEMONIC_ROOTS:
        return True
    if prev_upper in {"AND", "OR", "XOR", "PLUS", "MINUS", "TIMES", "DIV", "MODULE", "LEFTSHIFT", "RIGHTSHIFT"}:
        return True
    if prev_upper in {"TESTBIT", "SETBIT", "CLEARBIT", "TOGGLEBIT"}:
        return True
    return False


def reformat_literal(token: str, use_hex: bool, *, is_immediate: bool) -> str:
    if not is_immediate:
        return token
    if re.fullmatch(r"0x[0-9A-Fa-f]+", token):
        return token if use_hex else str(int(token, 16))
    if re.fullmatch(r"\+?\d+", token):
        value = int(token.lstrip("+"))
        if use_hex:
            digits = max(2, (value.bit_length() + 3) // 4)
            return format_hex(value, digits)
        return str(value)
    return token


def highlight_disassembly_text(text: str, use_hex: bool = True) -> list[HighlightToken]:
    parts = re.findall(r"0x[0-9A-Fa-f]+|[+-]?\d+|[A-Za-z]+(?:\.[A-Za-z]+)*|\[|\]|\s+|.", text)
    tokens = []
    for index, part in enumerate(parts):
        kind = classify_token(part)
        display = reformat_literal(part, use_hex, is_immediate=_is_immediate_literal_context(parts, index)) if kind == "literal" else part
        tokens.append(HighlightToken(display, kind))
    return tokens


def reg16_name(code: int) -> str:
    if code not in REG16_BY_CODE:
        raise DisassemblerError(f"invalid reg16 code {code}")
    return REG16_BY_CODE[code]


def reg24_name(code: int) -> str:
    if code not in REG24_BY_CODE:
        raise DisassemblerError(f"invalid reg24 code {code}")
    return REG24_BY_CODE[code]


def reg_name(code: int, kind: str) -> str:
    if kind == "reg16":
        return reg16_name(code)
    if kind == "reg24":
        return reg24_name(code)
    raise DisassemblerError(f"unsupported register kind {kind}")


def decode_reg_field(code: int, kind: str, field: str) -> str:
    if kind == "reg16":
        return reg16_name(code)
    if code & 0b100:
        raise DisassemblerError(f"{field} uses non-zero high bit for reg24 encoding: {code}")
    return reg24_name(code & 0b11)


def require_zero(value: int, mask: int, label: str) -> None:
    if value & mask:
        raise DisassemblerError(f"{label} must be zero, got 0x{value & mask:X}")


def segment_display_text(text: str) -> str | None:
    if text == "--DATA:":
        return "DATA SEGMENT:"
    if text == "--CODE:":
        return "CODE SEGMENT:"
    return None


def format_source(lines: list[str] | list[DisassembledLine], *, show_addresses: bool = False) -> str:
    rendered: list[str] = []
    for line in lines:
        if not isinstance(line, str) and hasattr(line, "text") and hasattr(line, "address"):
            text_value = line.text
            if text_value == "":
                rendered.append("")
                continue
            segment_text = segment_display_text(text_value)
            if segment_text is not None:
                if not rendered or rendered[-1] != "":
                    rendered.append("")
                rendered.append(segment_text)
                continue
            text = text_value
            if show_addresses:
                text = f"{format_addr(line.address, 6)}: {text}"
            rendered.append(text)
        else:
            rendered.append(line)
    return "\n".join(rendered)
