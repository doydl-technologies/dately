<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/doydl-technologies/dately/main/assets/png/dately-endorsed-lockup-light-1135x409-384dpi.png">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/doydl-technologies/dately/main/assets/png/dately-endorsed-lockup-dark-1135x409-384dpi.png">
    <img src="https://raw.githubusercontent.com/doydl-technologies/dately/main/assets/png/dately-endorsed-lockup-dark-1135x409-384dpi.png" alt="dately — powered by DOYDL Technologies" width="700">
  </picture>
</p>

<p align="center">
  📅 Deterministic date, time, timezone, holiday, and natural-language temporal processing for Python.
</p>

<p align="center">
  <a href="https://pypi.org/project/dately/"><img src="https://img.shields.io/pypi/v/dately" alt="PyPI version"></a>
  <a href="https://pypi.org/project/dately/"><img src="https://img.shields.io/pypi/pyversions/dately" alt="Supported Python versions"></a>
  <a href="https://pepy.tech/project/dately"><img src="https://static.pepy.tech/badge/dately" alt="Downloads"></a>
  <a href="https://doydl.com"><img src="https://img.shields.io/badge/Powered%20by-DOYDL%20Technologies-blue" alt="Powered by DOYDL Technologies"></a>
</p>

> **🚀 New to dately?** Start with [Installation](#installation) and [Quick start](#quick-start), or jump to the [function guide](#overview) to find the right API.

---

<a id="overview"></a>
## 🔎 Overview

`dately` is a Python library for turning date and time text into values your code
can use. It can read a phrase such as `first Monday of next month`, reformat dates
for a report, calculate a deadline that skips weekends and public holidays, or
find the dates covered by a company's fiscal quarter.

You call its functions from your own Python program. Natural-language parsing
uses English grammar rules and calendar arithmetic; it runs locally without an
AI model or an API key. The library also includes compiled Cython extensions for
some date-processing operations.

### 🧰 Which function do I need?

| What you want to do | Use | What you get |
| --- | --- | --- |
| 🗣️ Understand a date phrase, such as `Q2 2025` | `parse()` | A date, a date range, or a list, depending on the phrase |
| 🔍 Identify how a date string is written | `detect_date_format()` | A Python format string, such as `%Y-%m-%d` |
| 🔄 Change a date's display format or turn text into a Python value | `convert_date()` | Formatted text, or a Python date/datetime value |
| 🧩 Read just the year, month, day, or a time component | `extract_datetime_component()` | The component as text, such as `"03"` |
| 🛠️ Change selected fields in an existing date/time string | `replace_datestring()` / `replace_timestring()` | An updated string |
| 🗓️ Generate every calendar date between two endpoints | `sequence()` | An inclusive list of dates or formatted strings |
| 💼 Count working days and exclude holidays or company closures | `BusinessCalendar` with `parse()` | A deadline or a selection of eligible dates |
| 📊 Define financial years, quarters, and periods | `FiscalCalendar` / `RetailFiscalCalendar` | Reusable calendar objects and inclusive date ranges |
| 🎉 List a country's public holidays | `Holidate.Holiday()` | Rows, records, or a pandas DataFrame |
| 🌍 Look up timezone names and country metadata | `TimeZoner` | Lists and dictionaries from bundled timezone data |

For example, use `convert_date()` to change `2024-03-13` into `13/03/2024`.
Use `parse()` to work out which dates `Q2 2025` covers. Use a business calendar
when an invoice is due a certain number of working days after an issue date.

<a id="contents"></a>
## 🧭 Contents

- [🔎 Overview](#overview)
- [📦 Installation](#installation)
- [🚀 Quick start](#quick-start)
- [🗓️ Working with date and time strings](#working-with-date-and-time-strings)
- [🗣️ Natural-language parsing](#natural-language-parsing)
- [💼 Business days](#business-days)
- [📊 Fiscal calendars](#fiscal-calendars-optional)
- [🎉 Public holidays](#public-holidays)
- [🌍 Timezones](#timezones)
- [⚠️ Errors and practical limits](#errors-and-practical-limits)
- [🖥️ Platform support, development, and releases](#platform-support-development-and-releases)
- [📚 More examples](#more-examples)
- [🏷️ Release history](#release-history)
- [⚖️ License](#license)

<a id="installation"></a>
## 📦 Installation

### 1️⃣ Install from PyPI

Install the latest published release from PyPI:

```bash
python -m pip install dately
```

### 2️⃣ Install a local checkout (optional)

This README describes **4.7.7**, including business-day and fiscal-calendar
features. To use a local checkout, run the following from the directory containing
`setup.py`:

```bash
python -m venv .venv
# Windows/MSYS2:
source .venv/Scripts/activate
# macOS/Linux instead: source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

**💡 Why use a virtual environment?** The virtual environment keeps this installation separate from other projects.
The `-e` option installs the checkout in editable mode. Installing from source
requires a compatible C compiler; installing a matching prebuilt wheel does not.
See [platform support](#platform-support-development-and-releases) for details.

### 3️⃣ Check your installation

Check which version and installation your Python interpreter is using:

```bash
python -c "import dately; print(dately.__version__); print(dately.__file__)"
```

<a id="quick-start"></a>
## 🚀 Quick start

```python
import dately as dtly

# Reformat an existing date for display.
print(dtly.convert_date("2024-03-13", to_format="%d/%m/%Y"))
# 13/03/2024

# Resolve a calendar quarter into its first and last dates.
start, end = dtly.parse("Q2 2025")
print(start.isoformat(), end.isoformat())
# 2025-04-01 2025-06-30

# Find the next working day after a date, skipping US Thanksgiving.
deadline = dtly.parse("1 business day after 2026-11-25", country="US")
print(deadline.isoformat())
# 2026-11-27

# Use a July-June financial year instead of January-December.
fiscal = dtly.FiscalCalendar(start_month=7, year_label="end")
start, end = dtly.parse("Q1 FY2027", fiscal_calendar=fiscal)
print(start.isoformat(), end.isoformat())
# 2026-07-01 2026-09-30
```

**📌 Reproducibility note:** These examples include explicit years so their results stay the same whenever
you run them. Phrases containing `today`, `next month`, or `last year` depend on
the parser's reference date, explained below.

<a id="working-with-date-and-time-strings"></a>
## 🗓️ Working with date and time strings

### 🔎 Detect, convert, and extract

Detection describes the input's structure. Conversion changes its display format
or creates a Python value. Extraction reads one component without changing it:

```python
import dately as dtly

dtly.detect_date_format("2024-03-13T14:30:00")
# '%Y-%m-%dT%H:%M:%S'

dtly.convert_date("2024-03-13", to_format="%d/%m/%Y")
# '13/03/2024'

dtly.convert_date("2024-03-13")  # no output format: return a Python value
# datetime.datetime(2024, 3, 13, 0, 0)

dtly.extract_datetime_component("2024-03-13", "month")
# '03' (a string, not the integer 3)
```

Format strings use Python's `strftime` conventions:

| Directive | Meaning | Example |
| --- | --- | --- |
| `%Y` | Four-digit year | `2024` |
| `%m` | Month, with a leading zero | `03` |
| `%d` | Day of the month, with a leading zero | `13` |
| `%H` | Hour on a 24-hour clock | `14` |
| `%M` | Minute | `30` |
| `%S` | Second | `00` |
| `%z` | UTC offset | `+0200` |

For example, `%m` means month and `%M` means minute. Text such as `-`, `/`, or
`T` is a literal separator. Dately also normalizes supported leading-zero flags
such as `%-m` and `%#m` across Windows, macOS, and Linux:

```python
dtly.convert_date("2026-03-04", to_format="%-m/%d/%Y")
# '3/04/2026'
```

### 📚 Process multiple values

The string utilities support collections such as lists, NumPy arrays, and pandas
Series. For example, conversion of a list returns a list:

```python
dtly.convert_date(["2024-03-13", "2024-03-14"], to_format="%d/%m/%Y")
# ['13/03/2024', '14/03/2024']

record = {"name": "Example", "issued": "2024-03-13"}
dtly.convert_date(record, to_format="%d/%m/%Y", dict_keys=["issued"])
# {'name': 'Example', 'issued': '13/03/2024'}
```

Dictionary conversion requires `dict_keys` so Dately knows which fields contain
dates. By default it returns a copy. Set `dict_inplace=True` to update the original
dictionary and return `None`. Collection support is specific to each utility;
`parse()` takes one expression string per call.

### 🛠️ Replace date or time components

Replacement edits selected fields, retaining the other components and the
original structure where supported. This is useful when you already have a
timestamp and only need to change its day or hour:

```python
dtly.replace_datestring("2024-03-13T14:30:00", year=2025, month=12, day=25)
# '2025-12-25T14:30:00'

dtly.replace_timestring("2024-03-13 14:30:45", hour=9, minute=15)
# '2024-03-13 09:15:45'
```

Replacing a field is different from adding elapsed time. For example, replacing
the month is a calendar edit; it is not a duration calculation. Changing `tzinfo`
attaches or replaces a timezone rather than converting the clock to another zone.

### 📅 Generate an inclusive sequence

```python
dtly.sequence("2024-01-01", "2024-01-03", to_format="%Y/%m/%d")
# ['2024/01/01', '2024/01/02', '2024/01/03']
```

Both endpoints are included. This generates every calendar day, including
weekends and holidays. Omit `to_format` to get Python values instead of strings.
For a selection of working days, use the business-day parser below.

<a id="natural-language-parsing"></a>
## 🗣️ Natural-language parsing

`parse()` interprets a complete date expression using supported English patterns.
It can resolve offsets, named weekdays, positions within a period, calendar
quarters, and date ranges:

```python
dtly.parse("Q2 2025")
# (datetime.date(2025, 4, 1), datetime.date(2025, 6, 30))

dtly.parse("start of Q3 2024")
# datetime.date(2024, 7, 1)

dtly.parse("in 3 days starting from 2026-11-06")
# datetime.date(2026, 11, 9)

dtly.parse("first Monday of next month")
# datetime.date(...) depending on the reference date
```

### 📤 Understand the return value

**📤 Return types vary by expression.** The phrase determines the result's shape. Dately does not always return a single
date or a string:

| Expression | Result type | Meaning |
| --- | --- | --- |
| `start of Q3 2024` | `datetime.date` | One calendar date |
| `2026-11-25` | `datetime.datetime` | A formatted date parsed at midnight |
| `Q2 2025` | A two-item tuple of dates | Inclusive start and end of a period |
| `first 3 business days of February 2027` | A list of dates | Individual selected days |
| An unrecognized expression | `None` | No supported interpretation was found |

A Python `date` holds a year, month, and day; a `datetime` also holds a time.
Call `.isoformat()` on either for readable ISO text. For a range, unpack the tuple
as `start, end`; Dately does not expand it into every intervening date. Some
selections, such as weekends, can return a list of ranges.

### ⏳ Relative dates and week settings

`in 3 days` means one date three days after the reference date. `next 3 days`
means an inclusive range beginning on the reference date and ending two days
later. Business-day selections have their own rules, described below.

The resolver initializes its reference date from the local current date when it
is imported. It is not automatically refreshed at midnight. The public `parse()`
API has no `reference_date` argument; use an explicit supported anchor such as
`starting from 2026-11-06` when the calculation needs a fixed starting date.

Configure week boundaries with either Monday or Sunday:

```python
dtly.set_week_start("monday")  # also accepts 0
dtly.parse("start of next week")
dtly.set_week_start("sunday")  # also accepts 6
```

This changes the shared resolver's week setting for subsequent calls. It is
separate from a business calendar's working weekdays and a retail fiscal
calendar's `week_start` setting.

<a id="business-days"></a>
## 💼 Business days

**📆 Default business week:** Business days and working days are aliases. By default they mean Monday-Friday,
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

**🎉 Observed holidays:** An observed holiday is the substitute day off when a holiday falls on a weekend,
where the country's rules provide one. For example, US Independence Day falls on
Saturday in 2026 and is observed on Friday, July 3. With the default
`observed=True`, the next business day after July 2 is July 6.

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
    country="US",  # optional; omit for a calendar of supplied dates only
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

# The same calendar can also be called directly, without parsing text.
calendar.is_business_day(date(2026, 11, 26))
# False
calendar.add_business_days(date(2026, 11, 25), 1)
# datetime.date(2026, 11, 30)
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

<a id="fiscal-calendars-optional"></a>
## 📊 Fiscal calendars (optional)

**📊 For finance and reporting:** A fiscal year is the year an organization uses for financial reporting. It may
start in a month other than January, or follow whole weeks rather than calendar
months. A fiscal **period** is one reporting block within that year; a fiscal
**quarter** groups several periods. `FY2027`, `Q1`, and `P2` mean fiscal year 2027,
quarter 1, and period 2 when used together in a fiscal expression.

| Calendar | Configuration | Periods and quarters |
| --- | --- | --- |
| 📆 January-December | `FiscalCalendar()` | 12 calendar months; three months per quarter |
| 🗓️ A different starting month | `FiscalCalendar(start_month=7)` | 12 calendar months, beginning in July in this example |
| 🛒 4-4-5 retail | `RetailFiscalCalendar(pattern=(4, 4, 5))` | Each quarter has periods of four, four, and five weeks |
| 🛒 4-5-4 retail | `RetailFiscalCalendar(pattern=(4, 5, 4))` | Each quarter has periods of four, five, and four weeks |
| 🛒 5-4-4 retail | `RetailFiscalCalendar(pattern=(5, 4, 4))` | Each quarter has periods of five, four, and four weeks |
| ⚙️ Custom week pattern | `RetailFiscalCalendar(pattern=..., quarter_periods=...)` | You define period lengths and how periods form quarters |

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

<details>
<summary><strong>🛒 Advanced: Retail fiscal calendars, custom patterns, and 53-week years</strong></summary>

For week-based years, select `RetailFiscalCalendar`. The same parser and direct
methods work with 4-4-5, 4-5-4, 5-4-4, or a custom period pattern:

```python
retail = dtly.RetailFiscalCalendar(
    pattern=(4, 4, 5),  # or (4, 5, 4), (5, 4, 4), or another custom pattern
    start_month=2,
    start_day=1,
    week_start=6,  # Sunday; Monday=0
    alignment="nearest",  # or "on_or_before" / "on_or_after"
    year_label="end",
    leap_week_period=12,  # place a 53rd week in period 12
)
dtly.parse("P2 FY2024", fiscal_calendar=retail)
# (datetime.date(2023, 2, 26), datetime.date(2023, 3, 25))
dtly.parse("Q4 FY2024", fiscal_calendar=retail)
retail.year_range(2024)
# (datetime.date(2023, 1, 29), datetime.date(2024, 2, 3)): a 53-week year

# Switch the pattern while retaining the default February anchor and Sunday start.
retail_454 = dtly.RetailFiscalCalendar(pattern=(4, 5, 4))
retail_454.period_range(2024, 2)
# (datetime.date(2023, 2, 26), datetime.date(2023, 4, 1))

retail_544 = dtly.RetailFiscalCalendar(pattern=(5, 4, 4))
retail_544.period_range(2024, 1)
# (datetime.date(2023, 1, 29), datetime.date(2023, 3, 4))

# An entire custom 52-week pattern with 13 periods of four weeks.
custom = dtly.RetailFiscalCalendar(
    pattern=(4,) * 13,
    quarter_periods=(3, 3, 3, 4),  # group the 13 periods into four quarters
    start_month=10,
    start_day=1,
    week_start=0,
    alignment="on_or_after",
    year_label="end",
    leap_week_period=13,
)
dtly.parse("P13 FY2024", fiscal_calendar=custom)
# (datetime.date(2024, 9, 2), datetime.date(2024, 10, 6))
```

`start_month` and `start_day` specify an annual anchor date. `week_start` selects
the weekday on which the year begins, and `alignment` chooses that weekday
nearest to, on or before, or on or after the anchor. For example, the default
February 1 anchor with `alignment="nearest"` starts on the nearest Sunday.

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

fiscal.fiscal_year(date(2026, 11, 7))  # 2027
fiscal.fiscal_quarter(date(2026, 11, 7))  # 2
fiscal.fiscal_period(date(2026, 11, 7))  # 5
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

</details>

<a id="public-holidays"></a>
## 🎉 Public holidays

Use `Holidate.Holiday()` when you want to inspect or display a holiday calendar,
rather than calculate a deadline. The default lookup uses
[python-holidays](https://holidays.readthedocs.io/) calendar rules locally and
requires no network access or API key. Country names are case,
whitespace, accent, and punctuation insensitive; existing aliases and ISO alpha-2
codes are accepted. Unknown names raise an error with a suggestion rather than
silently selecting a different country.

```python
import dately as dtly

dtly.Holidate.Holiday("united states", year=2026)
dtly.Holidate.Holiday("USA", year="2026", format="dict")
dtly.Holidate.Holiday("be", year=2026, format="df")
dtly.Holidate.Holiday("US", year=2026, subdiv="WI", observed=True)

rows = dtly.Holidate.Holiday("US", year=2026, format="dict")
rows[0]
# {'Date': '2026-01-01', 'Name': "New Year's Day", 'Type': 'Public holiday'}

# Discover the countries available with your installed holiday provider.
countries = dtly.Holidate.ListCountries

# Use the same public holiday data automatically in business-day parsing.
dtly.parse("1 business day after 2026-11-25", country="US")
# datetime.date(2026, 11, 27): skips Thanksgiving
```

**🌐 Public holiday source:** The default `source="public"` returns public holidays, with observed dates where
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

<a id="timezones"></a>
## 🌍 Timezones

`TimeZoner` provides bundled timezone names and country metadata. Like `Holidate`,
it is loaded when first used; ordinary imports do not make remote requests:

```python
import dately as dtly

zones = dtly.TimeZoner.Zones
country_codes = dtly.TimeZoner.CountryCodes
uk_zones = dtly.TimeZoner.ZonesByCountry["GB"]
dtly.TimeZoner.FilterZoneDetail("Europe/London")["countryCode"]
# 'GB'
```

The bundled metadata is a lookup dataset. Methods such as `CurrentTimebyZone()`,
`ConvertTimeZone()`, and the `MyTimeZone` property request information from
external services. Their availability depends on network access, the service,
and any credentials required by that service; unsuccessful requests can return
`None`.

Timezone replacement in a string has a different purpose:

```python
dtly.replace_timestring("2024-03-13T14:30:00", tzinfo="+02:00")
# '2024-03-13T14:30:00+02:00'
```

**⚠️ Assigning is not converting:** The clock still reads 14:30. This assigns an offset to that clock time; it does
not preserve an existing instant by converting it between timezones.

<a id="errors-and-practical-limits"></a>
## ⚠️ Errors and practical limits

**🩺 Check outcomes before use.** Check `parse()` results before using them. Unsupported phrases can return `None`,
while invalid calendar options and holiday lookup failures raise exceptions:

```python
import dately as dtly

try:
    result = dtly.parse("1 business day after 2026-11-25", country="US")
except (TypeError, ValueError) as exc:
    print(f"Check the calendar options: {exc}")
except dtly.HolidayLookupError as exc:
    print(f"Holiday data could not be loaded: {exc}")
else:
    if result is None:
        print("Use a supported date expression.")
    else:
        print(result)
```

- 🗣️ Give `parse()` one date expression, rather than a paragraph containing dates.
  It is a rule-based English parser, not a general text extraction or reminder
  service. Unsupported wording is not guaranteed to be understood.
- 📅 Prefer explicit years and unambiguous dates such as `2026-11-25`. A string such
  as `03/04/2026` does not communicate whether you intend March 4 or April 3.
- 📆 Ordinary `days`, `weekdays`, and `business days` have different meanings.
  Holidays are excluded only by a business calendar configured to exclude them.
- 📊 Fiscal settings affect explicit fiscal phrases. Configuring a July start does
  not change the meaning of the ordinary calendar expression `Q1 2027`.
- ⚠️ Format detection and conversion can raise `ValueError` for invalid or
  unrecognized date strings. Component extraction can return `None` when a
  component cannot be found. Do not assume every function uses the same failure
  convention.
- 🎉 Holiday coverage depends on the installed provider, country, subdivision,
  and year. A public holiday calendar is not a complete list of every employer's
  closures; add those dates to `BusinessCalendar` yourself.

<a id="platform-support-development-and-releases"></a>
## 🖥️ Platform support, development, and releases

The 4.7.7 build matrix targets CPython 3.8-3.14 on:

| System | Wheel architecture | Notes |
| --- | --- | --- |
| 🪟 Windows | x64 (AMD64) | Native Windows wheels |
| 🐧 Linux | x86-64 | manylinux, glibc 2.28 or newer |
| 🍎 macOS | Intel x86-64 | Built and tested on an Intel runner |
| 🍎 macOS | Apple Silicon arm64 | Built and tested on an ARM runner |

A wheel is a prebuilt Python package. Use one matching your Python version,
operating system, and architecture; pip normally selects it automatically when
it is available. Linux ARM, Alpine/musllinux, and Windows ARM wheels are outside
this release matrix. Native macOS and Linux support is verified by their CI jobs;
local Windows tests alone do not establish compatibility with those systems.

### 🧪 Building and testing a checkout

Source installs require a C compiler compatible with Python: MSVC on Windows,
Xcode Command Line Tools on macOS, or a C compiler and Python development headers
on Linux. Using an MSYS2 terminal on Windows does not change the compiler required
by a standard Windows CPython installation. The build installs Cython
automatically and compiles all seven required extensions; there is no pure Python
fallback. Precompiled Windows binaries are not kept in the source tree.
Timezone data is supplied by the `tzdata` dependency on Python 3.9+, with the
existing `pytz` path on Python 3.8.

After installing the checkout in the virtual environment described above, run:

```bash
python -m pip install pytest build
python -m pytest -q
python -m build
```

`python -m build` creates a source archive and a wheel in `dist/`. A wheel built
locally serves the current Python/platform combination, rather than every system
in the release matrix.

The build workflow uses pinned `cibuildwheel` 3.4.0, which supports the complete
Python 3.8-3.14 matrix. Every wheel is installed into an isolated test environment
and tested there. CI also rebuilds a wheel from the source archive and tests it.
The Python 3.8 Apple Silicon wheel has an additional native test job using a
managed CPython 3.8 interpreter because the wheel builder's installer is x86-only.
Release validation requires each Python/platform pair and a matching source
archive; it checks coverage rather than relying on a fixed download count.

### 🚀 Release workflow

<details>
<summary><strong>📦 Maintainer release and publication process</strong></summary>

Tagged builds can publish a GitHub release after the full matrix succeeds.
Create a draft GitHub release containing the approved notes before publication;
the workflow reads the notes from that draft's description.
Manual publication requires both a stable `vX.Y.Z` tag and its successful build
run ID. The release workflow checks the build's repository, workflow, event, and
commit against the tag, uploads all files to a draft, then publishes the complete
release. Branch/PR builds do not automatically publish releases.

</details>

<a id="more-examples"></a>
## 📚 More examples

Runnable examples with expected output are available in the [`examples`](examples/) directory:

- 🔄 [Date conversion and formatting](examples/convert_dates.py)
- 🛠️ [Replacing date and time components](examples/replace_datestring.py)
- 🌍 [Timezone operations](examples/timezone_operations.py)
- 🗣️ [Natural-language parsing](examples/nlp_parsing.py)

<a id="release-history"></a>
## 🏷️ Release history

See [CHANGELOG.md](CHANGELOG.md) for the release history and
[the 4.7.7 release notes](https://github.com/doydl-technologies/dately/releases/tag/v4.7.7) for upgrade guidance.

<a id="license"></a>
## ⚖️ License

`dately` is distributed under the MIT License. See [LICENSE](LICENSE) for details.
