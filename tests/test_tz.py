"""Tests for timezone types."""

import pytest
from dateutil import tz
from dateutil.tz import tzlocal, tzoffset, tzutc
from pydantic import BaseModel, ValidationError

from py_dateutil_pydantic import DateutilTz, TzLocal, TzOffset, TzUTC


class TzModel(BaseModel):
    timezone: DateutilTz


class UTCModel(BaseModel):
    timezone: TzUTC


class OffsetModel(BaseModel):
    timezone: TzOffset


class LocalModel(BaseModel):
    timezone: TzLocal


class TestDateutilTzPassthrough:
    def test_utc_instance(self):
        m = TzModel(timezone=tz.UTC)
        assert isinstance(m.timezone, tzutc)

    def test_tzlocal_instance(self):
        m = TzModel(timezone=tz.tzlocal())
        assert isinstance(m.timezone, tzlocal)


class TestDateutilTzFromString:
    def test_utc(self):
        m = TzModel(timezone="UTC")
        assert isinstance(m.timezone, tzutc)

    def test_iana(self):
        m = TzModel(timezone="America/New_York")
        assert m.timezone is not None

    def test_offset(self):
        m = TzModel(timezone="+05:30")
        assert isinstance(m.timezone, tzoffset)

    def test_local(self):
        m = TzModel(timezone="local")
        assert isinstance(m.timezone, tzlocal)

    def test_negative_offset(self):
        m = TzModel(timezone="-05:00")
        assert isinstance(m.timezone, tzoffset)


class TestDateutilTzSerialization:
    def test_utc(self):
        m = TzModel(timezone=tz.UTC)
        assert m.model_dump(mode="json") == {"timezone": "UTC"}

    def test_local(self):
        m = TzModel(timezone=tz.tzlocal())
        assert m.model_dump(mode="json") == {"timezone": "local"}

    def test_offset(self):
        m = TzModel(timezone=tz.tzoffset(None, 19800))
        data = m.model_dump(mode="json")
        assert data["timezone"] == "+05:30"

    def test_negative_offset(self):
        m = TzModel(timezone=tz.tzoffset(None, -18000))
        data = m.model_dump(mode="json")
        assert data["timezone"] == "-05:00"

    def test_utc_roundtrip(self):
        m = TzModel(timezone="UTC")
        data = m.model_dump(mode="json")
        m2 = TzModel.model_validate(data)
        assert isinstance(m2.timezone, tzutc)


class TestTzUTC:
    def test_utc_string(self):
        m = UTCModel(timezone="UTC")
        assert isinstance(m.timezone, tzutc)

    def test_instance(self):
        m = UTCModel(timezone=tz.UTC)
        assert isinstance(m.timezone, tzutc)

    def test_rejects_non_utc(self):
        with pytest.raises(ValidationError):
            UTCModel(timezone="+05:00")


class TestTzOffset:
    def test_offset_string(self):
        m = OffsetModel(timezone="+05:30")
        assert isinstance(m.timezone, tzoffset)

    def test_offset_dict(self):
        m = OffsetModel(timezone={"name": "EST", "offset": -18000})
        assert isinstance(m.timezone, tzoffset)

    def test_instance(self):
        m = OffsetModel(timezone=tz.tzoffset("EST", -18000))
        assert isinstance(m.timezone, tzoffset)

    def test_rejects_utc(self):
        with pytest.raises(ValidationError):
            OffsetModel(timezone="UTC")


class TestTzLocal:
    def test_local_string(self):
        m = LocalModel(timezone="local")
        assert isinstance(m.timezone, tzlocal)

    def test_instance(self):
        m = LocalModel(timezone=tz.tzlocal())
        assert isinstance(m.timezone, tzlocal)

    def test_rejects_utc(self):
        with pytest.raises(ValidationError):
            LocalModel(timezone="UTC")


class TestDateutilTzErrors:
    def test_unknown(self):
        with pytest.raises(ValidationError):
            TzModel(timezone="Not/A/Timezone")


class TestTzJsonSchema:
    def test_schema(self):
        schema = TzModel.model_json_schema()
        assert "timezone" in schema["properties"]
