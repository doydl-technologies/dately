from datetime import date

import dately
import pytest
from dately._temporal_scan import parse_temporal, resolver


@pytest.fixture(autouse=True)
def friday_reference():
    original = resolver.reference_date
    resolver.reference_date = date(2026, 11, 6)
    yield
    resolver.reference_date = original


@pytest.mark.parametrize(
    "phrase, expected",
    [
        ("next business day", date(2026, 11, 9)),
        ("the next business day", date(2026, 11, 9)),
        ("previous business day", date(2026, 11, 5)),
        ("in 3 business days", date(2026, 11, 11)),
        ("in three working days", date(2026, 11, 11)),
        ("3 business days ago", date(2026, 11, 3)),
        ("a business day ago", date(2026, 11, 5)),
        ("in 0 business days", date(2026, 11, 6)),
        ("NEXT BUSINESS DAY", date(2026, 11, 9)),
        ("in 2 business-days", date(2026, 11, 10)),
        ("next weekday", date(2026, 11, 9)),
        ("3 weekdays ago", date(2026, 11, 3)),
        ("3 business days after November 6", date(2026, 11, 11)),
        ("3 business days before 2026-11-09", date(2026, 11, 4)),
        ("3 business days from today", date(2026, 11, 11)),
        ("3 business days ago starting from April 10", date(2026, 4, 7)),
        ("in 3 business days starting from 2026-04-10", date(2026, 4, 15)),
        ("first business day of next month", date(2026, 12, 1)),
        ("last business day of this month", date(2026, 11, 30)),
        ("third business day of next month", date(2026, 12, 3)),
        ("3rd working day of next month", date(2026, 12, 3)),
        ("last business day of February 2024", date(2024, 2, 29)),
        ("in 3 days", date(2026, 11, 9)),
        ("in two weeks", date(2026, 11, 20)),
        ("in 2 months", date(2027, 1, 6)),
        ("in 1 year", date(2027, 11, 6)),
        ("in 3 days starting from 2026-04-10", date(2026, 4, 13)),
        ("first business day of January", date(2026, 1, 1)),
        ("last business day of 2026", date(2026, 12, 31)),
    ],
)
def test_calendar_phrases(phrase, expected):
    assert dately.parse(phrase) == expected


def test_filtered_spans_return_only_eligible_dates():
    assert dately.parse("next 3 business days") == [date(2026, 11, n) for n in (9, 10, 11)]
    assert dately.parse("last 3 working days") == [date(2026, 11, n) for n in (5, 4, 3)]
    assert dately.parse("first 3 business days of next month") == [date(2026, 12, n) for n in (1, 2, 3)]
    assert dately.parse("last 2 weekdays of this month") == [date(2026, 11, 27), date(2026, 11, 30)]


def test_holidays_custom_workweek_and_no_global_state():
    calendar = dately.BusinessCalendar(holidays={date(2026, 11, 9)})
    assert dately.parse("next business day", business_calendar=calendar) == date(2026, 11, 10)
    assert dately.parse("in 3 working days", business_calendar=calendar) == date(2026, 11, 12)
    assert dately.parse("next weekday", business_calendar=calendar) == date(2026, 11, 9)
    assert dately.parse("next business day") == date(2026, 11, 9)
    calendar = dately.BusinessCalendar(working_days=(6, 0, 1, 2, 3))
    assert dately.parse("next business day", business_calendar=calendar) == date(2026, 11, 8)


def test_scoped_holidays_and_year_crossing():
    calendar = dately.BusinessCalendar(holidays={date(2027, 1, 1), date(2026, 12, 1)})
    assert dately.parse("first business day of next month", business_calendar=calendar) == date(2026, 12, 2)
    assert dately.parse("in 1 business day starting from 2026-12-31", business_calendar=calendar) == date(2027, 1, 4)


@pytest.mark.parametrize(
    "day, following, previous",
    [
        (7, 9, 6),
        (8, 9, 6),
        (9, 10, 6),
    ],
)
def test_weekend_and_monday_anchors(day, following, previous):
    resolver.reference_date = date(2026, 11, day)
    assert dately.parse("next business day") == date(2026, 11, following)
    assert dately.parse("last business day") == date(2026, 11, previous)


@pytest.mark.parametrize(
    "phrase",
    [
        "banana business day",
        "in -3 business days",
        "in 1.5 business days",
        "next 0 business days",
        "in banana business days",
        "next business day banana",
        "24th business day of February 2026",
        "first 99 business days of this month",
        "3 business days after nonsense",
        "in 3 business days starting from nonsense",
        "last business day of nonsense",
        "first business day of 2026-11-06",
        "last business day of next month starting from April 10",
        "in 3 business days starting from today starting from April 10",
    ],
)
def test_invalid_expressions_are_rejected_without_changing_reference(phrase):
    assert dately.parse(phrase) is None
    assert resolver.reference_date == date(2026, 11, 6)


def test_direct_token_api_and_calendar_methods():
    assert parse_temporal(["in", "3", "business_day"], parse=False) == date(2026, 11, 11)
    assert parse_temporal(["NEXT", "BUSINESS", "DAY"]) == date(2026, 11, 9)
    calendar = dately.BusinessCalendar()
    assert not calendar.is_business_day(date(2026, 11, 7))
    assert calendar.add_business_days(date(2026, 11, 7), 0) == date(2026, 11, 7)
    with pytest.raises(TypeError):
        calendar.add_business_days(date(2026, 11, 6), 1.5)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"working_days": ()},
        {"working_days": (7,)},
        {"working_days": (True,)},
        {"holidays": {"2026-11-09"}},
    ],
)
def test_invalid_calendars(kwargs):
    with pytest.raises(ValueError):
        dately.BusinessCalendar(**kwargs)


def test_invalid_calendar_argument_and_input_snapshot():
    with pytest.raises(TypeError):
        dately.parse("next business day", business_calendar={})
    holidays = {date(2026, 11, 9)}
    calendar = dately.BusinessCalendar(holidays=holidays)
    holidays.clear()
    assert not calendar.is_business_day(date(2026, 11, 9))


def test_forward_offsets_clamp_month_and_leap_day():
    resolver.reference_date = date(2024, 1, 31)
    assert dately.parse("in 1 month") == date(2024, 2, 29)
    resolver.reference_date = date(2024, 2, 29)
    assert dately.parse("in 1 year") == date(2025, 2, 28)


def test_no_eligible_days_in_scope():
    calendar = dately.BusinessCalendar(holidays={date(2026, 11, n) for n in range(1, 31)})
    assert dately.parse("first business day of this month", business_calendar=calendar) is None


def test_legacy_anchor_restores_reference_on_failure(monkeypatch):
    from dately import _temporal_scan as scan

    monkeypatch.setattr(scan, "_compute_starting_point", lambda tokens: date(2026, 4, 10))

    def fail(tokens):
        raise ValueError("failed evaluation")

    monkeypatch.setattr(resolver, "compute", fail)
    with pytest.raises(ValueError, match="failed evaluation"):
        scan._compute_starting_from_expression(["3", "day", "ago", "starting", "from", "april 10"])
    assert resolver.reference_date == date(2026, 11, 6)
