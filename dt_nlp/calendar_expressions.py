"""Strict grammar for calendar-filtered days and explicit forward offsets.

These productions run before fuzzy token correction: multiword units must retain
their meaning, and unsupported business-day phrases must not become ordinary days.
"""

import re
from datetime import date, timedelta

from .arithmetic import numbers
from .business_calendar import DEFAULT_BUSINESS_CALENDAR


_FILTERED = re.compile(r"\b(?:business[ _-]+days?|working[ _-]+days?|weekdays?)\b")
_UNIT = r"(business_day|weekday|day|week|month|year)s?"


def _number(text, ordinal=False):
    if text in {"a", "an"} and not ordinal:
        return 1
    kind = numbers.num_type(text)
    allowed = {"ordinalWord", "ordinalNumber"} if ordinal else {"cardinalWord", "cardinalNumber"}
    if kind not in allowed:
        return None
    value = int(numbers.to_type(text, "cardinalNumber"))
    return value if value >= 0 else None


def parse_calendar_expression(phrase, reference, calendar, resolve, add_months, add_years):
    """Return (handled, result); full matches serve as syntax validation.

    ``resolve`` evaluates an ordinary date/period using the existing pipeline.
    All new arithmetic uses local dates, never changes the shared reference date.
    """
    filtered = bool(_FILTERED.search(phrase))
    text = _FILTERED.sub(lambda m: "weekday" if m[0].startswith("weekday") else "business_day", phrase)
    if filtered and text.startswith("the "):
        text = text[4:]
    # Explicit offsets have point semantics, unlike legacy 'next N days' spans.
    offset_text = text.split(" starting from ", 1)[0]
    handled = filtered or bool(re.fullmatch(r"in .+? " + _UNIT, offset_text))
    if not handled:
        return False, None

    def shift(base, amount, unit):
        if unit in {"business_day", "weekday"}:
            cal = calendar if unit == "business_day" else DEFAULT_BUSINESS_CALENDAR
            return cal.add_business_days(base, amount)
        if unit == "day":
            return base + timedelta(days=amount)
        if unit == "week":
            return base + timedelta(weeks=amount)
        if unit == "month":
            return add_months(base, amount)
        return add_years(base, amount)

    def point(anchor):
        result = resolve(anchor)
        return result if isinstance(result, date) else None

    # Re-evaluate the complete offset at an explicit anchor, without modifying
    # resolver.reference_date (including when the nested expression fails).
    anchored = re.fullmatch(r"(.+?) starting from (.+)", text)
    if anchored:
        # A starting point belongs to an offset or traversal, not to a scoped
        # selection or a second independently anchored expression.
        offset = anchored[1]
        if not (
            re.fullmatch(r"in .+? " + _UNIT, offset)
            or re.fullmatch(r".+? " + _UNIT + r" ago", offset)
            or re.fullmatch(r"(?:next|last|previous) (?:(?:.+?) )?(?:business_day|weekday)", offset)
        ):
            return True, None
        if " starting from " in anchored[2]:
            return True, None
        base = point(anchored[2])
        if base is None:
            return True, None
        return parse_calendar_expression(
            anchored[1].replace("business_day", "business day"), base,
            calendar, resolve, add_months, add_years,
        )

    match = re.fullmatch(r"in (.+?) " + _UNIT, text)
    if match:
        amount = _number(match[1])
        return True, None if amount is None else shift(reference, amount, match[2])

    match = re.fullmatch(r"(.+?) " + _UNIT + r" ago", text)
    if match:
        amount = _number(match[1])
        return True, None if amount is None else shift(reference, -amount, match[2])

    match = re.fullmatch(r"(.+?) " + _UNIT + r" (after|before|from) (.+)", text)
    if match:
        amount, base = _number(match[1]), point(match[4])
        if amount is None or base is None:
            return True, None
        return True, shift(base, -amount if match[3] == "before" else amount, match[2])

    match = re.fullmatch(r"(?:the )?(.+?) (business_day|weekday) of (.+)", text)
    if match:
        selection, unit, scope = match.groups()
        period = resolve(scope)
        if not isinstance(period, tuple) or len(period) != 2 or not all(isinstance(x, date) for x in period):
            return True, None
        cal = calendar if unit == "business_day" else DEFAULT_BUSINESS_CALENDAR
        eligible = []
        cursor, end = period
        while cursor <= end:
            if cal.is_business_day(cursor):
                eligible.append(cursor)
            if cursor == end:
                break
            cursor += timedelta(days=1)
        if selection in {"first", "last"}:
            return True, (eligible[0 if selection == "first" else -1] if eligible else None)
        segment = re.fullmatch(r"(first|last) (.+)", selection)
        if segment:
            amount = _number(segment[2])
            if amount is None or amount < 1 or amount > len(eligible):
                return True, None
            return True, eligible[:amount] if segment[1] == "first" else eligible[-amount:]
        ordinal = _number(selection, ordinal=True)
        return True, eligible[ordinal - 1] if ordinal and ordinal <= len(eligible) else None

    match = re.fullmatch(r"(next|last|previous) (?:(.+?) )?(business_day|weekday)", text)
    if match:
        amount = 1 if match[2] is None else _number(match[2])
        if amount is None or amount < 1:
            return True, None
        direction = 1 if match[1] == "next" else -1
        result, cursor = [], reference
        for _ in range(amount):
            cursor = shift(cursor, direction, match[3])
            result.append(cursor)
        return True, result[0] if amount == 1 else result
    return True, None
