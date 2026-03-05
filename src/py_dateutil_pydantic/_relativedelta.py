"""Pydantic v2 annotated type for dateutil relativedelta."""

from __future__ import annotations

from typing import Annotated, Any

from dateutil.relativedelta import relativedelta, weekday
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema

from ._weekday import _serialize_weekday, parse_weekday_string

_RELATIVE_KEYS = (
    "years",
    "months",
    "days",
    "weeks",
    "hours",
    "minutes",
    "seconds",
    "microseconds",
)
_ABSOLUTE_KEYS = (
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "second",
    "microsecond",
)
_ALL_KEYS = _RELATIVE_KEYS + _ABSOLUTE_KEYS + ("weekday",)


def _parse_relativedelta(value: dict[str, Any]) -> relativedelta:
    unknown = set(value.keys()) - set(_ALL_KEYS)
    if unknown:
        raise ValueError(f"Unknown relativedelta keys: {unknown}")

    kwargs: dict[str, Any] = {}
    for key in _RELATIVE_KEYS + _ABSOLUTE_KEYS:
        if key in value:
            kwargs[key] = value[key]

    if "weekday" in value:
        wd = value["weekday"]
        if isinstance(wd, str):
            kwargs["weekday"] = parse_weekday_string(wd)
        elif isinstance(wd, int):
            kwargs["weekday"] = weekday(wd)
        elif isinstance(wd, weekday):
            kwargs["weekday"] = wd
        else:
            raise ValueError(f"Invalid weekday value: {wd!r}")

    return relativedelta(**kwargs)


def _serialize_relativedelta(value: relativedelta) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in _RELATIVE_KEYS:
        v = getattr(value, key, 0)
        if key == "weeks":
            continue  # weeks is folded into days
        if v:
            result[key] = v
    for key in _ABSOLUTE_KEYS:
        v = getattr(value, key, None)
        if v is not None:
            result[key] = v
    if value.weekday is not None:
        result["weekday"] = _serialize_weekday(value.weekday)
    return result


class _RelativeDeltaAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        from_dict_schema = core_schema.chain_schema(
            [
                core_schema.dict_schema(
                    keys_schema=core_schema.str_schema(),
                    values_schema=core_schema.any_schema(),
                ),
                core_schema.no_info_plain_validator_function(_parse_relativedelta),
            ]
        )
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(relativedelta),
                from_dict_schema,
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                _serialize_relativedelta, info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "type": "object",
            "properties": {
                **{k: {"type": "number"} for k in _RELATIVE_KEYS},
                **{k: {"type": "integer"} for k in _ABSOLUTE_KEYS},
                "weekday": {"type": "string"},
            },
            "additionalProperties": False,
        }


RelativeDelta = Annotated[relativedelta, _RelativeDeltaAnnotation]
