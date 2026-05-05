#!/usr/bin/env python3
# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0
"""OpcodeOne structured object container helpers."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Literal


OBJECT_MAGIC = b"O1OB"
OBJECT_VERSION = (1, 3)
OBJECT_VERSION_MAJOR = OBJECT_VERSION[0]
OBJECT_VERSION_MINOR = OBJECT_VERSION[1]
OBJECT_HEADER_SIZE_V12 = 14
OBJECT_HEADER_SIZE_V13 = 16
OBJECT_HEADER_SIZE = OBJECT_HEADER_SIZE_V13
OBJECT_SEGMENT_ENTRY_SIZE = 16
OBJECT_EXPORT_NAME_SIZE = 32
OBJECT_EXPORT_ENTRY_SIZE = 4 + OBJECT_EXPORT_NAME_SIZE
OBJECT_LOCAL_SYMBOL_NAME_SIZE = 32
OBJECT_LOCAL_SYMBOL_ENTRY_SIZE = 4 + OBJECT_LOCAL_SYMBOL_NAME_SIZE
OBJECT_IMPORT_NAME_SIZE = 32
OBJECT_IMPORT_ENTRY_SIZE = OBJECT_IMPORT_NAME_SIZE
OBJECT_RELOCATION_ENTRY_SIZE = 32

RELOCATION_KIND_ABSOLUTE = 1
RELOCATION_KIND_PCREL = 2
RELOCATION_FLAG_SIGNED = 1 << 0
RELOCATION_FLAG_LOCAL_SYMBOL = 1 << 1

SEGMENT_TYPE_CODE = 1
SEGMENT_TYPE_DATA = 2

SEGMENT_FLAG_READABLE = 1 << 0
SEGMENT_FLAG_WRITABLE = 1 << 1
SEGMENT_FLAG_EXECUTABLE = 1 << 2


class ObjectFormatError(ValueError):
    pass


@dataclass(frozen=True)
class ObjectSegment:
    segment_type: int
    load_address: int
    data: bytes
    segment_flags: int


@dataclass(frozen=True)
class ObjectExport:
    name: str
    address: int


@dataclass(frozen=True)
class ObjectLocalSymbol:
    name: str
    address: int


@dataclass(frozen=True)
class ObjectImport:
    name: str


ObjectRelocationKind = Literal["absolute", "pcrel"]
ObjectRelocationSymbolScope = Literal["import", "local"]


@dataclass(frozen=True)
class ObjectRelocation:
    kind: ObjectRelocationKind
    segment_index: int
    offset_in_segment: int
    container_bytes: int
    field_lsb: int
    field_bits: int
    symbol_name: str
    addend: int = 0
    symbol_sign: int = 1
    value_lsb: int = 0
    value_bits: int | None = None
    signed: bool = False
    base_offset_in_segment: int = 0
    origin_bias: int = 0
    max_value: int | None = None
    symbol_scope: ObjectRelocationSymbolScope = "import"


@dataclass(frozen=True)
class ObjectFile:
    segments: list[ObjectSegment]
    exports: list[ObjectExport] = field(default_factory=list)
    imports: list[ObjectImport] = field(default_factory=list)
    relocations: list[ObjectRelocation] = field(default_factory=list)
    local_symbols: list[ObjectLocalSymbol] = field(default_factory=list)


def is_object_file(data: bytes) -> bool:
    return data.startswith(OBJECT_MAGIC)


def words_to_bytes(words: list[int]) -> bytes:
    output = bytearray()
    for word in words:
        if not 0 <= word <= 0xFFFF:
            raise ObjectFormatError(f"word out of range: {word}")
        output.extend(word.to_bytes(2, "little"))
    return bytes(output)


def bytes_to_words(data: bytes) -> list[int]:
    if len(data) % 2:
        raise ObjectFormatError("code payload size must be a multiple of 2 bytes")
    return [data[index] | (data[index + 1] << 8) for index in range(0, len(data), 2)]


def _validate_object(obj: ObjectFile) -> None:
    for index, segment in enumerate(obj.segments):
        if segment.segment_type not in {SEGMENT_TYPE_CODE, SEGMENT_TYPE_DATA}:
            raise ObjectFormatError(f"segment {index}: unsupported type {segment.segment_type}")
        if not 0 <= segment.load_address <= 0xFFFFFF:
            raise ObjectFormatError(f"segment {index}: load address out of 24-bit range")
        if segment.segment_type == SEGMENT_TYPE_CODE and len(segment.data) % 2:
            raise ObjectFormatError(f"segment {index}: CODE payload size must be even")
    seen_names: set[str] = set()
    for index, export in enumerate(obj.exports):
        if not export.name:
            raise ObjectFormatError(f"export {index}: name must not be empty")
        if export.name in seen_names:
            raise ObjectFormatError(f"export {index}: duplicate export name '{export.name}'")
        seen_names.add(export.name)
        if not 0 <= export.address <= 0xFFFFFF:
            raise ObjectFormatError(f"export {index}: address out of 24-bit range")
        encoded = export.name.encode("utf-8")
        if len(encoded) > OBJECT_EXPORT_NAME_SIZE:
            raise ObjectFormatError(
                f"export {index}: name exceeds {OBJECT_EXPORT_NAME_SIZE} bytes when encoded as UTF-8"
            )
    local_symbol_names: set[str] = set()
    for index, item in enumerate(obj.local_symbols):
        if not item.name:
            raise ObjectFormatError(f"local symbol {index}: name must not be empty")
        if item.name in local_symbol_names:
            raise ObjectFormatError(f"local symbol {index}: duplicate local symbol name '{item.name}'")
        local_symbol_names.add(item.name)
        if not 0 <= item.address <= 0xFFFFFF:
            raise ObjectFormatError(f"local symbol {index}: address out of 24-bit range")
        encoded = item.name.encode("utf-8")
        if len(encoded) > OBJECT_LOCAL_SYMBOL_NAME_SIZE:
            raise ObjectFormatError(
                f"local symbol {index}: name exceeds {OBJECT_LOCAL_SYMBOL_NAME_SIZE} bytes when encoded as UTF-8"
            )
    seen_imports: set[str] = set()
    for index, item in enumerate(obj.imports):
        if not item.name:
            raise ObjectFormatError(f"import {index}: name must not be empty")
        if item.name in seen_imports:
            raise ObjectFormatError(f"import {index}: duplicate import name '{item.name}'")
        seen_imports.add(item.name)
        encoded = item.name.encode("utf-8")
        if len(encoded) > OBJECT_IMPORT_NAME_SIZE:
            raise ObjectFormatError(
                f"import {index}: name exceeds {OBJECT_IMPORT_NAME_SIZE} bytes when encoded as UTF-8"
            )
    for index, reloc in enumerate(obj.relocations):
        if reloc.kind not in {"absolute", "pcrel"}:
            raise ObjectFormatError(f"relocation {index}: unsupported kind '{reloc.kind}'")
        if reloc.symbol_scope not in {"import", "local"}:
            raise ObjectFormatError(f"relocation {index}: unsupported symbol scope '{reloc.symbol_scope}'")
        if not 0 <= reloc.segment_index < len(obj.segments):
            raise ObjectFormatError(f"relocation {index}: invalid segment index {reloc.segment_index}")
        if not reloc.symbol_name:
            raise ObjectFormatError(f"relocation {index}: symbol name must not be empty")
        if reloc.symbol_scope == "local" and reloc.symbol_name not in local_symbol_names:
            raise ObjectFormatError(f"relocation {index}: unknown local symbol '{reloc.symbol_name}'")
        if reloc.symbol_sign not in (-1, 1):
            raise ObjectFormatError(f"relocation {index}: symbol_sign must be -1 or 1")
        if reloc.container_bytes <= 0:
            raise ObjectFormatError(f"relocation {index}: container_bytes must be positive")
        if not 0 <= reloc.offset_in_segment <= len(obj.segments[reloc.segment_index].data):
            raise ObjectFormatError(f"relocation {index}: offset is outside segment bounds")
        if reloc.offset_in_segment + reloc.container_bytes > len(obj.segments[reloc.segment_index].data):
            raise ObjectFormatError(f"relocation {index}: relocation container extends beyond segment bounds")
        if not 0 <= reloc.field_lsb <= 255:
            raise ObjectFormatError(f"relocation {index}: field_lsb out of range")
        if not 1 <= reloc.field_bits <= 255:
            raise ObjectFormatError(f"relocation {index}: field_bits out of range")
        if reloc.field_lsb + reloc.field_bits > reloc.container_bytes * 8:
            raise ObjectFormatError(f"relocation {index}: field does not fit inside container")
        if not 0 <= reloc.value_lsb <= 255:
            raise ObjectFormatError(f"relocation {index}: value_lsb out of range")
        if reloc.value_bits is not None and not 1 <= reloc.value_bits <= 255:
            raise ObjectFormatError(f"relocation {index}: value_bits out of range")
        if reloc.max_value is not None and reloc.max_value < 0:
            raise ObjectFormatError(f"relocation {index}: max_value must be non-negative")


def _encode_name(name: str, *, size: int, label: str) -> bytes:
    encoded = name.encode("utf-8")
    if len(encoded) > size:
        raise ObjectFormatError(f"{label} exceeds {size} bytes when encoded as UTF-8")
    return encoded.ljust(size, b"\x00")


def _relocation_kind_code(kind: ObjectRelocationKind) -> int:
    return {
        "absolute": RELOCATION_KIND_ABSOLUTE,
        "pcrel": RELOCATION_KIND_PCREL,
    }[kind]


def _relocation_kind_name(kind_code: int) -> ObjectRelocationKind:
    mapping: dict[int, ObjectRelocationKind] = {
        RELOCATION_KIND_ABSOLUTE: "absolute",
        RELOCATION_KIND_PCREL: "pcrel",
    }
    try:
        return mapping[kind_code]
    except KeyError as exc:
        raise ObjectFormatError(f"unsupported relocation kind {kind_code}") from exc


def serialize_object(obj: ObjectFile) -> bytes:
    _validate_object(obj)

    segment_count = len(obj.segments)
    export_count = len(obj.exports)
    local_symbol_count = len(obj.local_symbols)

    import_names: list[str] = []
    seen_import_names: set[str] = set()
    for item in obj.imports:
        if item.name not in seen_import_names:
            import_names.append(item.name)
            seen_import_names.add(item.name)
    for reloc in obj.relocations:
        if reloc.symbol_scope != "import":
            continue
        if reloc.symbol_name not in seen_import_names:
            import_names.append(reloc.symbol_name)
            seen_import_names.add(reloc.symbol_name)
    import_index_by_name = {name: index for index, name in enumerate(import_names)}
    local_index_by_name = {item.name: index for index, item in enumerate(obj.local_symbols)}

    import_count = len(import_names)
    relocation_count = len(obj.relocations)
    header_size = OBJECT_HEADER_SIZE
    table_offset = header_size
    export_table_offset = table_offset + (segment_count * OBJECT_SEGMENT_ENTRY_SIZE)
    local_symbol_table_offset = export_table_offset + (export_count * OBJECT_EXPORT_ENTRY_SIZE)
    import_table_offset = local_symbol_table_offset + (local_symbol_count * OBJECT_LOCAL_SYMBOL_ENTRY_SIZE)
    relocation_table_offset = import_table_offset + (import_count * OBJECT_IMPORT_ENTRY_SIZE)
    payload_offset = relocation_table_offset + (relocation_count * OBJECT_RELOCATION_ENTRY_SIZE)
    cursor = payload_offset
    entries = bytearray()
    export_entries = bytearray()
    local_symbol_entries = bytearray()
    import_entries = bytearray()
    relocation_entries = bytearray()
    payloads = bytearray()

    for segment in obj.segments:
        entries.extend(
            struct.pack(
                "<BBHIII",
                segment.segment_type,
                segment.segment_flags,
                0,
                segment.load_address,
                cursor,
                len(segment.data),
            )
        )
        payloads.extend(segment.data)
        cursor += len(segment.data)

    for export in obj.exports:
        export_entries.extend(
            struct.pack(
                f"<I{OBJECT_EXPORT_NAME_SIZE}s",
                export.address,
                _encode_name(export.name, size=OBJECT_EXPORT_NAME_SIZE, label=f"export '{export.name}'"),
            )
        )

    for item in obj.local_symbols:
        local_symbol_entries.extend(
            struct.pack(
                f"<I{OBJECT_LOCAL_SYMBOL_NAME_SIZE}s",
                item.address,
                _encode_name(item.name, size=OBJECT_LOCAL_SYMBOL_NAME_SIZE, label=f"local symbol '{item.name}'"),
            )
        )

    for name in import_names:
        import_entries.extend(_encode_name(name, size=OBJECT_IMPORT_NAME_SIZE, label=f"import '{name}'"))

    for reloc in obj.relocations:
        flags = RELOCATION_FLAG_SIGNED if reloc.signed else 0
        if reloc.symbol_scope == "local":
            flags |= RELOCATION_FLAG_LOCAL_SYMBOL
            symbol_index = local_index_by_name[reloc.symbol_name]
        else:
            symbol_index = import_index_by_name[reloc.symbol_name]
        value_bits = 0 if reloc.value_bits is None else reloc.value_bits
        max_value = 0xFFFFFFFF if reloc.max_value is None else reloc.max_value
        relocation_entries.extend(
            struct.pack(
                "<HBBIBBBB i BBIIIH",
                reloc.segment_index,
                _relocation_kind_code(reloc.kind),
                flags,
                reloc.offset_in_segment,
                reloc.container_bytes,
                reloc.field_lsb,
                reloc.field_bits,
                reloc.symbol_sign & 0xFF,
                reloc.addend,
                reloc.value_lsb,
                value_bits,
                reloc.base_offset_in_segment,
                reloc.origin_bias & 0xFFFFFFFF,
                max_value,
                symbol_index,
            )
        )

    header = struct.pack(
        "<4sBBHHHHH",
        OBJECT_MAGIC,
        OBJECT_VERSION[0],
        OBJECT_VERSION[1],
        segment_count,
        export_count,
        local_symbol_count,
        import_count,
        relocation_count,
    )
    return (
        header +
        bytes(entries) +
        bytes(export_entries) +
        bytes(local_symbol_entries) +
        bytes(import_entries) +
        bytes(relocation_entries) +
        bytes(payloads)
    )


def parse_object(data: bytes) -> ObjectFile:
    if len(data) < 4:
        raise ObjectFormatError("object is too small to contain a valid header")

    magic = data[:4]

    if magic != OBJECT_MAGIC:
        raise ObjectFormatError("missing O1OB object magic")

    version_major = data[4]
    version_minor = data[5]
    if (version_major, version_minor) not in {(1, 2), OBJECT_VERSION}:
        raise ObjectFormatError(f"unsupported object version {version_major}.{version_minor}")
    if (version_major, version_minor) == (1, 2):
        if len(data) < OBJECT_HEADER_SIZE_V12:
            raise ObjectFormatError("object is too small to contain a valid header")
        (
            magic,
            version_major,
            version_minor,
            segment_count,
            export_count,
            import_count,
            relocation_count,
        ) = struct.unpack("<4sBBHHHH", data[:OBJECT_HEADER_SIZE_V12])
        local_symbol_count = 0
        header_size = OBJECT_HEADER_SIZE_V12
    else:
        if len(data) < OBJECT_HEADER_SIZE_V13:
            raise ObjectFormatError("object is too small to contain a valid header")
        (
            magic,
            version_major,
            version_minor,
            segment_count,
            export_count,
            local_symbol_count,
            import_count,
            relocation_count,
        ) = struct.unpack("<4sBBHHHHH", data[:OBJECT_HEADER_SIZE_V13])
        header_size = OBJECT_HEADER_SIZE_V13

    segment_table_offset = header_size
    table_size = segment_count * OBJECT_SEGMENT_ENTRY_SIZE
    if segment_table_offset + table_size > len(data):
        raise ObjectFormatError("segment table extends beyond end of file")
    export_table_offset = segment_table_offset + table_size
    export_table_size = export_count * OBJECT_EXPORT_ENTRY_SIZE
    if export_table_offset + export_table_size > len(data):
        raise ObjectFormatError("export table extends beyond end of file")
    local_symbol_table_offset = export_table_offset + export_table_size
    local_symbol_table_size = local_symbol_count * OBJECT_LOCAL_SYMBOL_ENTRY_SIZE
    if local_symbol_table_offset + local_symbol_table_size > len(data):
        raise ObjectFormatError("local symbol table extends beyond end of file")
    import_table_offset = local_symbol_table_offset + local_symbol_table_size
    import_table_size = import_count * OBJECT_IMPORT_ENTRY_SIZE
    if import_table_offset + import_table_size > len(data):
        raise ObjectFormatError("import table extends beyond end of file")
    relocation_table_offset = import_table_offset + import_table_size
    relocation_table_size = relocation_count * OBJECT_RELOCATION_ENTRY_SIZE
    if relocation_table_offset + relocation_table_size > len(data):
        raise ObjectFormatError("relocation table extends beyond end of file")

    segments: list[ObjectSegment] = []
    for index in range(segment_count):
        offset = segment_table_offset + (index * OBJECT_SEGMENT_ENTRY_SIZE)
        (
            segment_type,
            segment_flags,
            reserved,
            load_address,
            file_offset,
            size_bytes,
        ) = struct.unpack("<BBHIII", data[offset : offset + OBJECT_SEGMENT_ENTRY_SIZE])

        if reserved != 0:
            raise ObjectFormatError(f"segment {index}: reserved field must be 0")
        if file_offset + size_bytes > len(data):
            raise ObjectFormatError(f"segment {index}: payload extends beyond end of file")

        payload = data[file_offset : file_offset + size_bytes]
        segments.append(
            ObjectSegment(
                segment_type=segment_type,
                load_address=load_address & 0xFFFFFF,
                data=payload,
                segment_flags=segment_flags,
            )
        )

    exports: list[ObjectExport] = []
    for index in range(export_count):
        offset = export_table_offset + (index * OBJECT_EXPORT_ENTRY_SIZE)
        address, raw_name = struct.unpack(
            f"<I{OBJECT_EXPORT_NAME_SIZE}s",
            data[offset : offset + OBJECT_EXPORT_ENTRY_SIZE],
        )
        name = raw_name.split(b"\x00", 1)[0].decode("utf-8")
        exports.append(ObjectExport(name=name, address=address & 0xFFFFFF))

    local_symbols: list[ObjectLocalSymbol] = []
    for index in range(local_symbol_count):
        offset = local_symbol_table_offset + (index * OBJECT_LOCAL_SYMBOL_ENTRY_SIZE)
        address, raw_name = struct.unpack(
            f"<I{OBJECT_LOCAL_SYMBOL_NAME_SIZE}s",
            data[offset : offset + OBJECT_LOCAL_SYMBOL_ENTRY_SIZE],
        )
        name = raw_name.split(b"\x00", 1)[0].decode("utf-8")
        local_symbols.append(ObjectLocalSymbol(name=name, address=address & 0xFFFFFF))

    imports: list[ObjectImport] = []
    for index in range(import_count):
        offset = import_table_offset + (index * OBJECT_IMPORT_ENTRY_SIZE)
        raw_name = data[offset : offset + OBJECT_IMPORT_ENTRY_SIZE]
        name = raw_name.split(b"\x00", 1)[0].decode("utf-8")
        imports.append(ObjectImport(name=name))

    relocations: list[ObjectRelocation] = []
    for index in range(relocation_count):
        offset = relocation_table_offset + (index * OBJECT_RELOCATION_ENTRY_SIZE)
        (
            segment_index,
            kind_code,
            flags,
            offset_in_segment,
            container_bytes,
            field_lsb,
            field_bits,
            symbol_sign_raw,
            addend,
            value_lsb,
            value_bits_raw,
            base_offset_in_segment,
            origin_bias_raw,
            max_value_raw,
            symbol_index,
        ) = struct.unpack(
            "<HBBIBBBB i BBIIIH",
            data[offset : offset + OBJECT_RELOCATION_ENTRY_SIZE],
        )
        local_symbol = (flags & RELOCATION_FLAG_LOCAL_SYMBOL) != 0
        if local_symbol:
            if symbol_index >= len(local_symbols):
                raise ObjectFormatError(f"relocation {index}: local symbol index {symbol_index} is out of range")
            symbol_name = local_symbols[symbol_index].name
            symbol_scope: ObjectRelocationSymbolScope = "local"
        else:
            if symbol_index >= len(imports):
                raise ObjectFormatError(f"relocation {index}: import index {symbol_index} is out of range")
            symbol_name = imports[symbol_index].name
            symbol_scope = "import"
        symbol_sign = symbol_sign_raw if symbol_sign_raw < 0x80 else symbol_sign_raw - 0x100
        origin_bias = origin_bias_raw if origin_bias_raw < 0x80000000 else origin_bias_raw - 0x100000000
        value_bits = None if value_bits_raw == 0 else value_bits_raw
        max_value = None if max_value_raw == 0xFFFFFFFF else max_value_raw
        relocations.append(
            ObjectRelocation(
                kind=_relocation_kind_name(kind_code),
                segment_index=segment_index,
                offset_in_segment=offset_in_segment,
                container_bytes=container_bytes,
                field_lsb=field_lsb,
                field_bits=field_bits,
                symbol_name=symbol_name,
                symbol_scope=symbol_scope,
                addend=addend,
                symbol_sign=symbol_sign,
                value_lsb=value_lsb,
                value_bits=value_bits,
                signed=bool(flags & RELOCATION_FLAG_SIGNED),
                base_offset_in_segment=base_offset_in_segment,
                origin_bias=origin_bias,
                max_value=max_value,
            )
        )

    obj = ObjectFile(
        segments=segments,
        exports=exports,
        local_symbols=local_symbols,
        imports=imports,
        relocations=relocations,
    )
    _validate_object(obj)
    return obj
