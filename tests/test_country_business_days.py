from datetime import date

import dately
import pytest
import requests
from dately._holiday import HolidayManager
from dately._temporal_scan import parse_temporal, resolver


@pytest.fixture(autouse=True)
def fixed_reference():
    original = resolver.reference_date
    resolver.reference_date = date(2026, 11, 25)
    yield
    resolver.reference_date = original


@pytest.mark.parametrize("country", ["US", "USA", "U.S.A.", "united states", "United States of America"])
def test_parse_country_aliases_skip_thanksgiving(country):
    assert dately.parse("next business day", country=country) == date(2026, 11, 27)
    assert dately.parse("1 working day after 2026-11-25", country=country) == date(2026, 11, 27)
    assert dately.parse("1 business day before 2026-11-27", country=country) == date(2026, 11, 25)


@pytest.mark.parametrize("country", ["BE", "Belgium", "belgium"])
def test_different_country_calendar(country):
    assert dately.parse("1 business day after 2026-11-10", country=country) == date(2026, 11, 12)


def test_observed_holidays_and_subdivisions():
    phrase = "1 business day after 2026-07-02"
    assert dately.parse(phrase, country="US") == date(2026, 7, 6)
    assert dately.parse(phrase, country="US", observed=False) == date(2026, 7, 3)
    assert dately.parse("1 business day after 2026-08-07", country="US", subdiv="RI") == date(2026, 8, 11)
    assert dately.parse("1 business day after 2026-08-07", country="US") == date(2026, 8, 10)


def test_scoped_selections_and_lists_use_country_holidays():
    assert dately.parse("first business day of January 2027", country="US") == date(2027, 1, 4)
    assert dately.parse("last business day of December 2021", country="US") == date(2021, 12, 30)
    assert dately.parse("next 3 business days", country="US") == [
        date(2026, 11, 27),
        date(2026, 11, 30),
        date(2026, 12, 1),
    ]


def test_anchored_and_cross_year_calculations_load_the_actual_year():
    assert dately.parse("in 1 business day starting from 2026-12-31", country="US") == date(2027, 1, 4)
    assert dately.parse("1 business day before 2022-01-03", country="US") == date(2021, 12, 30)
    # Independence Day 2024 is far from the reference date's year.
    assert dately.parse("1 business day after 2024-07-03", country="US") == date(2024, 7, 5)
    assert resolver.reference_date == date(2026, 11, 25)


def test_country_calendar_can_be_reused_with_company_closures():
    calendar = dately.BusinessCalendar(country="USA", holidays={date(2026, 11, 27)})
    assert calendar.country == "United States"
    assert dately.parse("next business day", business_calendar=calendar) == date(2026, 11, 30)
    assert dately.parse("1 business day after 2026-12-31", business_calendar=calendar) == date(2027, 1, 4)
    assert dately.parse("next business day", country="US") == date(2026, 11, 27)
    assert dately.parse("next business day") == date(2026, 11, 26)


def test_weekdays_and_ordinary_days_keep_their_existing_semantics():
    assert dately.parse("next weekday", country="US") == date(2026, 11, 26)
    assert dately.parse("in 1 day", country="US") == date(2026, 11, 26)
    assert dately.parse("in 0 business days", country="US") == date(2026, 11, 25)


def test_custom_workweek_is_explicit():
    calendar = dately.BusinessCalendar(country="US", working_days=(6, 0, 1, 2, 3))
    assert dately.parse("1 business day after 2026-11-25", business_calendar=calendar) == date(2026, 11, 29)


def test_country_calendars_are_offline(monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("Unexpected network request")

    monkeypatch.setattr(requests.sessions.Session, "request", no_network)
    assert dately.parse("next business day", country="US") == date(2026, 11, 27)


def test_holidays_are_loaded_lazily_and_cached_per_year_per_calendar(monkeypatch):
    calls = []

    def holidays(self, country_name, year=None, format="list", **kwargs):
        calls.append((country_name, year, format, kwargs))
        return [{"Date": f"{year}-01-01", "Name": "New Year", "Type": "Public holiday"}]

    monkeypatch.setattr(HolidayManager, "Holiday", holidays)
    calendar = dately.BusinessCalendar(country="US", holidays={date(2026, 11, 25)})
    assert calls == []
    assert not calendar.is_business_day(date(2026, 11, 25))  # supplied closure
    assert not calendar.is_business_day(date(2026, 11, 28))  # weekend
    assert calls == []
    assert not calendar.is_business_day(date(2026, 1, 1))
    assert calendar.is_business_day(date(2026, 1, 2))
    assert not calendar.is_business_day(date(2027, 1, 1))
    assert calendar.is_business_day(date(2027, 1, 4))
    assert [call[1] for call in calls] == [2026, 2027]
    assert all(call[2:] == ("dict", {"subdiv": None, "observed": True}) for call in calls)


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({"country": "Atlantis"}, ValueError),
        ({"country": "Belguim"}, ValueError),
        ({"country": 123}, TypeError),
        ({"country": "US", "subdiv": "XX"}, ValueError),
        ({"country": "US", "subdiv": []}, ValueError),
        ({"subdiv": "WI"}, ValueError),
        ({"observed": False}, ValueError),
        ({"country": "US", "observed": 1}, TypeError),
        ({"country": "US", "business_calendar": dately.BusinessCalendar()}, ValueError),
        ({"business_calendar": dately.BusinessCalendar(), "observed": False}, ValueError),
    ],
)
def test_invalid_country_options_raise_instead_of_falling_back(kwargs, error):
    with pytest.raises(error):
        dately.parse("next business day", **kwargs)


def test_unsupported_provider_country_is_explicit(monkeypatch):
    from dately._holiday import _holiday_library

    monkeypatch.setattr(_holiday_library(), "list_supported_countries", lambda **kwargs: {"US": []})
    with pytest.raises(ValueError, match="not supported by holidays"):
        dately.parse("next business day", country="Belgium")


@pytest.mark.parametrize(
    "error", [dately.HolidayLookupError("Calendar data unavailable"), ValueError("Year unavailable")]
)
def test_yearly_lookup_failures_propagate_through_both_parsers(monkeypatch, error):
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(HolidayManager, "Holiday", fail)
    with pytest.raises(dately.HolidayLookupError, match="unavailable"):
        dately.parse("next business day", country="US")
    calendar = dately.BusinessCalendar(country="US")
    with pytest.raises(dately.HolidayLookupError, match="unavailable"):
        parse_temporal("first business day of next month", business_calendar=calendar)
    assert resolver.reference_date == date(2026, 11, 25)
