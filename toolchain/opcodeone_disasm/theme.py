# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import curses
import json
from pathlib import Path

from .constants import (
    CURSES_ATTR_NAMES,
    CURSES_COLOR_NAMES,
    DEFAULT_DISASM_THEME,
    THEME_TOKEN_KEYS,
)


def default_disasm_theme_path() -> Path:
    return Path(__file__).resolve().parent / "theme.json"


def deep_copy_theme(theme: dict[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in theme.items():
        if isinstance(value, dict):
            result[key] = deep_copy_theme(value)
        elif isinstance(value, list):
            result[key] = list(value)
        else:
            result[key] = value
    return result


def merge_theme(base: dict[str, object], override: dict[str, object]) -> dict[str, object]:
    merged = deep_copy_theme(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_theme(merged[key], value)  # type: ignore[arg-type]
        else:
            merged[key] = value
    return merged


def load_disasm_theme(path: Path | None = None) -> dict[str, object]:
    theme = deep_copy_theme(DEFAULT_DISASM_THEME)
    theme_path = path or default_disasm_theme_path()
    try:
        override = json.loads(theme_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return theme
    except json.JSONDecodeError:
        return theme
    if not isinstance(override, dict):
        return theme
    return merge_theme(theme, override)


def resolve_theme_color(spec: dict[str, object], key: str, colors_supported: int) -> int:
    if colors_supported >= 256 and f"{key}256" in spec:
        return int(spec[f"{key}256"])
    if key in spec:
        name = str(spec[key]).lower()
        return CURSES_COLOR_NAMES.get(name, -1)
    return -1


def resolve_theme_attrs(spec: dict[str, object]) -> int:
    value = curses.A_NORMAL
    for name in spec.get("attrs", []):
        value |= CURSES_ATTR_NAMES.get(str(name).lower(), curses.A_NORMAL)
    return value


def build_curses_theme(theme: dict[str, object]) -> tuple[dict[str, int], dict[str, int], int]:
    normal_map = {key: curses.A_NORMAL for key in THEME_TOKEN_KEYS}
    current_map = {key: curses.A_NORMAL for key in THEME_TOKEN_KEYS}
    status_attr = curses.A_REVERSE
    if not curses.has_colors():
        return normal_map, current_map, status_attr

    curses.start_color()
    curses.use_default_colors()
    colors_supported = curses.COLORS
    pair_id = 1
    current_spec = theme.get("ui", {}).get("current_line", {})
    current_bg = resolve_theme_color(current_spec, "bg", colors_supported)
    current_fg = resolve_theme_color(current_spec, "fg", colors_supported)
    current_base_attrs = resolve_theme_attrs(current_spec)

    for token in THEME_TOKEN_KEYS:
        spec = theme.get("tokens", {}).get(token, {})
        fg = resolve_theme_color(spec, "fg", colors_supported)
        bg = resolve_theme_color(spec, "bg", colors_supported)
        attrs = resolve_theme_attrs(spec)

        curses.init_pair(pair_id, fg, bg)
        normal_map[token] = curses.color_pair(pair_id) | attrs
        pair_id += 1

        effective_current_fg = current_fg if current_fg != -1 else fg
        effective_current_bg = current_bg if current_bg != -1 else bg
        curses.init_pair(pair_id, effective_current_fg, effective_current_bg)
        current_map[token] = curses.color_pair(pair_id) | attrs | current_base_attrs
        pair_id += 1

    status_spec = theme.get("ui", {}).get("status", {})
    status_fg = resolve_theme_color(status_spec, "fg", colors_supported)
    status_bg = resolve_theme_color(status_spec, "bg", colors_supported)
    curses.init_pair(pair_id, status_fg, status_bg)
    status_attr = curses.color_pair(pair_id) | resolve_theme_attrs(status_spec)
    return normal_map, current_map, status_attr
