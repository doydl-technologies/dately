"""Offline business calendars, independent of locale and network services."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta


@dataclass(frozen=True)
class BusinessCalendar:
    """Eligible weekdays (Monday=0), closures, and optional country holidays.

    With country set, public holidays are loaded through HolidayManager for
    each year visited. Explicit holidays add company closures. Calendar options
    are immutable; a private per-instance cache avoids repeating yearly lookups.
    """

    working_days: tuple = (0, 1, 2, 3, 4)
    holidays: frozenset = frozenset()
    country: str = None
    subdiv: str = None
    observed: bool = True
    _holiday_manager: object = field(default=None, init=False, repr=False, compare=False)
    _country_holidays: dict = field(default_factory=dict, init=False, repr=False, compare=False)

    def __post_init__(self):
        days = frozenset(self.working_days)
        holidays = frozenset(self.holidays)
        if not days or any(type(day) is not int or not 0 <= day <= 6 for day in days):
            raise ValueError("working_days must contain weekday integers from 0 through 6")
        if any(not isinstance(day, date) or isinstance(day, datetime) for day in holidays):
            raise ValueError("holidays must contain datetime.date values (without times)")
        object.__setattr__(self, "working_days", days)
        object.__setattr__(self, "holidays", holidays)
        if type(self.observed) is not bool:
            raise TypeError("observed must be a boolean")
        if self.country is None:
            if self.subdiv is not None or self.observed is not True:
                raise ValueError("subdiv and observed options require a country")
        else:
            if self.subdiv is not None and (not isinstance(self.subdiv, str) or not self.subdiv.strip()):
                raise ValueError("subdiv must be a non-empty subdivision code or None")
            # Import lazily to keep the default calendar independent of the
            # holiday provider and avoid a package-initialization cycle.
            from .._holiday import HolidayManager

            manager = HolidayManager()
            name, code = manager._resolve_country(self.country)
            manager._public_calendar(name, code, None, self.subdiv, self.observed)
            object.__setattr__(self, "country", name)
            object.__setattr__(self, "_holiday_manager", manager)

    def is_business_day(self, day):
        if day.weekday() not in self.working_days or day in self.holidays:
            return False
        if self.country is None:
            return True
        if day.year not in self._country_holidays:
            from .._holiday import HolidayLookupError

            try:
                records = self._holiday_manager.Holiday(
                    self.country, day.year, format="dict",
                    subdiv=self.subdiv, observed=self.observed,
                )
            except (TypeError, ValueError) as exc:
                raise HolidayLookupError(
                    f"Could not load business-day holidays for '{self.country}' in {day.year}: {exc}"
                ) from exc
            self._country_holidays[day.year] = frozenset(date.fromisoformat(row["Date"]) for row in records)
        return day not in self._country_holidays[day.year]

    def add_business_days(self, day, amount):
        """Count eligible days strictly after/before day; zero preserves day."""
        if type(amount) is not int:
            raise TypeError("amount must be an integer")
        step = timedelta(days=1 if amount >= 0 else -1)
        remaining = abs(amount)
        while remaining:
            day += step
            if self.is_business_day(day):
                remaining -= 1
        return day


DEFAULT_BUSINESS_CALENDAR = BusinessCalendar()
