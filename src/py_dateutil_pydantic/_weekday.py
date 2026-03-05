"""Pydantic v2 annotated type for dateutil weekday."""

from __future__ import annotations

import re
from typing import Annotated, Any

from dateutil.relativedelta import weekday
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema

_WEEKDAY_NAMES = ("MO", "TU", "WE", "TH", "FR", "SA", "SU")
_WEEKDAY_RE = re.compile(
    r"^(MO|TU|WE|TH|FR|SA|SU)(?:\(([+-]?\d+)\))?$", re.IGNORECASE
)


def parse_weekday_string(value: str) -> weekday:
    """Parse a weekday string like 'MO', 'FR(+2)', 'SA(-1)' into a dateutil weekday."""
    m = _WEEKDAY_RE.match(value.strip())
    if not m:
        raise ValueError(
            f"Invalid weekday string: {value!r}. "
            f"Expected format like 'MO', 'FR(+2)', 'SA(-1)'."
        )
    name = m.group(1).upper()
    idx = _WEEKDAY_NAMES.index(name)
    n = int(m.group(2)) if m.group(2) else None
    return weekday(idx, n)


def _serialize_weekday(value: weekday) -> str:
    name = _WEEKDAY_NAMES[value.weekday]
    if value.n is None:
        return name
    return f"{name}({value.n:+d})"


class _WeekdayAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(parse_weekday_string),
            ]
        )
        from_int_schema = core_schema.chain_schema(
            [
                core_schema.int_schema(ge=0, le=6),
                core_schema.no_info_plain_validator_function(lambda v: weekday(v)),
            ]
        )
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(weekday),
                from_str_schema,
                from_int_schema,
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                _serialize_weekday, info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "anyOf": [
                {
                    "type": "string",
                    "pattern": r"^(MO|TU|WE|TH|FR|SA|SU)(\([+-]?\d+\))?$",
                },
                {"type": "integer", "minimum": 0, "maximum": 6},
            ]
        }


Weekday = Annotated[weekday, _WeekdayAnnotation]
