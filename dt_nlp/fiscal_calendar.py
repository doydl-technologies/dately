"""Month-based fiscal years and quarters, independent of the date parser."""

from calendar import monthrange
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class FiscalCalendar:
    """A fiscal year starting on day one of start_month.

    year_label='end' names July 2026-June 2027 FY2027; 'start' names it
    FY2026. January starts have the same label under either convention.
    Quarters are three calendar months; retail week-based calendars are excluded.
    """

    start_month: int = 1
    year_label: str = "end"

    def __post_init__(self):
        if type(self.start_month) is not int or not 1 <= self.start_month <= 12:
            raise ValueError("start_month must be an integer from 1 through 12")
        if self.year_label not in ("start", "end"):
            raise ValueError("year_label must be 'start' or 'end'")

    def fiscal_year(self, day):
        """Return the numeric fiscal-year label containing a date/datetime."""
        if not isinstance(day, date):
            raise TypeError("day must be a datetime.date or datetime.datetime")
        start_year = day.year - (day.month < self.start_month)
        return start_year + (self.year_label == "end" and self.start_month != 1)

    def fiscal_quarter(self, day):
        """Return the fiscal quarter number (1-4) containing a date/datetime."""
        if not isinstance(day, date):
            raise TypeError("day must be a datetime.date or datetime.datetime")
        return (day.month - self.start_month) % 12 // 3 + 1

    @property
    def periods_per_year(self):
        return 12

    def fiscal_period(self, day):
        """Return fiscal month/period number (1-12)."""
        if not isinstance(day, date):
            raise TypeError("day must be a datetime.date or datetime.datetime")
        return (day.month - self.start_month) % 12 + 1

    def _start_year(self, year):
        if type(year) is not int or not 1 <= year <= 9999:
            raise ValueError("fiscal year must be an integer from 1 through 9999")
        return year - (self.year_label == "end" and self.start_month != 1)

    def _month_span(self, start_year, offset, count):
        first = start_year * 12 + self.start_month - 1 + offset
        first_year, first_month = divmod(first, 12)
        last_year, last_month = divmod(first + count - 1, 12)
        if not 1 <= first_year <= last_year <= 9999:
            raise ValueError("Fiscal period extends outside the supported date range")
        return (
            date(first_year, first_month + 1, 1),
            date(last_year, last_month + 1, monthrange(last_year, last_month + 1)[1]),
        )

    def year_range(self, year):
        """Return inclusive (first_date, last_date) for a fiscal-year label."""
        return self._month_span(self._start_year(year), 0, 12)

    def quarter_range(self, year, quarter):
        """Return inclusive dates for quarter 1-4 in a fiscal-year label."""
        if type(quarter) is not int or not 1 <= quarter <= 4:
            raise ValueError("quarter must be an integer from 1 through 4")
        return self._month_span(self._start_year(year), (quarter - 1) * 3, 3)

    def period_range(self, year, period):
        """Return inclusive dates for fiscal month/period 1-12."""
        if type(period) is not int or not 1 <= period <= 12:
            raise ValueError("period must be an integer from 1 through 12")
        return self._month_span(self._start_year(year), period - 1, 1)


@dataclass(frozen=True)
class RetailFiscalCalendar(FiscalCalendar):
    """A week-based fiscal year with configurable periods and start rules.

    The start is a chosen weekday nearest/on-or-before/on-or-after a fixed
    annual anchor. A three-period pattern totaling 13 weeks repeats four times;
    alternatively supply the entire 52-week year's periods and quarter grouping.
    A 53rd week belongs to leap_week_period (last period by default).

    Labels use the nominal anchor year ('start') or the following year ('end'),
    except January anchors use the anchor year for both, like FiscalCalendar.
    Actual aligned starts may fall in the preceding/following calendar year.
    """

    start_month: int = 2
    start_day: int = 1
    week_start: int = 6  # Monday=0, Sunday=6
    alignment: str = "nearest"
    pattern: tuple = (4, 4, 5)
    quarter_periods: tuple = (3, 3, 3, 3)
    leap_week_period: int = None

    def __post_init__(self):
        super().__post_init__()
        if type(self.start_day) is not int:
            raise ValueError("start_day must be a day valid in every year's anchor month")
        try:
            date(2001, self.start_month, self.start_day)
        except ValueError as exc:
            raise ValueError("start_day must be valid in every year's anchor month (no February 29)") from exc
        if type(self.week_start) is not int or not 0 <= self.week_start <= 6:
            raise ValueError("week_start must be an integer from 0 through 6")
        if self.alignment not in ("nearest", "on_or_before", "on_or_after"):
            raise ValueError("alignment must be 'nearest', 'on_or_before', or 'on_or_after'")
        try:
            pattern, groups = tuple(self.pattern), tuple(self.quarter_periods)
        except TypeError as exc:
            raise ValueError("pattern and quarter_periods must be sequences of positive integers") from exc
        if not pattern or any(type(n) is not int or n < 1 for n in pattern):
            raise ValueError("pattern must contain positive week counts")
        if len(pattern) == 3 and sum(pattern) == 13:
            pattern *= 4
        if sum(pattern) != 52:
            raise ValueError("pattern must total 52 weeks, or be three periods totaling 13 weeks")
        if len(groups) != 4 or any(type(n) is not int or n < 1 for n in groups) or sum(groups) != len(pattern):
            raise ValueError("quarter_periods must contain four positive counts covering every period")
        leap = len(pattern) if self.leap_week_period is None else self.leap_week_period
        if type(leap) is not int or not 1 <= leap <= len(pattern):
            raise ValueError("leap_week_period must identify a period in the pattern")
        object.__setattr__(self, "pattern", pattern)
        object.__setattr__(self, "quarter_periods", groups)
        object.__setattr__(self, "leap_week_period", leap)

    def _aligned_start(self, anchor_year):
        if not 1 <= anchor_year <= 9999:
            raise ValueError("Fiscal period extends outside the supported date range")
        anchor = date(anchor_year, self.start_month, self.start_day)
        before = (anchor.weekday() - self.week_start) % 7
        after = (self.week_start - anchor.weekday()) % 7
        offset = -before
        if self.alignment == "on_or_after" or (self.alignment == "nearest" and after < before):
            offset = after
        try:
            return anchor + timedelta(days=offset)
        except OverflowError as exc:
            raise ValueError("Fiscal period extends outside the supported date range") from exc

    def year_range(self, year):
        start_year = self._start_year(year)
        first, following = self._aligned_start(start_year), self._aligned_start(start_year + 1)
        return first, following - timedelta(days=1)

    def fiscal_year(self, day):
        if not isinstance(day, date):
            raise TypeError("day must be a datetime.date or datetime.datetime")
        if hasattr(day, "date"):
            day = day.date()
        # A late-December anchor can start in the following January and end
        # two calendar years after its nominal anchor year.
        for anchor_year in range(max(1, day.year - 2), min(9998, day.year + 1) + 1):
            first, following = self._aligned_start(anchor_year), self._aligned_start(anchor_year + 1)
            if first <= day < following:
                return anchor_year + (self.year_label == "end" and self.start_month != 1)
        raise ValueError("Fiscal period extends outside the supported date range")

    @property
    def periods_per_year(self):
        return len(self.pattern)

    def _period_lengths(self, year):
        first, last = self.year_range(year)
        lengths = list(self.pattern)
        if (last - first).days + 1 == 371:
            lengths[self.leap_week_period - 1] += 1
        return first, lengths

    def period_range(self, year, period):
        if type(period) is not int or not 1 <= period <= self.periods_per_year:
            raise ValueError(f"period must be an integer from 1 through {self.periods_per_year}")
        first, lengths = self._period_lengths(year)
        start = first + timedelta(weeks=sum(lengths[:period - 1]))
        return start, start + timedelta(weeks=lengths[period - 1]) - timedelta(days=1)

    def quarter_range(self, year, quarter):
        if type(quarter) is not int or not 1 <= quarter <= 4:
            raise ValueError("quarter must be an integer from 1 through 4")
        first_period = sum(self.quarter_periods[:quarter - 1]) + 1
        last_period = sum(self.quarter_periods[:quarter])
        return self.period_range(year, first_period)[0], self.period_range(year, last_period)[1]

    def fiscal_period(self, day):
        year = self.fiscal_year(day)
        if hasattr(day, "date"):
            day = day.date()
        for period in range(1, self.periods_per_year + 1):
            if day <= self.period_range(year, period)[1]:
                return period

    def fiscal_quarter(self, day):
        period = self.fiscal_period(day)
        count = 0
        for quarter, size in enumerate(self.quarter_periods, 1):
            count += size
            if period <= count:
                return quarter


DEFAULT_FISCAL_CALENDAR = FiscalCalendar()
_calendar_setting = ContextVar("dately_fiscal_calendar", default=DEFAULT_FISCAL_CALENDAR)


def get_fiscal_calendar():
    """Return the default fiscal calendar in the current execution context."""
    return _calendar_setting.get()


def set_fiscal_calendar(calendar=None):
    """Set the current context's default; None restores January-December.

    Explicit parse(..., fiscal_calendar=...) settings override this default.
    Ordinary calendar-year/quarter expressions retain their existing meaning.
    """
    if calendar is None:
        calendar = DEFAULT_FISCAL_CALENDAR
    if not isinstance(calendar, FiscalCalendar):
        raise TypeError("calendar must be a FiscalCalendar or None")
    _calendar_setting.set(calendar)
