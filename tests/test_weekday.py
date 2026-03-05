"""Tests for Weekday type."""

import pytest
from dateutil.relativedelta import weekday
from pydantic import BaseModel, ValidationError

from py_dateutil_pydantic import Weekday


class WeekdayModel(BaseModel):
    day: Weekday


class TestWeekdayPassthrough:
    def test_weekday_instance(self):
        m = WeekdayModel(day=weekday(0))
        assert m.day == weekday(0)

    def test_weekday_with_n(self):
        m = WeekdayModel(day=weekday(4, 2))
        assert m.day == weekday(4, 2)


class TestWeekdayFromString:
    @pytest.mark.parametrize("s,expected", [
        ("MO", weekday(0)),
        ("TU", weekday(1)),
        ("WE", weekday(2)),
        ("TH", weekday(3)),
        ("FR", weekday(4)),
        ("SA", weekday(5)),
        ("SU", weekday(6)),
    ])
    def test_simple_names(self, s, expected):
        m = WeekdayModel(day=s)
        assert m.day == expected

    def test_case_insensitive(self):
        m = WeekdayModel(day="mo")
        assert m.day == weekday(0)

    def test_with_positive_n(self):
        m = WeekdayModel(day="FR(+2)")
        assert m.day == weekday(4, 2)

    def test_with_negative_n(self):
        m = WeekdayModel(day="SA(-1)")
        assert m.day == weekday(5, -1)


class TestWeekdayFromInt:
    def test_int_0(self):
        m = WeekdayModel(day=0)
        assert m.day == weekday(0)

    def test_int_6(self):
        m = WeekdayModel(day=6)
        assert m.day == weekday(6)


class TestWeekdaySerialization:
    def test_simple(self):
        m = WeekdayModel(day=weekday(0))
        assert m.model_dump() == {"day": "MO"}

    def test_with_n(self):
        m = WeekdayModel(day=weekday(4, 2))
        assert m.model_dump() == {"day": "FR(+2)"}

    def test_json_roundtrip(self):
        m = WeekdayModel(day="FR(+2)")
        data = m.model_dump(mode="json")
        m2 = WeekdayModel.model_validate(data)
        assert m2.day == m.day


class TestWeekdayErrors:
    def test_invalid_string(self):
        with pytest.raises(ValidationError):
            WeekdayModel(day="INVALID")

    def test_int_out_of_range(self):
        with pytest.raises(ValidationError):
            WeekdayModel(day=7)


class TestWeekdayJsonSchema:
    def test_schema_generated(self):
        schema = WeekdayModel.model_json_schema()
        assert "properties" in schema
        assert "day" in schema["properties"]
