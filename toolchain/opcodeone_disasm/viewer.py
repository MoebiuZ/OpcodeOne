# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import curses
import time

from .constants import DISASSEMBLER_VERSION
from .formatting import display_address_prefix, format_hex, highlight_disassembly_text, segment_display_text
from .model import DisassembledLine, DisassemblerError
from .theme import build_curses_theme, load_disasm_theme


def interactive_disassembly_viewer(
    listing_plain: list[DisassembledLine],
    listing_raw: list[DisassembledLine],
    source_name: str,
    *,
    compact_listing_plain: list[DisassembledLine] | None = None,
    compact_listing_raw: list[DisassembledLine] | None = None,
    initial_surface: str = "canonical",
) -> None:
    theme = load_disasm_theme()

    def visual_rows_for(listing: list[DisassembledLine]) -> tuple[list[tuple[int | None, DisassembledLine | None]], dict[int, int]]:
        rows: list[tuple[int | None, DisassembledLine | None]] = []
        logical_to_visual: dict[int, int] = {}
        for logical_index, entry in enumerate(listing):
            if segment_display_text(entry.text) is not None and rows:
                rows.append((None, None))
            logical_to_visual[logical_index] = len(rows)
            rows.append((logical_index, entry))
        return rows, logical_to_visual

    def run(stdscr: curses.window) -> None:
        curses.curs_set(0)
        stdscr.keypad(True)
        top = 0
        current = 0
        show_addresses = True
        show_raw_words = False
        use_hex_immediates = True
        message = ""
        compact_available = compact_listing_plain is not None and compact_listing_raw is not None
        surface = initial_surface if compact_available and initial_surface == "compact" else "canonical"
        listings_by_surface = {
            "canonical": {
                "plain": listing_plain,
                "raw": listing_raw,
            },
            "compact": {
                "plain": compact_listing_plain if compact_available else listing_plain,
                "raw": compact_listing_raw if compact_available else listing_raw,
            },
        }
        listing = listings_by_surface[surface]["plain"]
        plain_raw_col_width = max(0, (max((len(entry.raw_words) for entry in listing_plain), default=0) * 5) - 1)
        raw_raw_col_width = max(0, (max((len(entry.raw_words) for entry in listing_raw), default=0) * 5) - 1)
        visual_rows, logical_to_visual = visual_rows_for(listing)
        color_map, current_color_map, status_attr = build_curses_theme(theme)

        def draw_highlighted(row: int, entry: DisassembledLine, width: int, is_current: bool) -> None:
            raw_col_width = raw_raw_col_width if show_raw_words else plain_raw_col_width
            if entry.text == "":
                return
            if is_current:
                stdscr.addnstr(row, 0, " " * (width - 1), width - 1, current_color_map["plain"])
            if entry.text.startswith("#rcont:"):
                col = 0
                if show_addresses:
                    col = len(display_address_prefix(entry.address))
                    stdscr.addnstr(row, 0, " " * col, col, color_map["plain"])
                if show_raw_words:
                    raw_str = (" ".join(f"{w:04X}" for w in entry.raw_words)).ljust(raw_col_width) + "  "
                    stdscr.addnstr(row, col, raw_str, max(0, width - col - 1), color_map["literal"])
                    col += len(raw_str)
                pad = " " * len("byte ")
                stdscr.addnstr(row, col, pad, max(0, width - col - 1), color_map["plain"])
                col += len(pad)
                byte_text = entry.text[7:]
                for token in highlight_disassembly_text(byte_text, use_hex_immediates):
                    if col >= width - 1:
                        break
                    stdscr.addnstr(row, col, token.text, max(0, width - col - 1), color_map[token.kind])
                    col += len(token.text)
                return
            segment_text = segment_display_text(entry.text)
            if segment_text is not None:
                active_colors = current_color_map if is_current else color_map
                stdscr.addnstr(row, 0, segment_text, max(0, width - 1), active_colors["segment"])
                return

            col = 0
            active_colors = current_color_map if is_current else color_map
            if show_addresses:
                prefix = display_address_prefix(entry.address)
                stdscr.addnstr(row, col, prefix, max(0, width - col), active_colors["address"])
                col += len(prefix)
            if show_raw_words and entry.raw_words:
                raw_str = (" ".join(f"{w:04X}" for w in entry.raw_words)).ljust(raw_col_width) + "  "
                stdscr.addnstr(row, col, raw_str, max(0, width - col - 1), active_colors["literal"])
                col += len(raw_str)
            for token in highlight_disassembly_text(entry.text, use_hex_immediates):
                if col >= width - 1:
                    break
                stdscr.addnstr(row, col, token.text, max(0, width - col - 1), active_colors[token.kind])
                col += len(token.text)

        def show_help() -> None:
            import random

            MOEBIUZ = "MoebiuZ"
            LEET: dict[str, list[str]] = {"o": ["0", "ö"], "O": ["0", "ö"], "i": ["1", "|", "!"], "I": ["1", "|", "!"], "e": ["3", "€"], "E": ["3", "€"]}
            leet_eligible = [(i, c) for i, c in enumerate(MOEBIUZ) if c in LEET]
            leet_map: dict[int, str] = {}
            lit_a = 0
            lit_b = 1
            attr_normal = color_map["address"]
            blue_b = 51 if curses.COLORS >= 256 else curses.COLOR_CYAN
            curses.init_pair(50, curses.COLOR_WHITE, -1)
            curses.init_pair(51, blue_b, -1)
            attr_light_a = curses.color_pair(50) | curses.A_BOLD
            attr_light_b = curses.color_pair(51)

            now = time.time()
            next_color_a = now + random.uniform(0.12, 0.22)
            next_color_b = now + random.uniform(0.18, 0.28)
            next_leet = now + random.uniform(0.3, 0.6)
            author_prefix = "by A. Rodriguez "
            author_suffix = ", 2026"

            lines: list[list[tuple[str, int]]] = [
                [(f"OpcodeOne Disassembler v{DISASSEMBLER_VERSION} (Apache-2.0)", color_map["mnemonic"])],
                [],
                [("", color_map["plain"])],
                [("Up / Down    ", color_map["condition"]), ("  move current line", color_map["plain"])],
                [("PageUp / Down", color_map["condition"]), ("  move by page", color_map["plain"])],
                [("Home / End   ", color_map["condition"]), ("  jump to top or bottom", color_map["plain"])],
                [("g            ", color_map["condition"]), ("  goto address", color_map["plain"])],
                [("a            ", color_map["condition"]), ("  toggle addresses", color_map["plain"])],
                [("i            ", color_map["condition"]), ("  toggle raw words", color_map["plain"])],
                [("c            ", color_map["condition"]), ("  toggle canonical/compact", color_map["plain"])],
                [("t            ", color_map["condition"]), ("  toggle immediates hex/dec", color_map["plain"])],
                [("h            ", color_map["condition"]), ("  show this help", color_map["plain"])],
                [("q            ", color_map["condition"]), ("  quit", color_map["plain"])],
                [("", color_map["plain"])],
                [("Press any key to close", color_map["extender"])],
            ]
            AUTHOR_ROW = 1

            def plain(line: list[tuple[str, int]]) -> str:
                return "".join(t for t, _ in line)

            plain_lengths = [
                len(author_prefix + MOEBIUZ + author_suffix) if i == AUTHOR_ROW else len(plain(line))
                for i, line in enumerate(lines)
            ]
            height, width = stdscr.getmaxyx()
            box_width = min(width - 4, max(plain_lengths) + 4)
            box_height = min(height - 2, len(lines) + 2)
            top_row = max(0, (height - box_height) // 2)
            left_col = max(0, (width - box_width) // 2)
            window = stdscr.derwin(box_height, box_width, top_row, left_col)
            window.keypad(True)
            window.nodelay(True)

            def draw_author(row_idx: int) -> None:
                col = 2
                avail = max(0, box_width - col - 2)
                window.addnstr(row_idx, col, author_prefix, avail, attr_normal)
                col += len(author_prefix)
                for i, ch in enumerate(MOEBIUZ):
                    if col >= box_width - 2:
                        break
                    display = leet_map.get(i, ch)
                    attr = attr_light_a if i == lit_a else attr_light_b if i == lit_b else attr_normal
                    try:
                        window.addch(row_idx, col, display, attr)
                    except curses.error:
                        pass
                    col += 1
                avail = max(0, box_width - col - 2)
                if avail > 0:
                    window.addnstr(row_idx, col, author_suffix, avail, attr_normal)

            while True:
                now = time.time()
                if now >= next_color_a:
                    lit_a = random.choice([i for i in range(len(MOEBIUZ)) if i != lit_b])
                    next_color_a = now + random.uniform(0.12, 0.22)
                if now >= next_color_b:
                    lit_b = random.choice([i for i in range(len(MOEBIUZ)) if i != lit_a])
                    next_color_b = now + random.uniform(0.18, 0.28)
                if now >= next_leet and leet_eligible:
                    idx, ch = random.choice(leet_eligible)
                    if idx in leet_map:
                        del leet_map[idx]
                    else:
                        leet_map[idx] = random.choice(LEET[ch])
                    next_leet = now + random.uniform(0.3, 0.6)

                window.erase()
                window.box()
                for row_idx, line in enumerate(lines[: box_height - 2], start=1):
                    if row_idx - 1 == AUTHOR_ROW:
                        draw_author(row_idx)
                    else:
                        col = 2
                        for text, attr in line:
                            avail = max(0, box_width - col - 2)
                            if avail <= 0:
                                break
                            window.addnstr(row_idx, col, text, avail, attr)
                            col += len(text)
                window.refresh()
                time.sleep(0.05)
                if window.getch() != -1:
                    break
            window.nodelay(False)

        def goto_address(target: int, body_height: int) -> int:
            if target < 0:
                raise DisassemblerError("address must be non-negative")
            for index, entry in enumerate(listing):
                start = entry.address
                end = start + (entry.word_count * 2)
                if start <= target < end:
                    return index
            raise DisassemblerError(f"address {format_hex(target, 6)} is outside the listing")

        def prompt_goto() -> str | None:
            prompt = "goto address: "
            curses.curs_set(1)
            curses.echo()
            try:
                height, width = stdscr.getmaxyx()
                stdscr.move(height - 1, 0)
                stdscr.clrtoeol()
                stdscr.addnstr(height - 1, 0, prompt, max(1, width - 1), curses.A_REVERSE)
                stdscr.refresh()
                raw = stdscr.getstr(height - 1, len(prompt), max(1, width - len(prompt) - 1))
            finally:
                curses.noecho()
                curses.curs_set(0)
            if raw is None:
                return None
            return raw.decode("utf-8", errors="ignore").strip()

        while True:
            height, width = stdscr.getmaxyx()
            body_height = max(1, height - 1)
            max_index = max(0, len(listing) - 1)
            current = max(0, min(current, max_index))
            visual_rows, logical_to_visual = visual_rows_for(listing)
            current_visual = logical_to_visual.get(current, 0)
            max_top = max(0, len(visual_rows) - body_height)
            if current_visual < top:
                top = current_visual
            elif current_visual >= top + body_height:
                top = current_visual - body_height + 1
            top = max(0, min(top, max_top))

            stdscr.erase()
            visible = visual_rows[top : top + body_height]
            for row, (logical_index, entry) in enumerate(visible):
                if entry is None:
                    continue
                draw_highlighted(row, entry, width, logical_index == current)

            imm_fmt = "hex" if use_hex_immediates else "dec"
            surface_label = "compact" if surface == "compact" else "canonical"
            status = (
                f"{source_name}  line {current + 1}/{len(listing)}  "
                f"Up/Down scroll  PgUp/PgDn page  g goto  a addr  i words  c surface:{surface_label}  t imm:{imm_fmt}  h help  q quit"
            )
            if message:
                status = f"{status}  {message}"
            stdscr.addnstr(height - 1, 0, status, max(1, width - 1), status_attr)
            stdscr.refresh()

            key = stdscr.getch()
            message = ""
            if key in {ord("q"), ord("Q")}:
                return
            if key in {ord("a"), ord("A")}:
                show_addresses = not show_addresses
                continue
            if key in {ord("i"), ord("I")}:
                old_addr = listing[current].address
                show_raw_words = not show_raw_words
                listing = listings_by_surface[surface]["raw" if show_raw_words else "plain"]
                current = next(
                    (i for i, e in enumerate(listing) if e.address >= old_addr and e.text not in {"", "--DATA:", "--CODE:"} and not e.text.startswith("#rcont:")),
                    0,
                )
                continue
            if key in {ord("c"), ord("C")}:
                if not compact_available:
                    message = "compact surface is not available"
                    continue
                old_addr = listing[current].address
                surface = "compact" if surface == "canonical" else "canonical"
                listing = listings_by_surface[surface]["raw" if show_raw_words else "plain"]
                current = next(
                    (i for i, e in enumerate(listing) if e.address >= old_addr and e.text not in {"", "--DATA:", "--CODE:"} and not e.text.startswith("#rcont:")),
                    0,
                )
                continue
            if key in {ord("t"), ord("T")}:
                use_hex_immediates = not use_hex_immediates
                continue
            if key in {ord("h"), ord("H")}:
                show_help()
                continue
            if key in {ord("g"), ord("G")}:
                try:
                    raw = prompt_goto()
                    if not raw:
                        continue
                    current = goto_address(int(raw, 0), body_height)
                except (ValueError, DisassemblerError) as exc:
                    message = str(exc)
                continue
            if key == curses.KEY_UP:
                current = max(0, current - 1)
                continue
            if key == curses.KEY_DOWN:
                current = min(max_index, current + 1)
                continue
            if key == curses.KEY_PPAGE:
                current = max(0, current - body_height)
                continue
            if key == curses.KEY_NPAGE:
                current = min(max_index, current + body_height)
                continue
            if key == curses.KEY_HOME:
                current = 0
                continue
            if key == curses.KEY_END:
                current = max_index

    curses.wrapper(run)
