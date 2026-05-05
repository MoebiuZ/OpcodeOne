# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from .api import (
    ASSEMBLER_VERSION,
    IMPLEMENTATION_NAME,
    JsonAssembler,
    assemble_exports,
    assemble_line,
    assemble_object,
    assemble_object_bytes,
    assemble_segments,
    assemble_source,
    default_output_path,
    format_payload_size,
    format_words,
)
from .cli import main
from .constants import DEFAULT_OPCODE_MAP
from .model import (
    AddrItem,
    AlignItem,
    AssemblerError,
    BlockIR,
    BytesItem,
    ConstantRef,
    FillItem,
    Fixup,
    InstrItem,
    IntValue,
    LabelItem,
    MatchedInstruction,
    ModuleIR,
    PcRelativeRef,
    PreparedAssembly,
    SignedSymbolRef,
    SourceRef,
    SymbolRef,
    SymbolSliceRef,
    WordItem,
)
try:
    from common.opcodeone_operands import MemoryOperand, RegisterOperand
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_operands import MemoryOperand, RegisterOperand

__all__ = [
    "ASSEMBLER_VERSION",
    "IMPLEMENTATION_NAME",
    "DEFAULT_OPCODE_MAP",
    "AddrItem",
    "AlignItem",
    "AssemblerError",
    "BlockIR",
    "BytesItem",
    "ConstantRef",
    "FillItem",
    "Fixup",
    "InstrItem",
    "IntValue",
    "JsonAssembler",
    "LabelItem",
    "MatchedInstruction",
    "MemoryOperand",
    "ModuleIR",
    "PcRelativeRef",
    "PreparedAssembly",
    "RegisterOperand",
    "SignedSymbolRef",
    "SourceRef",
    "SymbolRef",
    "SymbolSliceRef",
    "WordItem",
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
