"""Tests for DateutilDatetime and ISODatetime types."""

import pytest
from datetime import datetime
from pydantic import BaseModel, ValidationError

from py_dateutil_pydantic import DateutilDatetime, ISODatetime


class DateutilModel(BaseModel):
    dt: DateutilDatetime


class ISOModel(BaseModel):
    dt: ISODatetime


class TestDateutilDatetimePassthrough:
    def test_instance(self):
        dt = datetime(2024, 1, 1, 12, 0)
        m = DateutilModel(dt=dt)
        assert m.dt == dt


class TestDateutilDatetimeFromString:
    def test_iso_format(self):
        m = DateutilModel(dt="2024-01-01T12:00:00")
        assert m.dt == datetime(2024, 1, 1, 12, 0)

    def test_natural_format(self):
        m = DateutilModel(dt="January 1, 2024")
        assert m.dt.year == 2024
        assert m.dt.month == 1
        assert m.dt.day == 1

    def test_us_date(self):
        m = DateutilModel(dt="01/15/2024")
        assert m.dt.month == 1
        assert m.dt.day == 15


class TestDateutilDatetimeSerialization:
    def test_isoformat(self):
        m = DateutilModel(dt=datetime(2024, 1, 1, 12, 0))
        data = m.model_dump(mode="json")
        assert data["dt"] == "2024-01-01T12:00:00"

    def test_json_roundtrip(self):
        m = DateutilModel(dt="January 1, 2024 12:00")
        data = m.model_dump(mode="json")
        m2 = DateutilModel.model_validate(data)
        assert m2.dt == m.dt


class TestISODatetimePassthrough:
    def test_instance(self):
        dt = datetime(2024, 6, 15, 10, 30)
        m = ISOModel(dt=dt)
        assert m.dt == dt


class TestISODatetimeFromString:
    def test_iso(self):
        m = ISOModel(dt="2024-06-15T10:30:00")
        assert m.dt == datetime(2024, 6, 15, 10, 30)

    def test_date_only(self):
        m = ISOModel(dt="2024-06-15")
        assert m.dt.year == 2024

    def test_with_timezone(self):
        m = ISOModel(dt="2024-06-15T10:30:00+05:30")
        assert m.dt.year == 2024
        assert m.dt.tzinfo is not None


class TestISODatetimeSerialization:
    def test_isoformat(self):
        m = ISOModel(dt=datetime(2024, 6, 15, 10, 30))
        data = m.model_dump(mode="json")
        assert data["dt"] == "2024-06-15T10:30:00"

    def test_json_roundtrip(self):
        m = ISOModel(dt="2024-06-15T10:30:00")
        data = m.model_dump(mode="json")
        m2 = ISOModel.model_validate(data)
        assert m2.dt == m.dt


class TestISODatetimeErrors:
    def test_non_iso(self):
        with pytest.raises(ValidationError):
            ISOModel(dt="January 1, 2024")


class TestParsingJsonSchema:
    def test_dateutil_schema(self):
        schema = DateutilModel.model_json_schema()
        assert schema["properties"]["dt"]["type"] == "string"

    def test_iso_schema(self):
        schema = ISOModel.model_json_schema()
        assert schema["properties"]["dt"]["type"] == "string"
        assert schema["properties"]["dt"]["format"] == "date-time"
