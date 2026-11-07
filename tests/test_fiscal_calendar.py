from contextvars import Context
from dataclasses import FrozenInstanceError
from datetime import date, datetime, timedelta

import pytest

import dately
from dately._temporal_scan import resolver


@pytest.fixture(autouse=True)
def restore_settings():
    original, reference = dately.get_fiscal_calendar(), resolver.reference_date
    dately.set_fiscal_calendar(None)
    resolver.reference_date = date(2026, 11, 7)
    yield
    dately.set_fiscal_calendar(original)
    resolver.reference_date = reference


def test_month_based_calendar_direct_methods():
    calendar = dately.FiscalCalendar(start_month=7)
    assert calendar.year_range(2027) == (date(2026, 7, 1), date(2027, 6, 30))
    assert calendar.quarter_range(2027, 1) == (date(2026, 7, 1), date(2026, 9, 30))
    assert calendar.quarter_range(2027, 4) == (date(2027, 4, 1), date(2027, 6, 30))
    assert calendar.fiscal_year(date(2026, 6, 30)) == 2026
    assert calendar.fiscal_year(date(2026, 7, 1)) == 2027
    assert calendar.fiscal_quarter(datetime(2026, 11, 7, 12)) == 2
    assert calendar.fiscal_period(date(2027, 1, 1)) == 7
    assert calendar.period_range(2024, 8) == (date(2024, 2, 1), date(2024, 2, 29))


@pytest.mark.parametrize("month", range(1, 13))
@pytest.mark.parametrize("label", ["start", "end"])
def test_all_start_months_and_label_conventions_partition_the_year(month, label):
    calendar = dately.FiscalCalendar(start_month=month, year_label=label)
    first, last = calendar.year_range(2024)
    assert first.month == month and first.day == 1
    assert calendar.fiscal_year(first) == calendar.fiscal_year(last) == 2024
    quarters = [calendar.quarter_range(2024, q) for q in range(1, 5)]
    assert quarters[0][0] == first and quarters[-1][1] == last
    for index, (start, end) in enumerate(quarters, 1):
        assert calendar.fiscal_quarter(start) == calendar.fiscal_quarter(end) == index
        if index < 4:
            assert end + timedelta(days=1) == quarters[index][0]


@pytest.mark.parametrize("phrase, expected", [
    ("FY2027", (date(2026, 7, 1), date(2027, 6, 30))),
    ("FY 2027", (date(2026, 7, 1), date(2027, 6, 30))),
    ("fiscal year 2027", (date(2026, 7, 1), date(2027, 6, 30))),
    ("this fiscal year", (date(2026, 7, 1), date(2027, 6, 30))),
    ("next fiscal year", (date(2027, 7, 1), date(2028, 6, 30))),
    ("previous fiscal year", (date(2025, 7, 1), date(2026, 6, 30))),
    ("Q1 FY2027", (date(2026, 7, 1), date(2026, 9, 30))),
    ("fiscal Q1 2027", (date(2026, 7, 1), date(2026, 9, 30))),
    ("FQ1 FY2027", (date(2026, 7, 1), date(2026, 9, 30))),
    ("fiscal Q1", (date(2026, 7, 1), date(2026, 9, 30))),
    ("first fiscal quarter of FY2027", (date(2026, 7, 1), date(2026, 9, 30))),
    ("fiscal quarter 1 of FY2027", (date(2026, 7, 1), date(2026, 9, 30))),
    ("Q1 of next fiscal year", (date(2027, 7, 1), date(2027, 9, 30))),
    ("this fiscal quarter", (date(2026, 10, 1), date(2026, 12, 31))),
    ("next fiscal quarter", (date(2027, 1, 1), date(2027, 3, 31))),
    ("last fiscal quarter", (date(2026, 7, 1), date(2026, 9, 30))),
    ("start of FY2027", date(2026, 7, 1)),
    ("end of Q1 FY2027", date(2026, 9, 30)),
    ("P8 FY2024", (date(2024, 2, 1), date(2024, 2, 29))),
    ("8th fiscal period of FY2024", (date(2024, 2, 1), date(2024, 2, 29))),
    ("fiscal period 8 of FY2024", (date(2024, 2, 1), date(2024, 2, 29))),
    ("FP8 FY2024", (date(2024, 2, 1), date(2024, 2, 29))),
    ("this fiscal period", (date(2026, 11, 1), date(2026, 11, 30))),
])
def test_explicit_fiscal_phrases(phrase, expected):
    assert dately.parse(phrase, fiscal_calendar=dately.FiscalCalendar(start_month=7)) == expected


def test_relative_quarters_and_periods_cross_fiscal_years():
    resolver.reference_date = date(2027, 6, 30)
    calendar = dately.FiscalCalendar(start_month=7)
    assert dately.parse("next fiscal quarter", fiscal_calendar=calendar) == (date(2027, 7, 1), date(2027, 9, 30))
    assert dately.parse("next fiscal period", fiscal_calendar=calendar) == (date(2027, 7, 1), date(2027, 7, 31))
    resolver.reference_date = date(2026, 7, 1)
    assert dately.parse("last fiscal quarter", fiscal_calendar=calendar) == (date(2026, 4, 1), date(2026, 6, 30))


def test_optional_default_override_and_context_isolation():
    july = dately.FiscalCalendar(start_month=7)
    dately.set_fiscal_calendar(july)
    assert dately.get_fiscal_calendar() is july
    assert dately.parse("FY2027") == july.year_range(2027)
    january = dately.FiscalCalendar()
    assert dately.parse("FY2027", fiscal_calendar=january) == january.year_range(2027)
    assert dately.get_fiscal_calendar() is july
    context = Context()
    assert context.run(dately.get_fiscal_calendar) == january
    context.run(dately.set_fiscal_calendar, dately.RetailFiscalCalendar())
    assert dately.get_fiscal_calendar() is july
    dately.set_fiscal_calendar(None)
    assert dately.get_fiscal_calendar() == january


def test_plain_calendar_expressions_retain_calendar_meaning():
    dately.set_fiscal_calendar(dately.FiscalCalendar(start_month=7))
    assert dately.parse("Q1 2027") == (date(2027, 1, 1), date(2027, 3, 31))
    assert dately.parse("this year") == (date(2026, 1, 1), date(2026, 12, 31))


def test_fiscal_scopes_work_with_country_business_days():
    july = dately.FiscalCalendar(start_month=7)
    assert dately.parse("first business day of FY2027", fiscal_calendar=july, country="US") == date(2026, 7, 1)
    assert dately.parse("first business day of Q3 FY2027", fiscal_calendar=july, country="US") == date(2027, 1, 4)
    assert dately.parse("last business day of FY2027", fiscal_calendar=july, country="US") == date(2027, 6, 30)


@pytest.mark.parametrize("kwargs", [
    {"start_month": 0}, {"start_month": 13}, {"start_month": True}, {"start_month": 7.0},
    {"year_label": "guess"},
])
def test_bad_month_based_configuration(kwargs):
    with pytest.raises(ValueError):
        dately.FiscalCalendar(**kwargs)


def test_bad_configuration_and_date_limits():
    with pytest.raises(TypeError):
        dately.set_fiscal_calendar({"start_month": 7})
    with pytest.raises(TypeError):
        dately.parse("FY2027", fiscal_calendar=7)
    calendar = dately.FiscalCalendar()
    with pytest.raises(ValueError):
        calendar.quarter_range(2027, True)
    with pytest.raises(ValueError):
        calendar.year_range(0)
    with pytest.raises(ValueError):
        dately.FiscalCalendar(start_month=7).year_range(1)
    assert calendar.year_range(9999) == (date(9999, 1, 1), date(9999, 12, 31))
    with pytest.raises(TypeError):
        calendar.fiscal_year("2026-11-07")
    with pytest.raises(FrozenInstanceError):
        calendar.start_month = 7


@pytest.mark.parametrize("phrase", [
    "FY0000", "FY27", "Q5 FY2027", "Q0 FY2027", "Q1 FY2027 banana",
    "first fiscal quarter of banana", "1th fiscal quarter of FY2027", "P13 FY2027",
    "banana fiscal year", "fiscal quarter 5 of FY2027",
])
def test_invalid_fiscal_phrases_do_not_become_calendar_dates(phrase):
    assert dately.parse(phrase, fiscal_calendar=dately.FiscalCalendar(start_month=7)) is None


@pytest.mark.parametrize("pattern", [(4, 4, 5), (4, 5, 4), (5, 4, 4), (3, 5, 5)])
@pytest.mark.parametrize("year, weeks", [(2023, 52), (2024, 53), (2025, 52)])
def test_retail_periods_and_quarters_cover_every_day(pattern, year, weeks):
    calendar = dately.RetailFiscalCalendar(pattern=pattern)
    start, end = calendar.year_range(year)
    assert (end - start).days + 1 == weeks * 7
    assert start.weekday() == 6 and end.weekday() == 5
    periods = [calendar.period_range(year, p) for p in range(1, 13)]
    assert periods[0][0] == start and periods[-1][1] == end
    for index, (first, last) in enumerate(periods, 1):
        assert calendar.fiscal_year(first) == calendar.fiscal_year(last) == year
        assert calendar.fiscal_period(first) == calendar.fiscal_period(last) == index
        assert calendar.fiscal_quarter(first) == (index - 1) // 3 + 1
        if index < 12:
            assert last + timedelta(days=1) == periods[index][0]
    quarters = [calendar.quarter_range(year, q) for q in range(1, 5)]
    assert quarters[0][0] == start and quarters[-1][1] == end
    for index in range(3):
        assert quarters[index][1] + timedelta(days=1) == quarters[index + 1][0]


def test_retail_patterns_change_periods_and_53rd_week_is_configurable():
    first = date(2023, 1, 29)
    calendar = dately.RetailFiscalCalendar()
    assert calendar.year_range(2024) == (first, date(2024, 2, 3))
    assert calendar.period_range(2024, 1) == (first, date(2023, 2, 25))
    assert calendar.period_range(2024, 2) == (date(2023, 2, 26), date(2023, 3, 25))
    alternative = dately.RetailFiscalCalendar(pattern=(4, 5, 4))
    assert alternative.period_range(2024, 2) == (date(2023, 2, 26), date(2023, 4, 1))
    early_leap = dately.RetailFiscalCalendar(leap_week_period=1)
    assert early_leap.period_range(2024, 1) == (first, date(2023, 3, 4))
    assert (early_leap.quarter_range(2024, 1)[1] - first).days + 1 == 14 * 7


def test_retail_anchor_alignment_label_and_custom_thirteen_period_year():
    before = dately.RetailFiscalCalendar(alignment="on_or_before", year_label="start")
    after = dately.RetailFiscalCalendar(alignment="on_or_after", year_label="start")
    assert before.year_range(2023)[0] == date(2023, 1, 29)
    assert after.year_range(2023)[0] == date(2023, 2, 5)
    custom = dately.RetailFiscalCalendar(
        start_month=10, start_day=1, week_start=0, alignment="on_or_after",
        pattern=(4,) * 13, quarter_periods=(3, 3, 3, 4),
    )
    assert custom.year_range(2024)[0] == date(2023, 10, 2)
    assert custom.periods_per_year == 13
    assert custom.period_range(2024, 13)[1] == custom.year_range(2024)[1]
    assert dately.parse("P13 FY2024", fiscal_calendar=custom) == custom.period_range(2024, 13)


def test_retail_calendar_uses_the_same_parser_and_business_days():
    calendar = dately.RetailFiscalCalendar(pattern=(4, 5, 4))
    assert dately.parse("Q1 FY2024", fiscal_calendar=calendar) == calendar.quarter_range(2024, 1)
    assert dately.parse("P2 FY2024", fiscal_calendar=calendar) == calendar.period_range(2024, 2)
    assert dately.parse("first business day of FY2024", fiscal_calendar=calendar, country="US") == date(2023, 1, 30)


@pytest.mark.parametrize("month, day", [(1, 1), (2, 1), (10, 1), (12, 31)])
@pytest.mark.parametrize("alignment", ["nearest", "on_or_before", "on_or_after"])
def test_retail_alignment_across_calendar_year_boundaries(month, day, alignment):
    calendar = dately.RetailFiscalCalendar(start_month=month, start_day=day, alignment=alignment)
    for year in (2023, 2024, 2025):
        start, end = calendar.year_range(year)
        assert (end - start).days + 1 in (364, 371)
        assert calendar.fiscal_year(start) == calendar.fiscal_year(end) == year
        assert end + timedelta(days=1) == calendar.year_range(year + 1)[0]


def test_retail_relative_periods_wrap_custom_period_count():
    custom = dately.RetailFiscalCalendar(pattern=(4,) * 13, quarter_periods=(3, 3, 3, 4))
    resolver.reference_date = custom.year_range(2024)[1]
    assert dately.parse("next fiscal period", fiscal_calendar=custom) == custom.period_range(2025, 1)
    resolver.reference_date = custom.year_range(2024)[0]
    assert dately.parse("previous fiscal period", fiscal_calendar=custom) == custom.period_range(2023, 13)


@pytest.mark.parametrize("kwargs", [
    {"start_day": 0}, {"start_day": 29}, {"week_start": 7}, {"week_start": True},
    {"alignment": "unknown"}, {"pattern": (4, 4, 4)}, {"pattern": (4, True, 8)},
    {"pattern": None}, {"quarter_periods": (3, 3, 3)},
    {"leap_week_period": 0}, {"leap_week_period": 13},
])
def test_bad_retail_configuration(kwargs):
    with pytest.raises(ValueError):
        dately.RetailFiscalCalendar(**kwargs)
