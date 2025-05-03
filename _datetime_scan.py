# -*- coding: utf-8 -*-

#
# doydl's Temporal Format & Transformation Utilities — dately
#
# The `dately` module provides foundational utilities for parsing, detecting, modifying,
# and vectorizing datetime strings and objects across a wide range of input types.
#
# Designed as infrastructure for robust and platform-agnostic date handling,
# it includes logic for format inference, ISO/non-ISO validation, timezone patching,
# and safe transformation of individual date/time components. It supports batch
# processing over lists, NumPy arrays, Pandas Series, and dictionaries — with
# consistent shape preservation and error handling.
#
# Core capabilities include:
# - Flexible strptime-format detection (`DateFormatFinder`)
# - Datetime component extraction (e.g., extract hour or weekday)
# - In-place modification of time and date fields
# - Uniform application of datetime logic to scalars and collections
#
# This logic is format-centric and independent of any language-level semantics.
# It serves as a reliable backend for preprocessing, standardization, and
# cross-platform datetime normalization workflows.
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
from datetime import datetime as dt

#────────── Third-party library imports (from PyPI or other package sources) ─────────────────────────────────
import numpy as num
import pandas as panda

# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from .mold.pyd.time_zones import time_zones_dict as tz_dict




#────────────────────────────────────────────────────────────────────────────
# REGEX FOR DETECTING TIME COMPONENTS IN STRINGS
#────────────────────────────────────────────────────────────────────────────
# This regex pattern is used to detect time-related components in a string. It 
# supports various time formats, including standard clock times, fractional 
# seconds, AM/PM markers, and optional time zones.
# 
# ### Pattern Details:
# - Prevention of False Matches:
#   - Ensures the detected pattern is not preceded by a digit (`(?<!\d)`) to 
#     avoid misinterpreting numbers as times.
# 
# - Option 1: Standard Time Formats
#   - Matches times written as:
#     - `HH:MM`, `HH:MM:SS`, or compact form `HHMMSS`
#     - Supports fractional seconds (e.g., `12:30:45.123456`)
#     - Recognizes AM/PM markers (e.g., `3:45 PM`)
#     - Optionally detects time zones (e.g., `UTC`, `+02:00`, `Z`)
# 
# - Option 2: Standalone Timezones
#   - Matches timezone-only strings if preceded by whitespace or start-of-string:
#     - `+02:00`, `-0400`, `EST`, `UTC`, `Z`
#   
# - Lookahead (`(?=\s|$)`)
#   - Ensures the match must be followed by whitespace or end-of-string to 
#     prevent partial matches inside words.
# 
# ### Use Case:
# - Primarily used in date format detection to extract time components 
#   from mixed datetime strings.
# - Works in conjunction with the DateFormatFinder class.
_TIME_DETECTION_RE = re.compile(
    r"(?<!\d)(?:"                                 	# Ensure not preceded by a digit.
        r"(?:(?:\d{1,2}:\d{2}(?::\d{2})?|\d{6})"  	# Option 1: time formats (HH:MM, HH:MM:SS, or HHMMSS)
        r"(?:\.\d{1,6})?"                         	# Optional fractional seconds.
        r"(?:\s*[AP]M)?"                          	# Optional AM/PM marker.
        r"(?:\s*(?:[+-]\d{2}:?\d{2}|[+-]\d{4}|[A-Z]{3,4}|Z))?"  # Optional timezone.
        r")"
        r"|"                                      	# OR
        r"(?:(?<=\s)|^)(?:[+-]\d{2}:?\d{2}|[+-]\d{4}|[A-Z]{3,4}|Z)"  # Option 2: timezone-only; must be preceded by whitespace or start-of-string.
    r")(?=\s|$)",                                 	# Lookahead: must be followed by whitespace or end-of-string.
    re.IGNORECASE
)

#────────────────────────────────────────────────────────────────────────────
# REGEX FOR DETECTING WEEKDAY NAMES IN STRINGS
#────────────────────────────────────────────────────────────────────────────
# This regex pattern is designed to detect and extract weekday names (e.g., "Monday", "Tue") 
# from a given string. It supports both full names (e.g., "Wednesday") and abbreviations 
# (e.g., "Wed").
# 
# ### Pattern Breakdown:
# - Capturing Group `(?P<weekday>...)`  
#   - Detects both full and abbreviated weekday names:
#     - `"Monday"`, `"Mon"`
#     - `"Tuesday"`, `"Tue"`
#     - `"Wednesday"`, `"Wed"`
#     - `"Thursday"`, `"Thu"`
#     - `"Friday"`, `"Fri"`
#     - `"Saturday"`, `"Sat"`
#     - `"Sunday"`, `"Sun"`
#   - The `(?:day)?` part ensures that both full and short forms match.
# 
# - Capturing Group `(?P<sep>...)`  
#   - Detects an optional separator (`", "` or `" "`) after the weekday:
#     - Matches a comma followed by a space (`, `)
#     - Matches a single space
#     - Useful for cases like: `"Monday, January 1st"` or `"Tue 14:30"`
# 
# ### Use Case:
# - Used in date format detection to identify weekdays within datetime strings.
# - Works alongside DateFormatFinder to help parse natural language dates.
_WEEKDAY_DETECTION_RE = re.compile(
    r'^(?P<weekday>('
        r'Mon(?:day)?|'      # Matches "Mon" or "Monday"
        r'Tue(?:sday)?|'     # Matches "Tue" or "Tuesday"
        r'Wed(?:nesday)?|'   # Matches "Wed" or "Wednesday"
        r'Thu(?:rsday)?|'    # Matches "Thu" or "Thursday"
        r'Fri(?:day)?|'      # Matches "Fri" or "Friday"
        r'Sat(?:urday)?|'    # Matches "Sat" or "Saturday"
        r'Sun(?:day)?'       # Matches "Sun" or "Sunday"
    r'))'
    r'(?P<sep>(?:,\s+|\s+))?',   # Capture optional separator (comma+space or single space)
    re.IGNORECASE
)

#────────────────────────────────────────────────────────────────────────────
# REGEX FOR STRICT TIME FORMAT DETECTION
#────────────────────────────────────────────────────────────────────────────
# This regex is used to detect standalone time strings without additional date components.
# It ensures that the input string represents only a time, making it useful
# for validating extracted time values before further processing.
#
# What It Matches:
# Basic time formats:
#    - `HH:MM`
#    - `HH:MM:SS`
#    - Compact format: `HHMMSS`
#
# Fractional seconds (optional):
#    - `14:30:45.123456` (up to 6 digits)
#
# AM/PM marker (optional, for 12-hour time formats):
#    - `3:45 PM`
#
# Timezone offsets (optional):
#    - `UTC`, `Z`, `+02:00`, `-0500`, `EST`
#
# Enforcement Rules:
# - The regex requires the entire string to match (`^...$`).
# - Ensures no additional characters before or after.
# - Designed to work in case-insensitive mode (`re.IGNORECASE`).
_STRICT_TIME_RE = re.compile(
    r'^(?:'
        r'(?:\d{1,2}:\d{2}(?::\d{2})?|\d{6})' 							# Matches HH:MM, HH:MM:SS, or compact HHMMSS format.
        r'(?:\.\d{1,6})?'                     							# Optionally matches fractional seconds (e.g., .123456).
        r'(?:\s*[AP]M)?'                      							# Optionally matches AM/PM marker (e.g., '3:45 PM').
    r')'
    r'(?:\s*(?:[+-]\d{2}:?\d{2}|[+-]\d{4}|[A-Z]{3,4}|Z))?'  # Optionally matches timezone info (UTC, +HH:MM, Z).
    r'$', 																									# Ensures the entire string must match (no extra characters before/after).
    re.IGNORECASE
)

#────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTION FOR DATEFORMATFINDER: DETECT TIME COMPONENTS IN STRINGS
#────────────────────────────────────────────────────────────────────────────

# This function is used by the `DateFormatFinder` class, which is the primary 
# logic in this module. It checks if a given string contains **time components** 
# while filtering out ISO 8601 formats (handled separately by `iso8601strptime`).
#
# Purpose:
# - Detects time components (HH:MM, HH:MM:SS, etc.) in mixed datetime strings.
# - Works with `_TIME_DETECTION_RE` to extract **non-ISO** time formats.
# - Helps `DateFormatFinder` determine whether a string includes a time component.
#
# Exclusion Rule:
# - If the string is a **valid ISO 8601 datetime**, this function **returns False** 
#   because ISO formats are handled by separate logic.
def _get_time_components(datetime_string):
    """
    Determines if the input string contains time components, excluding valid 
    ISO 8601 datetime formats.

    ### Logic:
    - Step 1: Cleans input by stripping unnecessary spaces.
    - Step 2: Checks if the string is a valid ISO 8601 datetime.  
      - If yes → Returns `False` (ISO formats are handled elsewhere).
    - Step 3: Searches for time components using:
      - `_STRICT_TIME_RE`: Detects standalone times.
      - `_TIME_DETECTION_RE`: Extracts time components from mixed datetime strings.
    - Step 4: Returns `True` if a non-ISO time component is found.
    """
    cleaned = " ".join(datetime_string.split())
    # Add extra measure to “shield” the regex from matching the time portion of an ISO 8601 string
    # because`iso8601strptime` handles iso formats.
    if validate_iso8601(cleaned, split=False):
        return False
    time_match = _STRICT_TIME_RE.search(cleaned)
    datetime_match = _TIME_DETECTION_RE.search(cleaned)
    if time_match:
        return False
    return datetime_match is not None










 
# =================================
# BASIC ISO FORMAT
# =================================
def _basic_iso8601(
    candidate: str,
    split: bool = False,
    # keep_t: bool = False
    ):
    """
    Validates or splits a **basic ISO 8601** date-time string.

    This function serves **two purposes**:
    1. **Validation Mode** (default): If `split=False`, the function returns:
        - `True` if the string is valid according to basic ISO 8601 rules.
        - `False` if the string is invalid.

    2. **Split Mode**: If `split=True`, the function attempts to split the string into:
        - `[date_part, time_part]` if valid.
        - `[date_part, "T", time_part]` if valid and `keep_t=True`.
        - `None` if invalid.

    Supported Format: Basic ISO 8601 date-time
    - Date portion: Exactly 8 digits in `YYYYMMDD` format.
    - Time portion: Compact time without separators, up to 20 characters:
        - Required hour (00-23)
        - Optional minutes (00-59)
        - Optional seconds (00-59)
        - Optional fractional seconds after `.` or `,` (up to 7 digits)
        - Optional timezone (`Z` for UTC or `+hhmm`/`-hhmm` for offsets)

    Restrictions:
    - No `-` or `:` within the date or time.
    - Exactly **one** capital `T` separating date and time.
    - No extra text before or after the date-time.
    - No spaces, lowercase letters, or unexpected symbols.
    """
    # Step 1: Global character check - only allowed characters permitted
    allowed_chars = set("0123456789TZ+-.,")
    for ch in candidate:
        if ch not in allowed_chars:
            return None if split else False

    # Step 2: Identify all 'T' positions that are nestled between digits
    valid_T_positions = []
    for i in range(1, len(candidate) - 1):
        if candidate[i] == 'T' and candidate[i - 1].isdigit() and candidate[i + 1].isdigit():
            valid_T_positions.append(i)

    # If no valid 'T' found, it's invalid
    if not valid_T_positions:
        return None if split else False

    # Step 3: Evaluate each candidate 'T' - attempt to split and validate
    for tpos in valid_T_positions:
        left_side = candidate[:tpos]     # Everything before 'T' (date portion)
        right_side = candidate[tpos + 1:] # Everything after 'T' (time portion)

        # Date portion must be exactly 8 digits (YYYYMMDD)
        if len(left_side) != 8 or not left_side.isdigit():
            continue  # Try the next 'T' if this doesn't work

        # Time portion must not exceed 20 characters
        if len(right_side) > 20:
            continue

        # Validate the time portion using helper function
        if __is_valid_basic_time(right_side):
            if split:
                # Split mode - return parts of the string if valid
                return [left_side, "T", right_side]
            else:
                # Validation mode - just return True if valid
                return True

    # If none of the 'T' splits worked, it's invalid
    return None if split else False


def __is_valid_basic_time(time_str: str) -> bool:
    """
    Validates the time portion after 'T' in basic ISO8601 format.
    """
    i = 0
    n = len(time_str)

    # We need at least 2 digits for hour
    if n < 2:
        return False

    # Parse hour (first 2 digits => 00–23)
    hour_str = time_str[0:2]
    if not hour_str.isdigit():
        return False
    hour_val = int(hour_str)
    if not (0 <= hour_val <= 23):
        return False
    i = 2  # consumed 2 digits (hour)

    # Case: Exactly 2 digits, this is 'T14' — allowed
    if i == n:
        return True

    # Special case: Directly after hour, allow 'Z', '+', '-'
    next_char = time_str[i]
    if next_char in ('Z', '+', '-'):
        return __validate_time_zone_basic(time_str[i:])

    # Otherwise, we expect 2 more digits for minutes (00–59)
    if n - i < 2 or not time_str[i:i+2].isdigit():
        return False
    minute_val = int(time_str[i:i+2])
    if not (0 <= minute_val <= 59):
        return False
    i += 2  # consumed minutes

    # If we used up all characters, we are done (T1430)
    if i == n:
        return True

    # Check for next character (seconds or timezone or fraction)
    next_char = time_str[i]

    if next_char in ('Z', '+', '-'):
        return __validate_time_zone_basic(time_str[i:])

    # Otherwise, expect 2 digits for seconds (00–59)
    if n - i < 2 or not time_str[i:i+2].isdigit():
        return False
    second_val = int(time_str[i:i+2])
    if not (0 <= second_val <= 59):
        return False
    i += 2  # consumed seconds

    # If done, success
    if i == n:
        return True

    # Next, we could have fractional seconds, timezone, or 'Z'
    next_char = time_str[i]
    if next_char in ('Z', '+', '-'):
        return __validate_time_zone_basic(time_str[i:])

    if next_char not in ('.', ','):
        return False  # invalid char after seconds

    # Fractional second parsing (after . or ,)
    i += 1  # consume '.' or ','
    frac_start = i
    while i < n and time_str[i].isdigit():
        i += 1
    frac_len = i - frac_start
    if frac_len == 0 or frac_len > 7:
        return False  # must have 1-7 digits after . or ,

    # If done, success
    if i == n:
        return True

    # After fractional seconds, only Z, +, or - is valid
    next_char = time_str[i]
    if next_char in ('Z', '+', '-'):
        return __validate_time_zone_basic(time_str[i:])

    return False  # anything else is invalid

def __validate_time_zone_basic(tz_str: str) -> bool:
    """
    Validates a timezone portion (starting with Z, +, or -).
    """
    if tz_str == "Z":
        return True  # Just Z is fine

    if tz_str[0] not in ('+', '-'):
        return False

    tz_str = tz_str[1:]  # drop the +/-
    if len(tz_str) not in (2, 4):
        return False

    if not tz_str.isdigit():
        return False

    offset_hour = int(tz_str[:2])
    if not (0 <= offset_hour <= 23):
        return False

    if len(tz_str) == 4:
        offset_minute = int(tz_str[2:])
        if not (0 <= offset_minute <= 59):
            return False
    return True


# =================================
# EXTENDED ISO FORMAT
# =================================
def _extended_iso8601(
    candidate: str,
    split: bool = False,
    # keep_t: bool = False
    ):
    """
    Validates or splits an **extended ISO 8601** date-time string.

    This function serves two purposes:
    1. **Validation Mode** (default): If `split=False`, the function returns:
        - `True` if the string conforms to extended ISO 8601 rules.
        - `False` if the string is invalid.

    2. **Split Mode**: If `split=True`, the function attempts to split the string into:
        - `[date_part, time_part]` if valid.
        - `[date_part, 'T', time_part]` if valid and `keep_t=True`.
        - `None` if invalid.

    Supported Format: Extended ISO 8601 date-time
    - Date portion: Exactly 10 characters in `YYYY-MM-DD` format.
    - Time portion: Extended time format with separators (`:` and optional `.`/`,` for fractions):
        - Required hour (00-23)
        - Optional minutes (00-59)
        - Optional seconds (00-59)
        - Optional fractional seconds (after `.` or `,`, up to 7 digits)
        - Optional timezone (`Z` for UTC or `±hh[:mm]` for offsets)

    Restrictions:
    - Date must use **dashes** (`-`) between year, month, day.
    - Time must use **colons** (`:`) between hours, minutes, and seconds.
    - Exactly one capital `T` must separate date and time.
    - No spaces, lowercase letters, or unexpected symbols.
    - No mixing of **basic** and **extended** formats.

    Parameters:
        candidate (str): The date-time string to check.
        split (bool): If True, return a split version instead of True/False.
        keep_t (bool): If True and `split=True`, include "T" as its own element.

    Returns:
        bool | list | None:
        - In validation mode (`split=False`): Returns `True` or `False`.
        - In split mode (`split=True`): Returns a list (split parts) if valid, or `None` if invalid.
    """
    # Step 1: Global character check - only allowed characters for extended format
    allowed_chars = set("0123456789T-:Z+-,.")
    for ch in candidate:
        if ch not in allowed_chars:
            return None if split else False

    # Step 2: Identify all 'T' positions - must separate date and time
    # Extended format uses 'T' to split "YYYY-MM-DD" from "hh:mm:ss"
    valid_T_positions = []
    for i in range(1, len(candidate) - 1):
        if candidate[i] == 'T':
            valid_T_positions.append(i)

    # Must have at least one valid 'T' or the string is invalid
    if not valid_T_positions:
        return None if split else False

    # Step 3: Check all 'T' positions to find a valid date-time split
    for tpos in valid_T_positions:
        left_side = candidate[:tpos]      # Portion before 'T' (date)
        right_side = candidate[tpos + 1:] # Portion after 'T' (time)

        # Date portion must match YYYY-MM-DD (exactly 10 characters)
        if len(left_side) != 10 or not __is_valid_extended_date(left_side):
            continue  # Try next 'T' if this doesn't work

        # Time portion must follow extended time rules
        if __is_valid_extended_time(right_side):
            if split:
                # Split mode - return parts if valid
                return [left_side, "T", right_side]
            else:
                # Validation mode - just return True if valid
                return True

    # If no valid date-time split was found, return None or False
    return None if split else False


def __is_valid_extended_date(date_str: str) -> bool:
    """
    Checks if `date_str` is exactly 'YYYY-MM-DD':
      - Positions [0..3]: digits => year
      - Position 4: '-'
      - Positions [5..6]: digits => month
      - Position 7: '-'
      - Positions [8..9]: digits => day

    This does NOT check real calendar validity (e.g., 2025-13-40),
    only that it's the correct format and that Y/M/D are digits.
    """
    if len(date_str) != 10:
        return False

    if date_str[4] != '-' or date_str[7] != '-':
        return False

    # YYYY => digits
    year_part = date_str[0:4]
    if not year_part.isdigit():
        return False

    # MM => digits
    month_part = date_str[5:7]
    if not month_part.isdigit():
        return False

    # DD => digits
    day_part = date_str[8:10]
    if not day_part.isdigit():
        return False

    # If we wanted to check actual month/day ranges, we'd do it here,
    # but for now, I assume any "##-##" is okay.
    return True

def __is_valid_extended_time(time_str: str) -> bool:
    """
    Validates extended time format, which can be:
      hh[:mm[:ss[.frac]]] [Z or ±hh[:mm]] ?

    Steps:
      1) hour => 2 digits, (00..23)
      2) optional ":mm" => (00..59)
      3) optional ":ss" => (00..59)
      4) optional fractional => '.' or ',' followed by 1..7 digits
      5) optional timezone => 'Z' or (+|-)hh(:mm)

    Examples of valid times:
      "14"                -> hour only (unusual in extended, but let's allow "14" if no colon).
      "14:00"             -> hour, minute
      "14:30:59"          -> hour, minute, second
      "14:30:59.123"      -> fractional seconds
      "14:30:59,123Z"     -> fractional with comma + Z
      "14:30Z"            -> hour, minute + Z
      "14Z"               -> hour only + Z
      "14:30:59+05:00"    -> with offset
      "14:30-03"          -> offset = -03 (no minutes)
    """
    i = 0
    n = len(time_str)

    # 1) Parse hour (2 digits => 00..23).
    #    But watch out: in extended format, we typically expect 'hh:' if more is coming.
    if not __parse_two_digits_in_range_extended(time_str, i, 0, 23):
        return False
    hour_val = int(time_str[i:i+2])
    i += 2

    # If we're done => e.g. "14" with no minutes => let's accept that as minimal extended time
    if i == n:
        return True

    # If next char is a colon => parse minutes
    if time_str[i] == ':':
        i += 1
        # Must have at least 2 digits for minutes
        if not __parse_two_digits_in_range_extended(time_str, i, 0, 59):
            return False
        minute_val = int(time_str[i:i+2])
        i += 2

        if i == n:
            return True

        # If next char is a colon => parse seconds
        if i < n and time_str[i] == ':':
            i += 1
            if not __parse_two_digits_in_range_extended(time_str, i, 0, 59):
                return False
            second_val = int(time_str[i:i+2])
            i += 2

            if i == n:
                return True

            # If there's a fractional part => parse it
            if i < n and time_str[i] in ('.', ','):
                i = __parse_fractional_seconds_extended(time_str, i)
                if i < 0:
                    return False
                if i == n:
                    return True

                # If more remains, it must be timezone
                return __parse_time_zone_if_any_extended(time_str, i)

            # No fraction => next must be timezone or done
            return __parse_time_zone_if_any_extended(time_str, i)

        # We have minutes only => next might be fraction or timezone
        if i < n and time_str[i] in ('.', ','):
            i = __parse_fractional_seconds_extended(time_str, i)
            if i < 0:
                return False
            if i == n:
                return True
            return __parse_time_zone_if_any_extended(time_str, i)

        return __parse_time_zone_if_any_extended(time_str, i)

    # If next char isn't ':', it might be fractional or timezone or 'Z' or offset
    if time_str[i] in ('.', ','):
        # Means: "14.123Z" (no minutes). It's unusual in fully extended format,
        # but let's allow it since the standard doesn't forbid "hh.frac" by itself.
        i = __parse_fractional_seconds_extended(time_str, i)
        if i < 0:
            return False
        if i == n:
            return True
        return __parse_time_zone_if_any_extended(time_str, i)

    # If it's not a colon nor fraction, we check timezone
    return __parse_time_zone_if_any_extended(time_str, i)

def __parse_two_digits_in_range_extended(s: str, idx: int, low: int, high: int) -> bool:
    """
    Checks if s[idx:idx+2] is two digits and within [low..high].
    Returns True/False. Does NOT advance an index; just a direct check.
    """
    if idx + 2 > len(s):
        return False
    part = s[idx:idx+2]
    if not part.isdigit():
        return False
    val = int(part)
    return low <= val <= high

def __parse_fractional_seconds_extended(s: str, idx: int) -> int:
    """
    s[idx] should be '.' or ','
    Then parse 1..7 digits as fractional seconds.
    Returns the new index if valid, or -1 if invalid.
    """
    if idx >= len(s) or s[idx] not in ('.', ','):
        return -1
    idx += 1  # consume '.' or ','
    start_frac = idx
    while idx < len(s) and s[idx].isdigit():
        idx += 1
    frac_len = idx - start_frac
    if frac_len == 0 or frac_len > 7:
        return -1
    return idx

def __parse_time_zone_if_any_extended(s: str, idx: int) -> bool:
    """
    If there's nothing left, that's valid (no timezone).
    If there's leftover, it must be a valid timezone => 'Z' or ±hh(:mm).
    """
    if idx == len(s):
        return True  # no timezone, that's fine

    return __validate_time_zone_extended(s[idx:])

def __validate_time_zone_extended(tz_str: str) -> bool:
    """
    Extended format timezone can be:
      'Z'               -> UTC
      +hh(:mm) or -hh(:mm)
        - hours => 00..23
        - optional :mm => 00..59

    Examples:
      "Z"
      "+05"
      "-05:00"
      "+00:59"
    """
    if tz_str == "Z":
        return True

    if not tz_str:
        return False

    sign = tz_str[0]
    if sign not in ('+', '-'):
        return False

    body = tz_str[1:]  # what's after the sign
    if not body:
        return False

    # We expect at least "hh"
    # Could be "05" or "05:30"
    # 1) parse 2 digits for hours
    if len(body) < 2:
        return False
    if not body[:2].isdigit():
        return False
    offset_hour = int(body[:2])
    if not (0 <= offset_hour <= 23):
        return False

    # If exactly 2 digits => done
    if len(body) == 2:
        return True

    # If there's more, it should start with ':'
    if body[2] != ':':
        return False

    # parse minutes
    minute_part = body[3:]
    if len(minute_part) != 2 or not minute_part.isdigit():
        return False
    offset_min = int(minute_part)
    if not (0 <= offset_min <= 59):
        return False
    return True


# =================================
# MAIN ISO FUNCTION
# =================================
def validate_iso8601(iso_string, split=True):
    """
    Validates and optionally splits an ISO 8601 string in extended format.

    This function attempts to validate the input string against one of the following formats:
      - YYYY-MM-DDTHH:MM:SS
      - YYYY-MM-DDTHH:MM:SS.ssssss
      - YYYY-MM-DDTHH:MM:SS+HH:MM
      - YYYY-MM-DDTHH:MM:SS-HH:MM

    It first normalizes whitespace in the input, then uses a regex to ensure the string is in one of
    the supported extended formats. If the regex matches, it further validates the string by attempting
    to create a datetime object using dt.fromisoformat().

    Parameters:
        iso_string (str): The ISO 8601 date-time string to validate.
        split (bool): If True, returns the split components instead of a Boolean.
        keepT (bool): If True and split is True, includes "T" as its own element in the returned list.

    Returns:
        bool or list:
          - If split is False: returns True if valid, False if invalid.
          - If split is True: returns a list of the components if valid, or None/False if invalid.
    """
    # Normalize whitespace in the input
    iso_string = " ".join(iso_string.split())

    # Regex to match supported extended ISO 8601 formats:
    fromiso_regex = re.compile(
        r"^(?P<date>\d{4}-\d{2}-\d{2})T"
        r"(?P<time>\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?)"
        r"(?P<tz>[+-]\d{2}:\d{2})?$"
    )
    match = fromiso_regex.match(iso_string)
    if match:
        try:
            # Attempt to convert the string to a datetime object.
            dt.fromisoformat(iso_string)
            valid = True
        except ValueError:
            valid = False

        if valid:
            if split:
                parts = iso_string.split("T", 1) # Split the string into date and time parts on the first 'T'.
                return [parts[0], "T", parts[1]] # Return three components: [date, "T", time]
            else:
                return True
        else:
            return False
    else:
        result = _basic_iso8601(candidate=iso_string, split=split) # If the regex does not match, fallback to other methods.
        if not result:
            return _extended_iso8601(candidate=iso_string, split=split)
        return result







#────────────────────────────────────────────────────────────────────────────
# ISO 8601 FORMAT DETECTION & PARSING (USED IN DateFormatFinder)
#────────────────────────────────────────────────────────────────────────────
# This function is a key component of the `DateFormatFinder` class.
#
# Why It's Important:
# - First-step check for ISO 8601 formats. If detected, we can skip expensive heuristics.
# - ISO 8601 is common in machine-generated timestamps (e.g., logs, APIs, databases).
# - Regex-based matching is significantly faster than attempting to infer a format.
#
# How It Works:
# - If the string matches a known ISO 8601 format, we immediately return the format.
# - The result is cached for efficiency, avoiding redundant analysis.
# - If no match is found, we proceed to heuristic-based format detection.
def iso8601strptime(iso_string, return_patched=False):
    """
    Given an ISO 8601 date-time string with 'T' as the separator (e.g. '2025-03-05T14:30:00+05:30'),
    returns a 2-tuple: (patched_iso_string, strptime_format)

    The returned strptime_format can be used with:
        df.strptime(patched_iso_string, strptime_format)

    Notes / Limitations:
      1) Offsets (like '+05:30') are handled as literal text in the format string.
         The resulting datetime is naive (ignores the offset).
      2) Fractional seconds are forced to 6 digits (padding or truncating).
      3) We only handle these date forms for the left side:
           - 'YYYY-MM-DD' (extended date)
           - 'YYYYMMDD'   (basic date)
      4) We only handle these time forms for the right side:
           - basic: HH, HHMM, HHMMSS (optional fraction)
           - extended: HH[:MM[:SS]] (optional fraction)
      5) Timezone offset can be:
           - Z
           - +HH, +HHMM, +HH:MM
           - -HH, -HHMM, -HH:MM
    """
    #--------------------------------------------------------------------
    # 1) Split the string at 'T' => [date_part, time_part_with_offset]
    #--------------------------------------------------------------------
    # We'll find the T that has digits on both sides (like the validate_iso8601 approach).
    match_t = re.search(r"(?<=\d)T(?=\d)", iso_string)
    if not match_t:
        raise ValueError("String does not contain a valid 'T' between digits.")

    date_part = iso_string[: match_t.start()]
    time_part_and_offset = iso_string[match_t.end() :]

    #--------------------------------------------------------------------
    # 2) Detect if date_part is basic or extended
    #    - extended => 'YYYY-MM-DD' (10 chars with 2 dashes at positions 4 and 7)
    #    - basic => 'YYYYMMDD' (8 digits, no dashes)
    #--------------------------------------------------------------------
    date_format = None
    patched_iso = iso_string  # we'll build a "patched" version as needed

    if len(date_part) == 10 and date_part[4] == "-" and date_part[7] == "-":
        # extended date => '%Y-%m-%d'
        date_format = "%Y-%m-%d"
    elif len(date_part) == 8 and date_part.isdigit():
        # basic date => '%Y%m%d'
        date_format = "%Y%m%d"
    else:
        raise ValueError(f"Unrecognized date format in '{date_part}'.")

    # We'll build the final format in pieces
    final_format = date_format + "T"

    #--------------------------------------------------------------------
    # 3) Split the offset from the pure time
    #    Possible offsets: Z, +HH, +HHMM, +HH:MM, -HH, -HHMM, -HH:MM
    #--------------------------------------------------------------------
    offset_pattern = re.compile(r"(Z|[+\-]\d{2}(:?\d{2})?)$")
    offset_str = ""
    pure_time = time_part_and_offset

    off_match = offset_pattern.search(time_part_and_offset)
    if off_match:
        offset_str = off_match.group(1)  # e.g. '+05:30', '-0530', 'Z'
        pure_time = time_part_and_offset[: off_match.start()]

    #--------------------------------------------------------------------
    # 4) Detect fraction in the time portion
    #    e.g. '14:30:00.123' or '143000,1234567'
    #--------------------------------------------------------------------
    frac_match = re.search(r"[.,](\d+)$", pure_time)
    fraction_digits = 0
    if frac_match:
        fraction_digits = len(frac_match.group(1))

    # We'll store a patched version of pure_time that has exactly 6 digits if there's fraction
    patched_pure_time = pure_time

    #--------------------------------------------------------------------
    # 5) Identify if time is basic or extended
    #    - extended => up to 2 colons => e.g. 'HH:MM', 'HH:MM:SS'
    #    - basic => no colons => 'HH', 'HHMM', 'HHMMSS'
    #--------------------------------------------------------------------
    colon_count = pure_time.count(":")

    # We'll figure out a base_time_format
    # Cases:
    #   extended, 2 colons => '%H:%M:%S'
    #   extended, 1 colon => '%H:%M'
    #   extended, 0 colons => not extended => basic
    #   basic => e.g. 'HH' (2 digits), 'HHMM' (4 digits), 'HHMMSS' (6 digits)
    base_time_format = None

    # A helper that gives the length ignoring fraction
    # e.g. '14:30:00.123' -> ignoring fraction => '14:30:00' => length=8
    # but let's do it more simply: remove fraction portion:
    if fraction_digits > 0:
        # remove the fraction part from pure_time
        frac_sep_pos = re.search(r"[.,]", pure_time).start()
        core_time = pure_time[:frac_sep_pos]
    else:
        core_time = pure_time

    if colon_count >= 1:
        # extended
        if colon_count == 2:
            base_time_format = "%H:%M:%S"
        elif colon_count == 1:
            base_time_format = "%H:%M"
        else:
            # theoretically colon_count could be >2 if invalid
            raise ValueError(f"Invalid extended time format: '{pure_time}'")
    else:
        # basic => no colons
        length_core = len(core_time)
        if length_core == 2:
            base_time_format = "%H"
        elif length_core == 4:
            base_time_format = "%H%M"
        elif length_core == 6:
            base_time_format = "%H%M%S"
        else:
            # unknown
            raise ValueError(f"Cannot determine basic time format for '{core_time}'")

    #--------------------------------------------------------------------
    # 6) If fraction is present => add ".%f" to the format
    #    But we must also patch the iso_string to have exactly 6 fraction digits
    #--------------------------------------------------------------------
    
    # Snippet: "Shoe-horn" approach if fraction > 6 digits
    if fraction_digits > 0:
        frac_format = ".%f"
        patched_pure_time = patched_pure_time.replace(",", ".")

        dot_pos = patched_pure_time.rfind(".")
        actual_frac_len = len(patched_pure_time) - (dot_pos + 1)

        if actual_frac_len < 6:
            # Pad with zeros
            needed = 6 - actual_frac_len
            patched_pure_time += "0" * needed
        elif actual_frac_len > 6:
            # "Shoe-horn" leftover digits in the format
            leftover_count = actual_frac_len - 6
            # leftover_str => the extra digit(s) beyond 6
            leftover_str = patched_pure_time[-leftover_count:]  # e.g. '7', '78', etc.
            # Remove them from the main string so that only 6 digits remain in the fraction
            patched_pure_time = patched_pure_time[:-leftover_count]

            # Example: If we had .1234567 => .%f7
            # If we had .12345678 => .%f78
            frac_format = f".%f{leftover_str}"
    else:
        frac_format = ""

    time_format = base_time_format + frac_format
    final_format += time_format

    #--------------------------------------------------------------------
    # 7) If offset_str is non-empty, we handle it as literal text
    #    e.g. +05:30 => add '+05:30' to the format
    #    e.g. 'Z' => add 'Z' to the format
    #
    # NOTE: This means strptime won't parse offset logically
    #       It just matches it as literal text
    #--------------------------------------------------------------------
    if offset_str:
        # If offset is something like '+05', '+05:30', we cannot do '+%H:%M',
        # because we'd get "redefinition of group name 'H'."
        # So we must add it as literal text in the format string.
        final_format += offset_str  # e.g. '+05:30'
        # We'll also ensure the patched time has the same offset text
        # i.e. time_part_and_offset -> (pure_time + offset_str)
        # so let's build the final patched time portion
        patched_time_part = patched_pure_time + offset_str
    else:
        patched_time_part = patched_pure_time

    #--------------------------------------------------------------------
    # 8) Build the patched iso_string => date_part + "T" + patched_time_part
    #--------------------------------------------------------------------
    patched_iso_string = date_part + "T" + patched_time_part
    result = (patched_iso_string, final_format) if return_patched else final_format  

    # Test Format before returning
    try:
        _test_format = dt.strptime(iso_string, final_format)        
        if _test_format:
            return result
    except:
        pass 





#────────────────────────────────────────────────────────────────────────────
# PREDEFINED DATE & TIME FORMATS FOR DETECTION
#────────────────────────────────────────────────────────────────────────────
# This class provides a collection of commonly used date and time formats 
# for use in DateFormatFinder. The formats are structured into:
#
# Dates - Standard date formats (YYYY-MM-DD, MM/DD/YY, etc.).
# Times - Various time formats (HH:MM, HH:MM:SS, 12-hour with AM/PM, etc.).
# Unique - Special formats, including ordinal dates and phrases.
# Precomputed - Formats expanded with alternative separators for flexibility.
#
# The `DateFormatFinder` class relies on these formats to detect and standardize
# various date-time representations efficiently.
class DateFormatLibrary:
    """
    A predefined collection of **date and time formats** used by `DateFormatFinder`
    to parse and detect various date-time representations.

    ### **Key Features:**
    - Organizes date-time formats into:
      - `dates`: Standard date formats.
      - `times`: Common time formats.
      - `unique`: Special formats (e.g., ordinal dates).
      - `precomputed`: Expanded versions with different separators (`/`, `.`, `-`, etc.).
    - Used by **DateFormatFinder** to efficiently **match input strings** to valid formats.
    - Supports **multiple locales and variations** of date and time notation.

    ---
    
    ### **Usage in `DateFormatFinder`**
    - `DateFormatFinder` calls `self.formats.Dates()` to retrieve standard date formats.
    - During detection, `DateFormatFinder` iterates through `self.formats.Precomputed()`
      to check for multiple format variations.
    - Used to **match** and **parse** date-time strings more effectively.
    """	
    def __init__(self):
        """Initializes predefined date, time, and special formats for `DateFormatFinder`."""
        #--------------------------------------------------------------------
        # Common Date Formats
        # - Includes both numeric and named month formats.
        # - Supports multiple region-specific layouts (US, EU, ISO).
        #--------------------------------------------------------------------
        self.dates = [
            '%m/%d/%y', '%B/%d/%Y', '%Y/%B/%d', '%y%m%d', '%m/%d/%Y', '%d/%m/%Y', '%y/%m/%d', '%d/%B/%Y',
            '%Y/%b/%d', '%b/%d/%Y', '%Y/%m/%d', '%Y%m%d', '%d/%m/%y', '%d/%b/%Y', '%a, %b %d, %Y',
            '%A, %B %d, %Y', '%d/%B/%y', '%B %d, %y', '%d %B %y',
        ]
        
        #--------------------------------------------------------------------
        # Common Time Formats
        # - Includes 24-hour and 12-hour (AM/PM) formats.
        # - Supports timezone-aware formats (`%z`, `%Z`).
        #--------------------------------------------------------------------
        self.times = [
            '%H', '%I', '%H:%M', '%H:%M:%S', '%H:%M:%S:%f', '%H:%M %p', '%H:%M:%S %p', '%H:%M:%S:%f %p', '%I:%M', '%I:%M %p', '%I:%M:%S', '%I:%M:%S %p',
            '%I:%M:%S:%f', '%I:%M:%S:%f %p', '%H:%M:%S %z', '%H:%M:%S %Z', '%I:%M %p %z', '%I:%M %p %Z', '%H:%M:%S:%f %z', '%H:%M:%S:%f %Z', '%I:%M:%S %p %z', '%I:%M:%S %p %Z', '%H %p', '%I %p',
            '%H:%M:%S:%f %p %z', '%H:%M:%S:%f %p %Z', '%I:%M:%S:%f %p %z', '%I:%M:%S:%f %p %Z', '%H%M%S', '%H:%M:%S%z', '%H:%M:%SZ', '%H:%M:%S.%f', '%H:%M:%S.%f%z', '%H:%M:%S', '%z', '%Z',            
        ]

        #--------------------------------------------------------------------
        # Unique Date Formats
        # - Covers ordinal dates, weekdays, abbreviated forms.
        # - Useful for natural language date parsing.
        #--------------------------------------------------------------------
        self.unique = [
            '%A the %dth of %B, %Y', '%A', '%a', '%A, %d %B %Y', '%Y, %b %d', '%B %d', '%B %d, %Y', '%b %d, %Y', '%b', '%B', '%B, %Y', '%b. %d, %Y',
            '%d %B', '%d %B, %Y', '%d of %B, %Y', '%d-%b-%y', '%d', '%dth %B %Y', '%dth of %B %Y', '%dth of %B, %Y', '%H', '%I', '%m-%Y-%d', '%m-%Y',
            '%m', '%M', '%m/%Y', '%m/%Y/%d', '%Y %B', '%Y Q%q', '%Y-%j', '%Y-%m', '%y', '%Y', '%Y, %B %d', '%Y.%m', '%Y/%m', '%Y-W%U-%w', '%Y-W%V-%u', '%a, %d %b %Y', '%b %d %y',
            '%b-%d-%y', '%b-%Y-%d', '%b.%Y-%d', '%d %b, %Y', '%d %B, %y', '%d-%Y.%m', '%d-%Y/%m', '%d.%Y-%m', '%d/%Y-%m', '%d/%Y.%m', '%m.%Y-%d', '%m.%Y/%d', '%m/%Y-%d', 'on %B %d, %Y',
            '%B %dth, %Y', '%d-%b-%Y %Z',
        ]
        
        #--------------------------------------------------------------------
        # 4 Precomputed Formats with Alternative Separators
        #--------------------------------------------------------------------        
        self.all_formats = self.dates + self.times + self.unique
        self.precomputed = self._precompute_with_separators()

    def _precompute_with_separators(self):
        """Generates format variations using different separators (`/`, `.`, `-`, ` `, `""`)."""    	
        separators = ['/', '.', '-', ' ', '']
        result = set(self.all_formats)
        for fmt in self.all_formats:
            for sep in separators:
                result.add(fmt.replace('/', sep))
        return list(result)

    def Dates(self):
        return self.dates

    def Times(self):
        return self.times

    def Unique(self):
        return self.unique

    def All(self):
        return self.all_formats

    def Precomputed(self):
        return self.precomputed





##━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## MAIN: DATE FORMAT FINDER CLASS
##━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 
## Purpose:
##   The `DateFormatFinder` class is designed to intelligently detect and 
##   construct `strptime`-compatible format strings for a wide range of 
##   date-time inputs.
## 
## Core Features:
##   ISO 8601 Detection:							Quickly identifies machine-generated timestamps.  
##   Time Component Recognition:			Separates and detects time values.  
##   Timezone Handling: 							Supports named and offset-based time zones (`UTC`, `EST`, `+05:30`).  
##   Ordinal Suffix Removal:					Cleans formats like `"5th"` → `"5"`.  
##   Weekday Preservation:						Recognizes and maintains weekdays (`Monday, Jan 1, 2023`).  
##   Caching for Performance: 				Previously successful formats are stored to optimize future lookups.  
## 
## How It Works:
##   1 -->  Cleans and normalizes input.  
##   2 -->  Checks for ISO 8601 format first (fastest detection method).  
##   3 -->  ️Identifies and removes timezones for separate parsing.  
##   4 -->  ️Matches against known format patterns using regex and heuristics.  
##   5 -->  ️Caches successful detections to improve performance.  
## 
##━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class DateFormatFinder:
    """
    A powerful class for detecting and reconstructing date-time format strings.

    This class attempts to infer the correct `strptime`-compatible format string
    for a given date-time input. It intelligently handles:
    """	
    successful_formats = {} 
    historical_formats = set() 

    def __init__(self, old_sep='/'):
        self.formats = DateFormatLibrary()
        self.old_sep = old_sep
        self.day_suffix = None        

    #──── GENERATING FORMAT VARIANTS ────────────────────────────────────────────────────────────────────────────────
    def _format_candidates(self, fmt):
        """
        Given a format string, generate a list of candidate formats
        by substituting certain specifiers with their alternatives.
        """
        alternate_map = {
            '%z': '%Z', '%Z': '%z',  # Timezone specifier swaps
            '%a': '%A', '%A': '%a',  # Weekday abbreviations
            '%b': '%B', '%B': '%b',  # Month abbreviations
            '%y': '%Y', '%Y': '%y',  # Year short/long swaps
        }
        candidates = {fmt}
        for spec, alt in alternate_map.items():
            new_candidates = set()
            for candidate in candidates:
                if spec in candidate and alt not in candidate: # If candidate contains the specifier but not its alternative, create a new candidate.
                    new_candidates.add(candidate.replace(spec, alt))
            candidates |= new_candidates
        return list(candidates)
       
    #──── CLEANING DATE STRING INPUT ────────────────────────────────────────────────────────────────────────────────       
    def _remove_ordinal_suffixes(self, date_string):
        """
        Remove ordinal suffixes (st, nd, rd, th) from day numbers,
        but capture them so we can re-inject into the final format later.

        E.g. "May 14th, 2022" -> "May 14, 2022"
        Also sets self.day_suffix = 'th' if found in '14th'.
        """
        def _replacer(match):
            day_num = match.group(1)  							# e.g. '14'
            suffix = match.group(2)   							# e.g. 'th', 'rd', 'st', etc.
            self.day_suffix = suffix  							# store for later
            return day_num            							# remove the suffix from the actual string

        # Regex captures a numeric day plus one of (st|nd|rd|th).
        pattern = re.compile(r'(\d+)(st|nd|rd|th)', re.IGNORECASE)
        return pattern.sub(_replacer, date_string)       
       
    #──── FORMAT DETECTION AND SEARCH ────────────────────────────────────────────────────────────────────────────────       
    def generate_formats(self, date_str, datetime_formats):
        """
        Try to parse the date_str using each format candidate.
        For formats with a timezone specifier, try both the given format and its alternative.
        """
        for fmt in datetime_formats:
            for candidate in self._format_candidates(fmt):
                try:
                    dt.strptime(date_str, candidate)
                    return candidate
                except ValueError:
                    continue
        return None

    def try_formats(self, formats, substring, local_seen):
        """
        Iterates through given formats and attempts to match `substring`.
        Also checks precomputed formats to maximize detection accuracy.
        """    	
        for fmt in formats:
            if (fmt, substring) in local_seen:
                continue
            result = self.generate_formats(substring, [fmt])
            local_seen.add((fmt, substring))
            if result:
                return result
        for fmt in self.formats.Precomputed():
            if (fmt, substring) in local_seen:
                continue
            result = self.generate_formats(substring, [fmt])
            local_seen.add((fmt, substring))
            if result:
                return result
        return None
      
    #──── CORE DETECTION LOGIC ────────────────────────────────────────────────────────────────────────────────
    def _search_scalar(self, date_string):
        """
        The core function for parsing a single date string.
        - Cleans input
        - Checks for ISO 8601
        - Detects timezones
        - Caches results for performance
        """
        # Store the exact original input for caching
        raw_input = date_string
        
        # ───────────────────────────────────────────────────────────────
        # Special Case: Abbreviated Month Names (e.g., "Apr", "Feb", "Jun")
        # ───────────────────────────────────────────────────────────────
        # * Why This Is Needed:
        # - Very short inputs like "Apr" or "Dec" are *valid* date indicators,
        #   but they don't contain enough context (like a day or year) to match
        #   standard date formats like "%b %d" or "%Y-%m-%d".
        # - These standalone inputs often occur in real-world cases:
        #   ▪ grouping logic in reports (e.g. "by Apr")
        #   ▪ month filters in dashboards
        #   ▪ column headers in spreadsheet tables
        #
        # * Why the Normal Logic Fails:
        # - The current search logic is designed to match full date/time
        #   patterns using strptime-compatible formats.
        # - It relies on having *at least* day or year data to anchor the pattern.
        # - Inputs like "Apr" fail because there’s no format like `"%b"` by itself
        #   in the `DateFormatLibrary` formats — and even if there were, matching
        #   just a month name with strptime is fragile.
        #
        # * Design Choice:
        # - We short-circuit here for inputs of length 3 (could be month abbrevs).
        # - This avoids unnecessary format searching and provides a clean escape.
        # - We trust that if the user is passing only "Apr", they *intend* it
        #   to refer to the month — not an ambiguous term.
        #
        # * Future-Proofing:
        # - This avoids accidental matches to unrelated precomputed formats.
        # - If we want to extend support later (e.g., to numeric months like "01"),
        #   this pattern gives us a clean place to hook in that logic.
        
        ## if len(raw_input) == 3:
        if len(" ".join(raw_input.split())) == 3:        
            try:
                # Build a lowercase map of month abbreviations
                month_abbr_to_full = {
                    month[:3].lower(): month
                    for month in [
                        'January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December'
                    ]
                }
                # If the input matches a known 3-letter abbreviation, return %b
                ## full_month = month_abbr_to_full[raw_input.lower()]
                full_month = month_abbr_to_full[" ".join(raw_input.split()).lower()]                
                return '%b'  # This directly maps to abbreviated month format in strptime
            except KeyError:
                pass  # If it doesn't match, continue with the rest of the pipeline

        # Reset the suffix for each new call
        self.day_suffix = None            
        
        #--------------------------------------------------------------------
        # Step 0: Normalize the date string.
        # - Remove extra spaces (double spaces, leading/trailing, etc.)
        # - Remove ordinal suffixes like 'st', 'nd', 'rd', 'th' (e.g., '5th' → '5')
        # This ensures cleaner input for all downstream parsing.
        #--------------------------------------------------------------------    
        date_string = " ".join(date_string.split())
        date_string = self._remove_ordinal_suffixes(date_string)        

        #--------------------------------------------------------------------
        # Step 1: Fast path - check for ISO 8601 format.
        # 
        # ISO 8601 (like "2025-03-05T14:30:00") is a **well-defined standard**.
        # If we detect this upfront, we can avoid expensive heuristics later.
        # 
        # This is particularly useful because:
        # - ISO 8601 is common in machine-generated data.
        # - It's faster to match against a known regex than trying to infer.
        # 
        # If `iso8601strptime` recognizes the format, we cache it immediately
        # and return — no further analysis needed.
        # 
        # If the string doesn't match, we silently move on to regular heuristics.
        #--------------------------------------------------------------------
        try:
            _is_iso = iso8601strptime(date_string)
            if _is_iso:
                DateFormatFinder.successful_formats[raw_input] = (_is_iso, None, None)            	
                return _is_iso # Done if it's ISO.
        except:
            # We gracefully ignore exceptions here, assuming non-ISO input.        	
            pass

        #--------------------------------------------------------------------
        # Step 2: Timezone Detection.
        # 
        # If the string ends with a known timezone abbreviation (like 'UTC' or 'EST'),
        # we temporarily remove that part to simplify format detection.
        # Later, we append it back into the final format.
        #--------------------------------------------------------------------        
        tz_pattern = r'\b(' + '|'.join(re.escape(tz) for tz in tz_dict.keys()) + r')\b\s*$'
        tz_match = re.search(tz_pattern, date_string, re.IGNORECASE)
        tz_literal = None
        if tz_match:
            tz_literal = tz_match.group(1)
            # Remove that timezone portion for the main parse
            date_string = date_string[:tz_match.start()].rstrip()

        #--------------------------------------------------------------------
        # Step 3: Check Cache.
        # 
        # If we previously saw this exact date string and successfully parsed it,
        # reuse the cached format to save processing time.
        # 
        # Note: Since ISO 8601 formats are cached directly in Step 1,
        # they won't reach this point.
        #--------------------------------------------------------------------     
        if raw_input in DateFormatFinder.successful_formats:
            cached_format, cached_date, cached_time = DateFormatFinder.successful_formats[raw_input]
            # Verify that cached_format still works
            if self.generate_formats(date_string, [cached_format]):
                final_format = None
                final_format = cached_format
                
                if tz_literal:
                    # Replace or append the timezone literal if needed
                    if '%Z' in final_format:
                        final_format = final_format.replace('%Z', tz_literal)
                    elif '%z' in final_format:
                        final_format = final_format.replace('%z', tz_literal)
                    else:
                        final_format += " " + tz_literal
                        
                    if final_format:
                        final_format = " ".join(final_format.split()) 
                    
                # Reapply ordinal suffix if one was found.
                if self.day_suffix:
                    suffix_lower = self.day_suffix.lower()
                    if "%d" in final_format:
                        final_format = final_format.replace("%d", f"%d{suffix_lower}")                    
                    
                # Cache back under the **original input** (with suffixes), not the cleaned string.                    
                DateFormatFinder.successful_formats[raw_input] = (final_format, cached_date, cached_time)                         
                return final_format
               
            # If it no longer works, remove from cache and record it
            del DateFormatFinder.successful_formats[raw_input]
            DateFormatFinder.historical_formats.add(cached_format)

        #--------------------------------------------------------------------
        # Step 4: Check for Leading Weekday.
        # 
        # If the string starts with a weekday name (like 'Mon' or 'Monday'),
        # we detect it, figure out whether it should be `%a` or `%A`,
        # and remove it from the string so the core date-time detection
        # doesn't get confused.
        #--------------------------------------------------------------------
        weekday_format_str = ""
        matched_weekday = None
        matched_sep = ""

        weekday_match = _WEEKDAY_DETECTION_RE.match(date_string)
        if weekday_match:
            matched_weekday = weekday_match.group('weekday')  # e.g. "Fri" or "Friday"
            matched_sep = weekday_match.group('sep') or ""     # e.g. "," or " "
            # Remove the matched portion (and trailing space) from the front
            date_string = date_string[weekday_match.end():].lstrip()

            # Decide whether to use "%a" or "%A" based on length
            if len(matched_weekday) <= 3:
                # Abbreviated weekday
                weekday_format_str = "%a"
            else:
                # Full weekday
                weekday_format_str = "%A"

            # If there's a comma or space (like "Fri, " or "Fri "), include it literally in the pattern
            # so the parser won't choke on leftover punctuation
            if matched_sep:
                weekday_format_str += matched_sep

            # Usually we also put a space if the user wrote something like "Fri, 23-Aug-2024"
            # That implies the final pattern looks like "%a, %d-%b-%Y"
            # or if it was "Friday 05-Feb-2024", we get "%A %d-%b-%Y"
            if matched_sep:
                weekday_format_str += " "

        #--------------------------------------------------------------------
        # Step 5: Time Detection.
        # 
        # If the string contains a time portion, we split the string into
        # 'date part' and 'time part' and handle them separately.
        # Otherwise, we treat it as date-only.
        #--------------------------------------------------------------------        
        if _get_time_components(date_string):
            # Split into date and time components
            date_only = _TIME_DETECTION_RE.sub("", date_string).strip()  # leftover is "pure date"
            time_matches = [m.group(0) for m in _TIME_DETECTION_RE.finditer(date_string)]
            time_string = " ".join(time_matches).strip()

            # Try date formats on date_only
            local_seen_date = set()
            date_format = self.try_formats(self.formats.Dates(), date_only, local_seen_date)
            if not date_format:
                date_format = self.try_formats(self.formats.Unique(), date_only, local_seen_date)
            if not date_format:
                raise ValueError("No matching date format found for the date part.")

            # Try time formats on time_string
            ampm_match = re.search(r'(?i)\b(?:AM|PM)\b', time_string)
            if ampm_match:
                # If there's an hour we can see (1-12 vs 13-23), choose time formats accordingly
                hour_match = re.match(r'\s*(\d{1,2})', time_string)
                if hour_match:
                    hour_val = int(hour_match.group(1))
                    if hour_val < 13:
                        candidate_time_formats = [fmt for fmt in self.formats.Times() if '%p' in fmt and '%I' in fmt]
                    else:
                        candidate_time_formats = [fmt for fmt in self.formats.Times() if '%p' in fmt and '%H' in fmt]
                else:
                    candidate_time_formats = [fmt for fmt in self.formats.Times() if '%p' in fmt and '%I' in fmt]
            else:
                candidate_time_formats = self.formats.Times()

            local_seen_time = set()
            time_format = None
            for fmt in candidate_time_formats:
                if (fmt, time_string) in local_seen_time:
                    continue
                result = self.generate_formats(time_string, [fmt])
                local_seen_time.add((fmt, time_string))
                if result:
                    time_format = result
                    break
                   
            # Fallback: we try all precomputed formats that contain %p and %I if there's an AM/PM
            #------------------------------------------------------------------------------------
            if not time_format:
                fallback_formats = (
                    [fmt for fmt in self.formats.Precomputed() if '%p' in fmt and '%I' in fmt]
                    if ampm_match else self.formats.Precomputed()
                )
                for fmt in fallback_formats:
                    if (fmt, time_string) in local_seen_time:
                        continue
                    result = self.generate_formats(time_string, [fmt])
                    local_seen_time.add((fmt, time_string))
                    if result:
                        time_format = result
                        break
            if not time_format:
                raise ValueError("No matching time format found for the time part.")

            # Combine date + time
            combined_format = None                 
            combined_format = f"{date_format} {time_format}"
            # If we had a weekday, prepend it: e.g. "%a, %d-%b-%Y %H:%M:%S"
            if matched_weekday:
                combined_format = weekday_format_str + combined_format

                # Validate we can parse the original text with weekday
                test_string = matched_weekday + matched_sep
                if matched_sep:
                    test_string += " "
                test_string += date_only
                if time_string:
                    test_string += " " + time_string
                if tz_literal:
                    test_string += " " + tz_literal

                # If this fails, it will raise ValueError; if success, all is good.
                self.generate_formats(test_string.strip(), [combined_format])

            # 5.01) TIMEZONE LITERAL
            #--------------------------------------------------------------------------------------             
            if tz_literal:
                if '%Z' in combined_format:
                    combined_format = combined_format.replace('%Z', tz_literal)
                elif '%z' in combined_format:
                    combined_format = combined_format.replace('%z', tz_literal)
                else:
                    combined_format += " " + tz_literal
                if combined_format:
                    combined_format = " ".join(combined_format.split())                     

            # 5.02) Cache and return
            #--------------------------------------------------------------------------------------              
            # Reapply ordinal suffix if we captured one (like '5th')
            if self.day_suffix:
                suffix_lower = self.day_suffix.lower()
                if "%d" in combined_format:
                    combined_format = combined_format.replace("%d", f"%d{suffix_lower}")
            DateFormatFinder.successful_formats[raw_input] = (combined_format, date_only, time_string)                             
            return combined_format            
            
        #--------------------------------------------------------------------
        # Step 6: Date-Only Handling.
        # 
        # No time component means we just try date formats directly.
        #--------------------------------------------------------------------          
        else:
            # No time portion → just parse as date
            local_seen = set()
            date_format = self.try_formats(self.formats.Dates(), date_string, local_seen)
            if not date_format:
                date_format = self.try_formats(self.formats.Unique(), date_string, local_seen)
            if not date_format:
                raise ValueError("No matching format found for the given date string.")

            final_format = None
            final_format = date_format
            # Prepend weekday if present
            if matched_weekday:
                final_format = weekday_format_str + final_format

                # Validate
                test_string = matched_weekday + matched_sep
                if matched_sep:
                    test_string += " "
                test_string += date_string
                if tz_literal:
                    test_string += " " + tz_literal
                self.generate_formats(test_string.strip(), [final_format])

            # Apply timezone literal if found
            if tz_literal:
                if '%Z' in final_format:
                    final_format = final_format.replace('%Z', tz_literal)
                elif '%z' in final_format:
                    final_format = final_format.replace('%z', tz_literal)
                else:
                    final_format += " " + tz_literal
                    
                if final_format:
                    final_format = " ".join(final_format.split()) 
            
            # Reapply ordinal suffix if we captured one (like '5th')
            if self.day_suffix:
                suffix_lower = self.day_suffix.lower()
                if "%d" in final_format:
                    final_format = final_format.replace("%d", f"%d{suffix_lower}")
                    
            # Cache result                    
            DateFormatFinder.successful_formats[raw_input] = (final_format, date_string, None)                                
            return final_format
    
    def search(self, date_input):
        """
        A single entry point for:
	        - Strings
	        - Lists, sets, tuples
	        - Pandas Series
	        - Dictionaries (per key)
        
        The output is converted back into the same type as the input.
        """
        # 1) If it's a scalar string, handle normally.
        if isinstance(date_input, str):
            return self._search_scalar(date_input)

        # 2) If it's a pandas Series, process each element and rebuild a Series
        if isinstance(date_input, panda.Series):
            original_index = date_input.index
            date_input = date_input.astype(str)
            results = [self._search_scalar(item) for item in date_input]
            return panda.Series(results, index=original_index, dtype=object)

        # 3) If it's a dictionary, do a dictionary comprehension
        if isinstance(date_input, dict):
            return {k: self._search_scalar(v) for k, v in date_input.items()}

        # 4) For all other iterables, process them as follows:
        try:
            # Save the original type for later reconstruction.
            original_type = type(date_input)
            results = [self._search_scalar(item) for item in date_input]
        except TypeError:
            # Not iterable, so treat it as scalar.
            return self._search_scalar(str(date_input))

        # 5) Rebuild the output in the same format as the input.
        if isinstance(date_input, list):
            return results
        elif isinstance(date_input, tuple):
            return tuple(results)
        elif isinstance(date_input, set):
            return set(results)
        elif isinstance(date_input, num.ndarray):
            return num.array(results, dtype=object)
        else:
            # Fallback: try to cast results to the original type
            try:
                return original_type(results)
            except Exception:
                return results
    
    @staticmethod
    def clear_cache():
        DateFormatFinder.successful_formats.clear()
        DateFormatFinder.historical_formats.clear()


DateTimeScan = DateFormatFinder()





__all__ = ['DateTimeScan']

