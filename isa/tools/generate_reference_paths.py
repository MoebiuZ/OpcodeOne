#!/usr/bin/env python3
# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0
"""Generate reference path timing entries from the RP2350 O3+LTO benchmark run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS = (
    PROJECT_ROOT
    / "superchocopico/cchip/docs/benchmarks/2026-04-23-pico-path-multiopt/o3-lto-rerun/results.json"
).resolve()
DEFAULT_TIMING_MODEL = (PROJECT_ROOT / "isa/v0.9/timing_model.json").resolve()
DEFAULT_MODEL_NOTES = [
    "This timing model uses integer picoseconds frozen from the latest 2026-04-23 RP2350 O3+LTO reference VM rerun.",
    "In the current canonical model, 1 chronon equals 1 measured picosecond on the reference VM implementation.",
    "paths contains the canonical exact per-path chronons from the reference run and is the complete timing view.",
    "Instruction forms derive their timing from the exact paths that reference the same family and form.",
]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str((PROJECT_ROOT / "superchocopico/cchip/tools").resolve()) not in sys.path:
    sys.path.insert(0, str((PROJECT_ROOT / "superchocopico/cchip/tools").resolve()))

import pico_cchip_path_benchmarks as path_benchmarks  # noqa: E402


def _entry(
    *,
    name: str,
    path_id: int,
    path_id_name: str,
    family: str,
    form: str,
    chronons: int,
    reference_asm: list[str],
    conditions: dict[str, Any],
) -> dict[str, Any]:
    return {
        "name": name,
        "path_id": path_id,
        "path_id_name": path_id_name,
        "family": family,
        "form": form,
        "chronons": chronons,
        "reference_asm": reference_asm,
        "conditions": conditions,
    }


def _condition_variant_from_text(condition_text: str) -> str:
    tokens = condition_text.split()
    if len(tokens) < 3:
        raise ValueError(f"invalid jump condition text: {condition_text}")
    return "_".join(token.lower() for token in tokens[1:-1])


def _movecopy_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    name = result["name"]
    if name.startswith("movecopy_copy_") or name.startswith("movecopy_move_"):
        _, operation, src_width, _, dest_width = name.split("_")
        return _entry(
            name=name,
            path_id=result["path_id"],
            path_id_name=result["path_id_name"],
            family="MOVECOPY",
            form="copy_or_move",
            chronons=chronons,
            reference_asm=reference_asm,
            conditions={
                "operation": operation,
                "src_width_bits": int(src_width),
                "dest_width_bits": int(dest_width),
            },
        )
    if name.startswith("movecopy_swap_"):
        _, _, width = name.split("_")
        return _entry(
            name=name,
            path_id=result["path_id"],
            path_id_name=result["path_id_name"],
            family="MOVECOPY",
            form="swap",
            chronons=chronons,
            reference_asm=reference_asm,
            conditions={"width_bits": int(width)},
        )

    special_forms = {
        "movecopy_special_from_k": ("copy_k_into_reg24", "K", "from_special"),
        "movecopy_special_from_sp": ("copy_sp_into_reg24", "SP", "from_special"),
        "movecopy_special_from_pc": ("copy_pc_into_reg24", "PC", "from_special"),
        "movecopy_special_to_k": ("copy_reg24_into_k", "K", "to_special"),
        "movecopy_special_to_sp": ("copy_reg24_into_sp", "SP", "to_special"),
    }
    form, special_register, direction = special_forms[name]
    return _entry(
        name=name,
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="MOVECOPY",
        form=form,
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={
            "special_register": special_register,
            "direction": direction,
        },
    )


def _stack_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    _, operation, width = result["name"].split("_")
    return _entry(
        name=result["name"],
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="STACK",
        form=f"{operation}_reg{width}",
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={
            "operation": operation,
            "width_bits": int(width),
        },
    )


def _flow_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    form_map = {
        "flow_enter_abs": "enter_addr",
        "flow_enter_reg": "enter_reg24",
        "flow_leave": "leave",
        "flow_leave_interrupt": "leave_interrupt",
    }
    asm_defaults = {
        "flow_enter_abs": ["ENTER 0x00F004"],
        "flow_enter_reg": ["ENTER X"],
        "flow_leave": ["LEAVE"],
        "flow_leave_interrupt": ["LEAVE interruption"],
    }
    return _entry(
        name=result["name"],
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="FLOW",
        form=form_map[result["name"]],
        chronons=chronons,
        reference_asm=reference_asm or asm_defaults[result["name"]],
        conditions={"operation": result["name"].removeprefix("flow_")},
    )


def _plus_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    name = result["name"]
    if "_imm6_" in name:
        width = int(name.rsplit("_", 1)[1])
        return _entry(
            name=name,
            path_id=result["path_id"],
            path_id_name=result["path_id_name"],
            family="PLUS",
            form="imm6",
            chronons=chronons,
            reference_asm=reference_asm,
            conditions={"width_bits": width, "immediate_bits": 6},
        )
    if "_imm16_" in name:
        width = int(name.rsplit("_", 1)[1])
        return _entry(
            name=name,
            path_id=result["path_id"],
            path_id_name=result["path_id_name"],
            family="PLUS",
            form="imm16",
            chronons=chronons,
            reference_asm=reference_asm,
            conditions={"width_bits": width, "immediate_bits": 16},
        )

    modifier = "normal"
    width = int(name.rsplit("_", 1)[1])
    if "keep_and_use_carry" in name:
        modifier = "keep_and_use_carry"
    elif "keep_carry" in name:
        modifier = "keep_carry"
    elif "use_carry" in name:
        modifier = "use_carry"
    return _entry(
        name=name,
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="PLUS",
        form="reg_reg",
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={"width_bits": width, "modifier": modifier},
    )


def _minus_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    name = result["name"]
    if "_imm6_" in name:
        width = int(name.rsplit("_", 1)[1])
        return _entry(
            name=name,
            path_id=result["path_id"],
            path_id_name=result["path_id_name"],
            family="MINUS",
            form="imm6",
            chronons=chronons,
            reference_asm=reference_asm,
            conditions={"width_bits": width, "immediate_bits": 6},
        )
    if "_imm16_" in name:
        width = int(name.rsplit("_", 1)[1])
        return _entry(
            name=name,
            path_id=result["path_id"],
            path_id_name=result["path_id_name"],
            family="MINUS",
            form="imm16",
            chronons=chronons,
            reference_asm=reference_asm,
            conditions={"width_bits": width, "immediate_bits": 16},
        )

    modifier = "normal"
    width = int(name.rsplit("_", 1)[1])
    if "keep_and_use_borrow" in name:
        modifier = "keep_and_use_borrow"
    elif "keep_borrow" in name:
        modifier = "keep_borrow"
    elif "use_borrow" in name:
        modifier = "use_borrow"
    return _entry(
        name=name,
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="MINUS",
        form="reg_reg",
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={"width_bits": width, "modifier": modifier},
    )


def _set_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    name = result["name"]
    if "_imm6_" in name:
        width = int(name.rsplit("_", 1)[1])
        form = "imm6"
        immediate_bits = 6
    else:
        width = int(name.rsplit("_", 1)[1])
        form = "imm16"
        immediate_bits = 16
    return _entry(
        name=name,
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="SET",
        form=form,
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={"width_bits": width, "immediate_bits": immediate_bits},
    )


def _logic_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    name = result["name"]
    parts = name.split("_")
    operation = parts[1]
    width = int(parts[-1])
    if "imm16" in parts:
        return _entry(
            name=name,
            path_id=result["path_id"],
            path_id_name=result["path_id_name"],
            family="LOGIC",
            form="imm16",
            chronons=chronons,
            reference_asm=reference_asm,
            conditions={"operation": operation, "width_bits": width, "immediate_bits": 16},
        )
    return _entry(
        name=name,
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="LOGIC",
        form="reg_reg_or_not",
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={"operation": operation, "width_bits": width},
    )


def _bit_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    _, operation, width = result["name"].split("_")
    return _entry(
        name=result["name"],
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="BIT",
        form="bit_op",
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={"operation": operation, "width_bits": int(width)},
    )


def _minmax_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    _, operation, signedness, width = result["name"].split("_")
    return _entry(
        name=result["name"],
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="MINMAX",
        form="minmax_reg_reg",
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={"operation": operation, "signedness": signedness, "width_bits": int(width)},
    )


def _times_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    name = result["name"]
    signedness = "unsigned" if "unsigned" in name else "signed"
    keep_high = "keep_high" in name
    width = int(name.rsplit("_", 1)[1])
    return _entry(
        name=name,
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="TIMES",
        form="times_reg_reg",
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={
            "signedness": signedness,
            "width_bits": width,
            "keep_high": keep_high,
        },
    )


def _div_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    name = result["name"]
    parts = name.split("_")
    operation = "module" if parts[0] == "module" else "div"
    signedness = parts[1]
    width = int(parts[2])
    return _entry(
        name=name,
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="DIV",
        form="div_or_module",
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={
            "operation": operation,
            "signedness": signedness,
            "width_bits": width,
        },
    )


def _unary_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    _, operation, width = result["name"].split("_")
    return _entry(
        name=result["name"],
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="UNARY",
        form="unary_reg",
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={"operation": operation, "width_bits": int(width)},
    )


def _shift_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    name = result["name"]
    width = int(name.rsplit("_", 1)[1])

    if "_carry_step_" in name:
        direction = name.removeprefix("shift_").split("_carry_step_", 1)[0]
        keep_token = name.split("_carry_step_", 1)[1].rsplit("_", 1)[0]
        carry_mode = {
            "use": "use_carry",
            "keep": "keep_and_use_carry",
        }[keep_token]
        return _entry(
            name=name,
            path_id=result["path_id"],
            path_id_name=result["path_id_name"],
            family="SHIFT",
            form="carry_step",
            chronons=chronons,
            reference_asm=reference_asm,
            conditions={
                "direction": direction,
                "width_bits": width,
                "count_source": "immediate_one",
                "carry_mode": carry_mode,
            },
        )

    regcount_prefix = name.removeprefix("shift_").rsplit("_", 1)[0]
    direction = regcount_prefix.removesuffix("_keep_carry_regcount").removesuffix("_regcount")
    carry_mode = "keep_carry" if "_keep_carry_regcount_" in name else "normal"
    return _entry(
        name=name,
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="SHIFT",
        form="reg_count",
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={
            "direction": direction,
            "width_bits": width,
            "count_source": "register",
            "carry_mode": carry_mode,
        },
    )


def _rotate_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    _, direction, width = result["name"].split("_")
    return _entry(
        name=result["name"],
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="ROTATE",
        form="rotate_reg_reg",
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={"direction": direction, "width_bits": int(width)},
    )


def _jump_entry(result: dict[str, Any], reference_asm: list[str], chronons: int, condition_text: str) -> dict[str, Any]:
    name = result["name"]
    if name == "jump_abs":
        return _entry(
            name=name,
            path_id=result["path_id"],
            path_id_name=result["path_id_name"],
            family="JABS",
            form="jump_abs",
            chronons=chronons,
            reference_asm=reference_asm or ["JUMP 0x00F004"],
            conditions={"target_kind": "addr24"},
        )
    if name == "jump_reg":
        return _entry(
            name=name,
            path_id=result["path_id"],
            path_id_name=result["path_id_name"],
            family="JREG",
            form="jump_reg",
            chronons=chronons,
            reference_asm=reference_asm or ["JUMP X"],
            conditions={"target_kind": "reg24"},
        )

    prefix = "jump_conditional_"
    remainder = name.removeprefix(prefix)
    if remainder.endswith("_not_taken"):
        branch_taken = False
        descriptor = remainder.removesuffix("_not_taken")
    elif remainder.endswith("_taken"):
        branch_taken = True
        descriptor = remainder.removesuffix("_taken")
    else:
        raise ValueError(f"unsupported jump conditional path name: {name}")

    if "_" in descriptor:
        condition_variant, width_text = descriptor.rsplit("_", 1)
    else:
        condition_variant = _condition_variant_from_text(condition_text)
        width_text = descriptor
    return _entry(
        name=name,
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="JCOND",
        form="jump_conditional_relative",
        chronons=chronons,
        reference_asm=reference_asm or [f"JUMP +4 when {condition_text}"],
        conditions={
            "width_bits": int(width_text),
            "branch_taken": branch_taken,
            "condition_variant": condition_variant,
        },
    )


def _memabs_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    _, _, width_token, access = result["name"].split("_")
    width_bits = 8 if width_token == "byte" else int(width_token.removeprefix("reg"))
    family = {
        8: "MEMABS8",
        16: "MEMABS16",
        24: "MEMABS24",
    }[width_bits]
    form = {
        (8, "read"): "takeabs_byte",
        (8, "write"): "giveabs_byte",
        (16, "read"): "takeabs_reg16",
        (16, "write"): "giveabs_reg16",
        (24, "read"): "takeabs_reg24",
        (24, "write"): "giveabs_reg24",
    }[(width_bits, access)]
    return _entry(
        name=result["name"],
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family=family,
        form=form,
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={"addressing": "[addr24]", "access": access, "width_bits": width_bits},
    )


def _memregoff_entry(result: dict[str, Any], reference_asm: list[str], chronons: int) -> dict[str, Any]:
    _, mode, width_token, access = result["name"].split("_")
    width_bits = 8 if width_token == "byte" else int(width_token.removeprefix("reg"))
    if mode == "indirect":
        form = {
            (8, "read"): "take_indirect_byte",
            (8, "write"): "give_indirect_byte",
            (16, "read"): "take_indirect_reg16",
            (16, "write"): "give_indirect_reg16",
            (24, "read"): "take_indirect_reg24",
            (24, "write"): "give_indirect_reg24",
        }[(width_bits, access)]
        addressing = "[reg24]"
    else:
        form = {
            (8, "read"): "take_regoff_byte",
            (8, "write"): "give_regoff_byte",
            (16, "read"): "take_regoff_reg16",
            (16, "write"): "give_regoff_reg16",
            (24, "read"): "take_regoff_reg24",
            (24, "write"): "give_regoff_reg24",
        }[(width_bits, access)]
        addressing = "[reg24+off16_signed]"
    return _entry(
        name=result["name"],
        path_id=result["path_id"],
        path_id_name=result["path_id_name"],
        family="MEMREGOFF",
        form=form,
        chronons=chronons,
        reference_asm=reference_asm,
        conditions={"addressing": addressing, "access": access, "width_bits": width_bits},
    )


def map_result(result: dict[str, Any], spec: path_benchmarks.PathBenchmarkSpec) -> dict[str, Any]:
    current_path = path_benchmarks.PATH_CYCLE_IDS_BY_NAME[spec.path_id_name]
    normalized_result = dict(result)
    normalized_result["name"] = current_path.label
    normalized_result["path_id"] = current_path.id
    normalized_result["path_id_name"] = spec.path_id_name
    name = normalized_result["name"]
    chronons = int(round(result["entry"]["average_ps"]))
    reference_asm = list(spec.body_lines)

    if name.startswith("system_"):
        operation = name.removeprefix("system_")
        form = {
            "pass": "pass",
            "stop": "stop",
            "interruptions_on": "interruptions_on",
            "interruptions_off": "interruptions_off",
        }[operation]
        return _entry(
            name=name,
            path_id=normalized_result["path_id"],
            path_id_name=normalized_result["path_id_name"],
            family="SYSTEM",
            form=form,
            chronons=chronons,
            reference_asm=reference_asm,
            conditions={"operation": operation},
        )
    if name.startswith("movecopy_"):
        return _movecopy_entry(normalized_result, reference_asm, chronons)
    if name.startswith("stack_"):
        return _stack_entry(normalized_result, reference_asm, chronons)
    if name.startswith("flow_"):
        return _flow_entry(normalized_result, reference_asm, chronons)
    if name.startswith("plus_"):
        return _plus_entry(normalized_result, reference_asm, chronons)
    if name.startswith("minus_"):
        return _minus_entry(normalized_result, reference_asm, chronons)
    if name.startswith("set_"):
        return _set_entry(normalized_result, reference_asm, chronons)
    if name.startswith("logic_"):
        return _logic_entry(normalized_result, reference_asm, chronons)
    if name.startswith("bit_"):
        return _bit_entry(normalized_result, reference_asm, chronons)
    if name.startswith("minmax_"):
        return _minmax_entry(normalized_result, reference_asm, chronons)
    if name.startswith("times_"):
        return _times_entry(normalized_result, reference_asm, chronons)
    if name.startswith("div_") or name.startswith("module_"):
        return _div_entry(normalized_result, reference_asm, chronons)
    if name.startswith("unary_"):
        return _unary_entry(normalized_result, reference_asm, chronons)
    if name.startswith("shift_"):
        return _shift_entry(normalized_result, reference_asm, chronons)
    if name.startswith("rotate_"):
        return _rotate_entry(normalized_result, reference_asm, chronons)
    if name.startswith("jump_"):
        return _jump_entry(normalized_result, reference_asm, chronons, spec.condition_text)
    if name.startswith("mem_abs_"):
        return _memabs_entry(normalized_result, reference_asm, chronons)
    if name.startswith("mem_indirect_") or name.startswith("mem_regoff_"):
        return _memregoff_entry(normalized_result, reference_asm, chronons)
    raise ValueError(f"unsupported reference path name: {name}")


def _expand_legacy_jump_result(
    result: dict[str, Any],
    specs_by_name: dict[str, path_benchmarks.PathBenchmarkSpec],
) -> list[dict[str, Any]]:
    name = result["name"]
    if not name.startswith("jump_conditional_"):
        return []

    remainder = name.removeprefix("jump_conditional_")
    if remainder.endswith("_not_taken"):
        branch_suffix = "NOT_TAKEN"
        width_text = remainder.removesuffix("_not_taken")
    elif remainder.endswith("_taken"):
        branch_suffix = "TAKEN"
        width_text = remainder.removesuffix("_taken")
    else:
        return []

    if width_text not in {"16", "24"}:
        return []

    expanded: list[dict[str, Any]] = []
    for condition_variant in ("EQUAL", "LESS_THAN", "BELOW", "CHECK"):
        path_id_name = f"JUMP_CONDITIONAL_{condition_variant}_{width_text}_{branch_suffix}"
        path_id = path_benchmarks.PATH_CYCLE_IDS_BY_NAME[path_id_name]
        spec = specs_by_name[path_id.label]
        synthetic_result = dict(result)
        synthetic_result["name"] = path_id.label
        synthetic_result["path_id"] = path_id.id
        synthetic_result["path_id_name"] = path_id_name
        expanded.append(map_result(synthetic_result, spec))
    return expanded


def generate_paths(results_path: Path) -> list[dict[str, Any]]:
    results = json.loads(results_path.read_text(encoding="utf-8"))
    specs_by_name = path_benchmarks.path_benchmark_specs_by_name()
    paths: list[dict[str, Any]] = []
    for result in results:
        spec = specs_by_name.get(result["name"])
        if spec is not None:
            paths.append(map_result(result, spec))
            continue

        expanded_jump_paths = _expand_legacy_jump_result(result, specs_by_name)
        if expanded_jump_paths:
            paths.extend(expanded_jump_paths)
            continue

        raise ValueError(f"unsupported reference path name: {result['name']}")
    paths.sort(key=lambda item: item["path_id"])
    return paths


def generate_timing_model(results_path: Path, timing_model_path: Path = DEFAULT_TIMING_MODEL) -> dict[str, Any]:
    timing_model = json.loads(timing_model_path.read_text(encoding="utf-8"))
    default_model = timing_model["default_model"]
    default_spec = timing_model["models"][default_model]
    paths = generate_paths(results_path)

    for model_spec in timing_model["models"].values():
        model_spec.pop("classes", None)
    default_spec["notes"] = list(DEFAULT_MODEL_NOTES)
    default_spec["paths"] = paths
    return timing_model


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results",
        type=Path,
        default=DEFAULT_RESULTS,
        help="Benchmark results JSON to convert into ISA reference paths.",
    )
    parser.add_argument(
        "--timing-model",
        type=Path,
        default=DEFAULT_TIMING_MODEL,
        help="Timing model JSON to update when --format=timing-model is selected.",
    )
    parser.add_argument(
        "--format",
        choices=("paths", "timing-model"),
        default="paths",
        help="Emit either only the exact paths list or the full timing_model.json structure.",
    )
    args = parser.parse_args(argv)
    if args.format == "paths":
        payload = generate_paths(args.results.resolve())
    else:
        payload = generate_timing_model(args.results.resolve(), args.timing_model.resolve())
    print(json.dumps(payload, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
