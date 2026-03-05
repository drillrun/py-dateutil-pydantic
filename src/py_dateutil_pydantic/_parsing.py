"""Pydantic v2 annotated types for dateutil datetime parsing."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from dateutil import parser as dateutil_parser
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema


def _parse_dateutil(value: str) -> datetime:
    """Parse a datetime string using dateutil.parser.parse."""
    return dateutil_parser.parse(value)


def _parse_iso(value: str) -> datetime:
    """Parse a strict ISO 8601 datetime string using dateutil.parser.isoparse."""
    return dateutil_parser.isoparse(value)


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat()


class _DateutilDatetimeAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(_parse_dateutil),
            ]
        )
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(datetime),
                from_str_schema,
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                _serialize_datetime, info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "type": "string",
            "description": "Datetime string parseable by dateutil.parser.parse",
        }


class _ISODatetimeAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(_parse_iso),
            ]
        )
        return core_schema.union_schema(
            [
                core_schema.is_instance_schema(datetime),
                from_str_schema,
            ],
            serialization=core_schema.plain_serializer_function_ser_schema(
                _serialize_datetime, info_arg=False
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        return {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 datetime string",
        }


DateutilDatetime = Annotated[datetime, _DateutilDatetimeAnnotation]
ISODatetime = Annotated[datetime, _ISODatetimeAnnotation]
