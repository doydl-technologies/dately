import re
from datetime import datetime
from pathlib import Path

import dately
import pytest
from dately.mold.pyd.cdatetime.iso8601Z import replaceZ
from dately.mold.pyd.cdatetime.UniversalDateFormatter import (
    date_format_leading_zero,
    replace_non_padded_with_padded,
)
from dately.mold.pyd.clean_str import cleanstr


@pytest.mark.parametrize("flag", ["-", "#"])
@pytest.mark.parametrize(
    "template, expected",
    [
        ("%{flag}m/%d/%Y", "3/04/2026"),
        ("%m/%{flag}d/%Y", "03/4/2026"),
        ("%{flag}H:%M:%S", "5:06:07"),
        ("%H:%{flag}M:%S", "05:6:07"),
        ("%H:%M:%{flag}S", "05:06:7"),
        ("%{flag}I %p", "5 AM"),
        ("%%{flag}m %d", "%{flag}m 04"),
        ("%%%{flag}m %d", "%3 04"),
    ],
)
def test_mixed_padding_and_literal_percent(flag, template, expected):
    assert date_format_leading_zero(datetime(2026, 3, 4, 5, 6, 7), template.format(flag=flag)) == expected.format(
        flag=flag
    )


def test_zero_values_and_padded_year_remain_correct():
    assert date_format_leading_zero(datetime(2001, 1, 1), "%-y/%m/%d %-H:%M:%S") == "1/01/01 0:00:00"
    assert date_format_leading_zero(datetime(2001, 1, 1), "%-I") == "12"
    assert replace_non_padded_with_padded("%%-m %-m %m %#d") == "%%-m %m %m %d"
    assert dately.convert_date("2026-03-04", to_format="%-m/%d/%Y") == "3/04/2026"


@pytest.mark.parametrize(
    "text",
    ["", "Z", "2026-01-01T00:00:00Z", "prefixZ", "already+00:00", "caf\u00e9Z", "x" * 10000 + "Z"],
    ids=["empty", "single", "iso", "prefix", "offset", "unicode", "long"],
)
def test_zulu_suffix_uses_owned_storage_and_preserves_input(text):
    original = text
    expected = text[:-1] + "+00:00" if text.endswith("Z") else text
    for _ in range(10):
        assert replaceZ(text) == expected
        assert text == original


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", ""),
        (" \t\n ", ""),
        ("  one\t two\r\nthree ", "one two three"),
        ("\u00a0caf\u00e9\u2003\u6771\u4eac\u00a0", "caf\u00e9 \u6771\u4eac"),
        ("  " + "abc " * 10000 + "  ", ("abc " * 10000).strip()),
        ("  " + "caf\u00e9 \u6771\u4eac " * 1000 + " ", ("caf\u00e9 \u6771\u4eac " * 1000).strip()),
    ],
    ids=["empty", "whitespace", "ascii", "unicode-whitespace", "long-ascii", "long-unicode"],
)
def test_cleaning_handles_empty_unicode_and_long_inputs(text, expected):
    assert cleanstr(text) == expected


def test_header_includes_have_exact_case():
    root = Path(__file__).resolve().parents[1]
    headers = {path.name for path in (root / "mold/include").glob("*.h")}
    for path in (root / "mold/pyx").glob("*.pyx"):
        for name in re.findall(r'extern from "([^"]+)"', path.read_text(encoding="utf-8")):
            assert name in headers, (path.name, name)


def test_timezone_database_is_available():
    try:
        from zoneinfo import ZoneInfo
    except ImportError:  # Python 3.8 uses the existing pytz path.
        import pytz

        assert pytz.timezone("America/New_York")
    else:
        assert datetime(2026, 1, 1, tzinfo=ZoneInfo("America/New_York")).utcoffset().total_seconds() == -18000
        assert datetime(2026, 7, 1, tzinfo=ZoneInfo("America/New_York")).utcoffset().total_seconds() == -14400
