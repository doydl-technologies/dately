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

import re
import datetime

from ._utils import is_leap_year, hundred_thousandths_place
from .mold.pyd.clean_str import cleanstr
from .mold.pyd.Compiled import (
    datetime_regex as datetime_pattern_search,
    anytime_regex,
    timemeridiem_regex,
    timeboundary_regex,
    time_only_regex,
    timezone_offset_regex,
    timezone_abbreviation_regex,
    iana_timezone_identifier_regex,
    full_timezone_name_regex,
    # get_time_fragment as gtf,
)


def _extract_time_details(datetime_string):
    """
    Return dict with details of the first matched time substring if it exists,
    or None if no time is found.
    """
    time_exists = timeboundary_regex.search(datetime_string)
    if time_exists:
        full_time_start_position = time_exists.start()
        full_time_end_position = time_exists.end()
        full_time_string = time_exists.group()

        time_match = time_only_regex.search(full_time_string)
        if time_match:
            return {
                'time_details': {
                    'time_found': time_match.group(),
                    'start': time_match.start() + full_time_start_position,
                    'end': time_match.end() + full_time_start_position
                },
                'full_time_details': {
                    'full_time_string': full_time_string,
                    'start': full_time_start_position,
                    'end': full_time_end_position
                }
            }
    return None

def datetime_offset(offset):
    if not isinstance(offset, (int, float)):
        raise ValueError("Offset must be an integer or float representing hours.")
    timezone = datetime.timezone(datetime.timedelta(hours=offset))
    return timezone


def coerce_timezone(value):
    """Return a ``tzinfo`` instance for a supported public ``tzinfo`` value."""
    if isinstance(value, datetime.tzinfo):
        return value
    if isinstance(value, (int, float)):
        return datetime_offset(value)
    if not isinstance(value, str):
        raise ValueError("tzinfo must be a timezone object, name, or numeric UTC offset.")

    value = value.strip()
    if not value:
        raise ValueError("tzinfo cannot be empty.")
    if value.upper() in {"UTC", "GMT", "Z"}:
        return datetime.timezone.utc

    offset_match = re.fullmatch(r"([+-]?)(\d{1,2})(?::?(\d{2}))?", value)
    if offset_match:
        sign, hours, minutes = offset_match.groups()
        total_minutes = int(hours) * 60 + int(minutes or 0)
        if sign == "-":
            total_minutes *= -1
        try:
            return datetime.timezone(datetime.timedelta(minutes=total_minutes))
        except ValueError as exc:
            raise ValueError(f"Invalid UTC offset: {value}") from exc

    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(value)
    except (ImportError, KeyError):
        try:
            import pytz
            return pytz.timezone(value)
        except (pytz.UnknownTimeZoneError, ModuleNotFoundError) as exc:
            raise ValueError(f"Unknown timezone: {value}") from exc


def _format_timezone_text(value):
    """Format a timezone value for a non-ISO datetime string."""
    if isinstance(value, (int, float)):
        offset = datetime_offset(value).utcoffset(None)
        total_minutes = int(offset.total_seconds() // 60)
        sign = "+" if total_minutes >= 0 else "-"
        hours, minutes = divmod(abs(total_minutes), 60)
        return f"{sign}{hours:02d}:{minutes:02d}"
    if isinstance(value, str):
        stripped = value.strip()
        offset_match = re.fullmatch(r"([+-]?)(\d{1,2})(?::?(\d{2}))?", stripped)
        if offset_match:
            tz = coerce_timezone(stripped)
            return _format_timezone_text(tz)
        # Validate named zones before preserving their human-readable spelling.
        coerce_timezone(stripped)
        return stripped
    if isinstance(value, datetime.tzinfo):
        zone_name = getattr(value, "key", None) or getattr(value, "zone", None)
        if zone_name:
            return zone_name
        offset = value.utcoffset(None)
        if offset is None:
            name = value.tzname(None)
            if name:
                return name
            raise ValueError("Timezone object has no usable name or UTC offset.")
        total_minutes = int(offset.total_seconds() // 60)
        sign = "+" if total_minutes >= 0 else "-"
        hours, minutes = divmod(abs(total_minutes), 60)
        return f"{sign}{hours:02d}:{minutes:02d}"
    raise ValueError("tzinfo must be a timezone object, name, or numeric UTC offset.")

def strTime(datetime_string):
    """ Extracts and returns detailed time information from a datetime string. """
    time_exists = timeboundary_regex.search(datetime_string)

    if time_exists:
        full_time_start_position = time_exists.start()
        full_time_end_position = time_exists.end()
        full_time_string = time_exists.group()

        time_match = time_only_regex.search(full_time_string)

        if time_match:
            time_details = {
                'time_found': time_match.group(),
                'start': time_match.start() + full_time_start_position,
                'end': time_match.end() + full_time_start_position
            }
            full_time_details = {
                'full_time_string': full_time_string,
                'start': full_time_start_position,
                'end': full_time_end_position
            }

            result = {
                'time_details': time_details,
                'full_time_details': full_time_details
            }
            return result
    return None

def _stripTimeIndicator(datetime_string):
    """
    Remove AM/PM markers in the substring after the recognized time portion.
    """
    match = _extract_time_details(datetime_string)
    if match:
        time_end = match['time_details']['end']
        full_time_start = match['full_time_details']['start']
        full_time_end = match['full_time_details']['end']
        timezone_data = datetime_string[time_end:]
        if not timezone_data:
            return datetime_string
        cleaned_string = re.sub(timemeridiem_regex, ' ', timezone_data)
        return (datetime_string[:full_time_start]
                + match['time_details']['time_found']
                + cleaned_string
                + datetime_string[full_time_end:])
    return datetime_string

def remove_marker(text):
    """
    Removes ' NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET' from the provided text.

    Parameters:
    text (str): The input text from which the marker needs to be removed.

    Returns:
    str: The cleaned text without the specified marker.
    """
    pattern = re.compile(r" NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET")

    cleaned_text = pattern.sub("", text)
    return cleaned_text

def validate_timezone(datetime_string):
    """
    Check the timezone portion of the datetime string. Before checking,
    remove any placeholder tokens so that spurious matches aren’t counted.
    """
    match = _extract_time_details(datetime_string)
    if match:
        time_end = match['time_details']["end"]
        # Extract the suffix following the time and remove the internal placeholder.
        timezone_data = datetime_string[time_end:]
        timezone_data = timezone_data.replace("NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET", "").strip()
        if timezone_data == '':
            return True, "The time string is valid."
        if len(timemeridiem_regex.findall(timezone_data)) > 1:
            return False, "More than one time indicator found."
        if len(timezone_offset_regex.findall(timezone_data)) > 1:
            return False, "More than one timezone offset found."
        if len(timezone_abbreviation_regex.findall(timezone_data)) > 1:
            return False, "More than one timezone abbreviation found."
        if len(iana_timezone_identifier_regex.findall(timezone_data)) > 1:
            return False, "More than one IANA timezone identifier found."
        if len(full_timezone_name_regex.findall(timezone_data)) > 1:
            return False, "More than one full timezone name found."
        return True, "The time string is valid."
    return False, "No valid time string found"

def validate_date(date_string, date_format):
    """
    Validates the given date string in the format of 'month/day/year'.
    It first extracts any localized time fragment and cleans the string,
    then identifies the components of the date (month, day, year) and
    checks their validity based on standard calendar rules.
    """

    def stripTime(datetime_string):
        """ Removes time from a datetime string. """
        time_exists = timeboundary_regex.search(datetime_string)
        if time_exists:
            full_time_start_position = time_exists.start()
            date_no_time = datetime_string[:full_time_start_position]
            return cleanstr(date_no_time)
        return datetime_string

    date_str = stripTime(date_string)
    components_spans = {"month": None, "day": None, "year": None}
    pattern = datetime_pattern_search(date_format)
    match = pattern.match(date_str)
    if match:
        for key in components_spans.keys():
            if key in match.groupdict():
                components_spans[key] = match.span(key)

    day = int(date_str[slice(*components_spans['day'])])
    month = int(date_str[slice(*components_spans['month'])])
    year = int(date_str[slice(*components_spans['year'])])

    month_days = {1: 31, 2: 29 if is_leap_year(year) else 28, 3: 31, 4: 30, 5: 31, 6: 30,
                  7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    if month < 1 or month > 12:
        return False  # Invalid month
    if day < 1 or day > month_days.get(month, 31):
        return False  # Day is not valid for the month
    return True

def exist_meridiem(time_fragment_str):
    """
    Check if a meridiem indicator (AM/PM) exists in a given time fragment string.

    This function uses a compiled regex pattern to search for the presence of meridiem indicators (AM or PM)
    in the provided time fragment string. It returns True if a match is found, otherwise None.

    Parameters:
        time_fragment_str (str): The time fragment string to be checked for a meridiem indicator.

    Returns:
        bool or None: Returns True if a meridiem indicator is found, otherwise None.
    """
    return bool(timemeridiem_regex.search(time_fragment_str))





###############################################################################
# CORE FUNCTIONS
###############################################################################
def make_datetime_string(date_string):
    """
    If a time is found in the date string, return the string with any
    placeholder removed. Otherwise, append a default time along with a
    placeholder so that later code can remove it.
    """
    def get_default_time():
        """
        Return a default time string for cases when a date string has no time.
        """
        return "00:00:00.000000"

    placeholder = "NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET"
    match = anytime_regex.search(date_string)
    if match:
        # Remove any placeholder that might already be present.
        return date_string.replace(placeholder, "").strip()
    else:
        # No time present, so append a default time and the placeholder.
        return f"{date_string.strip()} {get_default_time()} {placeholder}"


def replace_time_by_position(datetime_string, component, new_value):
    """
    Replaces the specified time component (hour, minute, second, microsecond, tzinfo)
    within the recognized time substring of the datetime string.
    """

    # Basic validation / bounding
    if component == 'hour':
        new_value = str(max(0, min(23, int(new_value))))
        if len(new_value) == 1:
            new_value = "0" + new_value
    elif component in ['minute', 'second']:
        new_value = str(max(0, min(59, int(new_value)))).zfill(2)
    elif component == 'microsecond':
        # Skip invalid candidates.
        if not str(new_value).isdigit():
            return datetime_string

    entire_time_match = timeboundary_regex.search(datetime_string)
    if not entire_time_match:
        # No recognized time => do nothing
        return datetime_string

    time_str_start = entire_time_match.start()
    time_substring = entire_time_match.group()

    if component == 'tzinfo':
        new_value = _format_timezone_text(new_value)
        time_match = time_only_regex.search(time_substring)
        tail_start = time_match.end() if time_match else 0
        timezone_tail = time_substring[tail_start:]
        existing_tz_matches = []
        for pattern in (
            iana_timezone_identifier_regex,
            full_timezone_name_regex,
            timezone_abbreviation_regex,
            timezone_offset_regex,
        ):
            match = pattern.search(timezone_tail)
            if match:
                existing_tz_matches.append(match)
        if existing_tz_matches:
            existing_match = min(existing_tz_matches, key=lambda m: m.start())
            match_start = time_str_start + tail_start + existing_match.start()
            match_end = time_str_start + tail_start + existing_match.end()
            part_before = datetime_string[:match_start]
            part_after = datetime_string[match_end:]
            updated = part_before + new_value + part_after
        else:
            if 'NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET' in datetime_string:
                updated = datetime_string.replace('NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET', new_value)
            else:
                updated = f"{datetime_string.rstrip()} {new_value}"
        return updated.strip()

    # For hour, minute, second, microsecond
    match_timeonly = time_only_regex.search(time_substring)
    if match_timeonly:
        # Fractional seconds are optional in the matched group dictionary.
        groups = match_timeonly.groupdict()
        # start(1) => the first capturing group (hours?), etc.
        # For hour/minute/second, it's typically group(1) or group(2)
        # Select the named group for the requested component.

        if component == 'hour':
            # group 'hours' => groupdict has 'hours'
            span = match_timeonly.span('hours')
        elif component == 'minute':
            span = match_timeonly.span('minutes')
        elif component == 'second':
            # 'seconds' can be absent, so check:
            if 'seconds' in groups and groups['seconds'] is not None:
                span = match_timeonly.span('seconds')
            else:
                # Insert missing seconds immediately after the minute field.
                minute_span = match_timeonly.span('minutes')
                insertion_pos = time_str_start + minute_span[1]
                return (
                    datetime_string[:insertion_pos]
                    + f":{new_value}"
                    + datetime_string[insertion_pos:]
                ).replace('NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET', '').strip()
        elif component == 'microsecond':
            # If there's a group 'microseconds'
            if 'microseconds' in groups and groups['microseconds'] is not None:
                span = match_timeonly.span('microseconds')
                new_value = hundred_thousandths_place(new_value, decimal=False)
            else:
                # Append missing fractional seconds to the matched time.
                end_time_span = match_timeonly.end()
                insertion_pos = time_str_start + end_time_span
                to_insert = '.' + hundred_thousandths_place(new_value, decimal=False)
                return (
                    datetime_string[:insertion_pos]
                    + to_insert
                    + datetime_string[insertion_pos:]
                ).replace('NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET', '').strip()

        # Now do the actual substring replacement
        comp_start = time_str_start + span[0]
        comp_end = time_str_start + span[1]
        updated = (
            datetime_string[:comp_start]
            + new_value
            + datetime_string[comp_end:]
        )
        return updated.replace('NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET', '').strip()

    return datetime_string.replace('NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET', '').strip()
