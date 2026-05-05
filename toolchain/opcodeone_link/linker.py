# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from common.opcodeone_object import (
        ObjectExport,
        ObjectFile,
        ObjectFormatError,
        ObjectRelocation,
        ObjectSegment,
        parse_object,
        serialize_object,
    )
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_object import (
        ObjectExport,
        ObjectFile,
        ObjectFormatError,
        ObjectRelocation,
        ObjectSegment,
        parse_object,
        serialize_object,
    )


LINKER_VERSION = 1
LAYOUT_FORMAT = "opcodeone-link-layout"
LAYOUT_VERSION = 1


class LinkerError(ValueError):
    pass


@dataclass(frozen=True)
class _PlacedObject:
    base_address: int
    obj: ObjectFile
    input_name: str
    region_name: str | None = None


@dataclass(frozen=True)
class _InputObject:
    name: str
    path: Path | None
    obj: ObjectFile


@dataclass(frozen=True)
class _LayoutRegion:
    name: str
    base_address: int
    max_size: int
    align: int
    reservations: tuple["_LayoutReservation", ...] = ()


@dataclass(frozen=True)
class _LayoutReservation:
    base_address: int
    size: int
    name: str | None = None


@dataclass(frozen=True)
class _LayoutRule:
    object_name: str
    region_name: str
    mode: str
    fixed_address: int | None = None


@dataclass(frozen=True)
class _LinkLayout:
    source_path: Path
    regions: list[_LayoutRegion]
    rules: list[_LayoutRule]


@dataclass(frozen=True)
class _SegmentPlacementInfo:
    input_name: str
    region_name: str | None
    segment_index_in_object: int


@dataclass
class _MutableSegment:
    segment_type: int
    load_address: int
    data: bytearray
    segment_flags: int


def _align_up(value: int, alignment: int) -> int:
    if alignment <= 1:
        return value
    return (value + alignment - 1) // alignment * alignment


def _object_extent(obj: ObjectFile) -> int:
    return max((segment.load_address + len(segment.data) for segment in obj.segments), default=0)


def _object_input_name(path: Path | None, index: int) -> str:
    if path is None:
        return f"object[{index}]"
    return str(path)


def _validate_uint24(value: int, *, label: str) -> int:
    if not 0 <= value <= 0xFFFFFF:
        raise LinkerError(f"{label} must be in range 0..0xFFFFFF")
    return value


def _validate_positive(value: int, *, label: str) -> int:
    if value <= 0:
        raise LinkerError(f"{label} must be positive")
    return value


def _validate_non_negative(value: int, *, label: str) -> int:
    if value < 0:
        raise LinkerError(f"{label} must be non-negative")
    return value


def _validate_unsigned(value: int, bits: int, *, label: str) -> int:
    hi = (1 << bits) - 1
    if not 0 <= value <= hi:
        raise LinkerError(f"{label} out of range for unsigned {bits}-bit field: {value}")
    return value


def _validate_signed(value: int, bits: int, *, label: str) -> int:
    lo = -(1 << (bits - 1))
    hi = (1 << (bits - 1)) - 1
    if not lo <= value <= hi:
        raise LinkerError(f"{label} out of range for signed {bits}-bit field: {value}")
    return value


def _pack_bits(value: int, bits: int) -> int:
    return value & ((1 << bits) - 1)


def _check_segment_overlaps(segments: list[_MutableSegment]) -> None:
    ordered = sorted(
        (
            (segment.load_address, segment.load_address + len(segment.data), index)
            for index, segment in enumerate(segments)
            if segment.data
        ),
        key=lambda item: item[0],
    )
    for current, nxt in zip(ordered, ordered[1:]):
        current_start, current_end, current_index = current
        next_start, _next_end, next_index = nxt
        if next_start < current_end:
            raise LinkerError(
                f"linked segment overlap between segment {current_index} ending at 0x{current_end:06X} "
                f"and segment {next_index} starting at 0x{next_start:06X}"
            )


def _parse_layout_int(value: object, *, field: str) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError as exc:
            raise LinkerError(f"layout field '{field}' must be an integer or base-prefixed integer string") from exc
    raise LinkerError(f"layout field '{field}' must be an integer or base-prefixed integer string")


def _parse_layout(path: Path) -> _LinkLayout:
    try:
        root = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LinkerError(f"missing layout file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LinkerError(f"invalid layout JSON: {exc}") from exc
    except OSError as exc:
        raise LinkerError(f"could not read layout file {path}: {exc.strerror or exc}") from exc

    if not isinstance(root, dict):
        raise LinkerError("layout root must be an object")
    if root.get("format") != LAYOUT_FORMAT:
        raise LinkerError(f"layout format must be '{LAYOUT_FORMAT}'")
    if root.get("version") != LAYOUT_VERSION:
        raise LinkerError(f"layout version must be {LAYOUT_VERSION}")

    raw_regions = root.get("regions")
    if not isinstance(raw_regions, list) or not raw_regions:
        raise LinkerError("layout field 'regions' must be a non-empty array")
    raw_rules = root.get("rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise LinkerError("layout field 'rules' must be a non-empty array")

    regions: list[_LayoutRegion] = []
    region_names: set[str] = set()
    for index, raw_region in enumerate(raw_regions):
        if not isinstance(raw_region, dict):
            raise LinkerError(f"layout region {index}: region entry must be an object")
        name = raw_region.get("name")
        if not isinstance(name, str) or not name:
            raise LinkerError(f"layout region {index}: 'name' must be a non-empty string")
        if name in region_names:
            raise LinkerError(f"layout region {index}: duplicate region name '{name}'")
        base_address = _validate_uint24(
            _parse_layout_int(raw_region.get("base"), field=f"regions[{index}].base"),
            label=f"layout region '{name}' base",
        )
        max_size = _validate_positive(
            _parse_layout_int(raw_region.get("max_size"), field=f"regions[{index}].max_size"),
            label=f"layout region '{name}' max_size",
        )
        align = _validate_positive(
            _parse_layout_int(raw_region.get("align", 1), field=f"regions[{index}].align"),
            label=f"layout region '{name}' align",
        )
        if base_address + max_size > 0x1000000:
            raise LinkerError(f"layout region '{name}' exceeds 24-bit address space")
        raw_reservations = raw_region.get("reservations", [])
        if not isinstance(raw_reservations, list):
            raise LinkerError(f"layout region {index}: 'reservations' must be an array when present")
        reservations: list[_LayoutReservation] = []
        for reservation_index, raw_reservation in enumerate(raw_reservations):
            if not isinstance(raw_reservation, dict):
                raise LinkerError(
                    f"layout region {index} reservation {reservation_index}: reservation entry must be an object"
                )
            reservation_name = raw_reservation.get("name")
            if reservation_name is not None and (not isinstance(reservation_name, str) or not reservation_name):
                raise LinkerError(
                    f"layout region {index} reservation {reservation_index}: 'name' must be a non-empty string"
                )
            reservation_base = _validate_uint24(
                _parse_layout_int(
                    raw_reservation.get("base"),
                    field=f"regions[{index}].reservations[{reservation_index}].base",
                ),
                label=f"layout region '{name}' reservation base",
            )
            reservation_size = _validate_positive(
                _parse_layout_int(
                    raw_reservation.get("size"),
                    field=f"regions[{index}].reservations[{reservation_index}].size",
                ),
                label=f"layout region '{name}' reservation size",
            )
            reservation_end = reservation_base + reservation_size
            region_end = base_address + max_size
            if reservation_base < base_address or reservation_end > region_end:
                raise LinkerError(
                    f"layout region '{name}' reservation {reservation_index} exceeds region bounds"
                )
            reservations.append(
                _LayoutReservation(
                    base_address=reservation_base,
                    size=reservation_size,
                    name=reservation_name,
                )
            )
        ordered_reservations = sorted(
            (
                (reservation.base_address, reservation.base_address + reservation.size, reservation)
                for reservation in reservations
            ),
            key=lambda item: item[0],
        )
        for current, nxt in zip(ordered_reservations, ordered_reservations[1:]):
            current_start, current_end, _current_reservation = current
            next_start, _next_end, next_reservation = nxt
            if next_start < current_end:
                overlap_name = next_reservation.name or f"reservation at 0x{next_start:06X}"
                raise LinkerError(f"layout region '{name}' has overlapping reservations near {overlap_name}")
        region_names.add(name)
        regions.append(
            _LayoutRegion(
                name=name,
                base_address=base_address,
                max_size=max_size,
                align=align,
                reservations=tuple(reservations),
            )
        )

    rules: list[_LayoutRule] = []
    for index, raw_rule in enumerate(raw_rules):
        if not isinstance(raw_rule, dict):
            raise LinkerError(f"layout rule {index}: rule entry must be an object")
        match = raw_rule.get("match")
        if not isinstance(match, dict):
            raise LinkerError(f"layout rule {index}: 'match' must be an object")
        object_name = match.get("object")
        if not isinstance(object_name, str) or not object_name:
            raise LinkerError(f"layout rule {index}: match.object must be a non-empty string")
        region_name = raw_rule.get("region")
        if not isinstance(region_name, str) or not region_name:
            raise LinkerError(f"layout rule {index}: 'region' must be a non-empty string")
        if region_name not in region_names:
            raise LinkerError(f"layout rule {index}: unknown region '{region_name}'")
        mode = raw_rule.get("mode")
        if mode != "keep-object":
            raise LinkerError(f"layout rule {index}: unsupported mode '{mode}'; expected 'keep-object'")
        fixed_address = raw_rule.get("fixed_address")
        if fixed_address is not None:
            fixed_address = _validate_uint24(
                _parse_layout_int(fixed_address, field=f"rules[{index}].fixed_address"),
                label=f"layout rule {index} fixed_address",
            )
        rules.append(
            _LayoutRule(
                object_name=object_name,
                region_name=region_name,
                mode=mode,
                fixed_address=fixed_address,
            )
        )

    return _LinkLayout(source_path=path, regions=regions, rules=rules)


def _rule_matches_input(rule: _LayoutRule, input_obj: _InputObject) -> bool:
    if input_obj.path is None:
        return input_obj.name == rule.object_name
    path = input_obj.path
    candidates = {
        str(path),
        path.as_posix(),
        path.name,
    }
    return rule.object_name in candidates


def _place_inputs_sequential(
    inputs: list[_InputObject],
    *,
    base_address: int,
    module_alignment: int,
) -> list[_PlacedObject]:
    cursor = _validate_uint24(base_address, label="base address")
    _validate_positive(module_alignment, label="module alignment")
    placed: list[_PlacedObject] = []
    for input_obj in inputs:
        module_base = _align_up(cursor, module_alignment)
        _validate_uint24(module_base, label="module base address")
        extent = _object_extent(input_obj.obj)
        if module_base + extent > 0x1000000:
            raise LinkerError(f"linked image exceeds 24-bit address space at module base 0x{module_base:06X}")
        placed.append(_PlacedObject(base_address=module_base, obj=input_obj.obj, input_name=input_obj.name))
        cursor = module_base + extent
    return placed


def _reservation_label(region_name: str, reservation: _LayoutReservation) -> str:
    if reservation.name:
        return f"reservation '{reservation.name}' in region '{region_name}'"
    return f"reservation at 0x{reservation.base_address:06X} in region '{region_name}'"


def _find_interval_conflict(
    start: int,
    end: int,
    *,
    occupied: list[tuple[int, int, str]],
) -> tuple[int, int, str] | None:
    for occupied_start, occupied_end, occupied_label in occupied:
        if start < occupied_end and occupied_start < end:
            return occupied_start, occupied_end, occupied_label
    return None


def _find_region_slot(
    region: _LayoutRegion,
    *,
    start_address: int,
    extent: int,
    occupied: list[tuple[int, int, str]],
) -> int | None:
    region_end = region.base_address + region.max_size
    candidate = _align_up(max(start_address, region.base_address), region.align)
    while candidate + extent <= region_end:
        conflict = _find_interval_conflict(candidate, candidate + extent, occupied=occupied)
        if conflict is None:
            return candidate
        _conflict_start, conflict_end, _conflict_label = conflict
        candidate = _align_up(conflict_end, region.align)
    return None


def _place_inputs_with_layout(inputs: list[_InputObject], layout: _LinkLayout) -> list[_PlacedObject]:
    regions = {region.name: region for region in layout.regions}
    region_cursors = {region.name: region.base_address for region in layout.regions}
    region_occupied = {
        region.name: sorted(
            [
                (
                    reservation.base_address,
                    reservation.base_address + reservation.size,
                    _reservation_label(region.name, reservation),
                )
                for reservation in region.reservations
            ],
            key=lambda item: item[0],
        )
        for region in layout.regions
    }
    rule_usage: dict[int, str] = {}
    placed: list[_PlacedObject] = []

    for input_obj in inputs:
        matched_rules = [(index, rule) for index, rule in enumerate(layout.rules) if _rule_matches_input(rule, input_obj)]
        if not matched_rules:
            raise LinkerError(f"layout '{layout.source_path}': object '{input_obj.name}' does not match any rule")
        if len(matched_rules) > 1:
            raise LinkerError(f"layout '{layout.source_path}': object '{input_obj.name}' matches multiple rules")

        rule_index, rule = matched_rules[0]
        previous_user = rule_usage.get(rule_index)
        if previous_user is not None:
            raise LinkerError(
                f"layout '{layout.source_path}': rule for '{rule.object_name}' already matched '{previous_user}'"
            )
        rule_usage[rule_index] = input_obj.name

        region = regions[rule.region_name]
        if rule.fixed_address is None:
            module_base = _find_region_slot(
                region,
                start_address=region_cursors[region.name],
                extent=_object_extent(input_obj.obj),
                occupied=region_occupied[region.name],
            )
            if module_base is None:
                raise LinkerError(
                    f"layout '{layout.source_path}': object '{input_obj.name}' does not fit in region '{region.name}'"
                )
        else:
            module_base = rule.fixed_address
        _validate_uint24(module_base, label=f"layout placement for '{input_obj.name}'")
        extent = _object_extent(input_obj.obj)
        region_end = region.base_address + region.max_size
        if module_base < region.base_address or module_base + extent > region_end:
            raise LinkerError(
                f"layout '{layout.source_path}': object '{input_obj.name}' does not fit in region '{region.name}'"
            )
        conflict = _find_interval_conflict(
            module_base,
            module_base + extent,
            occupied=region_occupied[region.name],
        )
        if conflict is not None:
            _conflict_start, _conflict_end, conflict_label = conflict
            raise LinkerError(
                f"layout '{layout.source_path}': object '{input_obj.name}' overlaps {conflict_label}"
            )
        placed.append(
            _PlacedObject(
                base_address=module_base,
                obj=input_obj.obj,
                input_name=input_obj.name,
                region_name=region.name,
            )
        )
        region_occupied[region.name].append((module_base, module_base + extent, f"object '{input_obj.name}'"))
        region_occupied[region.name].sort(key=lambda item: item[0])
        region_cursors[region.name] = max(region_cursors[region.name], module_base + extent)

    for index, rule in enumerate(layout.rules):
        if index not in rule_usage:
            raise LinkerError(
                f"layout '{layout.source_path}': rule for '{rule.object_name}' does not match any input object"
            )
    return placed


def _place_inputs(
    inputs: list[_InputObject],
    *,
    base_address: int,
    module_alignment: int,
    layout: _LinkLayout | None = None,
) -> list[_PlacedObject]:
    if layout is None:
        return _place_inputs_sequential(inputs, base_address=base_address, module_alignment=module_alignment)
    return _place_inputs_with_layout(inputs, layout)


def _build_global_symbols(
    placed_objects: list[_PlacedObject],
    *,
    external_symbols: dict[str, int] | None = None,
) -> tuple[dict[str, int], list[ObjectExport]]:
    symbols: dict[str, int] = {}
    placed_exports: list[ObjectExport] = []
    for placed in placed_objects:
        for export in placed.obj.exports:
            if export.name in symbols:
                raise LinkerError(f"duplicate global symbol '{export.name}'")
            resolved_address = placed.base_address + export.address
            symbols[export.name] = resolved_address
            placed_exports.append(ObjectExport(name=export.name, address=resolved_address))
    if external_symbols is not None:
        for name, address in sorted(external_symbols.items()):
            if name in symbols:
                raise LinkerError(f"duplicate global symbol '{name}'")
            symbols[name] = _validate_uint24(address, label=f"symbol '{name}' address")
    return symbols, placed_exports


def _materialize_segments(
    placed_objects: list[_PlacedObject],
) -> tuple[list[_MutableSegment], dict[tuple[int, int], int], list[_SegmentPlacementInfo]]:
    linked_segments: list[_MutableSegment] = []
    segment_map: dict[tuple[int, int], int] = {}
    segment_info: list[_SegmentPlacementInfo] = []
    for object_index, placed in enumerate(placed_objects):
        for segment_index, segment in enumerate(placed.obj.segments):
            linked_segment = _MutableSegment(
                segment_type=segment.segment_type,
                load_address=placed.base_address + segment.load_address,
                data=bytearray(segment.data),
                segment_flags=segment.segment_flags,
            )
            segment_map[(object_index, segment_index)] = len(linked_segments)
            linked_segments.append(linked_segment)
            segment_info.append(
                _SegmentPlacementInfo(
                    input_name=placed.input_name,
                    region_name=placed.region_name,
                    segment_index_in_object=segment_index,
                )
            )
    _check_segment_overlaps(linked_segments)
    return linked_segments, segment_map, segment_info


def _apply_relocation(
    reloc: ObjectRelocation,
    *,
    segment: _MutableSegment,
    symbol_value: int,
) -> None:
    resolved = (symbol_value * reloc.symbol_sign) + reloc.addend
    if reloc.kind == "pcrel":
        resolved -= segment.load_address + reloc.base_offset_in_segment + reloc.origin_bias

    if reloc.value_bits is not None:
        resolved = _validate_unsigned(resolved, reloc.value_bits, label=f"relocation '{reloc.symbol_name}'")
        field_value = resolved >> reloc.value_lsb
    elif reloc.signed:
        field_value = _validate_signed(resolved, reloc.field_bits, label=f"relocation '{reloc.symbol_name}'")
    else:
        field_value = _validate_unsigned(resolved, reloc.field_bits, label=f"relocation '{reloc.symbol_name}'")

    if reloc.max_value is not None and field_value > reloc.max_value:
        raise LinkerError(
            f"relocation '{reloc.symbol_name}' out of range for target width: {field_value}"
        )

    end_offset = reloc.offset_in_segment + reloc.container_bytes
    container = 0
    for index, byte in enumerate(segment.data[reloc.offset_in_segment:end_offset]):
        container |= byte << (index * 8)
    mask = ((1 << reloc.field_bits) - 1) << reloc.field_lsb
    container = (container & ~mask) | ((_pack_bits(field_value, reloc.field_bits) << reloc.field_lsb) & mask)
    for index in range(reloc.container_bytes):
        segment.data[reloc.offset_in_segment + index] = (container >> (index * 8)) & 0xFF


def _image_end_from_segments(
    segments: list[_MutableSegment] | list[ObjectSegment],
    *,
    base_address: int,
) -> int:
    image_end = base_address
    for segment in segments:
        image_end = max(image_end, segment.load_address + len(segment.data))
    return image_end


def _validate_image_span(
    segments: list[_MutableSegment] | list[ObjectSegment],
    *,
    base_address: int,
    max_size: int | None,
) -> None:
    if max_size is None:
        return
    image_size = _image_end_from_segments(segments, base_address=base_address) - base_address
    if image_size > max_size:
        raise LinkerError(f"linked image size {image_size} bytes exceeds max size of {max_size} bytes")


def link_objects(
    objects: list[ObjectFile],
    *,
    base_address: int = 0,
    module_alignment: int = 2,
    max_size: int | None = None,
    external_symbols: dict[str, int] | None = None,
) -> ObjectFile:
    linked, _placed_objects, _segment_info = _link_inputs(
        [_InputObject(name=_object_input_name(None, index), path=None, obj=obj) for index, obj in enumerate(objects)],
        base_address=base_address,
        module_alignment=module_alignment,
        max_size=max_size,
        external_symbols=external_symbols,
    )
    return linked


def _link_inputs(
    inputs: list[_InputObject],
    *,
    base_address: int = 0,
    module_alignment: int = 2,
    max_size: int | None = None,
    external_symbols: dict[str, int] | None = None,
    layout: _LinkLayout | None = None,
) -> tuple[ObjectFile, list[_PlacedObject], list[_SegmentPlacementInfo]]:
    _validate_uint24(base_address, label="base address")
    if max_size is not None:
        _validate_non_negative(max_size, label="max size")
    if layout is not None and (base_address != 0 or module_alignment != 2 or max_size is not None):
        raise LinkerError("layout placement cannot be combined with base/max-size/module-align")

    placed_objects = _place_inputs(
        inputs,
        base_address=base_address,
        module_alignment=module_alignment,
        layout=layout,
    )
    global_symbols, placed_exports = _build_global_symbols(placed_objects, external_symbols=external_symbols)
    linked_segments, segment_map, segment_info = _materialize_segments(placed_objects)

    for object_index, placed in enumerate(placed_objects):
        local_symbols = {item.name: placed.base_address + item.address for item in placed.obj.local_symbols}
        for reloc in placed.obj.relocations:
            if reloc.symbol_scope == "local":
                symbol_value = local_symbols.get(reloc.symbol_name)
                if symbol_value is None:
                    raise LinkerError(f"undefined local symbol '{reloc.symbol_name}'")
            else:
                symbol_value = global_symbols.get(reloc.symbol_name)
                if symbol_value is None:
                    raise LinkerError(f"undefined external symbol '{reloc.symbol_name}'")
            segment = linked_segments[segment_map[(object_index, reloc.segment_index)]]
            _apply_relocation(reloc, segment=segment, symbol_value=symbol_value)

    _validate_image_span(linked_segments, base_address=base_address, max_size=max_size)
    linked_object_segments = [
        ObjectSegment(
            segment_type=segment.segment_type,
            load_address=segment.load_address,
            data=bytes(segment.data),
            segment_flags=segment.segment_flags,
        )
        for segment in linked_segments
    ]
    linked_exports = sorted(placed_exports, key=lambda item: item.name)
    return ObjectFile(segments=linked_object_segments, exports=linked_exports), placed_objects, segment_info


def _parse_object_path(path: Path) -> ObjectFile:
    try:
        data = path.read_bytes()
    except FileNotFoundError as exc:
        raise LinkerError(f"missing object file: {path}") from exc
    except OSError as exc:
        raise LinkerError(f"could not read object file {path}: {exc.strerror or exc}") from exc
    try:
        return parse_object(data)
    except ObjectFormatError as exc:
        raise LinkerError(f"{path}: {exc}") from exc


def _load_symbol_exports(paths: list[Path]) -> dict[str, int]:
    symbols: dict[str, int] = {}
    for path in paths:
        obj = _parse_object_path(path)
        if obj.imports or obj.relocations:
            raise LinkerError(f"{path}: symbol source object must be closed and free of imports/relocations")
        for export in obj.exports:
            if export.name in symbols:
                raise LinkerError(f"duplicate global symbol '{export.name}'")
            symbols[export.name] = export.address
    return symbols


def link_paths(
    paths: list[Path],
    *,
    base_address: int = 0,
    module_alignment: int = 2,
    max_size: int | None = None,
    symbol_paths: list[Path] | None = None,
    layout_path: Path | None = None,
) -> ObjectFile:
    objects = [_InputObject(name=_object_input_name(path, index), path=path, obj=_parse_object_path(path)) for index, path in enumerate(paths)]
    external_symbols = _load_symbol_exports(symbol_paths or [])
    layout = _parse_layout(layout_path) if layout_path is not None else None
    linked, _placed_objects, _segment_info = _link_inputs(
        base_address=base_address,
        module_alignment=module_alignment,
        max_size=max_size,
        external_symbols=external_symbols,
        inputs=objects,
        layout=layout,
    )
    return linked


def linked_object_to_binary(obj: ObjectFile, *, raw_origin: int = 0) -> bytes:
    if obj.imports or obj.relocations:
        raise LinkerError("cannot write raw binary from an object with unresolved imports or relocations")
    _validate_uint24(raw_origin, label="raw origin")

    image = bytearray()
    cursor = 0
    for segment in sorted(obj.segments, key=lambda item: item.load_address):
        if segment.load_address < raw_origin:
            raise LinkerError(
                f"linked segment at address 0x{segment.load_address:06X} falls below raw origin 0x{raw_origin:06X}"
            )
        segment_offset = segment.load_address - raw_origin
        if segment_offset < cursor:
            raise LinkerError(f"linked object segments overlap near address 0x{segment.load_address:06X}")
        if segment_offset > cursor:
            image.extend(b"\x00" * (segment_offset - cursor))
            cursor = segment_offset
        image.extend(segment.data)
        cursor += len(segment.data)
    return bytes(image)


def format_payload_size(payload: bytes) -> str:
    size_bytes = len(payload)
    size_kib = size_bytes / 1024.0
    return f"generated {size_bytes} bytes ({size_kib:.2f} KiB)"


def default_output_path(binary: bool) -> str:
    return "out.linked.bin" if binary else "out.linked.obj"


def _parse_int(text: str) -> int:
    return int(text, 0)


def _segment_type_name(segment_type: int) -> str:
    if segment_type == 1:
        return "CODE"
    if segment_type == 2:
        return "DATA"
    return f"TYPE{segment_type}"


def _format_segment_flags(flags: int) -> str:
    return "".join(
        (
            "r" if flags & (1 << 0) else "-",
            "w" if flags & (1 << 1) else "-",
            "x" if flags & (1 << 2) else "-",
        )
    )


def format_link_map(
    obj: ObjectFile,
    *,
    base_address: int = 0,
    max_size: int | None = None,
    raw_origin: int | None = None,
    object_paths: list[Path] | None = None,
    symbol_paths: list[Path] | None = None,
    extra_sections: list[tuple[str, list[str]]] | None = None,
) -> str:
    _validate_uint24(base_address, label="base address")
    if max_size is not None:
        _validate_non_negative(max_size, label="max size")
    if raw_origin is not None:
        _validate_uint24(raw_origin, label="raw origin")
    image_end = _image_end_from_segments(obj.segments, base_address=base_address)
    image_size = image_end - base_address

    lines = [
        "OpcodeOne Link Map",
        f"Base: 0x{base_address:06X}",
        f"End: 0x{image_end:06X}",
        f"Size: {image_size} bytes (0x{image_size:X})",
    ]
    if max_size is not None:
        lines.append(f"Max Size: {max_size} bytes (0x{max_size:X})")
    if raw_origin is not None:
        lines.append(f"Raw Origin: 0x{raw_origin:06X}")

    lines.append("")
    lines.append("Inputs:")
    if object_paths:
        lines.extend(f"  {path}" for path in object_paths)
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("Symbol Sources:")
    if symbol_paths:
        lines.extend(f"  {path}" for path in symbol_paths)
    else:
        lines.append("  (none)")

    if extra_sections:
        for title, items in extra_sections:
            lines.append("")
            lines.append(f"{title}:")
            if items:
                lines.extend(f"  {item}" for item in items)
            else:
                lines.append("  (none)")

    lines.append("")
    lines.append("Segments:")
    if obj.segments:
        for index, segment in enumerate(obj.segments):
            lines.append(
                f"  [{index}] {_segment_type_name(segment.segment_type)} "
                f"addr=0x{segment.load_address:06X} size={len(segment.data)} "
                f"flags={_format_segment_flags(segment.segment_flags)}"
            )
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("Exports:")
    if obj.exports:
        for export in obj.exports:
            lines.append(f"  {export.name} = 0x{export.address:06X}")
    else:
        lines.append("  (none)")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Link one or more OpcodeOne O1OB objects")
    parser.add_argument("objects", nargs="+", help="Input O1OB object files")
    parser.add_argument("-o", "--output", help="Output file. Writes to out.linked.obj or out.linked.bin when omitted.")
    parser.add_argument("-b", "--binary", action="store_true", help="Write linked raw binary instead of a closed O1OB object.")
    parser.add_argument("--base", type=_parse_int, default=0, help="Base address for the first linked module. Default: 0.")
    parser.add_argument("--max-size", type=_parse_int, help="Maximum allowed image size from the chosen base.")
    parser.add_argument("--map", dest="map_output", help="Write a plain-text linker map to this file.")
    parser.add_argument(
        "--layout",
        help="Apply placement rules from a layout JSON file with generic regions, reservations and keep-object rules.",
    )
    parser.add_argument("--module-align", type=_parse_int, default=2, help="Alignment applied between linked modules. Default: 2.")
    parser.add_argument(
        "--raw-origin",
        type=_parse_int,
        help="Address mapped to file offset 0 when writing raw binary. Defaults to --base.",
    )
    parser.add_argument(
        "--symbols-from",
        action="append",
        default=[],
        metavar="OBJECT",
        help="Read exports from another object file for symbol resolution without placing its segments.",
    )
    args = parser.parse_args(argv)

    try:
        if args.raw_origin is not None and not args.binary:
            raise LinkerError("--raw-origin requires -b/--binary")
        object_paths = [Path(item) for item in args.objects]
        symbol_paths = [Path(item) for item in args.symbols_from]
        layout_path = Path(args.layout) if args.layout is not None else None
        layout = _parse_layout(layout_path) if layout_path is not None else None
        input_objects = [
            _InputObject(name=_object_input_name(path, index), path=path, obj=_parse_object_path(path))
            for index, path in enumerate(object_paths)
        ]
        linked, placed_objects, segment_info = _link_inputs(
            input_objects,
            base_address=args.base,
            module_alignment=args.module_align,
            max_size=args.max_size,
            external_symbols=_load_symbol_exports(symbol_paths),
            layout=layout,
        )
        raw_origin = None
        if args.binary:
            if args.raw_origin is None:
                if layout is None:
                    raw_origin = args.base
                else:
                    raw_origin = min((segment.load_address for segment in linked.segments), default=0)
            else:
                raw_origin = args.raw_origin
        payload = linked_object_to_binary(linked, raw_origin=raw_origin) if args.binary else serialize_object(linked)
        map_payload = None
        if args.map_output is not None:
            map_base_address = args.base if layout is None else min((segment.load_address for segment in linked.segments), default=0)
            extra_sections: list[tuple[str, list[str]]] = []
            if layout is not None:
                extra_sections.append(("Layout", [str(layout.source_path)]))
                extra_sections.append(
                    (
                        "Regions",
                        [
                            f"{region.name} base=0x{region.base_address:06X} max_size={region.max_size} align={region.align}"
                            for region in layout.regions
                        ],
                    )
                )
                extra_sections.append(
                    (
                        "Reservations",
                        [
                            f"{region.name} base=0x{reservation.base_address:06X} size={reservation.size}"
                            + (f" name={reservation.name}" if reservation.name else "")
                            for region in layout.regions
                            for reservation in region.reservations
                        ],
                    )
                )
                extra_sections.append(
                    (
                        "Object Placements",
                        [
                            f"{placed.input_name} region={placed.region_name or '-'} base=0x{placed.base_address:06X} "
                            f"extent={_object_extent(placed.obj)}"
                            for placed in placed_objects
                        ],
                    )
                )
                extra_sections.append(
                    (
                        "Segment Owners",
                        [
                            f"[{index}] {info.input_name} region={info.region_name or '-'} segment={info.segment_index_in_object}"
                            for index, info in enumerate(segment_info)
                        ],
                    )
                )
            map_payload = format_link_map(
                linked,
                base_address=map_base_address,
                max_size=args.max_size,
                raw_origin=raw_origin,
                object_paths=object_paths,
                symbol_paths=symbol_paths,
                extra_sections=extra_sections or None,
            ).encode("utf-8")
    except (LinkerError, ObjectFormatError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    output_path = Path(args.output or default_output_path(args.binary))
    try:
        output_path.write_bytes(payload)
    except OSError as exc:
        print(f"could not write output file {output_path}: {exc.strerror or exc}", file=sys.stderr)
        return 1
    if map_payload is not None:
        map_path = Path(args.map_output)
        try:
            map_path.write_bytes(map_payload)
        except OSError as exc:
            print(f"could not write map file {map_path}: {exc.strerror or exc}", file=sys.stderr)
            return 1
    print(format_payload_size(payload), file=sys.stderr)
    return 0


__all__ = [
    "LINKER_VERSION",
    "LinkerError",
    "default_output_path",
    "format_link_map",
    "format_payload_size",
    "link_objects",
    "link_paths",
    "linked_object_to_binary",
    "main",
]
