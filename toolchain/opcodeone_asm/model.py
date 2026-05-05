# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

try:
    from common.opcodeone_operands import MemoryOperand, RegisterOperand
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_operands import MemoryOperand, RegisterOperand
try:
    from common.opcodeone_isa_runtime import RuntimeForm, RuntimePattern
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_isa_runtime import RuntimeForm, RuntimePattern


class AssemblerError(Exception):
    def __init__(
        self,
        message: str,
        *,
        line_no: int | None = None,
        source_path: Path | None = None,
        source_line: str | None = None,
    ) -> None:
        extracted_line_no = line_no
        extracted_message = message
        if extracted_line_no is None:
            match = re.fullmatch(r"line (\d+): (.+)", message)
            if match:
                extracted_line_no = int(match.group(1))
                extracted_message = match.group(2)
        super().__init__(extracted_message)
        self.message = extracted_message
        self.line_no = extracted_line_no
        self.source_path = source_path
        self.source_line = source_line.rstrip() if source_line is not None else None

    def with_context(
        self,
        *,
        line_no: int | None = None,
        source_path: Path | None = None,
        source_line: str | None = None,
    ) -> AssemblerError:
        return AssemblerError(
            self.message,
            line_no=self.line_no if self.line_no is not None else line_no,
            source_path=self.source_path or source_path,
            source_line=self.source_line if self.source_line is not None else source_line,
        )

    def __str__(self) -> str:
        location: str | None = None
        if self.source_path is not None and self.line_no is not None:
            location = f"{self.source_path}:{self.line_no}"
        elif self.line_no is not None:
            location = f"line {self.line_no}"
        elif self.source_path is not None:
            location = str(self.source_path)

        text = f"{location}: {self.message}" if location is not None else self.message
        if self.source_line:
            text += f"\n    {self.source_line}"
        return text


def lookup_source_line(lines: list[str], line_no: int | None) -> str | None:
    if line_no is None or not 1 <= line_no <= len(lines):
        return None
    return lines[line_no - 1]


RegisterValue = RegisterOperand


# Materialized segment ready to be written into an object file.
@dataclass(frozen=True)
class AssembledSegment:
    mode: str
    data: bytes
    load_address: int
    alignment: int


# Instruction match shared across layout, fixups, and encoding.
@dataclass(frozen=True)
class MatchedInstruction:
    line_no: int
    form: RuntimeForm | None = None
    pattern: RuntimePattern | None = None
    inputs: dict[str, Any] | None = None
    derived: dict[str, Any] | None = None
    words: list[int] | None = None


BlockKind = Literal["code", "data"]
FixupKind = Literal["absolute", "pcrel"]


# Exact source location kept on IR nodes for diagnostics and listings.
@dataclass(frozen=True)
class SourceRef:
    line_no: int
    source_path: Path | None = None
    text: str | None = None


# Closed numeric value already known during assembly.
@dataclass(frozen=True)
class IntValue:
    value: int


# Named constant reference used inside deferred symbolic addends.
@dataclass(frozen=True)
class ConstantRef:
    name: str
    sign: int = 1


# Symbolic reference that will be resolved later, optionally with an addend.
@dataclass(frozen=True)
class SymbolRef:
    name: str
    addend: int | ConstantRef = 0


# Symbolic value that must fit in a signed field before encoding.
@dataclass(frozen=True)
class SignedSymbolRef:
    symbol: SymbolRef
    bits: int
    sign: int = 1


# Slice of a wider symbolic value used when the encoding splits it across fields.
@dataclass(frozen=True)
class SymbolSliceRef:
    symbol: SymbolRef
    source_bits: int
    msb: int
    lsb: int


# PC-relative symbolic reference resolved against the current instruction address.
@dataclass(frozen=True)
class PcRelativeRef:
    symbol: SymbolRef
    bits: int
    origin_bias: int


# Expression accepted by data directives and symbolic instruction operands.
ValueExpr = IntValue | SymbolRef


# Label anchored at the current offset inside a block.
@dataclass(frozen=True)
class LabelItem:
    name: str
    source: SourceRef


# Raw bytes already materialized by the frontend, such as byte/file payloads.
@dataclass(frozen=True)
class BytesItem:
    data: bytes
    source: SourceRef


# Sequence of 16-bit values that may still reference symbols.
@dataclass(frozen=True)
class WordItem:
    values: list[ValueExpr]
    source: SourceRef


# Sequence of 24-bit addresses that may still reference symbols.
@dataclass(frozen=True)
class AddrItem:
    values: list[ValueExpr]
    source: SourceRef


# Repeated byte fill used for padding or zero-initialized gaps.
@dataclass(frozen=True)
class FillItem:
    count: int
    byte_value: int
    source: SourceRef


# Alignment request that advances the offset to the next matching boundary.
@dataclass(frozen=True)
class AlignItem:
    alignment: int
    source: SourceRef


# Instruction item carrying its current size and, when available, a matched ISA form.
@dataclass(frozen=True)
class InstrItem:
    source: SourceRef
    size_bytes: int
    match: MatchedInstruction | None = None


# Any item that may appear inside a code or data block.
BlockItem = LabelItem | BytesItem | WordItem | AddrItem | FillItem | AlignItem | InstrItem


# Ordered block of code or data exactly as it appears in the source.
@dataclass(frozen=True)
class BlockIR:
    kind: BlockKind
    items: list[BlockItem]


# Whole assembled module before layout resolution and object emission.
@dataclass(frozen=True)
class ModuleIR:
    blocks: list[BlockIR]
    exports: list[str]


# Patch site that must be resolved after layout for symbolic references.
@dataclass(frozen=True)
class Fixup:
    kind: FixupKind
    block_index: int
    offset_in_block: int
    container_bytes: int
    field_lsb: int
    field_bits: int
    symbol: str
    addend: int = 0
    symbol_sign: int = 1
    value_lsb: int = 0
    value_bits: int | None = None
    signed: bool = False
    base_offset_in_block: int = 0
    origin_bias: int = 0
    max_value: int | None = None
    label: str = "value"
    source: SourceRef | None = None


# Transitional preprocessed state that now carries ModuleIR plus resolved symbols.
@dataclass(frozen=True)
class PreparedAssembly:
    symbols: dict[str, int]
    relocatable_symbols: set[str]
    exports: dict[str, int]
    imports: list[str]
    module_ir: ModuleIR
    source_lines: list[str]
    source_path: Path | None
    base_dir: Path
