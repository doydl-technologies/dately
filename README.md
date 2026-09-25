<p align="center">
  <img src="https://raw.githubusercontent.com/cedricmoorejr/dately/main/assets/dately-logo-lockup-1600.png" alt="dately" width="700">
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
source .venv-test/Scripts/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
python -m pytest -q
```

Release downloads provide Windows x64 wheels for supported CPython versions and a source distribution. See [Distribution builds](docs/distribution-builds.md) for the artifact matrix and release procedure.

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

### Timezones and holidays

`TimeZoner` and `Holidate` are exposed as lazy-loaded public objects:

```python
import dately as dtly

country_codes = dtly.TimeZoner.CountryCodes
zones = dtly.TimeZoner.Zones
holidays = dtly.Holidate
```

Bundled timezone and holiday properties work with local data. Operations that request current remote information still depend on their respective external services being available. See the [issue and fix log](docs/issue-fix-log.md) for implementation details.

### Cross-platform formatting

Windows and Unix-like platforms differ in their support for flags that suppress leading zeros in `strftime` directives. `dately` detects and normalizes these cases so formatting behavior remains consistent across supported platforms.

## Examples

Runnable examples with expected output are available in the [`examples`](examples/) directory:

- [Date conversion and formatting](examples/convert_dates.py)
- [Replacing date and time components](examples/replace_datestring.py)
- [Timezone operations](examples/timezone_operations.py)
- [Natural-language parsing](examples/nlp_parsing.py)

## Documentation

- [Distribution builds](docs/distribution-builds.md)
- [Issue and fix log](docs/issue-fix-log.md)

## License

`dately` is distributed under the MIT License. See [LICENSE](LICENSE) for details.
