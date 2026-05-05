#!/usr/bin/env python3
# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0
"""Build the aggregated OpcodeOne ISA bundle from modular source files."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INDEX = (PROJECT_ROOT / "isa/v0.9/index.json").resolve()
FAMILY_KEYS = {"name", "opcode_ref", "status", "forms"}
FORM_KEYS = {"name", "syntax", "constraints", "defaults", "derived_fields", "decode_rule", "encoding", "semantics"}
SYNTAX_KEYS = {"style", "patterns"}
PATTERN_KEYS = {"name", "sequence"}
LITERAL_TOKEN_KEYS = {"kind", "value", "name"}
SLOT_TOKEN_KEYS = {"kind", "name", "slot_kind", "operand_kind_ref", "enum_ref", "keyword_ref", "optional", "omit_keys"}
SLOT_KINDS = {"operand", "enum", "keyword"}
COMPACT_OVERLAY_KEYS = {"family", "entries"}
COMPACT_ENTRY_KEYS = {"form", "pattern", "template", "relation"}


class IsaValidationError(ValueError):
    pass


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def resolve(base: Path, relpath: str) -> Path:
    return (base / relpath).resolve()


def project_relative(path: Path) -> str:
    return Path(os.path.relpath(path, PROJECT_ROOT)).as_posix()


def render_canonical_pattern_template(pattern: dict[str, Any]) -> str:
    parts: list[str] = []
    for token in pattern["sequence"]:
        kind = token.get("kind")
        if kind == "literal":
            parts.append(token["value"])
            continue
        if kind == "slot":
            parts.append(f"<{token['name']}>")
            continue
        raise IsaValidationError(f"unsupported pattern token kind '{kind}' while rendering canonical template")
    return " ".join(parts)


def build_compact_surface(base: Path, compact_source_path: Path, families: list[dict[str, Any]]) -> dict[str, Any]:
    compact_surface = read_json(compact_source_path)
    compact_files = compact_surface.get("files")
    if not isinstance(compact_files, list) or not compact_files or any(not isinstance(path, str) or not path for path in compact_files):
        raise IsaValidationError("compact_syntax: files must be a non-empty list of relative paths")

    expected_patterns: dict[tuple[str, str, str], str] = {}
    for family in families:
        family_name = family["name"]
        for form in family["forms"]:
            form_name = form["name"]
            for pattern in form["syntax"]["patterns"]:
                expected_patterns[(family_name, form_name, pattern["name"])] = render_canonical_pattern_template(pattern)

    seen_families: set[str] = set()
    seen_patterns: set[tuple[str, str, str]] = set()
    coverage: list[dict[str, str]] = []

    for relpath in compact_files:
        overlay_path = resolve(base, relpath)
        overlay = read_json(overlay_path)
        if set(overlay.keys()) != COMPACT_OVERLAY_KEYS:
            raise IsaValidationError(
                f"compact overlay '{project_relative(overlay_path)}': expected keys {sorted(COMPACT_OVERLAY_KEYS)}, "
                f"got {sorted(overlay.keys())}"
            )

        family_name = overlay.get("family")
        if not isinstance(family_name, str) or not family_name:
            raise IsaValidationError(f"compact overlay '{project_relative(overlay_path)}': family must be a non-empty string")
        if family_name in seen_families:
            raise IsaValidationError(f"compact overlay '{project_relative(overlay_path)}': duplicate family '{family_name}'")
        seen_families.add(family_name)

        entries = overlay.get("entries")
        if not isinstance(entries, list) or not entries:
            raise IsaValidationError(f"compact overlay '{project_relative(overlay_path)}': entries must be a non-empty list")

        for index, entry in enumerate(entries):
            if set(entry.keys()) != COMPACT_ENTRY_KEYS:
                raise IsaValidationError(
                    f"compact overlay '{project_relative(overlay_path)}' entry {index}: expected keys "
                    f"{sorted(COMPACT_ENTRY_KEYS)}, got {sorted(entry.keys())}"
                )
            if any(not isinstance(entry[key], str) or not entry[key] for key in COMPACT_ENTRY_KEYS):
                raise IsaValidationError(
                    f"compact overlay '{project_relative(overlay_path)}' entry {index}: all fields must be non-empty strings"
                )

            key = (family_name, entry["form"], entry["pattern"])
            canonical = expected_patterns.get(key)
            if canonical is None:
                raise IsaValidationError(
                    f"compact overlay '{project_relative(overlay_path)}' entry {index}: "
                    f"unknown canonical pattern {family_name}.{entry['form']}.{entry['pattern']}"
                )
            if key in seen_patterns:
                raise IsaValidationError(
                    f"compact overlay '{project_relative(overlay_path)}' entry {index}: duplicate pattern "
                    f"{family_name}.{entry['form']}.{entry['pattern']}"
                )
            seen_patterns.add(key)
            coverage.append(
                {
                    "family": family_name,
                    "form": entry["form"],
                    "pattern": entry["pattern"],
                    "canonical": canonical,
                    "compact": entry["template"],
                    "relation": entry["relation"],
                }
            )

    covered_families = {entry["family"] for entry in coverage}
    covered_forms = {(entry["family"], entry["form"]) for entry in coverage}
    fully_covered = seen_patterns == set(expected_patterns)
    compact_surface["coverage_summary"] = {
        "family_count": len(covered_families),
        "form_count": len(covered_forms),
        "pattern_count": len(coverage),
        "fully_covered": fully_covered,
    }
    if not fully_covered:
        missing = sorted(set(expected_patterns) - seen_patterns)
        missing_labels = ", ".join(f"{family}.{form}.{pattern}" for family, form, pattern in missing)
        raise IsaValidationError(f"compact_syntax: missing compact overlay entries for {missing_labels}")
    compact_surface["coverage"] = coverage
    return compact_surface


def build_bundle(index_path: Path) -> dict[str, Any]:
    index_path = index_path.resolve()
    index = read_json(index_path)
    base = index_path.parent
    files = index["files"]
    families = [read_json(resolve(base, rel)) for rel in files["families"]]
    compact_syntax = build_compact_surface(base, resolve(base, files["compact_syntax"]), families)

    return {
        "schema_name": index["schema_name"],
        "schema_version": index["schema_version"],
        "source_layout": "modular",
        "source_manifest": project_relative(index_path),
        "index_notes": index.get("notes", []),
        "isa": read_json(resolve(base, files["meta"])),
        "register_sets": read_json(resolve(base, files["registers"])),
        "operand_kinds": read_json(resolve(base, files["operand_kinds"])),
        "syntax_model": read_json(resolve(base, files["syntax_model"])),
        "compact_syntax": compact_syntax,
        "encoding_model": read_json(resolve(base, files["encoding_model"])),
        "abstract_enums": read_json(resolve(base, files["abstract_enums"])),
        "abstract_kinds": read_json(resolve(base, files["abstract_kinds"])),
        "opcode_slots": read_json(resolve(base, files["opcode_slots"])),
        "timing_model": read_json(resolve(base, files["timing_model"])),
        "families": families,
    }


def operand_source_paths(operand_kinds: dict[str, Any], operand_kind_ref: str, memo: dict[str, set[tuple[str, ...]]]) -> set[tuple[str, ...]]:
    if operand_kind_ref in memo:
        return memo[operand_kind_ref]

    spec = operand_kinds[operand_kind_ref]
    kind = spec["type"]
    paths: set[tuple[str, ...]]

    if kind in {"register", "register_subset"}:
        paths = {
            (),
            ("kind",),
            ("name",),
            ("code",),
            ("width_bits",),
        }
    elif kind == "union":
        paths = set()
        for member_ref in spec["members"]:
            paths.update(operand_source_paths(operand_kinds, member_ref, memo))
    elif kind in {"immediate", "address", "relative_offset"}:
        paths = {()}
    elif kind == "memory":
        addressing = spec["addressing"]
        if addressing == "[reg24]":
            paths = {(), ("base",)}
        elif addressing == "[reg24+off16_signed]":
            paths = {(), ("base",), ("offset",)}
        elif addressing == "[addr24]":
            paths = {
                (),
                ("addr",),
                ("addr_hi",),
                ("addr_lo",),
                ("addr_hi8",),
                ("addr_lo16",),
            }
        else:
            raise IsaValidationError(f"unsupported memory addressing kind '{addressing}' in operand_kinds")
    else:
        raise IsaValidationError(f"unsupported operand kind type '{kind}' in operand_kinds")

    memo[operand_kind_ref] = paths
    return paths


def validate_source_ref(
    source: str,
    *,
    family_name: str,
    sequence_paths: dict[str, set[tuple[str, ...]]],
    derived_names: set[str],
    allow_family_opcode: bool = False,
) -> None:
    if source == "family_opcode":
        if not allow_family_opcode:
            raise IsaValidationError(f"{family_name}: family_opcode is not valid in this context")
        return

    if source.startswith("sequence."):
        parts = source.split(".")
        if len(parts) < 2 or not parts[1]:
            raise IsaValidationError(f"{family_name}: invalid sequence source '{source}'")
        if parts[1] not in sequence_paths:
            raise IsaValidationError(f"{family_name}: source '{source}' references unknown sequence input '{parts[1]}'")
        path = tuple(parts[2:])
        if path not in sequence_paths[parts[1]]:
            raise IsaValidationError(f"{family_name}: source '{source}' is not valid for sequence input '{parts[1]}'")
        return

    if source.startswith("derived."):
        parts = source.split(".")
        if len(parts) != 2 or not parts[1]:
            raise IsaValidationError(f"{family_name}: invalid derived source '{source}'")
        if parts[1] not in derived_names:
            raise IsaValidationError(f"{family_name}: source '{source}' references unknown derived field '{parts[1]}'")
        return

    raise IsaValidationError(f"{family_name}: unsupported source ref '{source}'")


def validate_constraints(family_name: str, form_name: str, constraints: list[Any], slot_names: set[str]) -> None:
    for constraint in constraints:
        if not isinstance(constraint, dict):
            raise IsaValidationError(f"{family_name}.{form_name}: constraints must be objects")
        constraint_type = constraint.get("type")
        if not isinstance(constraint_type, str):
            raise IsaValidationError(f"{family_name}.{form_name}: constraint missing string type")

        for key in ("slot", "bit_operand", "target_operand"):
            value = constraint.get(key)
            if value is not None and value not in slot_names:
                raise IsaValidationError(f"{family_name}.{form_name}: constraint references unknown slot '{value}'")

        for operand in constraint.get("operands", []):
            if operand not in slot_names:
                raise IsaValidationError(f"{family_name}.{form_name}: constraint references unknown operand slot '{operand}'")


def validate_timing_model(timing_model: dict[str, Any]) -> None:
    if not isinstance(timing_model, dict):
        raise IsaValidationError("timing_model: expected object")

    default_model = timing_model.get("default_model")
    if not isinstance(default_model, str):
        raise IsaValidationError("timing_model: default_model must be a string")

    models = timing_model.get("models")
    if not isinstance(models, dict) or not models:
        raise IsaValidationError("timing_model: models must be a non-empty object")
    if default_model not in models:
        raise IsaValidationError(f"timing_model: default_model '{default_model}' is not defined")

    for model_name, spec in models.items():
        if not isinstance(spec, dict):
            raise IsaValidationError(f"timing_model.{model_name}: model entry must be an object")
        unexpected_keys = set(spec.keys()) - {"units", "notes", "paths"}
        if unexpected_keys:
            raise IsaValidationError(
                f"timing_model.{model_name}: unexpected model keys {sorted(unexpected_keys)}"
            )
        if spec.get("units") != "chronons":
            raise IsaValidationError(f"timing_model.{model_name}: units must be 'chronons'")
        if not isinstance(spec.get("notes"), list):
            raise IsaValidationError(f"timing_model.{model_name}: notes must be a list")
        paths = spec.get("paths")
        if paths is None:
            continue
        if not isinstance(paths, list) or not paths:
            raise IsaValidationError(f"timing_model.{model_name}: paths must be a non-empty list when present")

        expected_keys = {
            "name",
            "path_id",
            "path_id_name",
            "family",
            "form",
            "chronons",
            "reference_asm",
            "conditions",
        }
        seen_names: set[str] = set()
        seen_path_ids: set[int] = set()
        seen_path_id_names: set[str] = set()
        for index, path_spec in enumerate(paths):
            if not isinstance(path_spec, dict):
                raise IsaValidationError(f"timing_model.{model_name}.paths[{index}]: entry must be an object")
            if set(path_spec.keys()) != expected_keys:
                raise IsaValidationError(
                    f"timing_model.{model_name}.paths[{index}]: expected path keys {sorted(expected_keys)}, got {sorted(path_spec.keys())}"
                )

            name = path_spec["name"]
            if not isinstance(name, str) or not name:
                raise IsaValidationError(f"timing_model.{model_name}.paths[{index}]: name must be a non-empty string")
            if name in seen_names:
                raise IsaValidationError(f"timing_model.{model_name}.paths[{index}]: duplicate path name '{name}'")
            seen_names.add(name)

            path_id = path_spec["path_id"]
            if not isinstance(path_id, int) or path_id < 1:
                raise IsaValidationError(f"timing_model.{model_name}.paths[{index}]: path_id must be a positive integer")
            if path_id in seen_path_ids:
                raise IsaValidationError(f"timing_model.{model_name}.paths[{index}]: duplicate path_id '{path_id}'")
            seen_path_ids.add(path_id)

            path_id_name = path_spec["path_id_name"]
            if not isinstance(path_id_name, str) or not path_id_name:
                raise IsaValidationError(
                    f"timing_model.{model_name}.paths[{index}]: path_id_name must be a non-empty string"
                )
            if path_id_name in seen_path_id_names:
                raise IsaValidationError(
                    f"timing_model.{model_name}.paths[{index}]: duplicate path_id_name '{path_id_name}'"
                )
            seen_path_id_names.add(path_id_name)

            for key in ("family", "form"):
                if not isinstance(path_spec[key], str) or not path_spec[key]:
                    raise IsaValidationError(
                        f"timing_model.{model_name}.paths[{index}]: {key} must be a non-empty string"
                    )

            path_chronons = path_spec["chronons"]
            if not isinstance(path_chronons, int) or path_chronons < 1:
                raise IsaValidationError(
                    f"timing_model.{model_name}.paths[{index}]: chronons must be a positive integer"
                )

            reference_asm = path_spec["reference_asm"]
            if not isinstance(reference_asm, list) or any(not isinstance(line, str) for line in reference_asm):
                raise IsaValidationError(
                    f"timing_model.{model_name}.paths[{index}]: reference_asm must be a list of strings"
                )

            if not isinstance(path_spec["conditions"], dict):
                raise IsaValidationError(f"timing_model.{model_name}.paths[{index}]: conditions must be an object")


def validate_bundle(bundle: dict[str, Any]) -> None:
    operand_kinds = bundle["operand_kinds"]
    abstract_enums = bundle["abstract_enums"]
    abstract_kinds = bundle["abstract_kinds"]
    opcode_slots = bundle["opcode_slots"]["slots"]
    operand_path_memo: dict[str, set[tuple[str, ...]]] = {}
    validate_timing_model(bundle["timing_model"])
    default_model = bundle["timing_model"]["default_model"]
    family_forms = {
        family["name"]: {form["name"]: form for form in family["forms"]}
        for family in bundle["families"]
    }

    for family in bundle["families"]:
        family_name = family.get("name")
        if set(family.keys()) != FAMILY_KEYS:
            raise IsaValidationError(f"{family_name}: expected family keys {sorted(FAMILY_KEYS)}, got {sorted(family.keys())}")
        if family["opcode_ref"] not in opcode_slots:
            raise IsaValidationError(f"{family_name}: opcode_ref '{family['opcode_ref']}' is not declared in opcode_slots")

        for form in family["forms"]:
            form_name = form.get("name")
            if set(form.keys()) != FORM_KEYS:
                raise IsaValidationError(
                    f"{family_name}.{form_name}: expected form keys {sorted(FORM_KEYS)}, got {sorted(form.keys())}"
                )

            syntax = form["syntax"]
            if set(syntax.keys()) != SYNTAX_KEYS:
                raise IsaValidationError(
                    f"{family_name}.{form_name}: expected syntax keys {sorted(SYNTAX_KEYS)}, got {sorted(syntax.keys())}"
                )

            slot_names: set[str] = set()
            sequence_paths: dict[str, set[tuple[str, ...]]] = {}
            sequence_input_kinds: dict[str, str] = {}
            patterns = syntax["patterns"]
            if not isinstance(patterns, list) or not patterns:
                raise IsaValidationError(f"{family_name}.{form_name}: syntax.patterns must be a non-empty list")

            for pattern in patterns:
                if set(pattern.keys()) != PATTERN_KEYS:
                    raise IsaValidationError(
                        f"{family_name}.{form_name}: expected pattern keys {sorted(PATTERN_KEYS)}, got {sorted(pattern.keys())}"
                    )
                for token in pattern["sequence"]:
                    kind = token.get("kind")
                    if kind == "literal":
                        if not {"kind", "value"}.issubset(token.keys()) or not set(token.keys()).issubset(LITERAL_TOKEN_KEYS):
                            raise IsaValidationError(
                                f"{family_name}.{form_name}: literal token must use keys {sorted(LITERAL_TOKEN_KEYS)}"
                            )
                        name = token.get("name")
                        if name is not None:
                            if not isinstance(name, str) or not name:
                                raise IsaValidationError(
                                    f"{family_name}.{form_name}: named literal token must use a non-empty string name"
                                )
                            existing_kind = sequence_input_kinds.setdefault(name, "literal")
                            if existing_kind != "literal":
                                raise IsaValidationError(
                                    f"{family_name}.{form_name}: sequence input '{name}' mixes literal and slot emitters"
                                )
                            sequence_paths.setdefault(name, {()})
                        continue

                    if kind != "slot":
                        raise IsaValidationError(f"{family_name}.{form_name}: unknown token kind '{kind}'")
                    if not set(token.keys()).issubset(SLOT_TOKEN_KEYS):
                        raise IsaValidationError(f"{family_name}.{form_name}: unsupported slot token keys {sorted(token.keys())}")

                    slot_name = token["name"]
                    slot_names.add(slot_name)
                    existing_kind = sequence_input_kinds.setdefault(slot_name, "slot")
                    if existing_kind != "slot":
                        raise IsaValidationError(
                            f"{family_name}.{form_name}: sequence input '{slot_name}' mixes literal and slot emitters"
                        )
                    slot_kind = token.get("slot_kind")
                    if slot_kind not in SLOT_KINDS:
                        raise IsaValidationError(f"{family_name}.{form_name}: invalid slot_kind '{slot_kind}'")

                    if slot_kind == "operand":
                        ref = token.get("operand_kind_ref")
                        if ref not in operand_kinds:
                            raise IsaValidationError(f"{family_name}.{form_name}: unknown operand_kind_ref '{ref}'")
                        sequence_paths.setdefault(slot_name, set()).update(
                            operand_source_paths(operand_kinds, ref, operand_path_memo)
                        )
                    elif slot_kind == "enum":
                        ref = token.get("enum_ref")
                        if ref not in abstract_enums:
                            raise IsaValidationError(f"{family_name}.{form_name}: unknown enum_ref '{ref}'")
                        sequence_paths.setdefault(slot_name, {()})
                        for omitted in token.get("omit_keys", []):
                            if omitted not in abstract_enums[ref]:
                                raise IsaValidationError(
                                    f"{family_name}.{form_name}: omit_keys references '{omitted}' outside enum '{ref}'"
                                )
                    elif slot_kind == "keyword":
                        ref = token.get("keyword_ref")
                        if ref not in abstract_kinds:
                            raise IsaValidationError(f"{family_name}.{form_name}: unknown keyword_ref '{ref}'")
                        if abstract_kinds[ref].get("kind") != "keyword":
                            raise IsaValidationError(f"{family_name}.{form_name}: keyword_ref '{ref}' is not a keyword kind")
                        sequence_paths.setdefault(slot_name, {()})

            validate_constraints(family_name, form_name, form["constraints"], slot_names)

            for default_slot in form["defaults"]:
                if default_slot not in slot_names:
                    raise IsaValidationError(
                        f"{family_name}.{form_name}: defaults references unknown slot '{default_slot}'"
                    )

            derived_fields = form["derived_fields"]
            if not isinstance(derived_fields, dict):
                raise IsaValidationError(f"{family_name}.{form_name}: derived_fields must be an object")
            derived_names = set(derived_fields.keys())

            for derived_name, spec in derived_fields.items():
                if not isinstance(spec, dict):
                    raise IsaValidationError(f"{family_name}.{form_name}: derived field '{derived_name}' must be an object")
                derived_type = spec.get("type")
                if not isinstance(derived_type, str):
                    raise IsaValidationError(f"{family_name}.{form_name}: derived field '{derived_name}' missing string type")
                if "enum_ref" in spec and spec["enum_ref"] not in abstract_enums:
                    raise IsaValidationError(
                        f"{family_name}.{form_name}: derived field '{derived_name}' uses unknown enum_ref '{spec['enum_ref']}'"
                    )
                if "source" in spec:
                    validate_source_ref(
                        spec["source"],
                        family_name=f"{family_name}.{form_name}",
                        sequence_paths=sequence_paths,
                        derived_names=derived_names,
                    )
                for source in spec.get("sources", []):
                    validate_source_ref(
                        source,
                        family_name=f"{family_name}.{form_name}",
                        sequence_paths=sequence_paths,
                        derived_names=derived_names,
                    )

            encoding = form["encoding"]
            if encoding["word_count"] != len(encoding["words"]):
                raise IsaValidationError(
                    f"{family_name}.{form_name}: word_count {encoding['word_count']} does not match actual word list"
                )
            for word in encoding["words"]:
                for field in word:
                    if field["kind"] == "fixed":
                        if "value" not in field:
                            raise IsaValidationError(
                                f"{family_name}.{form_name}: fixed field '{field['name']}' must define a value"
                            )
                    elif field["kind"] == "slot":
                        if "source" not in field:
                            raise IsaValidationError(
                                f"{family_name}.{form_name}: slot field '{field['name']}' must define a source"
                            )
                        validate_source_ref(
                            field["source"],
                            family_name=f"{family_name}.{form_name}",
                            sequence_paths=sequence_paths,
                            derived_names=derived_names,
                            allow_family_opcode=True,
                        )
                    else:
                        raise IsaValidationError(
                            f"{family_name}.{form_name}: unknown encoding field kind '{field['kind']}'"
                        )

            if not isinstance(form["semantics"].get("summary"), str):
                raise IsaValidationError(f"{family_name}.{form_name}: semantics.summary must be a string")

    default_model_paths: set[tuple[str, str]] = set()
    for model_name, model_spec in bundle["timing_model"]["models"].items():
        model_paths: set[tuple[str, str]] = set()
        for index, path_spec in enumerate(model_spec.get("paths", [])):
            family_name = path_spec["family"]
            if family_name not in family_forms:
                raise IsaValidationError(
                    f"timing_model.{model_name}.paths[{index}]: family '{family_name}' is not declared in families"
                )
            form_name = path_spec["form"]
            if form_name not in family_forms[family_name]:
                raise IsaValidationError(
                    f"timing_model.{model_name}.paths[{index}]: form '{family_name}.{form_name}' is not declared in families"
                )
            model_paths.add((family_name, form_name))
        if model_name == default_model:
            default_model_paths = model_paths

    for family_name, forms in family_forms.items():
        for form_name in forms:
            if (family_name, form_name) not in default_model_paths:
                raise IsaValidationError(
                    f"{family_name}.{form_name}: no exact timing path is declared in the default timing model"
                )


def write_bundle(bundle: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bundle, indent=2) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX, help="Path to the ISA index manifest")
    parser.add_argument("--output", type=Path, help="Path to the generated bundle; defaults to the index manifest setting")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    index_path = args.index.resolve()
    index = read_json(index_path)
    output = args.output
    if output is None:
        output = resolve(index_path.parent, index["generated"]["bundle"])

    bundle = build_bundle(index_path)
    validate_bundle(bundle)
    write_bundle(bundle, output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
