# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import sys

from .constants import DISASSEMBLER_VERSION
from .formatting import format_source
from .io import read_interactive_input, read_legacy_input, read_object_input
from .listing import disassemble_listing_relaxed, disassemble_object_listing
from .model import DisassemblerError
from .viewer import interactive_disassembly_viewer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reference disassembler for the currently closed OpcodeOne ISA families")
    parser.add_argument("--version", action="version", version=f"%(prog)s {DISASSEMBLER_VERSION}")
    parser.add_argument("source", nargs="?", help="Object file or text word listing. Reads stdin when omitted.")
    parser.add_argument("-b", "--binary", action="store_true", help="Use legacy raw/text heuristics instead of the O1OB object container.")
    parser.add_argument("--input-format", choices=("auto", "raw", "text"), default="auto", help="How to interpret legacy -b input. 'raw' expects little-endian 16-bit words.")
    parser.add_argument("--compact", action="store_true", help="Render the documented non-normative compact syntax instead of canonical syntax.")
    dump_group = parser.add_mutually_exclusive_group()
    dump_group.add_argument("--dump", action="store_true", help="Dump the disassembly to stdout without addresses.")
    dump_group.add_argument("--dump-with-addr", action="store_true", help="Dump the disassembly to stdout with addresses.")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    surface = "compact" if args.compact else "canonical"

    try:
        if args.dump or args.dump_with_addr:
            if args.binary:
                words = read_legacy_input(args.source, args.input_format)
                listing = disassemble_listing_relaxed(words, raw_mode=args.dump_with_addr, surface=surface)
            else:
                listing = disassemble_object_listing(read_object_input(args.source), raw_mode=args.dump_with_addr, surface=surface)
            print(format_source(listing, show_addresses=args.dump_with_addr))
            return 0

        if args.binary and args.source:
            words = read_legacy_input(args.source, args.input_format)
            listing_plain = disassemble_listing_relaxed(words, raw_mode=False, surface="canonical")
            listing_raw = disassemble_listing_relaxed(words, raw_mode=True, surface="canonical")
            listing_plain_compact = disassemble_listing_relaxed(words, raw_mode=False, surface="compact")
            listing_raw_compact = disassemble_listing_relaxed(words, raw_mode=True, surface="compact")
            interactive_disassembly_viewer(
                listing_plain,
                listing_raw,
                args.source,
                compact_listing_plain=listing_plain_compact,
                compact_listing_raw=listing_raw_compact,
                initial_surface=surface,
            )
            return 0

        if (not args.binary) and args.source:
            obj = read_object_input(args.source)
            listing_plain = disassemble_object_listing(obj, raw_mode=False, surface="canonical")
            listing_raw = disassemble_object_listing(obj, raw_mode=True, surface="canonical")
            listing_plain_compact = disassemble_object_listing(obj, raw_mode=False, surface="compact")
            listing_raw_compact = disassemble_object_listing(obj, raw_mode=True, surface="compact")
            interactive_disassembly_viewer(
                listing_plain,
                listing_raw,
                args.source,
                compact_listing_plain=listing_plain_compact,
                compact_listing_raw=listing_raw_compact,
                initial_surface=surface,
            )
            return 0

        input_data, source_name = read_interactive_input(args.binary, args.input_format)
        if args.binary:
            words = input_data
            listing_plain = disassemble_listing_relaxed(words, raw_mode=False, surface="canonical")
            listing_raw = disassemble_listing_relaxed(words, raw_mode=True, surface="canonical")
            listing_plain_compact = disassemble_listing_relaxed(words, raw_mode=False, surface="compact")
            listing_raw_compact = disassemble_listing_relaxed(words, raw_mode=True, surface="compact")
        else:
            obj = input_data
            listing_plain = disassemble_object_listing(obj, raw_mode=False, surface="canonical")
            listing_raw = disassemble_object_listing(obj, raw_mode=True, surface="canonical")
            listing_plain_compact = disassemble_object_listing(obj, raw_mode=False, surface="compact")
            listing_raw_compact = disassemble_object_listing(obj, raw_mode=True, surface="compact")
        interactive_disassembly_viewer(
            listing_plain,
            listing_raw,
            source_name,
            compact_listing_plain=listing_plain_compact,
            compact_listing_raw=listing_raw_compact,
            initial_surface=surface,
        )
        return 0
    except (DisassemblerError, OSError, UnicodeDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
