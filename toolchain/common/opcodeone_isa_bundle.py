# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GENERATED_BUNDLE = (PROJECT_ROOT / "isa/v0.9/generated/opcodeone_isa_v0.9.full.json").resolve()


def load_generated_bundle(path: Path = DEFAULT_GENERATED_BUNDLE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_default_bundle() -> dict[str, Any]:
    return load_generated_bundle(DEFAULT_GENERATED_BUNDLE)


__all__ = [
    "DEFAULT_GENERATED_BUNDLE",
    "load_default_bundle",
    "load_generated_bundle",
]
