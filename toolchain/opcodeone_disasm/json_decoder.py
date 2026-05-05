# Copyright 2026 Antonio Rodríguez (MoebiuZ)
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from functools import lru_cache
import re
from typing import Any

try:
    from common.opcodeone_isa_bundle import load_default_bundle
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_isa_bundle import load_default_bundle
try:
    from common.opcodeone_bundle_runtime import build_coded_register_sets
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_bundle_runtime import build_coded_register_sets
try:
    from common.opcodeone_constraints import validate_constraints as validate_shared_constraints
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_constraints import validate_constraints as validate_shared_constraints
try:
    from common.opcodeone_derived_fields import (
        invert_enum_value,
        invert_keyword_case,
        invert_mapping_value,
        match_named_literal_derived_fields,
        match_slot_or_constant_derived_fields,
        merge_bit_slices,
    )
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_derived_fields import (
        invert_enum_value,
        invert_keyword_case,
        invert_mapping_value,
        match_named_literal_derived_fields,
        match_slot_or_constant_derived_fields,
        merge_bit_slices,
    )
try:
    from common.opcodeone_isa_runtime import RuntimeFixedField, RuntimeForm, RuntimePattern, RuntimeSourceField, build_runtime_bundle
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_isa_runtime import RuntimeFixedField, RuntimeForm, RuntimePattern, RuntimeSourceField, build_runtime_bundle
try:
    from common.opcodeone_operands import MemoryOperand, RegisterOperand
except ModuleNotFoundError:  # pragma: no cover - exercised via package-style imports
    from toolchain.common.opcodeone_operands import MemoryOperand, RegisterOperand

from .formatting import format_hex, format_signed, sign_extend
from .model import DisassembledLine, DisassemblerError


DecodedRegister = RegisterOperand
DecodedMemory = MemoryOperand


class _NeedMoreWords(Exception):
    pass


class JsonDisassembler:
    def __init__(self, bundle: dict[str, Any]) -> None:
        self.bundle = bundle
        self.runtime = build_runtime_bundle(bundle)
        self.operand_kinds = bundle["operand_kinds"]
        self.abstract_enums = bundle["abstract_enums"]
        self.abstract_kinds = bundle["abstract_kinds"]
        self.compact_templates = {
            (entry["family"], entry["form"], entry["pattern"]): entry["compact"]
            for entry in bundle.get("compact_syntax", {}).get("coverage", [])
        }
        self.register_sets = build_coded_register_sets(
            bundle["register_sets"],
            lambda set_name, name, code, width_bits: DecodedRegister(
                kind=set_name,
                name=name,
                code=code,
                width_bits=width_bits,
            ),
        )
        self.forms_by_opcode = self.runtime.forms_by_opcode

    @classmethod
    def from_default_bundle(cls) -> JsonDisassembler:
        return cls(load_default_bundle())

    def disassemble_listing(self, words: list[int], *, base_address: int = 0, surface: str = "canonical") -> list[DisassembledLine]:
        lines: list[DisassembledLine] = []
        index = 0
        while index < len(words):
            line = self._disassemble_at(words, index, base_address=base_address, surface=surface)
            lines.append(line)
            index += line.word_count
        return lines

    def disassemble_words(self, words: list[int], *, surface: str = "canonical") -> list[str]:
        return [entry.text for entry in self.disassemble_listing(words, surface=surface)]

    def _disassemble_at(self, words: list[int], index: int, *, base_address: int, surface: str) -> DisassembledLine:
        word = words[index]
        opcode = (word >> 11) & 0x1F
        family_entry = self.forms_by_opcode.get(opcode)
        if family_entry is None:
            raise DisassemblerError(f"word {index}: unknown family opcode {opcode}")

        family_name, forms = family_entry
        incomplete_error: DisassemblerError | None = None
        matched: DisassembledLine | None = None

        for runtime in forms:
            try:
                candidate = self._try_decode_form(runtime, words, index, base_address=base_address, surface=surface)
            except _NeedMoreWords as exc:
                if incomplete_error is None:
                    incomplete_error = DisassemblerError(str(exc))
                continue
            if candidate is None:
                continue
            if matched is not None:
                raise DisassemblerError(
                    f"word {index}: ambiguous {family_name} encoding matched both "
                    f"{matched.text!r} and {candidate.text!r}"
                )
            matched = candidate

        if matched is not None:
            return matched
        if incomplete_error is not None:
            raise incomplete_error
        raise DisassemblerError(f"word {index}: unsupported encoding for family {family_name}")

    def _try_decode_form(
        self,
        runtime: RuntimeForm,
        words: list[int],
        index: int,
        *,
        base_address: int,
        surface: str,
    ) -> DisassembledLine | None:
        available = len(words) - index
        if available < runtime.word_count:
            available_words = tuple(words[index:])
            if self._fixed_fields_match(runtime.fixed_fields, available_words):
                raise _NeedMoreWords(
                    f"word {index}: {runtime.family_name}.{runtime.form_name} missing "
                    f"{runtime.word_count - available} trailing word(s)"
                )
            return None

        raw_words = tuple(words[index : index + runtime.word_count])
        if not self._fixed_fields_match(runtime.fixed_fields, raw_words):
            return None

        source_values = self._extract_source_values(runtime.source_fields, raw_words)
        if source_values is None:
            return None
        pattern = self._select_pattern(runtime, source_values)
        if pattern is None:
            return None

        slots = self._decode_slots(runtime, pattern, source_values)
        self._validate_constraints(runtime, slots)
        text = self._render_surface(pattern, runtime, slots, surface=surface)
        return DisassembledLine(
            address=base_address + (index * 2),
            word_count=runtime.word_count,
            text=text,
            raw_words=raw_words,
        )

    def _render_surface(
        self,
        pattern: RuntimePattern,
        runtime: RuntimeForm,
        slots: dict[str, Any],
        *,
        surface: str,
    ) -> str:
        if surface == "canonical":
            return self._render_pattern(pattern, runtime, slots)
        if surface == "compact":
            return self._render_compact_pattern(pattern, runtime, slots)
        raise DisassemblerError(f"unsupported disassembly surface {surface!r}")

    @staticmethod
    def _fixed_fields_match(fixed_fields: tuple[RuntimeFixedField, ...], raw_words: tuple[int, ...]) -> bool:
        for field in fixed_fields:
            if field.word_index >= len(raw_words):
                continue
            if raw_words[field.word_index] & field.mask != field.expected:
                return False
        return True

    def _extract_source_values(
        self,
        source_fields: tuple[RuntimeSourceField, ...],
        raw_words: tuple[int, ...],
    ) -> dict[str, int] | None:
        values: dict[str, int] = {}
        for field in source_fields:
            value = (raw_words[field.word_index] >> field.lsb) & ((1 << field.width) - 1)
            existing = values.get(field.source)
            if existing is not None and existing != value:
                return None
            values[field.source] = value
        return values

    def _select_pattern(self, runtime: RuntimeForm, source_values: dict[str, int]) -> RuntimePattern | None:
        matches: list[RuntimePattern] = []
        for pattern in runtime.syntax_patterns:
            if not self._pattern_named_literal_match(runtime, pattern, source_values):
                continue
            if not self._pattern_slot_or_constant_match(runtime, pattern, source_values):
                continue
            matches.append(pattern)
        if len(matches) > 1:
            names = ", ".join(pattern.name for pattern in matches)
            raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: ambiguous syntax patterns {names}")
        return matches[0] if matches else None

    def _pattern_named_literal_match(
        self,
        runtime: RuntimeForm,
        pattern: RuntimePattern,
        source_values: dict[str, int],
    ) -> bool:
        return match_named_literal_derived_fields(
            runtime.derived_fields,
            pattern.named_literals,
            source_values,
            abstract_enums=self.abstract_enums,
            error_factory=lambda message: DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: {message}"),
        )

    def _pattern_slot_or_constant_match(
        self,
        runtime: RuntimeForm,
        pattern: RuntimePattern,
        source_values: dict[str, int],
    ) -> bool:
        return match_slot_or_constant_derived_fields(
            runtime.derived_fields,
            pattern.slot_names,
            source_values,
            error_factory=lambda message: DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: {message}"),
        )

    def _decode_slots(
        self,
        runtime: RuntimeForm,
        pattern: RuntimePattern,
        source_values: dict[str, int],
    ) -> dict[str, Any]:
        slots = dict(runtime.defaults)
        path_values: dict[str, int] = {}
        path_fragments: dict[str, list[tuple[int, int, int]]] = {}
        width_hints: dict[str, str] = {}
        slot_or_constant_values: dict[str, int] = {}

        for source, value in source_values.items():
            if source.startswith("sequence."):
                path_values[source] = value
                continue
            if not source.startswith("derived."):
                continue
            derived_name = source.split(".", 1)[1]
            spec = runtime.derived_fields[derived_name]
            source_ref = spec.get("source")
            if spec["type"] == "enum_lookup":
                if not isinstance(source_ref, str):
                    raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: enum_lookup missing string source")
                if source_ref.startswith("sequence."):
                    slot_name = source_ref.split(".", 2)[1]
                    if slot_name not in runtime.slot_specs:
                        continue
                    slots[slot_name] = invert_enum_value(
                        spec["enum_ref"],
                        value,
                        abstract_enums=self.abstract_enums,
                        error_factory=lambda message: DisassemblerError(
                            f"{runtime.family_name}.{runtime.form_name}.{derived_name}: {message}"
                        ),
                    )
                continue
            if spec["type"] == "width_flag":
                if not isinstance(source_ref, str) or not source_ref.startswith("sequence."):
                    raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: width_flag source must be sequence.*")
                slot_name = source_ref.split(".", 2)[1]
                width_hints[slot_name] = invert_mapping_value(
                    spec["mapping"],
                    value,
                    error_factory=lambda message: DisassemblerError(
                        f"{runtime.family_name}.{runtime.form_name}.{derived_name}: {message}"
                    ),
                )
                continue
            if spec["type"] == "bit_slice":
                if not isinstance(source_ref, str) or not source_ref.startswith("sequence."):
                    raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: bit_slice source must be sequence.*")
                path_fragments.setdefault(source_ref, []).append((spec["lsb"], spec["msb"], value))
                continue
            if spec["type"] == "keyword_presence_flag":
                if value not in {0, 1}:
                    raise DisassemblerError(
                        f"{runtime.family_name}.{runtime.form_name}.{derived_name}: keyword presence flag must be 0 or 1, got {value}"
                    )
                if not isinstance(source_ref, str) or not source_ref.startswith("sequence."):
                    raise DisassemblerError(
                        f"{runtime.family_name}.{runtime.form_name}: keyword_presence_flag source must be sequence.*"
                    )
                slot_name = source_ref.split(".", 2)[1]
                slots[slot_name] = bool(value)
                continue
            if spec["type"] == "keyword_combination_lookup":
                case = invert_keyword_case(
                    spec["cases"],
                    value,
                    error_factory=lambda message: DisassemblerError(
                        f"{runtime.family_name}.{runtime.form_name}.{derived_name}: {message}"
                    ),
                )
                for source_path, case_value in zip(spec["sources"], case["when"]):
                    if not source_path.startswith("sequence."):
                        raise DisassemblerError(
                            f"{runtime.family_name}.{runtime.form_name}: keyword_combination source must be sequence.*, got {source_path!r}"
                        )
                    slot_name = source_path.split(".", 2)[1]
                    slots[slot_name] = bool(case_value)
                continue
            if spec["type"] == "slot_or_constant":
                if not isinstance(source_ref, str) or not source_ref.startswith("sequence."):
                    raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: slot_or_constant source must be sequence.*")
                slot_name = source_ref.split(".", 2)[1]
                slot_or_constant_values[slot_name] = value
                continue
            raise DisassemblerError(
                f"{runtime.family_name}.{runtime.form_name}: unsupported derived field type {spec['type']!r}"
            )

        for path, fragments in path_fragments.items():
            path_values[path] = merge_bit_slices(
                fragments,
                error_factory=lambda message: DisassemblerError(
                    f"{runtime.family_name}.{runtime.form_name}: {message} for {path}"
                ),
            )

        self._propagate_width_hints(runtime, pattern, width_hints)

        for token in pattern.slot_tokens:
            name = token["name"]
            slot_spec = runtime.slot_specs[name]
            if slot_spec.slot_kind == "operand":
                if f"sequence.{name}" not in path_values and name in slot_or_constant_values:
                    path_values[f"sequence.{name}"] = slot_or_constant_values[name]
                slots[name] = self._decode_operand_value(name, slot_spec.operand_kind_ref, path_values, width_hints, runtime)
                continue
            if slot_spec.slot_kind == "enum":
                if name not in slots:
                    raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: missing enum slot '{name}'")
                continue
            if slot_spec.slot_kind == "keyword":
                if name not in slots:
                    raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: missing keyword slot '{name}'")
                continue
            raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: unsupported slot kind {slot_spec.slot_kind!r}")

        return slots

    def _propagate_width_hints(
        self,
        runtime: RuntimeForm,
        pattern: RuntimePattern,
        width_hints: dict[str, str],
    ) -> None:
        changed = True
        while changed:
            changed = False
            for constraint in runtime.constraints:
                if constraint["type"] not in {"same_width", "same_width_when_present"}:
                    continue
                operands = [name for name in constraint["operands"] if name in pattern.operand_slot_names]
                if not operands:
                    continue
                hinted = {width_hints[name] for name in operands if name in width_hints}
                if len(hinted) > 1:
                    raise DisassemblerError(
                        f"{runtime.family_name}.{runtime.form_name}: incompatible width hints for {constraint['operands']}"
                    )
                if not hinted:
                    continue
                hint = next(iter(hinted))
                for name in operands:
                    if name not in width_hints:
                        width_hints[name] = hint
                        changed = True

    def _decode_operand_value(
        self,
        slot_name: str,
        operand_kind_ref: str | None,
        path_values: dict[str, int],
        width_hints: dict[str, str],
        runtime: RuntimeForm,
    ) -> DecodedRegister | DecodedMemory | int:
        if operand_kind_ref is None:
            raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: operand slot '{slot_name}' is missing operand_kind_ref")

        spec = self.operand_kinds[operand_kind_ref]
        kind = spec["type"]
        if kind == "union":
            hint = width_hints.get(slot_name)
            if hint is None:
                raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: operand slot '{slot_name}' needs width hint")
            member_ref = self._select_union_member(operand_kind_ref, hint, runtime, slot_name)
            return self._decode_operand_value(slot_name, member_ref, path_values, width_hints, runtime)

        if kind == "register":
            raw = self._require_path(path_values, f"sequence.{slot_name}", runtime, slot_name)
            return self._decode_register(raw, spec["register_set"], runtime, slot_name)

        if kind == "register_subset":
            raw = self._require_path(path_values, f"sequence.{slot_name}", runtime, slot_name)
            register = self._decode_register(raw, spec["register_set"], runtime, slot_name)
            if register.name not in spec["members"]:
                raise DisassemblerError(
                    f"{runtime.family_name}.{runtime.form_name}: register {register.name} is not valid for subset {operand_kind_ref}"
                )
            return register

        if kind == "immediate":
            raw = self._require_path(path_values, f"sequence.{slot_name}", runtime, slot_name)
            return sign_extend(raw, spec["bits"]) if spec["signed"] else raw

        if kind == "address":
            return self._require_path(path_values, f"sequence.{slot_name}", runtime, slot_name)

        if kind == "relative_offset":
            raw = self._require_path(path_values, f"sequence.{slot_name}", runtime, slot_name)
            return sign_extend(raw, spec["bits"])

        if kind == "memory":
            addressing = spec["addressing"]
            if addressing == "[reg24]":
                base_raw = self._require_path(path_values, f"sequence.{slot_name}.base", runtime, slot_name)
                return DecodedMemory(addressing=addressing, base=self._decode_register(base_raw, "reg24", runtime, slot_name))
            if addressing == "[reg24+off16_signed]":
                base_raw = self._require_path(path_values, f"sequence.{slot_name}.base", runtime, slot_name)
                offset_raw = self._require_path(path_values, f"sequence.{slot_name}.offset", runtime, slot_name)
                return DecodedMemory(
                    addressing=addressing,
                    base=self._decode_register(base_raw, "reg24", runtime, slot_name),
                    offset=sign_extend(offset_raw, 16),
                )
            if addressing == "[addr24]":
                if f"sequence.{slot_name}.addr" in path_values:
                    addr = path_values[f"sequence.{slot_name}.addr"]
                else:
                    hi = self._require_path(path_values, f"sequence.{slot_name}.addr_hi8", runtime, slot_name)
                    lo = self._require_path(path_values, f"sequence.{slot_name}.addr_lo16", runtime, slot_name)
                    addr = (hi << 16) | lo
                return DecodedMemory(addressing=addressing, addr=addr)
            raise DisassemblerError(
                f"{runtime.family_name}.{runtime.form_name}: unsupported memory addressing kind {addressing!r}"
            )

        raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: unsupported operand kind type {kind!r}")

    def _validate_constraints(self, runtime: RuntimeForm, slots: dict[str, Any]) -> None:
        validate_shared_constraints(
            runtime.constraints,
            slots,
            error_factory=lambda message: DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: {message}"),
        )

    def _render_pattern(self, pattern: RuntimePattern, runtime: RuntimeForm, slots: dict[str, Any]) -> str:
        rendered: list[str] = []
        for token in pattern.sequence:
            if token["kind"] == "literal":
                rendered.append(token["value"])
                continue

            slot_spec = runtime.slot_specs[token["name"]]
            value = slots.get(slot_spec.name)
            if slot_spec.slot_kind == "operand":
                rendered.append(self._format_operand(value, slot_spec.operand_kind_ref))
                continue

            if slot_spec.slot_kind == "enum":
                if value in slot_spec.omit_keys and slot_spec.optional:
                    continue
                rendered.append(str(value))
                continue

            if slot_spec.slot_kind == "keyword":
                if not value and slot_spec.optional:
                    continue
                rendered.append(self.abstract_kinds[slot_spec.keyword_ref]["literal"])
                continue

            raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: unsupported slot kind {slot_spec.slot_kind!r}")
        return " ".join(rendered)

    def _render_compact_pattern(self, pattern: RuntimePattern, runtime: RuntimeForm, slots: dict[str, Any]) -> str:
        template = self.compact_templates.get((runtime.family_name, runtime.form_name, pattern.name))
        if template is None:
            raise DisassemblerError(
                f"{runtime.family_name}.{runtime.form_name}.{pattern.name}: missing compact syntax template"
            )
        suffix_codes = self._compact_suffix_codes(slots)
        resolved = re.sub(r"\[([^\]]+)\]", lambda match: self._resolve_compact_group(match.group(1), suffix_codes), template)
        return re.sub(
            r"<([A-Za-z_][A-Za-z0-9_]*)>",
            lambda match: self._render_compact_placeholder(runtime, slots, match.group(1)),
            resolved,
        )

    @staticmethod
    def _compact_suffix_codes(slots: dict[str, Any]) -> set[str]:
        suffix_codes: set[str] = set()
        modifier = slots.get("modifier")
        modifier_suffixes = {
            "keep carry": "KC",
            "use carry": "UC",
            "keep and use carry": "KUC",
            "keep borrow": "KB",
            "use borrow": "UB",
            "keep and use borrow": "KUB",
        }
        if isinstance(modifier, str) and modifier in modifier_suffixes:
            suffix_codes.add(modifier_suffixes[modifier])
        if slots.get("unsigned_kw"):
            suffix_codes.add("U")
        if slots.get("keep_high_kw"):
            suffix_codes.add("KH")
        return suffix_codes

    @staticmethod
    def _resolve_compact_group(group_text: str, suffix_codes: set[str]) -> str:
        for option in group_text.split("|"):
            code = option.lstrip(".")
            if code in suffix_codes:
                return option
        return ""

    def _render_compact_placeholder(self, runtime: RuntimeForm, slots: dict[str, Any], name: str) -> str:
        slot_spec = runtime.slot_specs.get(name)
        if slot_spec is None:
            raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: compact placeholder '{name}' has no slot")
        value = slots.get(name)
        if slot_spec.slot_kind == "operand":
            return self._format_operand(value, slot_spec.operand_kind_ref)
        if slot_spec.slot_kind == "enum":
            return str(value)
        if slot_spec.slot_kind == "keyword":
            if not value:
                return ""
            return self.abstract_kinds[slot_spec.keyword_ref]["literal"]
        raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: unsupported slot kind {slot_spec.slot_kind!r}")

    def _format_operand(self, value: DecodedRegister | DecodedMemory | int, operand_kind_ref: str | None) -> str:
        if operand_kind_ref is None:
            raise DisassemblerError("operand formatting requires operand_kind_ref")

        spec = self.operand_kinds[operand_kind_ref]
        kind = spec["type"]
        if kind == "union":
            if not isinstance(value, DecodedRegister):
                raise DisassemblerError(f"union operand {operand_kind_ref} expected DecodedRegister")
            return value.name
        if kind in {"register", "register_subset"}:
            if not isinstance(value, DecodedRegister):
                raise DisassemblerError(f"register operand {operand_kind_ref} expected DecodedRegister")
            return value.name
        if kind == "immediate":
            if not isinstance(value, int):
                raise DisassemblerError(f"immediate operand {operand_kind_ref} expected int")
            if spec["signed"]:
                return format_signed(value)
            if spec["bits"] <= 8:
                return str(value)
            return format_hex(value, (spec["bits"] + 3) // 4)
        if kind == "address":
            if not isinstance(value, int):
                raise DisassemblerError(f"address operand {operand_kind_ref} expected int")
            return format_hex(value, (spec["bits"] + 3) // 4)
        if kind == "relative_offset":
            if not isinstance(value, int):
                raise DisassemblerError(f"relative operand {operand_kind_ref} expected int")
            return format_signed(value)
        if kind == "memory":
            if not isinstance(value, DecodedMemory):
                raise DisassemblerError(f"memory operand {operand_kind_ref} expected DecodedMemory")
            if value.addressing == "[reg24]":
                assert value.base is not None
                return f"[{value.base.name}]"
            if value.addressing == "[reg24+off16_signed]":
                assert value.base is not None
                assert value.offset is not None
                return f"[{value.base.name}{format_signed(value.offset)}]"
            if value.addressing == "[addr24]":
                assert value.addr is not None
                return f"[{format_hex(value.addr, 6)}]"
        raise DisassemblerError(f"unsupported operand formatting for kind {kind!r}")

    def _decode_register(self, raw_code: int, register_set: str, runtime: RuntimeForm, slot_name: str) -> DecodedRegister:
        if register_set == "reg24" and raw_code & 0b100:
            raise DisassemblerError(
                f"{runtime.family_name}.{runtime.form_name}: slot '{slot_name}' uses non-zero high bit for reg24 encoding: {raw_code}"
            )
        code = raw_code & 0b11 if register_set == "reg24" else raw_code
        members = self.register_sets[register_set]
        register = members.get(code)
        if register is None:
            raise DisassemblerError(
                f"{runtime.family_name}.{runtime.form_name}: invalid {register_set} code {code} in slot '{slot_name}'"
            )
        return register

    def _select_union_member(
        self,
        operand_kind_ref: str,
        hint: str,
        runtime: RuntimeForm,
        slot_name: str,
    ) -> str:
        members = self.operand_kinds[operand_kind_ref]["members"]
        for member_ref in members:
            member_spec = self.operand_kinds[member_ref]
            if member_spec["type"] in {"register", "register_subset"} and member_spec["register_set"] == hint:
                return member_ref
        raise DisassemblerError(
            f"{runtime.family_name}.{runtime.form_name}: union {operand_kind_ref} has no member for width hint {hint!r} in slot '{slot_name}'"
        )

    @staticmethod
    def _require_path(path_values: dict[str, int], path: str, runtime: RuntimeForm, slot_name: str) -> int:
        if path not in path_values:
            raise DisassemblerError(f"{runtime.family_name}.{runtime.form_name}: missing encoded value for slot '{slot_name}' via {path}")
        return path_values[path]

@lru_cache(maxsize=1)
def default_disassembler() -> JsonDisassembler:
    return JsonDisassembler.from_default_bundle()
