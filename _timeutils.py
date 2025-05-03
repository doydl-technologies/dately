# -*- coding: utf-8 -*-

import re
import datetime
import time

# ────────── Project-specific imports (directly from this project's source code) ─────────────────────────────
from ._utils import is_leap_year, hundred_thousandths_place
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


# ━━━━━━━━━━━━━━ Core Module Implementation ━━━━━━━━━━━━━━━━━━━━━━━━━━
# This segment delineates the functional backbone of the module.
# It comprises the abstractions and behaviors essential for runtime
# execution—if applicable—encapsulated in class and function constructs.
# In minimal implementations, this may simply define constants, metadata,
# or serve as an interface placeholder.
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
        # Extract what follows the time and remove our placeholder if present.
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
    
    def offset_convert(number):
        """
        Converts a numeric or string time offset into a formatted string representing the offset in hours and minutes.

        The function takes either a floating-point, an integer, or a string representing a time offset in hours,
        and returns a string formatted as +-HH:MM. The sign (plus or minus) is determined based on
        whether the input number is non-negative or negative.

        Parameters:
        number (float, int, or str): The time offset in hours. Can be positive, negative, or zero.

        Returns:
        str: The formatted time offset as a string with a leading sign (either '+' or '-') followed
             by two digits for hours and two digits for minutes, separated by a colon.
        """
        if isinstance(number, str):
            number = float(number)
        sign = '+' if number >= 0 else '-'
        abs_number = abs(number)
        hours = int(abs_number)
        minutes = int((abs_number - hours) * 60)
        formatted_time = f"{sign}{hours:02}:{minutes:02}"
        return formatted_time
       
    # Basic validation / bounding
    if component == 'hour':
        new_value = str(max(0, min(23, int(new_value))))
        if len(new_value) == 1:
            new_value = "0" + new_value
    elif component in ['minute', 'second']:
        new_value = str(max(0, min(59, int(new_value)))).zfill(2)
    elif component == 'microsecond':
        # If it's invalid, we skip
        if not str(new_value).isdigit():
            return datetime_string

    time_pattern = get_pattern("timeonly")  # or use time_only_regex
    tzinfo_pattern = get_pattern("datetime_timezone")  # or use timezone_regex

    entire_time_match = timeboundary_regex.search(datetime_string)
    if not entire_time_match:
        # No recognized time => do nothing
        return datetime_string

    time_str_start = entire_time_match.start()
    time_str_end = entire_time_match.end()
    time_substring = entire_time_match.group()

    if component == 'tzinfo':
        # Convert numeric offset to e.g. +02:30
        new_value = offset_convert(new_value)
        # Find if there's already a tzinfo
        existing_tz_matches = list(tzinfo_pattern.finditer(time_substring))
        if existing_tz_matches:
            # Replace last occurrence
            largest_match = max(existing_tz_matches, key=lambda m: m.end())
            part_before = datetime_string[:time_str_start + largest_match.start()]
            part_after = datetime_string[time_str_start + largest_match.end():]
            updated = part_before + new_value + part_after
        else:
            # If no tz info found, just append or replace placeholder
            updated = datetime_string.replace('NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET', new_value)
        return updated.strip()

    # For hour, minute, second, microsecond
    match_timeonly = time_pattern.search(time_substring)
    if match_timeonly:
        # For microsecond replacement, we only store 'microsecond' if in groupdict
        groups = match_timeonly.groupdict()
        # start(1) => the first capturing group (hours?), etc.
        # For hour/minute/second, it's typically group(1) or group(2)
        # We'll do a small check which group index to replace:

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
                # If the original string had no seconds, let's just append
                # Or we can do nothing. For now, we do a naive approach:
                # We'll replace the substring from the end of 'minutes' group.
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
                # If there's no microseconds part, do we append? 
                # For simplicity, let's do nothing or append a .<value>
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
