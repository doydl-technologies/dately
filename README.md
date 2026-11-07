<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/doydl-technologies/dately/main/assets/png/dately-endorsed-lockup-light-1135x409-384dpi.png">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/doydl-technologies/dately/main/assets/png/dately-endorsed-lockup-dark-1135x409-384dpi.png">
    <img src="https://raw.githubusercontent.com/doydl-technologies/dately/main/assets/png/dately-endorsed-lockup-dark-1135x409-384dpi.png" alt="dately — powered by DOYDL Technologies" width="700">
  </picture>
</p>

<p align="center">
  Deterministic date, time, timezone, holiday, and natural-language temporal processing for Python.
</p>

<p align="center">
  <a href="https://pypi.org/project/dately/"><img src="https://img.shields.io/pypi/v/dately" alt="PyPI version"></a>
  <a href="https://pypi.org/project/dately/"><img src="https://img.shields.io/pypi/pyversions/dately" alt="Supported Python versions"></a>
  <a href="https://pepy.tech/project/dately"><img src="https://static.pepy.tech/badge/dately" alt="Downloads"></a>
  <a href="https://doydl.com"><img src="https://img.shields.io/badge/Powered%20by-DOYDL%20Technologies-blue" alt="Powered by DOYDL Technologies"></a>
</p>

## Overview

`dately` parses, detects, converts, replaces, and normalizes date and time values. It accepts individual strings as well as lists, dictionaries, NumPy arrays, and pandas Series. Its rule-based NLP engine also resolves expressions such as:

- `first Monday of next month`
- `last 5 weekends`
- `Q3 of last year`
- `3 days ago starting from April 10`

The library includes Cython extensions for frequently used parsing operations and compatibility handling for platform-specific date-format behavior.

## Installation

Install the latest published release from PyPI:

```bash
python -m pip install dately
```

To test a local checkout in an isolated environment:

```bash
python -m venv .venv-test
# Windows/MSYS2:
source .venv-test/Scripts/activate
# macOS/Linux instead: source .venv-test/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
python -m pytest -q
```

The release build matrix targets CPython 3.8-3.14 on:

| System | Wheel architecture | Notes |
| --- | --- | --- |
| Windows | x64 (AMD64) | Native Windows wheels |
| Linux | x86-64 | manylinux, glibc 2.28 or newer |
| macOS | Intel x86-64 | Built and tested on an Intel runner |
| macOS | Apple Silicon arm64 | Built and tested on an ARM runner |

Use the wheel matching your Python version and architecture. Linux ARM, Alpine/
musllinux, and Windows ARM wheels are outside this release matrix. Native macOS
and Linux support is verified by their CI jobs; local Windows tests alone do not
establish compatibility with those systems.

Source installs require a C compiler compatible with Python (MSVC on Windows,
Xcode Command Line Tools on macOS, or a C compiler/Python development headers on
Linux). The build installs Cython automatically and compiles all seven extensions.
Precompiled Windows binaries are not kept in the source tree. Timezone data is
supplied by the `tzdata` dependency on Python 3.9+, with the existing `pytz` path
on Python 3.8.

The build workflow uses pinned `cibuildwheel` 3.4.0, which supports the complete
Python 3.8-3.14 matrix. Every wheel is installed into an isolated test environment
and tested there. CI also rebuilds a wheel from the source archive and tests it.
The Python 3.8 Apple Silicon wheel has an additional native test job using a
managed CPython 3.8 interpreter because the wheel builder's installer is x86-only.
Release validation requires each Python/platform pair and a matching source
archive; it checks coverage rather than relying on a fixed download count.

Tagged builds can publish a GitHub release after the full matrix succeeds.
Manual publication requires both a stable `vX.Y.Z` tag and its successful build
run ID. The release workflow checks the build's repository, workflow, event, and
commit against the tag, uploads all files to a draft, then publishes the complete
release. Branch/PR builds do not automatically publish releases.

## Quick start

```python
import dately as dtly

dtly.detect_date_format("2024-03-13T14:30:00")
# '%Y-%m-%dT%H:%M:%S'

dtly.replace_datestring(
    "2024-03-13T14:30:00",
    year=2025,
    month=12,
    day=25,
)
# '2025-12-25T14:30:00'

dtly.replace_timestring(
    "2024-03-13 T14:30:00",
    hour=9,
    minute=15,
    tzinfo="Europe/London",
)
# '2024-03-13 T09:15:00 Europe/London'

dtly.parse("first Monday of next month")
# datetime.date(...) relative to the current date
```

## Capabilities

### Format detection and conversion

- Detect common and custom date/time formats.
- Convert values to a requested output format.
- Extract individual year, month, day, time, and timezone components.
- Process scalar values and nested collections.

### Date and time replacement

- Replace selected date or time components without rebuilding the input manually.
- Preserve the original date/time separator where supported.
- Work with ISO-8601 and non-ISO strings.

### Natural-language parsing

- Resolve relative, ordinal, anchored, and range expressions.
- Interpret quarters, weeks, weekends, weekdays, months, and years.
- Configure the first day of the week with `set_week_start()`.
- Return exact dates or date ranges through a deterministic rule-based pipeline.

### Business days (3.4.0)

Business days and working days are aliases. By default they mean Monday-Friday,
without holiday exclusions. Specify a country to exclude its public holidays
automatically, including observed dates where supported:

```python
import dately as dtly

dtly.parse("1 business day after 2026-11-25", country="US")
# datetime.date(2026, 11, 27): skips Thanksgiving

dtly.parse("next working day", country="united states", subdiv="WI")
dtly.parse("last business day of next month", country="Belgium")
dtly.parse("1 business day after 2026-07-02", country="US", observed=False)
# datetime.date(2026, 7, 3): excludes the actual holiday, without its observed date
```

`country` accepts the same names, aliases, and ISO alpha-2 codes as `Holidate`.
`subdiv` is an optional state/province code, and `observed` defaults to `True`.
Holidays are loaded offline through the holiday module for each year visited by
the calculation, including dates in other years and crossings into a new year.
Only the calendar's requested years are cached, separately for each calendar.
Country selection supplies holidays; the working week still defaults to
Monday-Friday. A country does not automatically select a different working week.

For company closures or a different workweek, supply a reusable calendar. You can
combine a country with extra closure dates:

```python
from datetime import date
import dately as dtly

calendar = dtly.BusinessCalendar(
    country="US",              # optional; omit for a calendar of supplied dates only
    working_days=(0, 1, 2, 3, 4),  # Monday=0, Sunday=6
    holidays={date(2026, 11, 27)},  # additional company closure after Thanksgiving
)

dtly.parse("1 business day after 2026-11-25", business_calendar=calendar)
# datetime.date(2026, 11, 30): skips Thanksgiving, the closure, and the weekend

dtly.parse("in 3 business days", business_calendar=calendar)
dtly.parse("next working day", business_calendar=calendar)
dtly.parse("3 business days after November 6", business_calendar=calendar)
dtly.parse("3 business days ago starting from April 10")
dtly.parse("last business day of next month")
dtly.parse("third business day of February 2027")
dtly.parse("first 5 business days of next month")
```

`in N business days` and `N business days ago` return a single date, excluding
the starting date from the count. Zero preserves the starting date.
`next N business days` / `last N business days` return eligible dates in traversal
order (a single date when N=1). Scoped selections such as `first 5 business days
of next month` return eligible dates in chronological order. They return `None`
if the scope has too few eligible dates. A scope can be a week, month, quarter,
year, or another period already supported by Dately.

`weekday` expressions always use Monday-Friday and ignore a supplied business
calendar or country holiday exclusions. `country` and `business_calendar` are
mutually exclusive parser arguments; put `country`, `subdiv`, and `observed` on
the calendar when supplying one. Calendar definitions are immutable, and country
options on one parse call do not affect later calls.

Invalid or unsupported countries/subdivisions raise `TypeError`/`ValueError`.
Unavailable holiday data raises `HolidayLookupError` through the parser; it does
not silently fall back to counting dates without the requested holidays.

Explicit forward offsets (`in 3 days`, `in 2 weeks`, `in 1 month`, `in 1 year`)
now return the offset date. Existing `next N days` range behavior is preserved.

### Fiscal calendars (optional)

Choose a calendar object and either pass it to `parse()` or set it as the default
for the current execution context. The default fiscal calendar is January-December.
Fiscal configuration applies to explicit phrases such as `FY2027`, `this fiscal
quarter`, and `P2 FY2027`. Ordinary `this year` and `Q1 2027` keep their existing
calendar-year meanings.

```python
import dately as dtly

# July-June; FY2027 means July 2026 through June 2027.
fiscal = dtly.FiscalCalendar(start_month=7, year_label="end")
dtly.parse("Q1 FY2027", fiscal_calendar=fiscal)
# (datetime.date(2026, 7, 1), datetime.date(2026, 9, 30))

# Optional default: choose once, reuse for subsequent calls in this context.
dtly.set_fiscal_calendar(fiscal)
dtly.parse("this fiscal year")
dtly.parse("next fiscal quarter")
dtly.parse("end of FY2027")
dtly.parse("first business day of Q3 FY2027", country="US")
# datetime.date(2027, 1, 4): skips New Year's Day and the weekend
dtly.get_fiscal_calendar()
dtly.set_fiscal_calendar(None)  # restore the January-December default
```

`FiscalCalendar` starts on the first day of any month, with three-month quarters
and monthly periods. `year_label="start"` instead labels July 2026-June 2027 as
FY2026. For January starts, both conventions use the same year.

For week-based years, select `RetailFiscalCalendar`. The same parser and direct
methods work with 4-4-5, 4-5-4, 5-4-4, or a custom period pattern:

```python
retail = dtly.RetailFiscalCalendar(
    pattern=(4, 4, 5),        # or (4, 5, 4), (5, 4, 4), or another custom pattern
    start_month=2, start_day=1,
    week_start=6,             # Sunday; Monday=0
    alignment="nearest",     # or "on_or_before" / "on_or_after"
    year_label="end",
    leap_week_period=12,      # place a 53rd week in period 12
)
dtly.parse("P2 FY2024", fiscal_calendar=retail)
dtly.parse("Q4 FY2024", fiscal_calendar=retail)
retail.year_range(2024)
# (datetime.date(2023, 1, 29), datetime.date(2024, 2, 3)): a 53-week year

# An entire custom 52-week pattern with 13 periods of four weeks.
custom = dtly.RetailFiscalCalendar(
    pattern=(4,) * 13,
    quarter_periods=(3, 3, 3, 4),  # group the 13 periods into four quarters
    start_month=10, start_day=1,
    week_start=0, alignment="on_or_after",
)
dtly.parse("P13 FY2024", fiscal_calendar=custom)
```

A three-period pattern totaling 13 weeks repeats four times. Alternatively,
supply a full pattern of positive week counts totaling 52, with four positive
`quarter_periods` counts covering every period. A year has 52 or 53 weeks based
on its aligned annual starts; the additional week goes into `leap_week_period`
(the last period by default). The anchor day must exist every year, so February
29 is rejected. This configuration models fixed annual anchors and week patterns;
it does not infer an organization's accounting policy.

Week-based year labels refer to the nominal anchor year (`"start"`) or the next
year (`"end"`); January anchors use the anchor year for both, matching the
month-based convention. Actual aligned starts can fall in an adjacent calendar
year. Choose the label convention explicitly to match your organization.

Both calendar types are immutable and expose these callable methods:

```python
from datetime import date

fiscal.fiscal_year(date(2026, 11, 7))       # 2027
fiscal.fiscal_quarter(date(2026, 11, 7))    # 2
fiscal.fiscal_period(date(2026, 11, 7))     # 5
fiscal.year_range(2027)
fiscal.quarter_range(2027, 1)
fiscal.period_range(2027, 1)
```

Ranges include both endpoints. Fiscal phrases also include `fiscal year 2027`,
`Q1 of next fiscal year`, `first fiscal quarter of FY2027`, `this fiscal period`,
`next fiscal period`, and `start`/`end`/`middle of` a fiscal scope. Invalid calendar
configuration raises `TypeError`/`ValueError`; unrecognized fiscal phrases return
`None`. Per-call settings override the current default without changing it.
Defaults are isolated by execution context; pass the calendar explicitly when
sharing work between threads or configuring separate requests/customers.

### Timezones and holidays

`TimeZoner` and `Holidate` are exposed as lazy-loaded public objects:

```python
import dately as dtly

country_codes = dtly.TimeZoner.CountryCodes
zones = dtly.TimeZoner.Zones
holidays = dtly.Holidate
```

Public holiday lookups now use [python-holidays](https://holidays.readthedocs.io/)
calendar rules locally, avoiding the blocked web scraper. Country names are case,
whitespace, accent, and punctuation insensitive; existing aliases and ISO alpha-2
codes are accepted. Unknown names raise an error with a suggestion rather than
silently selecting a different country.

```python
from datetime import date
import dately as dtly

dtly.Holidate.Holiday("united states", year=2026)
dtly.Holidate.Holiday("USA", year="2026", format="dict")
dtly.Holidate.Holiday("be", year=2026, format="df")
dtly.Holidate.Holiday("US", year=2026, subdiv="WI", observed=True)

# Use the same public holiday data automatically in business-day parsing.
dtly.parse("1 business day after 2026-11-25", country="US")
# datetime.date(2026, 11, 27): skips Thanksgiving
```

The default `source="public"` returns public holidays, with observed dates where
the selected calendar supports them. `subdiv` selects an optional state/province;
without it, the provider's country calendar is used. Names are returned in English
where the provider supports English. The three formats retain the `Date`, `Name`,
and `Type` columns; dates are ISO strings and the type is `Public holiday`.
List output includes a header row, dictionary output is a list of records, and
`df` output is a pandas DataFrame. Results are restricted to the requested year
and sorted by date.

This default is a scope change from the old scraper: it does **not** include all
cultural/religious observances, seasonal events, or every regional holiday.
`ListCountries` now lists countries supported by the installed calendar provider.
Country and year coverage depends on its version; older Python versions can use
older provider releases. Dately declares `holidays>=0.58,<1`, allowing pip to
select a compatible release. Keep that dependency updated for calendar-rule changes.

The original broader feed remains explicitly available:

```python
try:
    rows = dtly.Holidate.Holiday("Belgium", 2026, source="timeanddate")
except dtly.HolidayLookupError as exc:
    print(exc)  # Includes HTTP failures such as 403, rather than returning None.
```

`source="timeanddate"` requires network access and may be blocked by the provider;
it preserves the source's holiday-type labels. There is no automatic switch between
sources with different coverage. `subdiv` and `observed` options apply only to the
public source.

Unknown/unsupported countries, invalid years, subdivisions, formats, or sources
raise `TypeError`/`ValueError`. `HolidayLookupError` covers missing dependencies,
unavailable calendar data, transport errors, and missing/malformed web tables.
No failed lookup returns `None`. Omitting `year` uses the current year at call time.

Bundled timezone properties work with local data. Timezone methods that request
current remote information still depend on their respective external services.

### Cross-platform formatting

Windows and Unix-like platforms differ in their support for flags that suppress leading zeros in `strftime` directives. `dately` detects and normalizes these cases so formatting behavior remains consistent across supported platforms.

## Examples

Runnable examples with expected output are available in the [`examples`](examples/) directory:

- [Date conversion and formatting](examples/convert_dates.py)
- [Replacing date and time components](examples/replace_datestring.py)
- [Timezone operations](examples/timezone_operations.py)
- [Natural-language parsing](examples/nlp_parsing.py)

## License

`dately` is distributed under the MIT License. See [LICENSE](LICENSE) for details.
