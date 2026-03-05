# py-dateutil-pydantic

Pydantic v2 annotated types for [python-dateutil](https://dateutil.readthedocs.io/). Validate dateutil objects from JSON-friendly inputs (strings, dicts) and serialize them back — with zero-cost pass-through when you already have a Python object.

## Installation

```bash
pip install py-dateutil-pydantic
```

## Quick Start

```python
from pydantic import BaseModel
from py_dateutil_pydantic import (
    DateutilDatetime,
    DateutilTz,
    RelativeDelta,
    RRule,
    Weekday,
)


class Schedule(BaseModel):
    start: DateutilDatetime
    recurrence: RRule
    offset: RelativeDelta
    day: Weekday
    timezone: DateutilTz


# From JSON-friendly inputs
schedule = Schedule(
    start="January 1, 2024 9:00 AM",
    recurrence="DTSTART:20240101T090000\nRRULE:FREQ=WEEKLY;COUNT=4",
    offset={"hours": 1, "minutes": 30},
    day="MO",
    timezone="America/New_York",
)

# Serialize back to JSON
print(schedule.model_dump(mode="json"))
# {
#     "start": "2024-01-01T09:00:00",
#     "recurrence": "DTSTART:...\nRRULE:FREQ=WEEKLY;COUNT=4",
#     "offset": {"hours": 1, "minutes": 30},
#     "day": "MO",
#     "timezone": "America/New_York",
# }
```

Existing Python objects pass through without parsing overhead:

```python
from datetime import datetime
from dateutil.relativedelta import relativedelta, weekday
from dateutil.rrule import rrule, WEEKLY
from dateutil import tz

schedule = Schedule(
    start=datetime(2024, 1, 1, 9),
    recurrence=rrule(WEEKLY, count=4, dtstart=datetime(2024, 1, 1, 9)),
    offset=relativedelta(hours=1, minutes=30),
    day=weekday(0),
    timezone=tz.gettz("America/New_York"),
)
```

## Types

### `Weekday`

Wraps `dateutil.relativedelta.weekday`.

| Input | Example |
|-------|---------|
| String | `"MO"`, `"FR(+2)"`, `"SA(-1)"` |
| Integer | `0` (Monday) through `6` (Sunday) |

Serializes to string: `"MO"`, `"FR(+2)"`.

### `RelativeDelta`

Wraps `dateutil.relativedelta.relativedelta`.

Accepts a dict with any combination of:

- **Relative keys:** `years`, `months`, `days`, `weeks`, `hours`, `minutes`, `seconds`, `microseconds`
- **Absolute keys:** `year`, `month`, `day`, `hour`, `minute`, `second`, `microsecond`
- **Weekday:** `weekday` (string like `"MO"` or `"FR(+2)"`)

Serializes to a dict of non-default attributes.

### `RRule`

Wraps `dateutil.rrule.rrule`.

| Input | Example |
|-------|---------|
| RFC 5545 string | `"DTSTART:20240101T000000\nRRULE:FREQ=WEEKLY;COUNT=3"` |

Serializes to RFC 5545 string.

### `RRuleSet`

Wraps `dateutil.rrule.rruleset`.

| Input | Example |
|-------|---------|
| RFC 5545 string | Multi-line string with `RRULE`, `RDATE`, `EXRULE`, `EXDATE` lines |

Serializes to RFC 5545 string.

### `DateutilTz`

Wraps `datetime.tzinfo` (via `dateutil.tz`).

| Input | Example |
|-------|---------|
| IANA name | `"America/New_York"`, `"Europe/London"` |
| UTC | `"UTC"` |
| Offset | `"+05:30"`, `"-05:00"` |
| Local | `"local"` |

Serializes with type dispatch: `tzutc` -> `"UTC"`, `tzoffset` -> `"+HH:MM"`, `tzlocal` -> `"local"`, `tzfile` -> IANA name.

### `TzUTC`, `TzOffset`, `TzLocal`

Constrained variants of `DateutilTz` that only accept their specific timezone type.

- **`TzUTC`** — only `"UTC"`
- **`TzOffset`** — offset string `"+05:30"` or dict `{"name": "EST", "offset": -18000}`
- **`TzLocal`** — only `"local"`

### `DateutilDatetime`

Wraps `datetime.datetime`. Accepts any string that `dateutil.parser.parse` can handle:

```python
"January 1, 2024"
"2024-01-01"
"01/15/2024 3:30 PM"
```

Serializes to ISO 8601 via `.isoformat()`.

### `ISODatetime`

Wraps `datetime.datetime`. Accepts only strict ISO 8601 strings (via `dateutil.parser.isoparse`):

```python
"2024-01-01T12:00:00"
"2024-06-15T10:30:00+05:30"
```

Serializes to ISO 8601 via `.isoformat()`.

## JSON Schema

All types generate JSON schemas, so they work with OpenAPI and other tools that consume Pydantic model schemas:

```python
print(Schedule.model_json_schema())
```

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v
```

## License

MIT
