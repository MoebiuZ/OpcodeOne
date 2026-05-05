# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

try:
    from common.opcodeone_object import ObjectFile, ObjectSegment, SEGMENT_TYPE_CODE, SEGMENT_TYPE_DATA, bytes_to_words
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_object import (
        ObjectFile,
        ObjectSegment,
        SEGMENT_TYPE_CODE,
        SEGMENT_TYPE_DATA,
        bytes_to_words,
    )

from .model import DisassembledLine, DisassemblerError


def _fmt_bytes(data: list[int]) -> str:
    return ", ".join(f"0x{b:02X}" for b in data)


def _raw_words_from_bytes(data: list[int]) -> tuple[int, ...]:
    if len(data) % 2:
        data = data + [0]
    return tuple(data[index] | (data[index + 1] << 8) for index in range(0, len(data), 2))


def data_listing_from_bytes(data_bytes: bytes, load_address: int, raw_mode: bool = False, *, leading_blank: bool = False) -> list[DisassembledLine]:
    if not data_bytes:
        return []
    lines: list[DisassembledLine] = [DisassembledLine(address=load_address, word_count=0, text="--DATA:")]
    chunk = 8
    all_bytes = list(data_bytes)
    byte_addr = load_address
    i = 0
    while i < len(all_bytes):
        data = all_bytes[i : i + chunk]
        hi = data[:4]
        lo = data[4:]
        wc = (len(data) + 1) // 2
        if raw_mode:
            lines.append(DisassembledLine(address=byte_addr, word_count=(len(hi) + 1) // 2, text="byte " + _fmt_bytes(hi), raw_words=_raw_words_from_bytes(hi)))
            if lo:
                lines.append(DisassembledLine(address=byte_addr + 4, word_count=(len(lo) + 1) // 2, text="#rcont:" + _fmt_bytes(lo), raw_words=_raw_words_from_bytes(lo)))
        else:
            lines.append(DisassembledLine(address=byte_addr, word_count=wc, text="byte " + _fmt_bytes(data), raw_words=_raw_words_from_bytes(data)))
        i += chunk
        byte_addr += chunk
    return lines


def data_listing_from_words(words: list[int], start_word: int, raw_mode: bool = False) -> list[DisassembledLine]:
    if start_word >= len(words):
        return []
    payload = bytearray()
    for index in range(start_word, len(words)):
        payload.extend(words[index].to_bytes(2, "little"))
    return data_listing_from_bytes(bytes(payload), start_word * 2, raw_mode, leading_blank=(start_word > 0))


def disassemble_listing_relaxed(words: list[int], raw_mode: bool = False, *, surface: str = "canonical") -> list[DisassembledLine]:
    from .decode import disassemble_listing, find_last_strict_prefix

    try:
        listing = disassemble_listing(words, surface=surface)
        if listing:
            listing.insert(0, DisassembledLine(address=0, word_count=0, text="--CODE:"))
        return listing
    except DisassemblerError:
        last_ok = find_last_strict_prefix(words)
        if last_ok == len(words):
            listing = disassemble_listing(words, surface=surface)
            if listing:
                listing.insert(0, DisassembledLine(address=0, word_count=0, text="--CODE:"))
            return listing
        listing = disassemble_listing(words[:last_ok], surface=surface) if last_ok else []
        if listing:
            listing.insert(0, DisassembledLine(address=0, word_count=0, text="--CODE:"))
        listing.extend(data_listing_from_words(words, last_ok, raw_mode))
        return listing


def disassemble_segment(segment: ObjectSegment, *, raw_mode: bool = False, surface: str = "canonical") -> list[DisassembledLine]:
    from .decode import disassemble_listing

    if segment.segment_type == SEGMENT_TYPE_CODE:
        lines = [DisassembledLine(address=segment.load_address, word_count=0, text="--CODE:")]
        lines.extend(disassemble_listing(bytes_to_words(segment.data), base_address=segment.load_address, surface=surface))
        return lines
    if segment.segment_type == SEGMENT_TYPE_DATA:
        return data_listing_from_bytes(segment.data, segment.load_address, raw_mode, leading_blank=True)
    raise DisassemblerError(f"unsupported object segment type {segment.segment_type}")


def disassemble_object_listing(obj: ObjectFile, *, raw_mode: bool = False, surface: str = "canonical") -> list[DisassembledLine]:
    listing: list[DisassembledLine] = []
    for segment in obj.segments:
        listing.extend(disassemble_segment(segment, raw_mode=raw_mode, surface=surface))
    return listing
