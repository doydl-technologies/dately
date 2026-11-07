"""Explicit fiscal grammar; ordinary year/quarter phrases remain calendar-based."""

import re


_MARKER = re.compile(r"\bfiscal\b|\bfy(?=\s|\d|$)|\bf[qp](?=\s|\d|$)")
_DIRECTION = {"this": 0, "next": 1, "last": -1, "previous": -1}
_ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4,
             "1st": 1, "2nd": 2, "3rd": 3, "4th": 4}


def parse_fiscal_expression(phrase, reference, calendar):
    """Return (handled, date/range/None) using a validated fiscal calendar."""
    if not _MARKER.search(phrase):
        return False, None
    text = phrase[4:] if phrase.startswith("the ") else phrase
    current_year = calendar.fiscal_year(reference)

    def year_label(scope):
        explicit = re.fullmatch(r"(?:fy\s*|fiscal year\s+)([0-9]{4})", scope)
        if explicit:
            return int(explicit[1])
        relative = re.fullmatch(r"(this|next|last|previous) fiscal year", scope)
        if relative:
            return current_year + _DIRECTION[relative[1]]
        return None

    boundary = re.fullmatch(r"(start|end|middle) of (.+)", text)
    if boundary:
        _, span = parse_fiscal_expression(boundary[2], reference, calendar)
        if not isinstance(span, tuple):
            return True, None
        first, last = span
        return True, {"start": first, "end": last, "middle": first + (last - first) // 2}[boundary[1]]

    year = year_label(text)
    if year is not None:
        return True, calendar.year_range(year)

    relative = re.fullmatch(r"(this|next|last|previous) fiscal (quarter|period)", text)
    if relative:
        if relative[2] == "quarter":
            count, number, resolve = 4, calendar.fiscal_quarter(reference), calendar.quarter_range
        else:
            count, number, resolve = calendar.periods_per_year, calendar.fiscal_period(reference), calendar.period_range
        position = current_year * count + number - 1 + _DIRECTION[relative[1]]
        year, number = divmod(position, count)
        return True, resolve(year, number + 1)

    # Q1 FY2027; fiscal Q1 2027; FQ1 FY2027; Q1 of next fiscal year.
    part = re.fullmatch(r"(fiscal q|fq|q|fiscal p|fp|p)([0-9]{1,2})(?: (?:of )?(.+))?", text)
    if part:
        scope = part[3]
        if scope is None:
            year = current_year if part[1] not in {"q", "p"} else None
        elif part[1] not in {"q", "p"} and re.fullmatch(r"[0-9]{4}", scope):
            year = int(scope)
        else:
            year = year_label(scope)
        resolve = calendar.quarter_range if part[1].endswith("q") else calendar.period_range
        return True, resolve(year, int(part[2])) if year is not None else None

    # first fiscal quarter of FY2027; fiscal quarter 2 of next fiscal year.
    ordinal = re.fullmatch(r"(first|second|third|fourth|[0-9]{1,2}(?:st|nd|rd|th)) fiscal (quarter|period)(?: of (.+))?", text)
    numeric = re.fullmatch(r"fiscal (quarter|period) ([0-9]{1,2})(?: (?:of )?(.+))?", text)
    if ordinal or numeric:
        match = ordinal or numeric
        if ordinal:
            number = _ORDINALS.get(match[1])
            digits = re.fullmatch(r"([0-9]{1,2})(st|nd|rd|th)", match[1])
            if number is None and digits:
                value = int(digits[1])
                suffix = "th" if 10 <= value % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
                number = value if digits[2] == suffix else None
            kind = match[2]
        else:
            kind, number = match[1], int(match[2])
        scope = match[3]
        year = current_year if scope is None else year_label(scope)
        if numeric and scope and re.fullmatch(r"[0-9]{4}", scope):
            year = int(scope)
        resolve = calendar.quarter_range if kind == "quarter" else calendar.period_range
        return True, resolve(year, number) if year is not None and number is not None else None
    return True, None
