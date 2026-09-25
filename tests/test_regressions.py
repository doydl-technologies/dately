# -*- coding: utf-8 -*-

#
# doydl's Temporal Parsing & Normalization Engine — dately
#
# The `dately` module is a deterministic engine for parsing, resolving, and normalizing
# temporal expressions across both natural and symbolic language contexts — built for NLP
# workflows, cross-platform date handling, and fine-grained temporal reasoning.
#
# Designed with formal grammatical rigor, `dately` interprets phrases like “first five days of next month,”
# “Q3 of last year,” and “April 3” — handling cardinal/ordinal resolution, anchored structures, and
# ambiguous or implicit references with linguistic sensitivity.
#
# The engine combines structured tokenization, symbolic transformation, and rule-based semantic
# composition to support precision across tasks such as entity recognition, information extraction,
# and temporal normalization in noisy or informal text.
#
# It guarantees invertibility, transparency, and cross-platform consistency, resolving platform-specific
# formatting differences (e.g. Windows vs. Unix) while maintaining NLP-grade flexibility for English-language
# temporal constructions.
#
# Whether embedded in intelligent agents, ETL pipelines, or legal/medical NLP systems, `dately` brings
# clarity and structure to temporal meaning — bridging symbolic logic with real-world language.
#
# Copyright (c) 2024 by doydl technologies. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from datetime import date

import pytest

import dately
from dately._temporal_scan import resolver


@pytest.fixture(autouse=True)
def fixed_reference_date():
    original = resolver.reference_date
    original_week_start = resolver.week_start
    resolver.reference_date = date(2026, 9, 24)
    yield
    resolver.reference_date = original
    resolver.week_start = original_week_start


def test_non_iso_time_components_are_replaced():
    value = "2024-03-13 14:30:45"
    assert dately.replace_timestring(value, hour=1) == "2024-03-13 01:30:45"
    assert dately.replace_timestring(value, minute=2) == "2024-03-13 14:02:45"
    assert dately.replace_timestring(value, second=3) == "2024-03-13 14:30:03"


def test_non_iso_timezone_is_added():
    value = "2024-03-13 14:30:45"
    assert dately.replace_timestring(value, tzinfo=2) == "2024-03-13 14:30:45 +02:00"
    assert dately.replace_timestring(value, tzinfo="Europe/London").endswith(" Europe/London")


def test_iso_replacement_forwards_all_arguments():
    value = "2024-03-13T14:30:45Z"
    assert dately.replace_timestring(value, hour=1) == "2024-03-13T01:30:45+00:00"
    assert dately.replace_timestring(value, tzinfo=2) == "2024-03-13T14:30:45+02:00"


def test_replace_datestring_preserves_time_separator():
    assert dately.replace_datestring("2024-03-13 14:30:00", day=14) == "2024-03-14 14:30:00"
    assert dately.replace_datestring("2024-03-13T14:30:00", month=4) == "2024-4-13T14:30:00"


def test_formatted_sequence_formats_results_not_endpoints():
    assert dately.sequence("2024-01-01", "2024-01-03", to_format="%Y/%m/%d") == [
        "2024/01/01",
        "2024/01/02",
        "2024/01/03",
    ]


def test_numeric_week_start_values():
    dately.set_week_start(0)
    assert resolver.week_start == "monday"
    dately.set_week_start(6)
    assert resolver.week_start == "sunday"


def test_relative_weekdays_do_not_skip_a_week():
    assert dately.parse("next Friday") == date(2026, 9, 25)
    assert dately.parse("last Friday") == date(2026, 9, 18)
    assert dately.parse("next 2 Fridays") == [date(2026, 9, 25), date(2026, 10, 2)]


def test_repeated_weekends_are_consecutive():
    assert dately.parse("last 2 weekends") == [
        (date(2026, 9, 19), date(2026, 9, 20)),
        (date(2026, 9, 12), date(2026, 9, 13)),
    ]
    assert dately.parse("next 3 weekends") == [
        (date(2026, 10, 3), date(2026, 10, 4)),
        (date(2026, 10, 10), date(2026, 10, 11)),
        (date(2026, 10, 17), date(2026, 10, 18)),
    ]


def test_documented_nlp_forms():
    assert dately.parse("5 days ago") == date(2026, 9, 19)
    assert dately.parse("Q2 2025") == (date(2025, 4, 1), date(2025, 6, 30))
    assert dately.parse("middle of this year") == date(2026, 7, 2)
    assert dately.parse("first half of last year") == (date(2025, 1, 1), date(2025, 6, 30))
    assert dately.parse("start of Q3 2024") == date(2024, 7, 1)
    assert dately.parse("3 days ago starting from April 10") == date(2026, 4, 7)


def test_semantic_bounds_and_vocabulary_still_reject_invalid_input():
    assert dately.parse("55th day of week") is None
    assert dately.parse("banana tomorrow") is None


def test_timezoner_and_holidate_are_enabled_without_network_access():
    assert "Europe/London" in dately.TimeZoner.Zones
    assert "GB" in dately.TimeZoner.CountryCodes
    assert dately.TimeZoner.FilterZoneDetail("Europe/London")["countryCode"] == "GB"
    assert "Belgium" in dately.Holidate.ListCountries
    assert callable(dately.TimeZoner.CurrentTimebyZone)
    assert callable(dately.Holidate.Holiday)


def test_public_version_matches_release():
    assert dately.__version__ == "3.3.0"
