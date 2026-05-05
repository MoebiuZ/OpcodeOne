# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .constants import (
    ADDR_DIRECTIVE_RE,
    CONST_DEF_RE,
    EXPORT_RE,
    FILL_DIRECTIVE_RE,
    IMPORT_RE,
    INVALID_EXPORT_LABEL_RE,
    INVALID_IMPORT_LABEL_RE,
    INVALID_LABEL_DEF_RE,
    RESERVED_SYMBOLS,
    WORD_DIRECTIVE_RE,
)
from .model import (
    AddrItem,
    AlignItem,
    AssemblerError,
    BlockIR,
    BytesItem,
    FillItem,
    InstrItem,
    LabelItem,
    ModuleIR,
    PreparedAssembly,
    SourceRef,
    WordItem,
    lookup_source_line,
)
from .syntax import (
    alignment_padding,
    is_data_directive,
    parse_align_directive,
    parse_byte_directive,
    parse_file_directive,
    invalid_label_name_error,
    parse_label_definition,
    parse_number,
    parse_section_directive,
    parse_symbol_ref_expr,
    parse_unsigned,
    parse_value_expr,
    set_active_symbols,
    split_directive_items,
)


def _align_up(value: int, alignment: int) -> int:
    if alignment <= 1:
        return value
    return (value + alignment - 1) // alignment * alignment


def _symbol_value_is_relocatable(value_text: str, relocatable_symbols: set[str]) -> bool:
    symbol_ref = parse_symbol_ref_expr(value_text)
    return symbol_ref is not None and symbol_ref.name in relocatable_symbols


def _preprocess_lines(
    lines: list[str],
    *,
    source_path: Path | None,
    base_dir: Path,
    symbols: dict[str, int],
    relocatable_symbols: set[str],
    export_names: set[str],
    export_order: list[str],
    import_names: set[str],
    import_order: list[str],
    blocks: list[BlockIR],
    current_block_ref: list[BlockIR | None],
    section_declared_ref: list[bool],
    cursor_ref: list[int],
    mode_ref: list[str | None],
    build_instruction_item: Callable[[str, int, SourceRef], InstrItem],
) -> None:
    for line_no, line in enumerate(lines, start=1):
        raw = line.split(";", 1)[0].strip()
        if not raw:
            continue
        source = SourceRef(line_no=line_no, source_path=source_path, text=raw)

        section = parse_section_directive(raw)
        if section is not None:
            section_declared_ref[0] = True
            if section == "code":
                cursor_ref[0] = _align_up(cursor_ref[0], 2)
            mode_ref[0] = section
            block = BlockIR(kind=section, items=[])
            blocks.append(block)
            current_block_ref[0] = block
            continue

        if not section_declared_ref[0]:
            raise AssemblerError(f"line {line_no}: segment must be declared first with --CODE: or --DATA:")

        invalid_label_match = INVALID_LABEL_DEF_RE.fullmatch(raw)
        if invalid_label_match:
            raise invalid_label_name_error(line_no, invalid_label_match.group(1))

        label = parse_label_definition(raw)
        if label is not None:
            if label in symbols:
                raise AssemblerError(f"line {line_no}: symbol '{label}' is already defined")
            symbols[label] = cursor_ref[0]
            relocatable_symbols.add(label)
            assert current_block_ref[0] is not None
            current_block_ref[0].items.append(LabelItem(name=label, source=source))
            continue

        match = CONST_DEF_RE.fullmatch(raw)
        if match:
            name, value_text = match.groups()
            symbol = name
            if symbol.upper() in RESERVED_SYMBOLS:
                raise AssemblerError(f"line {line_no}: symbol '{name}' uses a reserved name")
            if symbol in symbols:
                raise AssemblerError(f"line {line_no}: symbol '{name}' is already defined")
            if symbol in import_names:
                raise AssemblerError(f"line {line_no}: symbol '{name}' is already declared as import")
            symbols[symbol] = parse_number(value_text, line_no)
            if _symbol_value_is_relocatable(value_text, relocatable_symbols):
                relocatable_symbols.add(symbol)
            continue

        invalid_export_match = INVALID_EXPORT_LABEL_RE.fullmatch(raw)
        if invalid_export_match:
            raise invalid_label_name_error(line_no, invalid_export_match.group(1))

        export_match = EXPORT_RE.fullmatch(raw)
        if export_match:
            symbol = export_match.group(1).lower()
            if symbol.upper() in RESERVED_SYMBOLS:
                raise AssemblerError(f"line {line_no}: export '{symbol}' uses a reserved name")
            if symbol in export_names:
                raise AssemblerError(f"line {line_no}: export '{symbol}' is already declared")
            if symbol in import_names:
                raise AssemblerError(f"line {line_no}: export '{symbol}' conflicts with an import of the same name")
            export_names.add(symbol)
            export_order.append(symbol)
            continue

        invalid_import_match = INVALID_IMPORT_LABEL_RE.fullmatch(raw)
        if invalid_import_match:
            raise AssemblerError(
                f"line {line_no}: import '{invalid_import_match.group(1)}' must use a global symbol name without leading '.'"
            )

        if raw.split(None, 1)[0].lower() == "import":
            import_match = IMPORT_RE.fullmatch(raw)
            if import_match is None:
                raise AssemblerError(f"line {line_no}: import expects a global symbol name like 'import foo'")
            symbol = import_match.group(1).lower()
            if symbol.upper() in RESERVED_SYMBOLS:
                raise AssemblerError(f"line {line_no}: import '{symbol}' uses a reserved name")
            if symbol in import_names:
                raise AssemblerError(f"line {line_no}: import '{symbol}' is already declared")
            if symbol in symbols:
                raise AssemblerError(f"line {line_no}: import '{symbol}' conflicts with an existing definition")
            if symbol in export_names:
                raise AssemblerError(f"line {line_no}: import '{symbol}' conflicts with an export of the same name")
            import_names.add(symbol)
            import_order.append(symbol)
            continue

        if is_data_directive(raw):
            if mode_ref[0] != "data":
                raise AssemblerError(f"line {line_no}: data directives are only valid in --DATA: blocks")
            item = _build_data_item(raw, line_no, source, base_dir=base_dir)
            assert current_block_ref[0] is not None
            current_block_ref[0].items.append(item)
            cursor_ref[0] += _data_item_size(item, cursor_ref[0])
            continue

        if mode_ref[0] != "code":
            raise AssemblerError(f"line {line_no}: instructions are only valid in --CODE: blocks")
        instruction_item = build_instruction_item(raw, line_no, source)
        assert current_block_ref[0] is not None
        current_block_ref[0].items.append(instruction_item)
        cursor_ref[0] += instruction_item.size_bytes


def _build_data_item(raw: str, line_no: int, source: SourceRef, *, base_dir: Path) -> BytesItem | WordItem | AddrItem | FillItem | AlignItem:
    alignment = parse_align_directive(raw, line_no)
    if alignment is not None:
        return AlignItem(alignment=alignment, source=source)

    byte_data = parse_byte_directive(raw, line_no)
    if byte_data is not None:
        return BytesItem(data=bytes(byte_data), source=source)

    match = WORD_DIRECTIVE_RE.fullmatch(raw)
    if match:
        values = [parse_value_expr(item, line_no) for item in split_directive_items(match.group(1), line_no, "word")]
        return WordItem(values=values, source=source)

    match = ADDR_DIRECTIVE_RE.fullmatch(raw)
    if match:
        values = [parse_value_expr(item, line_no) for item in split_directive_items(match.group(1), line_no, "addr")]
        return AddrItem(values=values, source=source)

    match = FILL_DIRECTIVE_RE.fullmatch(raw)
    if match:
        count_text, byte_text = match.groups()
        return FillItem(
            count=parse_unsigned(count_text, 24, line_no, "fill count"),
            byte_value=parse_unsigned(byte_text, 8, line_no, "fill byte value"),
            source=source,
        )

    file_data = parse_file_directive(raw, line_no, base_dir=base_dir)
    if file_data is not None:
        return BytesItem(data=bytes(file_data), source=source)

    raise AssemblerError(f"line {line_no}: unsupported data directive")


def _data_item_size(item: BytesItem | WordItem | AddrItem | FillItem | AlignItem, offset: int) -> int:
    if isinstance(item, BytesItem):
        return len(item.data)
    if isinstance(item, WordItem):
        return len(item.values) * 2
    if isinstance(item, AddrItem):
        return len(item.values) * 3
    if isinstance(item, FillItem):
        return item.count
    return alignment_padding(offset, item.alignment)


def preprocess_source(
    text: str,
    *,
    build_instruction_item: Callable[[str, int, SourceRef], InstrItem],
    source_path: Path | None = None,
) -> PreparedAssembly:
    symbols: dict[str, int] = {}
    relocatable_symbols: set[str] = set()
    export_names: set[str] = set()
    export_order: list[str] = []
    import_names: set[str] = set()
    import_order: list[str] = []
    blocks: list[BlockIR] = []
    current_block_ref: list[BlockIR | None] = [None]
    section_declared_ref = [False]
    cursor_ref = [0]
    mode_ref: list[str | None] = [None]
    source_lines = text.splitlines()
    root_path = source_path.resolve() if source_path is not None else None
    base_dir = root_path.parent if root_path is not None else Path.cwd()

    previous_symbols = set_active_symbols(symbols)
    try:
        try:
            _preprocess_lines(
                source_lines,
                source_path=source_path,
                base_dir=base_dir,
                symbols=symbols,
                relocatable_symbols=relocatable_symbols,
                export_names=export_names,
                export_order=export_order,
                import_names=import_names,
                import_order=import_order,
                blocks=blocks,
                current_block_ref=current_block_ref,
                section_declared_ref=section_declared_ref,
                cursor_ref=cursor_ref,
                mode_ref=mode_ref,
                build_instruction_item=build_instruction_item,
            )
        except AssemblerError as exc:
            raise exc.with_context(source_path=source_path, source_line=lookup_source_line(source_lines, exc.line_no)) from exc
    finally:
        set_active_symbols(previous_symbols)

    exports: dict[str, int] = {}
    for name in sorted(export_names):
        if name not in symbols:
            raise AssemblerError(f"export '{name}' refers to an undefined symbol")
        exports[name] = symbols[name]

    return PreparedAssembly(
        symbols=symbols,
        relocatable_symbols=relocatable_symbols,
        exports=exports,
        imports=import_order,
        module_ir=ModuleIR(blocks=blocks, exports=export_order),
        source_lines=source_lines,
        source_path=source_path,
        base_dir=base_dir,
    )


__all__ = ["_align_up", "preprocess_source"]
