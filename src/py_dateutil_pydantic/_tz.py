"""Pydantic v2 annotated types for dateutil timezone types."""

from __future__ import annotations

import re
from datetime import tzinfo
from typing import Annotated, Any

from dateutil import tz
from dateutil.tz import tzfile, tzlocal, tzoffset, tzutc
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema

_OFFSET_RE = re.compile(r"^([+-])(\d{2}):(\d{2})$")


def _parse_tz(value: str) -> tzinfo:
    """Parse a timezone string into a dateutil tzinfo object."""
    value = value.strip()
    if value.lower() == "local":
        return tz.tzlocal()

    # Explicit UTC handling — tz.gettz("UTC") returns tzfile on some systems
    if value.upper() == "UTC":
        return tz.UTC

    # Try offset format
    m = _OFFSET_RE.match(value)
    if m:
        sign = 1 if m.group(1) == "+" else -1
        hours, minutes = int(m.group(2)), int(m.group(3))
        offset_seconds = sign * (hours * 3600 + minutes * 60)
        return tz.tzoffset(None, offset_seconds)

    # Try IANA / UTC via gettz
    result = tz.gettz(value)
    if result is None:
        raise ValueError(f"Unknown timezone: {value!r}")
    return result


def _serialize_tz(value: tzinfo) -> str:
    """Serialize a tzinfo to a JSON-friendly string."""
    if isinstance(value, tzutc):
        return "UTC"
    if isinstance(value, tzoffset):
        offset = value._offset  # type: ignore[attr-defined]
        total = int(offset.total_seconds())
        sign = "+" if total >= 0 else "-"
        total = abs(total)
        hours, remainder = divmod(total, 3600)
        minutes = remainder // 60
        return f"{sign}{hours:02d}:{minutes:02d}"
    if isinstance(value, tzlocal):
        return "local"
    if isinstance(value, tzfile):
        # tzfile objects from gettz store the IANA name in _filename
        name = getattr(value, "_filename", None)
        if name:
            # Strip zoneinfo path prefix to get IANA name
            parts = name.split("/zoneinfo/")
            if len(parts) > 1:
                return parts[-1]
            return name
    # Fallback: use str
    return str(value)


class _DateutilTzAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(_parse_tz),
            ]
        )
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(tzinfo),
                from_str_schema,
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                _serialize_tz, info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "type": "string",
            "description": "Timezone: IANA name, 'UTC', offset like '+05:30', or 'local'",
        }


class _TzUTCAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        def _validate_utc(value: str) -> tzinfo:
            result = _parse_tz(value)
            if not isinstance(result, tzutc):
                raise ValueError(f"Expected UTC timezone, got {type(result).__name__}")
            return result

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(_validate_utc),
            ]
        )
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(tzutc),
                from_str_schema,
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                _serialize_tz, info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string", "const": "UTC"}


class _TzOffsetAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        def _validate_offset_str(value: str) -> tzinfo:
            result = _parse_tz(value)
            if not isinstance(result, tzoffset):
                raise ValueError(
                    f"Expected offset timezone, got {type(result).__name__}"
                )
            return result

        def _validate_offset_dict(value: dict[str, Any]) -> tzinfo:
            name = value.get("name")
            offset = value.get("offset")
            if offset is None:
                raise ValueError("Offset dict must contain 'offset' key (seconds)")
            return tz.tzoffset(name, int(offset))

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(_validate_offset_str),
            ]
        )
        from_dict_schema = core_schema.chain_schema(
            [
                core_schema.dict_schema(
                    keys_schema=core_schema.str_schema(),
                    values_schema=core_schema.any_schema(),
                ),
                core_schema.no_info_plain_validator_function(_validate_offset_dict),
            ]
        )
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(tzoffset),
                from_str_schema,
                from_dict_schema,
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                _serialize_tz, info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "anyOf": [
                {"type": "string", "pattern": r"^[+-]\d{2}:\d{2}$"},
                {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "offset": {"type": "integer"},
                    },
                    "required": ["offset"],
                },
            ]
        }


class _TzLocalAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        def _validate_local(value: str) -> tzinfo:
            result = _parse_tz(value)
            if not isinstance(result, tzlocal):
                raise ValueError(
                    f"Expected local timezone, got {type(result).__name__}"
                )
            return result

        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(_validate_local),
            ]
        )
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(tzlocal),
                from_str_schema,
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                _serialize_tz, info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {"type": "string", "const": "local"}


DateutilTz = Annotated[tzinfo, _DateutilTzAnnotation]
TzUTC = Annotated[tzutc, _TzUTCAnnotation]
TzOffset = Annotated[tzoffset, _TzOffsetAnnotation]
TzLocal = Annotated[tzlocal, _TzLocalAnnotation]
