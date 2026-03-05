"""Pydantic v2 annotated types for dateutil rrule and rruleset."""

from __future__ import annotations

from typing import Annotated, Any

from dateutil.rrule import rrule, rruleset, rrulestr
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema


def _parse_rrule(value: str) -> rrule:
    result = rrulestr(value)
    if not isinstance(result, rrule):
        raise ValueError(
            f"Input parsed as rruleset, not rrule. Use RRuleSet type instead."
        )
    return result


def _serialize_rrule(value: rrule) -> str:
    return str(value)


def _parse_rruleset(value: str) -> rruleset:
    result = rrulestr(value, forceset=True)
    assert isinstance(result, rruleset)
    return result


def _serialize_rruleset(value: rruleset) -> str:
    parts: list[str] = []

    # dtstart from first rrule if available
    rrules = value._rrule  # type: ignore[attr-defined]
    if rrules:
        dtstart = rrules[0]._dtstart  # type: ignore[attr-defined]
        if dtstart is not None:
            parts.append(f"DTSTART:{dtstart.strftime('%Y%m%dT%H%M%S')}")

    for r in rrules:
        line = str(r)
        # str(rrule) includes DTSTART, extract just the RRULE line
        for ln in line.splitlines():
            if ln.startswith("RRULE:"):
                parts.append(ln)

    for dt in value._rdate:  # type: ignore[attr-defined]
        parts.append(f"RDATE:{dt.strftime('%Y%m%dT%H%M%S')}")

    for r in value._exrule:  # type: ignore[attr-defined]
        line = str(r)
        for ln in line.splitlines():
            if ln.startswith("RRULE:"):
                parts.append(ln.replace("RRULE:", "EXRULE:", 1))

    for dt in value._exdate:  # type: ignore[attr-defined]
        parts.append(f"EXDATE:{dt.strftime('%Y%m%dT%H%M%S')}")

    return "\n".join(parts)


class _RRuleAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(_parse_rrule),
            ]
        )
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(rrule),
                from_str_schema,
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                _serialize_rrule, info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "type": "string",
            "description": "RFC 5545 RRULE string",
        }


class _RRuleSetAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(_parse_rruleset),
            ]
        )
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(rruleset),
                from_str_schema,
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                _serialize_rruleset, info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "type": "string",
            "description": "RFC 5545 RRULE set string (may contain RRULE, RDATE, EXRULE, EXDATE lines)",
        }


RRule = Annotated[rrule, _RRuleAnnotation]
RRuleSet = Annotated[rruleset, _RRuleSetAnnotation]
