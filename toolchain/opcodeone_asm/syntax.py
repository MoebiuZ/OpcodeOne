# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import ast
import re
from pathlib import Path

from .constants import ADDR_DIRECTIVE_RE, ALIGN_DIRECTIVE_RE, BYTE_DIRECTIVE_RE, FILE_DIRECTIVE_RE, FILL_DIRECTIVE_RE, INVALID_LABEL_REF_RE, LABEL_DEF_RE, LABEL_REF_RE, SECTION_CODE_RE, SECTION_DATA_RE, WORD_DIRECTIVE_RE
from .model import AssemblerError, ConstantRef, IntValue, SignedSymbolRef, SymbolRef


_ACTIVE_SYMBOLS: dict[str, int] = {}
_SYMBOL_EXPR_RE = re.compile(
    r"(?P<lead>[+-])?\s*(?P<symbol>\.[A-Za-z_][A-Za-z0-9_]*|%[A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s*(?P<op>[+-])\s*(?P<addend>0[xX][0-9A-Fa-f]+|\d+|%[A-Za-z_][A-Za-z0-9_]*))?"
)


def set_active_symbols(symbols: dict[str, int]) -> dict[str, int]:
    global _ACTIVE_SYMBOLS
    previous = _ACTIVE_SYMBOLS
    _ACTIVE_SYMBOLS = symbols
    return previous


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _normalize_symbol_name(token: str) -> str:
    return token[1:].lower() if token.startswith("%") else token.lower()


def invalid_label_name_error(line_no: int, label: str) -> AssemblerError:
    return AssemblerError(
        f"line {line_no}: invalid label name '{label}'; labels must start with a letter or underscore"
    )


def extract_invalid_label_ref(token: str) -> str | None:
    match = INVALID_LABEL_REF_RE.fullmatch(normalize_space(token))
    if not match:
        return None
    return match.group("label")


def _resolve_constant_ref(constant_ref: ConstantRef) -> int | None:
    value = _ACTIVE_SYMBOLS.get(constant_ref.name)
    if value is None:
        return None
    return value * constant_ref.sign


def _parse_symbol_addend(addend_text: str, op: str | None) -> int | ConstantRef:
    if addend_text.startswith("%"):
        sign = -1 if op == "-" else 1
        return ConstantRef(addend_text[1:].lower(), sign=sign)
    addend = int(addend_text, 0)
    if op == "-":
        addend = -addend
    return addend


def _parse_symbol_expression(token: str) -> tuple[str | None, str, int | ConstantRef] | None:
    token = normalize_space(token)
    match = _SYMBOL_EXPR_RE.fullmatch(token)
    if not match:
        return None
    lead = match.group("lead")
    symbol = _normalize_symbol_name(match.group("symbol"))
    addend: int | ConstantRef = 0
    addend_text = match.group("addend")
    if addend_text is not None:
        addend = _parse_symbol_addend(addend_text, match.group("op"))
    return lead, symbol, addend


def parse_symbol_ref_expr(token: str) -> SymbolRef | None:
    symbol_expr = _parse_symbol_expression(token)
    if symbol_expr is None:
        return None
    lead, symbol, addend = symbol_expr
    if lead not in (None, "+"):
        return None
    return SymbolRef(symbol, addend=addend)


def parse_number(token: str, line_no: int) -> int:
    token = token.strip()
    try:
        return int(token, 0)
    except ValueError as exc:
        if token.startswith("."):
            value = _ACTIVE_SYMBOLS.get(token.lower())
            if value is not None:
                return value
        if token.startswith("%"):
            value = _ACTIVE_SYMBOLS.get(token[1:].lower())
            if value is not None:
                return value
        match = re.fullmatch(r"([+-])%([A-Za-z_][A-Za-z0-9_]*)", token)
        if match:
            sign, name = match.groups()
            value = _ACTIVE_SYMBOLS.get(name.lower())
            if value is not None:
                return value if sign == "+" else -value
        match = re.fullmatch(r"([+-])(\.[A-Za-z_][A-Za-z0-9_]*)", token)
        if match:
            sign, name = match.groups()
            value = _ACTIVE_SYMBOLS.get(name.lower())
            if value is not None:
                return value if sign == "+" else -value
        symbol_expr = _parse_symbol_expression(token)
        if symbol_expr is not None:
            lead, name, addend = symbol_expr
            value = _ACTIVE_SYMBOLS.get(name)
            resolved_addend = addend if isinstance(addend, int) else _resolve_constant_ref(addend)
            if value is not None and resolved_addend is not None:
                if lead == "-":
                    return -value + resolved_addend
                return value + resolved_addend
        invalid_label = extract_invalid_label_ref(token)
        if invalid_label is not None:
            raise invalid_label_name_error(line_no, invalid_label) from exc
        raise AssemblerError(f"line {line_no}: invalid numeric literal '{token}'") from exc


def parse_signed(token: str, bits: int, line_no: int, label: str) -> int:
    value = parse_number(token, line_no)
    lo = -(1 << (bits - 1))
    hi = (1 << (bits - 1)) - 1
    if not lo <= value <= hi:
        raise AssemblerError(f"line {line_no}: {label} out of range for signed {bits}-bit field: {value}")
    return value


def parse_unsigned(token: str, bits: int, line_no: int, label: str) -> int:
    value = parse_number(token, line_no)
    hi = (1 << bits) - 1
    if not 0 <= value <= hi:
        raise AssemblerError(f"line {line_no}: {label} out of range for unsigned {bits}-bit field: {value}")
    return value


def parse_value_expr(token: str, line_no: int) -> IntValue | SymbolRef:
    token = token.strip()
    symbol_ref = parse_symbol_ref_expr(token)
    if symbol_ref is not None:
        return symbol_ref
    try:
        return IntValue(parse_number(token, line_no))
    except AssemblerError as exc:
        if LABEL_REF_RE.fullmatch(token):
            return SymbolRef(token.lower())
        match = re.fullmatch(r"%([A-Za-z_][A-Za-z0-9_]*)", token)
        if match:
            return SymbolRef(match.group(1).lower())
        raise exc


def parse_signed_value_expr(token: str, bits: int, line_no: int, label: str) -> int | SignedSymbolRef:
    token = token.strip()
    symbol_expr = _parse_symbol_expression(token)
    if symbol_expr is not None:
        lead, symbol, addend = symbol_expr
        if lead != "-" or addend == 0:
            sign = -1 if lead == "-" else 1
            return SignedSymbolRef(symbol=SymbolRef(symbol, addend=addend), bits=bits, sign=sign)
    try:
        return parse_signed(token, bits, line_no, label)
    except AssemblerError as exc:
        match = re.fullmatch(r"([+-])?(\.[A-Za-z_][A-Za-z0-9_]*|%[A-Za-z_][A-Za-z0-9_]*)", token)
        if not match:
            raise exc
        sign_text, symbol_text = match.groups()
        expr = parse_value_expr(symbol_text, line_no)
        if isinstance(expr, SymbolRef):
            sign = -1 if sign_text == "-" else 1
            return SignedSymbolRef(symbol=expr, bits=bits, sign=sign)
        raise exc


def parse_unsigned_value_expr(token: str, bits: int, line_no: int, label: str) -> int | SymbolRef:
    token = token.strip()
    symbol_ref = parse_symbol_ref_expr(token)
    if symbol_ref is not None:
        return symbol_ref
    try:
        return parse_unsigned(token, bits, line_no, label)
    except AssemblerError as exc:
        expr = parse_value_expr(token, line_no)
        if isinstance(expr, SymbolRef):
            return expr
        raise exc


def pack_bits(value: int, bits: int) -> int:
    return value & ((1 << bits) - 1)


def split_directive_items(text: str, line_no: int, directive_name: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    quote: str | None = None
    escaped = False
    index = 0
    while index < len(text):
        ch = text[index]
        if quote is not None:
            current.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            index += 1
            continue
        if ch == "U" and index + 1 < len(text) and text[index + 1] in {'"', "'"}:
            current.append(ch)
            index += 1
            ch = text[index]
            quote = ch
            current.append(ch)
            index += 1
            continue
        if ch in {'"', "'"}:
            quote = ch
            current.append(ch)
            index += 1
            continue
        if ch == ",":
            item = "".join(current).strip()
            if not item:
                raise AssemblerError(f"line {line_no}: empty {directive_name} item")
            items.append(item)
            current = []
            index += 1
            continue
        current.append(ch)
        index += 1
    if quote is not None:
        raise AssemblerError(f"line {line_no}: unterminated string in {directive_name} directive")
    item = "".join(current).strip()
    if not item:
        raise AssemblerError(f"line {line_no}: empty {directive_name} item")
    items.append(item)
    return items


def parse_byte_string(token: str, line_no: int) -> list[int]:
    encoding = "ascii"
    literal = token
    if token.startswith("U") and len(token) > 1 and token[1] in {'"', "'"}:
        encoding = "utf-8"
        literal = token[1:]
    try:
        value = ast.literal_eval(literal)
    except (SyntaxError, ValueError) as exc:
        raise AssemblerError(f"line {line_no}: invalid byte string literal {token!r}") from exc
    if not isinstance(value, str):
        raise AssemblerError(f"line {line_no}: byte string literal must be a quoted string")
    try:
        return list(value.encode(encoding))
    except UnicodeEncodeError as exc:
        if encoding == "ascii":
            raise AssemblerError(f"line {line_no}: byte string literal must be ASCII; use U\"...\" for UTF-8") from exc
        raise AssemblerError(f"line {line_no}: invalid UTF-8 byte string literal") from exc


def parse_byte_directive(raw: str, line_no: int) -> list[int] | None:
    match = BYTE_DIRECTIVE_RE.fullmatch(raw)
    if not match:
        return None
    data: list[int] = []
    for item in split_directive_items(match.group(1), line_no, "byte"):
        if item[0] in {'"', "'"} or (item[0] == "U" and len(item) > 1 and item[1] in {'"', "'"}):
            data.extend(parse_byte_string(item, line_no))
            continue
        data.append(parse_unsigned(item, 8, line_no, "byte value"))
    return data


def _parse_numeric_directive(
    raw: str,
    line_no: int,
    *,
    directive_re: re.Pattern[str],
    directive_name: str,
    bits: int,
    value_label: str,
) -> list[int] | None:
    match = directive_re.fullmatch(raw)
    if not match:
        return None
    data: list[int] = []
    for item in split_directive_items(match.group(1), line_no, directive_name):
        if item[0] in {'"', "'"} or (item[0] == "U" and len(item) > 1 and item[1] in {'"', "'"}):
            raise AssemblerError(f"line {line_no}: {directive_name} items must be numeric")
        value = parse_unsigned(item, bits, line_no, value_label)
        for shift in range(0, bits, 8):
            data.append((value >> shift) & 0xFF)
    return data


def parse_word_directive(raw: str, line_no: int) -> list[int] | None:
    return _parse_numeric_directive(
        raw,
        line_no,
        directive_re=WORD_DIRECTIVE_RE,
        directive_name="word",
        bits=16,
        value_label="word value",
    )


def parse_addr_directive(raw: str, line_no: int) -> list[int] | None:
    return _parse_numeric_directive(
        raw,
        line_no,
        directive_re=ADDR_DIRECTIVE_RE,
        directive_name="addr",
        bits=24,
        value_label="address value",
    )


def parse_fill_directive(raw: str, line_no: int) -> list[int] | None:
    match = FILL_DIRECTIVE_RE.fullmatch(raw)
    if not match:
        return None
    count_text, byte_text = match.groups()
    count = parse_unsigned(count_text, 24, line_no, "fill count")
    fill_byte = parse_unsigned(byte_text, 8, line_no, "fill byte value")
    return [fill_byte] * count


def parse_align_directive(raw: str, line_no: int) -> int | None:
    match = ALIGN_DIRECTIVE_RE.fullmatch(raw)
    if not match:
        return None
    alignment = parse_unsigned(match.group(1), 24, line_no, "alignment")
    if alignment == 0 or alignment & (alignment - 1):
        raise AssemblerError(f"line {line_no}: align value must be a positive power of two: {alignment}")
    return alignment


def _parse_path_token(token: str, line_no: int) -> str:
    token = token.strip()
    if not token:
        raise AssemblerError(f"line {line_no}: missing file path")
    if token[0] in {'"', "'"}:
        try:
            value = ast.literal_eval(token)
        except (SyntaxError, ValueError) as exc:
            raise AssemblerError(f"line {line_no}: invalid file path literal {token!r}") from exc
        if not isinstance(value, str):
            raise AssemblerError(f"line {line_no}: file path literal must be a quoted string")
        if not value:
            raise AssemblerError(f"line {line_no}: file path must not be empty")
        return value
    return token


def parse_file_directive(raw: str, line_no: int, *, base_dir: Path | None = None) -> list[int] | None:
    match = FILE_DIRECTIVE_RE.fullmatch(raw)
    if not match:
        return None
    path_text = _parse_path_token(match.group(1), line_no)
    path = Path(path_text)
    if not path.is_absolute():
        path = (base_dir or Path.cwd()) / path
    resolved = path.resolve()
    try:
        return list(resolved.read_bytes())
    except FileNotFoundError as exc:
        raise AssemblerError(f"line {line_no}: file directive target not found: {resolved}") from exc
    except OSError as exc:
        raise AssemblerError(f"line {line_no}: could not read file directive target: {resolved}: {exc.strerror or exc}") from exc


def parse_data_directive(raw: str, line_no: int, *, base_dir: Path | None = None) -> list[int] | None:
    for parser in (parse_byte_directive, parse_word_directive, parse_addr_directive, parse_fill_directive):
        data = parser(raw, line_no)
        if data is not None:
            return data
    file_data = parse_file_directive(raw, line_no, base_dir=base_dir)
    if file_data is not None:
        return file_data
    return None


def is_data_directive(raw: str) -> bool:
    return any(
        directive_re.fullmatch(raw) is not None
        for directive_re in (
            BYTE_DIRECTIVE_RE,
            WORD_DIRECTIVE_RE,
            ADDR_DIRECTIVE_RE,
            FILL_DIRECTIVE_RE,
            FILE_DIRECTIVE_RE,
            ALIGN_DIRECTIVE_RE,
        )
    )


def alignment_padding(offset: int, alignment: int) -> int:
    return (-offset) & (alignment - 1)


def parse_section_directive(raw: str) -> str | None:
    if SECTION_CODE_RE.fullmatch(raw):
        return "code"
    if SECTION_DATA_RE.fullmatch(raw):
        return "data"
    return None


def parse_label_definition(raw: str) -> str | None:
    match = LABEL_DEF_RE.fullmatch(raw)
    if not match:
        return None
    return match.group(1).lower()


def is_label_reference(token: str) -> bool:
    return LABEL_REF_RE.fullmatch(token.strip()) is not None


def flush_pending_bytes(words: list[int], pending_bytes: list[int]) -> None:
    if not pending_bytes:
        return
    if len(pending_bytes) % 2:
        pending_bytes.append(0)
    for index in range(0, len(pending_bytes), 2):
        words.append(pending_bytes[index] | (pending_bytes[index + 1] << 8))
    pending_bytes.clear()
