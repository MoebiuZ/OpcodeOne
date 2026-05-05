# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from common.opcodeone_isa_bundle import load_default_bundle
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_isa_bundle import load_default_bundle
try:
    from common.opcodeone_bundle_runtime import build_named_register_sets
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_bundle_runtime import build_named_register_sets
try:
    from common.opcodeone_constraints import validate_constraints as validate_shared_constraints
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_constraints import validate_constraints as validate_shared_constraints
try:
    from common.opcodeone_derived_fields import evaluate_derived_fields as evaluate_shared_derived_fields
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_derived_fields import evaluate_derived_fields as evaluate_shared_derived_fields
try:
    from common.opcodeone_isa_runtime import RuntimeForm, RuntimePattern, build_runtime_bundle
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_isa_runtime import RuntimeForm, RuntimePattern, build_runtime_bundle
try:
    from common.opcodeone_object import (
        ObjectExport,
        ObjectFile,
        ObjectImport,
        ObjectLocalSymbol,
        ObjectRelocation,
        ObjectSegment,
        SEGMENT_FLAG_EXECUTABLE,
        SEGMENT_FLAG_READABLE,
        SEGMENT_FLAG_WRITABLE,
        SEGMENT_TYPE_CODE,
        SEGMENT_TYPE_DATA,
        serialize_object,
        words_to_bytes,
    )
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_object import (
        ObjectExport,
        ObjectFile,
        ObjectImport,
        ObjectLocalSymbol,
        ObjectRelocation,
        ObjectSegment,
        SEGMENT_FLAG_EXECUTABLE,
        SEGMENT_FLAG_READABLE,
        SEGMENT_FLAG_WRITABLE,
        SEGMENT_TYPE_CODE,
        SEGMENT_TYPE_DATA,
        serialize_object,
        words_to_bytes,
    )
try:
    from common.opcodeone_operands import MemoryOperand, RegisterOperand, resolve_sequence_value, scalarize_operand
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_operands import MemoryOperand, RegisterOperand, resolve_sequence_value, scalarize_operand

from .constants import DEFAULT_OPCODE_MAP
from .model import (
    AddrItem,
    AlignItem,
    AssembledSegment,
    AssemblerError,
    BytesItem,
    ConstantRef,
    FillItem,
    Fixup,
    InstrItem,
    IntValue,
    LabelItem,
    MatchedInstruction,
    PcRelativeRef,
    PreparedAssembly,
    SignedSymbolRef,
    SourceRef,
    SymbolRef,
    SymbolSliceRef,
    WordItem,
)
from .preprocess import _align_up, preprocess_source
from .syntax import (
    alignment_padding,
    normalize_space,
    pack_bits,
    parse_signed,
    parse_signed_value_expr,
    parse_symbol_ref_expr,
    parse_unsigned,
    parse_unsigned_value_expr,
    parse_value_expr,
    set_active_symbols,
)


ASSEMBLER_VERSION = 2
IMPLEMENTATION_NAME = "json"


@dataclass
class _MaterializedBlock:
    kind: str
    load_address: int
    alignment: int
    data: bytearray


class JsonAssembler:
    def __init__(self, bundle: dict[str, Any]) -> None:
        self.bundle = bundle
        self.abstract_enums = bundle["abstract_enums"]
        self.abstract_kinds = bundle["abstract_kinds"]
        self.operand_kinds = bundle["operand_kinds"]
        self.runtime = build_runtime_bundle(bundle)
        self.families = self.runtime.families
        self.reg_sets = build_named_register_sets(
            bundle["register_sets"],
            lambda set_name, name, code, width_bits: RegisterOperand(
                kind=set_name,
                name=name,
                code=code,
                width_bits=width_bits,
            ),
        )
        self.symbols: dict[str, int] = {}
        self.relocatable_symbols: set[str] = set()
        self.imports: set[str] = set()
        self.current_address: int | None = None

    def assemble_segments(self, text: str, *, source_path: Path | None = None) -> list[AssembledSegment]:
        prepared = self.preprocess_source(text, source_path=source_path)
        return self._assemble_preprocessed_segments(prepared)

    def _assemble_preprocessed_segments(self, prepared: PreparedAssembly) -> list[AssembledSegment]:
        return self._assembled_segments_from_blocks(self._materialize_preprocessed_blocks(prepared))

    def assemble_source(self, text: str, *, source_path: Path | None = None) -> list[int]:
        prepared = self.preprocess_source(text, source_path=source_path)
        return self._assemble_preprocessed_source(prepared)

    def _assemble_preprocessed_source(self, prepared: PreparedAssembly) -> list[int]:
        image = self._build_flat_image_bytes(self._materialize_preprocessed_blocks(prepared))
        if len(image) % 2:
            image.append(0)
        return [image[index] | (image[index + 1] << 8) for index in range(0, len(image), 2)]

    def _assembled_segments_from_blocks(self, blocks: list[_MaterializedBlock]) -> list[AssembledSegment]:
        segments: list[AssembledSegment] = []
        for block in blocks:
            if not block.data:
                continue
            segments.append(
                AssembledSegment(
                    mode=block.kind,
                    data=bytes(block.data),
                    load_address=block.load_address,
                    alignment=block.alignment,
                )
            )
        return segments

    def _build_flat_image_bytes(self, blocks: list[_MaterializedBlock]) -> bytearray:
        image = bytearray()
        cursor = 0
        for block in blocks:
            if not block.data:
                continue
            if block.load_address > cursor:
                image.extend(b"\x00" * (block.load_address - cursor))
                cursor = block.load_address
            image.extend(block.data)
            cursor += len(block.data)
        return image

    def _materialize_preprocessed_blocks(self, prepared: PreparedAssembly) -> list[_MaterializedBlock]:
        blocks, _ = self._materialize_blocks_and_collect_unresolved(prepared, keep_unresolved=False)
        return blocks

    def _materialize_blocks_and_collect_unresolved(
        self,
        prepared: PreparedAssembly,
        *,
        keep_unresolved: bool,
    ) -> tuple[list[_MaterializedBlock], list[Fixup]]:
        blocks, fixups = self._emit_preprocessed_blocks(prepared)
        unresolved = self._apply_fixups(
            blocks,
            fixups,
            keep_unresolved=keep_unresolved,
            defer_relocatable_absolute=False,
        )
        return blocks, unresolved

    def _materialize_blocks_for_object(self, prepared: PreparedAssembly) -> tuple[list[_MaterializedBlock], list[Fixup]]:
        blocks, fixups = self._emit_preprocessed_blocks(prepared)
        unresolved = self._apply_fixups(
            blocks,
            fixups,
            keep_unresolved=True,
            defer_relocatable_absolute=True,
        )
        return blocks, unresolved

    def _emit_preprocessed_blocks(self, prepared: PreparedAssembly) -> tuple[list[_MaterializedBlock], list[Fixup]]:
        blocks: list[_MaterializedBlock] = []
        fixups: list[Fixup] = []
        cursor = 0

        previous_symbols = set_active_symbols({})
        try:
            self.symbols = prepared.symbols
            self.relocatable_symbols = prepared.relocatable_symbols
            self.imports = set(prepared.imports)
            set_active_symbols(self.symbols)
            for block_index, block in enumerate(prepared.module_ir.blocks):
                alignment = 2 if block.kind == "code" else 1
                cursor = _align_up(cursor, alignment)
                payload = bytearray()
                materialized = _MaterializedBlock(kind=block.kind, load_address=cursor, alignment=alignment, data=payload)
                blocks.append(materialized)

                for item in block.items:
                    if isinstance(item, LabelItem):
                        continue
                    try:
                        offset_in_block = len(payload)
                        if block.kind == "code":
                            if not isinstance(item, InstrItem):
                                raise AssemblerError(f"line {item.source.line_no}: instructions are only valid in --CODE: blocks")
                            data_bytes, item_fixups = self._emit_instr_item_bytes(item, block_index, offset_in_block)
                        else:
                            data_bytes, item_fixups = self._emit_data_item_with_fixups(item, block_index, offset_in_block)
                        payload.extend(data_bytes)
                        fixups.extend(item_fixups)
                    except AssemblerError as exc:
                        raise exc.with_context(source_path=prepared.source_path, source_line=item.source.text) from exc

                cursor += len(payload)
            return blocks, fixups
        finally:
            self.current_address = None
            set_active_symbols(previous_symbols)

    def preprocess_source(
        self,
        text: str,
        *,
        source_path: Path | None = None,
    ) -> PreparedAssembly:
        return preprocess_source(
            text,
            build_instruction_item=self._build_instruction_item,
            source_path=source_path,
        )

    def _build_instruction_item(self, line: str, line_no: int, source: SourceRef) -> InstrItem:
        matched = self.match_line(line, line_no)
        return InstrItem(source=source, size_bytes=self._matched_instruction_size_bytes(matched), match=matched)

    @staticmethod
    def _matched_instruction_size_bytes(matched: MatchedInstruction) -> int:
        if matched.words is not None:
            return len(matched.words) * 2
        assert matched.form is not None
        return matched.form.word_count * 2

    def assemble_line(self, line: str, line_no: int) -> list[int]:
        return self._encode_matched_instruction(self.match_line(line, line_no))

    def match_line(self, line: str, line_no: int) -> MatchedInstruction:
        raw = line.split(";", 1)[0].strip()
        if not raw:
            return MatchedInstruction(line_no=line_no, words=[])

        normalized = normalize_space(raw)
        best_error: AssemblerError | None = None
        for family in self.families:
            for runtime_form in family.forms:
                for pattern in runtime_form.syntax_patterns:
                    match, match_error = self._match_pattern(pattern, normalized, line_no)
                    if match_error is not None and best_error is None:
                        best_error = match_error
                    if match is None:
                        continue
                    inputs = match
                    for key, value in runtime_form.defaults.items():
                        inputs.setdefault(key, value)
                    self._validate_constraints(runtime_form, inputs, line_no)
                    derived = self._evaluate_derived_fields(runtime_form, inputs, line_no)
                    return MatchedInstruction(
                        line_no=line_no,
                        form=runtime_form,
                        pattern=pattern,
                        inputs=inputs,
                        derived=derived,
                    )

        if best_error is not None:
            raise best_error
        raise AssemblerError(f"line {line_no}: unsupported or non-canonical syntax")

    def _encode_matched_instruction(self, matched: MatchedInstruction) -> list[int]:
        if matched.words is not None:
            return matched.words
        assert matched.form is not None
        assert matched.inputs is not None
        assert matched.derived is not None
        self._validate_runtime_constraints(matched.form, matched.inputs, matched.line_no)
        return self._encode_form(matched.form, matched.inputs, matched.derived, matched.line_no)

    def _encode_instr_item(self, item: InstrItem) -> list[int]:
        if item.match is not None:
            return self._encode_matched_instruction(item.match)
        if item.source.text is None:
            raise AssemblerError(f"line {item.source.line_no}: internal error: missing instruction text for deferred match")
        return self.assemble_line(item.source.text, item.source.line_no)

    def _emit_instr_item_bytes(self, item: InstrItem, block_index: int, offset_in_block: int) -> tuple[list[int], list[Fixup]]:
        if item.match is not None:
            return self._emit_matched_instruction_bytes(item.match, item.source, block_index, offset_in_block)
        if item.source.text is None:
            raise AssemblerError(f"line {item.source.line_no}: internal error: missing instruction text for deferred match")
        return self._emit_matched_instruction_bytes(
            self.match_line(item.source.text, item.source.line_no),
            item.source,
            block_index,
            offset_in_block,
        )

    def _emit_matched_instruction_bytes(
        self,
        matched: MatchedInstruction,
        source: SourceRef,
        block_index: int,
        offset_in_block: int,
    ) -> tuple[list[int], list[Fixup]]:
        if matched.words is not None:
            return list(words_to_bytes(matched.words)), []
        assert matched.form is not None
        assert matched.inputs is not None
        assert matched.derived is not None
        words, fixups = self._emit_form_with_fixups(
            matched.form,
            matched.inputs,
            matched.derived,
            matched.line_no,
            source,
            block_index,
            offset_in_block,
        )
        return list(words_to_bytes(words)), fixups

    def _emit_data_item_with_fixups(
        self,
        item: BytesItem | WordItem | AddrItem | FillItem | AlignItem,
        block_index: int,
        offset_in_block: int,
    ) -> tuple[list[int], list[Fixup]]:
        if isinstance(item, BytesItem):
            return list(item.data), []
        if isinstance(item, WordItem):
            data: list[int] = []
            fixups: list[Fixup] = []
            for value in item.values:
                entry_offset = offset_in_block + len(data)
                if isinstance(value, IntValue):
                    resolved = self._validate_unsigned_value(value.value, 16, item.source.line_no, "word value")
                    data.append(resolved & 0xFF)
                    data.append((resolved >> 8) & 0xFF)
                    continue
                data.extend([0, 0])
                fixups.append(
                    self._build_symbol_fixup(
                        value,
                        item.source,
                        "word value",
                        block_index,
                        entry_offset,
                        container_bytes=2,
                        field_lsb=0,
                        field_bits=16,
                    )
                )
            return data, fixups
        if isinstance(item, AddrItem):
            data = []
            fixups: list[Fixup] = []
            for value in item.values:
                entry_offset = offset_in_block + len(data)
                if isinstance(value, IntValue):
                    resolved = self._validate_unsigned_value(value.value, 24, item.source.line_no, "address value")
                    data.append(resolved & 0xFF)
                    data.append((resolved >> 8) & 0xFF)
                    data.append((resolved >> 16) & 0xFF)
                    continue
                data.extend([0, 0, 0])
                fixups.append(
                    self._build_symbol_fixup(
                        value,
                        item.source,
                        "address value",
                        block_index,
                        entry_offset,
                        container_bytes=3,
                        field_lsb=0,
                        field_bits=24,
                    )
                )
            return data, fixups
        if isinstance(item, FillItem):
            return [item.byte_value] * item.count, []
        return [0] * alignment_padding(offset_in_block, item.alignment), []

    def _resolve_value_expr(self, value: IntValue | SymbolRef, bits: int, line_no: int, label: str) -> int:
        if isinstance(value, IntValue):
            resolved = value.value
        else:
            resolved = self._resolve_symbol_ref(value, line_no)
        return self._validate_unsigned_value(resolved, bits, line_no, label)

    def _resolve_constant_ref(self, value: ConstantRef, line_no: int) -> int:
        constant_value = self.symbols.get(value.name)
        if constant_value is None:
            raise AssemblerError(f"line {line_no}: undefined symbol '{value.name}'")
        return constant_value * value.sign

    def _resolve_symbol_ref(self, value: SymbolRef, line_no: int) -> int:
        symbol_value = self.symbols.get(value.name)
        if symbol_value is None:
            raise AssemblerError(f"line {line_no}: undefined symbol '{value.name}'")
        addend = value.addend if isinstance(value.addend, int) else self._resolve_constant_ref(value.addend, line_no)
        return symbol_value + addend

    def _validate_unsigned_value(self, value: int, bits: int, line_no: int, label: str) -> int:
        hi = (1 << bits) - 1
        if not 0 <= value <= hi:
            raise AssemblerError(f"line {line_no}: {label} out of range for unsigned {bits}-bit field: {value}")
        return value

    def _validate_signed_value(self, value: int, bits: int, line_no: int, label: str) -> int:
        lo = -(1 << (bits - 1))
        hi = (1 << (bits - 1)) - 1
        if not lo <= value <= hi:
            raise AssemblerError(f"line {line_no}: {label} out of range for signed {bits}-bit field: {value}")
        return value

    def _resolve_symbol_slice_ref(self, value: SymbolSliceRef, line_no: int, label: str) -> int:
        resolved = self._resolve_symbol_ref(value.symbol, line_no)
        self._validate_unsigned_value(resolved, value.source_bits, line_no, label)
        width = value.msb - value.lsb + 1
        return (resolved >> value.lsb) & ((1 << width) - 1)

    def _resolve_signed_symbol_ref(self, value: SignedSymbolRef, line_no: int, label: str) -> int:
        resolved = self._resolve_symbol_ref(value.symbol, line_no) * value.sign
        return self._validate_signed_value(resolved, value.bits, line_no, label)

    def _resolve_pc_relative_ref(self, value: PcRelativeRef, line_no: int, label: str) -> int:
        if self.current_address is None:
            raise AssemblerError(f"line {line_no}: internal error: current address required for relative symbol resolution")
        resolved = self._resolve_symbol_ref(value.symbol, line_no) - (self.current_address + value.origin_bias)
        return self._validate_signed_value(resolved, value.bits, line_no, label)

    def _resolve_fixup_addend(self, value: int | ConstantRef, line_no: int) -> int:
        if isinstance(value, int):
            return value
        return self._resolve_constant_ref(value, line_no)

    def _bit_index_constraint_max(self, form: RuntimeForm, inputs: dict[str, Any], field_source: str) -> int | None:
        for constraint in form.constraints:
            if constraint["type"] != "bit_index_within_width":
                continue
            if field_source != f"sequence.{constraint['bit_operand']}":
                continue
            target = inputs[constraint["target_operand"]]
            return target.width_bits - 1
        return None

    def _build_symbol_fixup(
        self,
        value: SymbolRef,
        source: SourceRef,
        label: str,
        block_index: int,
        offset_in_block: int,
        *,
        container_bytes: int,
        field_lsb: int,
        field_bits: int,
        max_value: int | None = None,
    ) -> Fixup:
        return Fixup(
            kind="absolute",
            block_index=block_index,
            offset_in_block=offset_in_block,
            container_bytes=container_bytes,
            field_lsb=field_lsb,
            field_bits=field_bits,
            symbol=value.name,
            addend=self._resolve_fixup_addend(value.addend, source.line_no),
            max_value=max_value,
            label=label,
            source=source,
        )

    def _build_signed_symbol_fixup(
        self,
        value: SignedSymbolRef,
        source: SourceRef,
        label: str,
        block_index: int,
        offset_in_block: int,
        *,
        container_bytes: int,
        field_lsb: int,
        field_bits: int,
        max_value: int | None = None,
    ) -> Fixup:
        return Fixup(
            kind="absolute",
            block_index=block_index,
            offset_in_block=offset_in_block,
            container_bytes=container_bytes,
            field_lsb=field_lsb,
            field_bits=field_bits,
            symbol=value.symbol.name,
            addend=self._resolve_fixup_addend(value.symbol.addend, source.line_no),
            symbol_sign=value.sign,
            signed=True,
            max_value=max_value,
            label=label,
            source=source,
        )

    def _build_pc_relative_fixup(
        self,
        value: PcRelativeRef,
        source: SourceRef,
        label: str,
        block_index: int,
        offset_in_block: int,
        *,
        base_offset_in_block: int,
        container_bytes: int,
        field_lsb: int,
        field_bits: int,
    ) -> Fixup:
        return Fixup(
            kind="pcrel",
            block_index=block_index,
            offset_in_block=offset_in_block,
            container_bytes=container_bytes,
            field_lsb=field_lsb,
            field_bits=field_bits,
            symbol=value.symbol.name,
            addend=self._resolve_fixup_addend(value.symbol.addend, source.line_no),
            signed=True,
            base_offset_in_block=base_offset_in_block,
            origin_bias=value.origin_bias,
            label=label,
            source=source,
        )

    def _build_symbol_slice_fixup(
        self,
        value: SymbolSliceRef,
        source: SourceRef,
        label: str,
        block_index: int,
        offset_in_block: int,
        *,
        container_bytes: int,
        field_lsb: int,
        field_bits: int,
    ) -> Fixup:
        return Fixup(
            kind="absolute",
            block_index=block_index,
            offset_in_block=offset_in_block,
            container_bytes=container_bytes,
            field_lsb=field_lsb,
            field_bits=field_bits,
            symbol=value.symbol.name,
            addend=self._resolve_fixup_addend(value.symbol.addend, source.line_no),
            value_lsb=value.lsb,
            value_bits=value.source_bits,
            label=label,
            source=source,
        )

    def _emit_form_with_fixups(
        self,
        form: RuntimeForm,
        inputs: dict[str, Any],
        derived: dict[str, Any],
        line_no: int,
        source: SourceRef,
        block_index: int,
        offset_in_block: int,
    ) -> tuple[list[int], list[Fixup]]:
        words: list[int] = []
        fixups: list[Fixup] = []
        opcode = form.opcode

        for word_index, word_fields in enumerate(form.encoding_words):
            word = 0
            word_offset = offset_in_block + (word_index * 2)
            for field in word_fields:
                width = field["msb"] - field["lsb"] + 1
                if field["kind"] == "fixed":
                    value = field["value"]
                elif field["kind"] == "slot":
                    if field["source"] == "family_opcode":
                        value = opcode
                    else:
                        value = self._resolve_source(field["source"], inputs, derived, scalar=False)
                else:
                    raise AssemblerError(f"line {line_no}: unsupported encoding field kind '{field['kind']}'")
                if value is None:
                    raise AssemblerError(f"line {line_no}: missing value for field '{field['name']}'")

                if isinstance(value, SymbolSliceRef):
                    fixups.append(
                        self._build_symbol_slice_fixup(
                            value,
                            source,
                            field["name"],
                            block_index,
                            word_offset,
                            container_bytes=2,
                            field_lsb=field["lsb"],
                            field_bits=width,
                        )
                    )
                    value = 0
                elif isinstance(value, SignedSymbolRef):
                    fixups.append(
                        self._build_signed_symbol_fixup(
                            value,
                            source,
                            field["name"],
                            block_index,
                            word_offset,
                            container_bytes=2,
                            field_lsb=field["lsb"],
                            field_bits=width,
                            max_value=self._bit_index_constraint_max(form, inputs, field["source"]),
                        )
                    )
                    value = 0
                elif isinstance(value, PcRelativeRef):
                    fixups.append(
                        self._build_pc_relative_fixup(
                            value,
                            source,
                            field["name"],
                            block_index,
                            word_offset,
                            base_offset_in_block=offset_in_block,
                            container_bytes=2,
                            field_lsb=field["lsb"],
                            field_bits=width,
                        )
                    )
                    value = 0
                elif isinstance(value, SymbolRef):
                    fixups.append(
                        self._build_symbol_fixup(
                            value,
                            source,
                            field["name"],
                            block_index,
                            word_offset,
                            container_bytes=2,
                            field_lsb=field["lsb"],
                            field_bits=width,
                            max_value=self._bit_index_constraint_max(form, inputs, field["source"]),
                        )
                    )
                    value = 0
                else:
                    value = self._scalarize(value)
                word |= pack_bits(int(value), width) << field["lsb"]
            words.append(word)
        return words, fixups

    def _apply_fixups(
        self,
        blocks: list[_MaterializedBlock],
        fixups: list[Fixup],
        *,
        keep_unresolved: bool,
        defer_relocatable_absolute: bool,
    ) -> list[Fixup]:
        unresolved: list[Fixup] = []
        for fixup in fixups:
            if not self._apply_fixup(
                blocks,
                fixup,
                keep_unresolved=keep_unresolved,
                defer_relocatable_absolute=defer_relocatable_absolute,
            ):
                unresolved.append(fixup)
        return unresolved

    def _apply_fixup(
        self,
        blocks: list[_MaterializedBlock],
        fixup: Fixup,
        *,
        keep_unresolved: bool,
        defer_relocatable_absolute: bool,
    ) -> bool:
        if fixup.source is None:
            raise AssemblerError("internal error: fixup is missing source information")
        if fixup.block_index >= len(blocks):
            raise AssemblerError(f"line {fixup.source.line_no}: internal error: invalid fixup block index {fixup.block_index}")

        block = blocks[fixup.block_index]
        if (
            keep_unresolved and
            defer_relocatable_absolute and
            fixup.kind == "absolute" and
            fixup.symbol in self.relocatable_symbols
        ):
            return False

        symbol_value = self.symbols.get(fixup.symbol)
        if symbol_value is None:
            if keep_unresolved and fixup.symbol in self.imports:
                return False
            if keep_unresolved and not fixup.symbol.startswith("."):
                raise AssemblerError(
                    f"line {fixup.source.line_no}: undefined symbol '{fixup.symbol}'; declare external symbols with 'import {fixup.symbol}'"
                )
            raise AssemblerError(f"line {fixup.source.line_no}: undefined symbol '{fixup.symbol}'")

        resolved = (symbol_value * fixup.symbol_sign) + fixup.addend
        if fixup.kind == "pcrel":
            resolved -= block.load_address + fixup.base_offset_in_block + fixup.origin_bias

        label = fixup.label
        line_no = fixup.source.line_no
        if fixup.value_bits is not None:
            resolved = self._validate_unsigned_value(resolved, fixup.value_bits, line_no, label)
            field_value = resolved >> fixup.value_lsb
        elif fixup.signed:
            field_value = self._validate_signed_value(resolved, fixup.field_bits, line_no, label)
        else:
            field_value = self._validate_unsigned_value(resolved, fixup.field_bits, line_no, label)

        if fixup.max_value is not None and field_value > fixup.max_value:
            raise AssemblerError(f"line {line_no}: {label} out of range for target width: {field_value}")

        end_offset = fixup.offset_in_block + fixup.container_bytes
        container = 0
        for index, byte in enumerate(block.data[fixup.offset_in_block:end_offset]):
            container |= byte << (index * 8)
        mask = ((1 << fixup.field_bits) - 1) << fixup.field_lsb
        container = (container & ~mask) | ((pack_bits(field_value, fixup.field_bits) << fixup.field_lsb) & mask)
        for index in range(fixup.container_bytes):
            block.data[fixup.offset_in_block + index] = (container >> (index * 8)) & 0xFF
        return True

    def _match_pattern(self, pattern: RuntimePattern, text: str, line_no: int) -> tuple[dict[str, Any] | None, AssemblerError | None]:
        regex = self._build_pattern_regex(pattern)
        match = re.fullmatch(regex, text, flags=re.IGNORECASE)
        if not match:
            return None, None

        inputs: dict[str, Any] = dict(pattern.named_literals)
        captures = match.groupdict()
        try:
            for token in pattern.slot_tokens:
                name = token["name"]
                captured = captures.get(name)
                if captured is None:
                    continue
                captured = normalize_space(captured)
                inputs[name] = self._parse_slot_value(token, captured, line_no)
        except AssemblerError as exc:
            return None, exc
        return inputs, None

    def _build_pattern_regex(self, pattern: RuntimePattern) -> str:
        parts: list[str] = []
        sequence = pattern.sequence
        for index, token in enumerate(sequence):
            prefix = r"\s+" if index > 0 else r"\s*"
            if token["kind"] == "literal":
                literal = re.escape(token["value"]).replace(r"\ ", r"\s+")
                parts.append(prefix + literal)
                continue

            slot_name = token["name"]
            if token["slot_kind"] == "operand":
                body = r"(?P<%s>.+?)" % slot_name
            elif token["slot_kind"] == "enum":
                values = [value for value in self.abstract_enums[token["enum_ref"]] if value not in token.get("omit_keys", [])]
                values.sort(key=len, reverse=True)
                body = r"(?P<%s>%s)" % (slot_name, "|".join(re.escape(v).replace(r"\ ", r"\s+") for v in values))
            elif token["slot_kind"] == "keyword":
                literal = self.abstract_kinds[token["keyword_ref"]]["literal"]
                body = r"(?P<%s>%s)" % (slot_name, re.escape(literal).replace(r"\ ", r"\s+"))
            else:
                raise AssemblerError(f"unsupported slot kind '{token['slot_kind']}' in JSON syntax")

            piece = prefix + body
            if token.get("optional"):
                piece = r"(?:%s)?" % piece
            parts.append(piece)

        return "".join(parts) + r"\s*"

    def _parse_slot_value(self, token: dict[str, Any], captured: str, line_no: int) -> Any:
        slot_kind = token["slot_kind"]
        if slot_kind == "operand":
            return self._parse_operand(token["operand_kind_ref"], captured, line_no)
        if slot_kind == "enum":
            return captured
        if slot_kind == "keyword":
            return True
        raise AssemblerError(f"unsupported slot kind '{slot_kind}'")

    def _describe_operand_kind(self, operand_kind_ref: str) -> str:
        spec = self.operand_kinds[operand_kind_ref]
        operand_type = spec["type"]
        if operand_type == "register":
            return f"{spec['register_set']} register"
        if operand_type == "register_subset":
            return "register " + ", ".join(spec["members"])
        if operand_type == "union":
            return " or ".join(self._describe_operand_kind(member_ref) for member_ref in spec["members"])
        if operand_type == "immediate":
            signedness = "signed" if spec["signed"] else "unsigned"
            return f"{signedness} {spec['bits']}-bit immediate"
        if operand_type == "address":
            return f"{spec['bits']}-bit address"
        if operand_type == "relative_offset":
            return f"signed {spec['bits']}-bit relative offset"
        if operand_type == "memory":
            return f"{spec['addressing']} memory operand"
        return operand_kind_ref

    def _parse_operand(self, operand_kind_ref: str, token: str, line_no: int) -> Any:
        spec = self.operand_kinds[operand_kind_ref]
        operand_type = spec["type"]

        if operand_type == "register":
            return self._parse_register(token, spec["register_set"], line_no)
        if operand_type == "register_subset":
            reg = self._parse_register(token, spec["register_set"], line_no)
            if reg.name not in spec["members"]:
                allowed = ", ".join(spec["members"])
                raise AssemblerError(f"line {line_no}: register '{token}' must be one of {allowed}")
            return reg
        if operand_type == "union":
            for member_ref in spec["members"]:
                try:
                    return self._parse_operand(member_ref, token, line_no)
                except AssemblerError:
                    continue
            raise AssemblerError(
                f"line {line_no}: invalid operand '{token}'; expected {self._describe_operand_kind(operand_kind_ref)}"
            )
        if operand_type == "immediate":
            if spec["signed"]:
                if spec["bits"] == 16:
                    return parse_signed_value_expr(token, spec["bits"], line_no, "immediate")
                return parse_signed(token, spec["bits"], line_no, "immediate")
            if operand_kind_ref == "bit_index_5" or spec["bits"] == 16:
                return parse_unsigned_value_expr(token, spec["bits"], line_no, "immediate")
            return parse_unsigned(token, spec["bits"], line_no, "immediate")
        if operand_type == "address":
            expr = parse_value_expr(token, line_no)
            if isinstance(expr, SymbolRef):
                return expr
            return self._validate_unsigned_value(expr.value, spec["bits"], line_no, "address")
        if operand_type == "relative_offset":
            symbol_ref = parse_symbol_ref_expr(token)
            normalized_token = normalize_space(token)
            if symbol_ref is not None and (normalized_token.startswith(".") or normalized_token.startswith("+.")):
                return PcRelativeRef(symbol=symbol_ref, bits=spec["bits"], origin_bias=4)
            return parse_signed(token, spec["bits"], line_no, "relative offset")
        if operand_type == "memory":
            return self._parse_memory(token, spec["addressing"], line_no)

        raise AssemblerError(f"unsupported operand kind type '{operand_type}'")

    def _parse_register(self, token: str, register_set: str, line_no: int) -> RegisterOperand:
        name = token.strip().upper()
        mapping = self.reg_sets[register_set]
        if name not in mapping:
            raise AssemblerError(f"line {line_no}: invalid {register_set} register '{token}'")
        return mapping[name]

    def _parse_memory(self, token: str, addressing: str, line_no: int) -> MemoryOperand:
        token = token.strip()
        if not (token.startswith("[") and token.endswith("]")):
            raise AssemblerError(f"line {line_no}: expected memory operand, got '{token}'")
        inner = token[1:-1].strip()
        upper = inner.upper()

        if addressing == "[reg24]":
            reg = self._parse_register(upper, "reg24", line_no)
            return MemoryOperand(addressing=addressing, base=reg)

        if addressing == "[reg24+off16_signed]":
            match = re.fullmatch(r"([XYZW])\s*([+-])\s*(.+)", inner, flags=re.IGNORECASE)
            if not match:
                raise AssemblerError(f"line {line_no}: expected [reg24+off16], got '{token}'")
            reg_name, sign, imm_text = match.groups()
            reg = self._parse_register(reg_name, "reg24", line_no)
            signed_text = imm_text if sign == "+" else f"-{imm_text}"
            offset = parse_signed_value_expr(signed_text, 16, line_no, "memory offset")
            if isinstance(offset, SignedSymbolRef):
                return MemoryOperand(addressing=addressing, base=reg, offset=offset)
            return MemoryOperand(addressing=addressing, base=reg, offset=pack_bits(offset, 16))

        if addressing == "[addr24]":
            expr = parse_value_expr(inner, line_no)
            if isinstance(expr, SymbolRef):
                return self._build_abs24_operand(expr)
            addr = self._validate_unsigned_value(expr.value, 24, line_no, "address")
            return self._build_abs24_operand(addr)

        raise AssemblerError(f"unsupported memory addressing kind '{addressing}'")

    def _build_abs24_operand(self, value: int | SymbolRef) -> MemoryOperand:
        if isinstance(value, SymbolRef):
            hi_ref = SymbolSliceRef(symbol=value, source_bits=24, msb=23, lsb=16)
            lo_ref = SymbolSliceRef(symbol=value, source_bits=24, msb=15, lsb=0)
            return MemoryOperand(addressing="[addr24]", addr=value, addr_hi8=hi_ref, addr_lo16=lo_ref)
        return MemoryOperand(
            addressing="[addr24]",
            addr=value,
            addr_hi8=(value >> 16) & 0xFF,
            addr_lo16=value & 0xFFFF,
        )

    def _validate_constraints(self, runtime_form: RuntimeForm, inputs: dict[str, Any], line_no: int) -> None:
        validate_shared_constraints(
            runtime_form.constraints,
            inputs,
            error_factory=lambda message: AssemblerError(f"line {line_no}: {message}"),
            symbolic_bit_index_types=(SymbolRef, SignedSymbolRef),
        )

    def _validate_runtime_constraints(self, form: RuntimeForm, inputs: dict[str, Any], line_no: int) -> None:
        runtime_inputs = dict(inputs)
        for constraint in form.constraints:
            if constraint["type"] != "bit_index_within_width":
                continue
            bit_slot = constraint["bit_operand"]
            bit_index = runtime_inputs[bit_slot]
            if isinstance(bit_index, SymbolRef):
                runtime_inputs[bit_slot] = self._resolve_value_expr(bit_index, 5, line_no, "bit index")
            elif isinstance(bit_index, SignedSymbolRef):
                runtime_inputs[bit_slot] = self._resolve_signed_symbol_ref(bit_index, line_no, "bit index")
        validate_shared_constraints(
            form.constraints,
            runtime_inputs,
            error_factory=lambda message: AssemblerError(f"line {line_no}: {message}"),
        )

    def _evaluate_derived_fields(self, form: RuntimeForm, inputs: dict[str, Any], line_no: int) -> dict[str, Any]:
        return evaluate_shared_derived_fields(
            form.derived_fields,
            resolve_source=lambda source, derived: self._resolve_source(source, inputs, derived, scalar=False),
            abstract_enums=self.abstract_enums,
            scalarize=self._scalarize,
            symbol_slice_factory=lambda value, spec: self._build_symbol_slice(value, spec, line_no),
            error_factory=lambda message: AssemblerError(f"line {line_no}: {message}"),
        )

    @staticmethod
    def _build_symbol_slice(value: Any, spec: dict[str, Any], line_no: int) -> SymbolSliceRef:
        if not isinstance(value, SymbolRef):
            raise AssemblerError(f"line {line_no}: bit_slice expects an address-like source")
        return SymbolSliceRef(symbol=value, source_bits=24, msb=spec["msb"], lsb=spec["lsb"])

    def _resolve_source(self, source: str, inputs: dict[str, Any], derived: dict[str, Any], *, scalar: bool) -> Any:
        if source.startswith("sequence."):
            value = self._resolve_sequence_path(source[len("sequence.") :], inputs)
        elif source.startswith("derived."):
            value = derived[source[len("derived.") :]]
        else:
            raise AssemblerError(f"unsupported source ref '{source}'")
        return self._scalarize(value) if scalar else value

    def _resolve_sequence_path(self, path: str, inputs: dict[str, Any]) -> Any:
        return resolve_sequence_value(inputs, path)

    @staticmethod
    def _scalarize(value: Any) -> Any:
        return scalarize_operand(value)

    def _encode_form(
        self,
        form: RuntimeForm,
        inputs: dict[str, Any],
        derived: dict[str, Any],
        line_no: int,
    ) -> list[int]:
        words: list[int] = []
        opcode = form.opcode
        for word_fields in form.encoding_words:
            word = 0
            for field in word_fields:
                width = field["msb"] - field["lsb"] + 1
                if field["kind"] == "fixed":
                    value = field["value"]
                elif field["kind"] == "slot":
                    if field["source"] == "family_opcode":
                        value = opcode
                    else:
                        value = self._resolve_source(field["source"], inputs, derived, scalar=True)
                else:
                    raise AssemblerError(f"line {line_no}: unsupported encoding field kind '{field['kind']}'")
                if value is None:
                    raise AssemblerError(f"line {line_no}: missing value for field '{field['name']}'")
                if isinstance(value, SymbolSliceRef):
                    value = self._resolve_symbol_slice_ref(value, line_no, field["name"])
                elif isinstance(value, SignedSymbolRef):
                    value = self._resolve_signed_symbol_ref(value, line_no, field["name"])
                elif isinstance(value, PcRelativeRef):
                    value = self._resolve_pc_relative_ref(value, line_no, field["name"])
                elif isinstance(value, SymbolRef):
                    value = self._resolve_value_expr(value, width, line_no, field["name"])
                word |= pack_bits(int(value), width) << field["lsb"]
            words.append(word)
        return words


def assemble_segments(
    text: str,
    *,
    source_path: Path | None = None,
) -> list[AssembledSegment]:
    assembler = JsonAssembler(load_default_bundle())
    return assembler.assemble_segments(text, source_path=source_path)


def assemble_line(
    line: str,
    line_no: int,
    *,
    current_address: int | None = None,
) -> list[int]:
    assembler = JsonAssembler(load_default_bundle())
    assembler.current_address = current_address
    try:
        return assembler.assemble_line(line, line_no)
    except AssemblerError as exc:
        raise exc.with_context(source_line=line) from exc


def assemble_source(text: str, *, source_path: Path | None = None) -> list[int]:
    assembler = JsonAssembler(load_default_bundle())
    return assembler.assemble_source(text, source_path=source_path)


def assemble_object(text: str, *, source_path: Path | None = None) -> ObjectFile:
    assembler = JsonAssembler(load_default_bundle())
    prepared = assembler.preprocess_source(text, source_path=source_path)
    blocks, unresolved_fixups = assembler._materialize_blocks_for_object(prepared)
    object_segments: list[ObjectSegment] = []
    block_to_segment_index: dict[int, int] = {}

    for block_index, block in enumerate(blocks):
        if not block.data:
            continue
        if block.kind == "code":
            block_to_segment_index[block_index] = len(object_segments)
            object_segments.append(
                ObjectSegment(
                    segment_type=SEGMENT_TYPE_CODE,
                    load_address=block.load_address,
                    data=bytes(block.data),
                    segment_flags=SEGMENT_FLAG_READABLE | SEGMENT_FLAG_EXECUTABLE,
                )
            )
        else:
            block_to_segment_index[block_index] = len(object_segments)
            object_segments.append(
                ObjectSegment(
                    segment_type=SEGMENT_TYPE_DATA,
                    load_address=block.load_address,
                    data=bytes(block.data),
                    segment_flags=SEGMENT_FLAG_READABLE | SEGMENT_FLAG_WRITABLE,
                )
            )

    object_exports = [ObjectExport(name=name, address=address) for name, address in sorted(prepared.exports.items())]
    local_relocation_names = {
        fixup.symbol
        for fixup in unresolved_fixups
        if fixup.symbol in prepared.relocatable_symbols
    }
    unresolved_import_names = {
        fixup.symbol
        for fixup in unresolved_fixups
        if fixup.symbol not in prepared.relocatable_symbols
    }
    object_local_symbols = [
        ObjectLocalSymbol(name=name, address=prepared.symbols[name])
        for name in sorted(local_relocation_names)
    ]
    object_imports = [ObjectImport(name=name) for name in prepared.imports if name in unresolved_import_names]
    object_relocations = [
        ObjectRelocation(
            kind=fixup.kind,
            segment_index=block_to_segment_index[fixup.block_index],
            offset_in_segment=fixup.offset_in_block,
            container_bytes=fixup.container_bytes,
            field_lsb=fixup.field_lsb,
            field_bits=fixup.field_bits,
            symbol_name=fixup.symbol,
            symbol_scope="local" if fixup.symbol in prepared.relocatable_symbols else "import",
            addend=fixup.addend,
            symbol_sign=fixup.symbol_sign,
            value_lsb=fixup.value_lsb,
            value_bits=fixup.value_bits,
            signed=fixup.signed,
            base_offset_in_segment=fixup.base_offset_in_block,
            origin_bias=fixup.origin_bias,
            max_value=fixup.max_value,
        )
        for fixup in unresolved_fixups
    ]
    return ObjectFile(
        segments=object_segments,
        exports=object_exports,
        local_symbols=object_local_symbols,
        imports=object_imports,
        relocations=object_relocations,
    )


def assemble_object_bytes(text: str, *, source_path: Path | None = None) -> bytes:
    return serialize_object(assemble_object(text, source_path=source_path))


def assemble_exports(text: str, *, source_path: Path | None = None) -> dict[str, int]:
    assembler = JsonAssembler(load_default_bundle())
    return assembler.preprocess_source(text, source_path=source_path).exports


def format_words(words: list[int]) -> str:
    return "\n".join(f"0x{word:04X}" for word in words)


def format_payload_size(payload: bytes) -> str:
    size_bytes = len(payload)
    size_kib = size_bytes / 1024.0
    return f"generated {size_bytes} bytes ({size_kib:.2f} KiB)"


def default_output_path(binary: bool) -> str:
    return "out.bin" if binary else "out.obj"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simple OpcodeOne assembler driven by the JSON ISA source")
    parser.add_argument("source", nargs="?", help="Assembly file. Reads stdin when omitted.")
    parser.add_argument("-o", "--output", help="Output file. Writes to out.obj or out.bin when omitted.")
    parser.add_argument("-b", "--binary", action="store_true", help="Write raw binary without O1OB headers.")
    args = parser.parse_args(argv)

    try:
        if args.source:
            source_path = Path(args.source)
            text = source_path.read_text(encoding="utf-8")
        else:
            source_path = None
            text = sys.stdin.read()

        payload = (
            words_to_bytes(assemble_source(text, source_path=source_path))
            if args.binary
            else assemble_object_bytes(text, source_path=source_path)
        )
        output_path = Path(args.output or default_output_path(args.binary))
        output_path.write_bytes(payload)
    except (AssemblerError, OSError, UnicodeDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(format_payload_size(payload), file=sys.stderr)
    return 0


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
    "main",
]
