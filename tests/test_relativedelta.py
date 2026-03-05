"""Tests for RelativeDelta type."""

import pytest
from dateutil.relativedelta import relativedelta, weekday
from pydantic import BaseModel, ValidationError

from py_dateutil_pydantic import RelativeDelta


class RDModel(BaseModel):
    delta: RelativeDelta


class TestRelativeDeltaPassthrough:
    def test_instance(self):
        rd = relativedelta(years=1, months=2)
        m = RDModel(delta=rd)
        assert m.delta == rd


class TestRelativeDeltaFromDict:
    def test_relative_keys(self):
        m = RDModel(delta={"years": 1, "months": 2, "days": 3})
        assert m.delta.years == 1
        assert m.delta.months == 2
        assert m.delta.days == 3

    def test_absolute_keys(self):
        m = RDModel(delta={"year": 2024, "month": 6, "day": 15})
        assert m.delta.year == 2024
        assert m.delta.month == 6
        assert m.delta.day == 15

    def test_with_weekday_string(self):
        m = RDModel(delta={"weekday": "FR(+2)"})
        assert m.delta.weekday == weekday(4, 2)

    def test_with_weekday_int(self):
        m = RDModel(delta={"weekday": 0})
        assert m.delta.weekday == weekday(0)

    def test_empty_dict(self):
        m = RDModel(delta={})
        assert m.delta == relativedelta()


class TestRelativeDeltaSerialization:
    def test_relative(self):
        m = RDModel(delta=relativedelta(years=1, days=5))
        d = m.model_dump()
        assert d["delta"]["years"] == 1
        assert d["delta"]["days"] == 5

    def test_absolute(self):
        m = RDModel(delta=relativedelta(year=2024, month=1))
        d = m.model_dump()
        assert d["delta"]["year"] == 2024
        assert d["delta"]["month"] == 1

    def test_weekday_serialized(self):
        m = RDModel(delta=relativedelta(weekday=weekday(4, 2)))
        d = m.model_dump()
        assert d["delta"]["weekday"] == "FR(+2)"

    def test_json_roundtrip(self):
        m = RDModel(delta={"years": 1, "months": 2, "weekday": "MO"})
        data = m.model_dump(mode="json")
        m2 = RDModel.model_validate(data)
        assert m2.delta.years == m.delta.years
        assert m2.delta.months == m.delta.months


class TestRelativeDeltaErrors:
    def test_unknown_key(self):
        with pytest.raises(ValidationError):
            RDModel(delta={"invalid_key": 1})


class TestRelativeDeltaJsonSchema:
    def test_schema(self):
        schema = RDModel.model_json_schema()
        assert "delta" in schema["properties"]
