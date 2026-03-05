"""Integration tests: multiple types combined in a single model."""

from datetime import datetime, tzinfo

from dateutil.relativedelta import relativedelta, weekday
from dateutil.rrule import WEEKLY, rrule
from pydantic import BaseModel

from py_dateutil_pydantic import (
    DateutilDatetime,
    DateutilTz,
    RelativeDelta,
    RRule,
    Weekday,
)


class ScheduleModel(BaseModel):
    start: DateutilDatetime
    recurrence: RRule
    offset: RelativeDelta
    day: Weekday
    timezone: DateutilTz


class TestIntegration:
    def test_from_json_types(self):
        m = ScheduleModel(
            start="2024-01-01T09:00:00",
            recurrence="DTSTART:20240101T090000\nRRULE:FREQ=WEEKLY;COUNT=4",
            offset={"hours": 1, "minutes": 30},
            day="MO",
            timezone="America/New_York",
        )
        assert isinstance(m.start, datetime)
        assert isinstance(m.offset, relativedelta)
        assert isinstance(m.day, weekday)
        assert isinstance(m.timezone, tzinfo)
        assert len(list(m.recurrence)) == 4

    def test_from_python_types(self):
        from dateutil import tz

        m = ScheduleModel(
            start=datetime(2024, 1, 1, 9),
            recurrence=rrule(WEEKLY, count=4, dtstart=datetime(2024, 1, 1, 9)),
            offset=relativedelta(hours=1, minutes=30),
            day=weekday(0),
            timezone=tz.gettz("America/New_York"),
        )
        assert m.start.year == 2024

    def test_json_roundtrip(self):
        m = ScheduleModel(
            start="2024-01-01T09:00:00",
            recurrence="DTSTART:20240101T090000\nRRULE:FREQ=WEEKLY;COUNT=4",
            offset={"hours": 1, "minutes": 30},
            day="MO",
            timezone="UTC",
        )
        data = m.model_dump(mode="json")
        m2 = ScheduleModel.model_validate(data)
        assert m2.start == m.start
        assert m2.day == m.day
        assert list(m2.recurrence) == list(m.recurrence)

    def test_json_schema(self):
        schema = ScheduleModel.model_json_schema()
        assert set(schema["properties"].keys()) == {
            "start",
            "recurrence",
            "offset",
            "day",
            "timezone",
        }
