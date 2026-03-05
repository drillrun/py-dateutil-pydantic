"""Tests for RRule and RRuleSet types."""

import pytest
from dateutil.rrule import WEEKLY, rrule, rruleset
from datetime import datetime
from pydantic import BaseModel, ValidationError

from py_dateutil_pydantic import RRule, RRuleSet


class RRuleModel(BaseModel):
    rule: RRule


class RRuleSetModel(BaseModel):
    ruleset: RRuleSet


class TestRRulePassthrough:
    def test_instance(self):
        r = rrule(WEEKLY, count=3, dtstart=datetime(2024, 1, 1))
        m = RRuleModel(rule=r)
        assert list(m.rule) == list(r)


class TestRRuleFromString:
    def test_simple(self):
        s = "DTSTART:20240101T000000\nRRULE:FREQ=WEEKLY;COUNT=3"
        m = RRuleModel(rule=s)
        dates = list(m.rule)
        assert len(dates) == 3
        assert dates[0] == datetime(2024, 1, 1)

    def test_daily(self):
        s = "DTSTART:20240101T000000\nRRULE:FREQ=DAILY;COUNT=5"
        m = RRuleModel(rule=s)
        assert len(list(m.rule)) == 5


class TestRRuleSerialization:
    def test_serialize(self):
        r = rrule(WEEKLY, count=3, dtstart=datetime(2024, 1, 1))
        m = RRuleModel(rule=r)
        data = m.model_dump(mode="json")
        assert isinstance(data["rule"], str)
        assert "FREQ=WEEKLY" in data["rule"]

    def test_json_roundtrip(self):
        s = "DTSTART:20240101T000000\nRRULE:FREQ=WEEKLY;COUNT=3"
        m = RRuleModel(rule=s)
        data = m.model_dump(mode="json")
        m2 = RRuleModel(rule=data["rule"])
        assert list(m2.rule) == list(m.rule)


class TestRRuleSetFromString:
    def test_simple(self):
        s = "DTSTART:20240101T000000\nRRULE:FREQ=WEEKLY;COUNT=3"
        m = RRuleSetModel(ruleset=s)
        dates = list(m.ruleset)
        assert len(dates) == 3

    def test_passthrough(self):
        rs = rruleset()
        rs.rrule(rrule(WEEKLY, count=2, dtstart=datetime(2024, 1, 1)))
        m = RRuleSetModel(ruleset=rs)
        assert len(list(m.ruleset)) == 2


class TestRRuleSetSerialization:
    def test_serialize(self):
        rs = rruleset()
        rs.rrule(rrule(WEEKLY, count=2, dtstart=datetime(2024, 1, 1)))
        m = RRuleSetModel(ruleset=rs)
        data = m.model_dump(mode="json")
        assert isinstance(data["ruleset"], str)
        assert "FREQ=WEEKLY" in data["ruleset"]


class TestRRuleErrors:
    def test_invalid_string(self):
        with pytest.raises(ValidationError):
            RRuleModel(rule="not a valid rrule")


class TestRRuleJsonSchema:
    def test_schema(self):
        schema = RRuleModel.model_json_schema()
        assert schema["properties"]["rule"]["type"] == "string"
