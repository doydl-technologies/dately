import re
import datetime
import time

# Import all functions and classes from custom utility modules
from .utils import *
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
    get_time_fragment as gtf, 
)


# Define public interface
__all__ = [
    "exist_meridiem",
    "extract_time_fragment",
    "make_datetime_string",
    "offset_convert",
    "replace_time_by_position",
    "stripTimeIndicator",
    "stripTime",
    "datetime_offset",
    "strTime",
    "stripTimeZone",
    "validate_timezone",
    "validate_date",
    "remove_marker",
]

def get_time():
    current_time = time.time()
    local_time = time.localtime(current_time)
    formatted_time = time.strftime("%H:%M:%S", local_time) + f".{int(current_time % 1 * 1_000_000)}"
    return formatted_time
   
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

def stripTime(datetime_string):
    """ Removes time from a datetime string. """
    time_exists = timeboundary_regex.search(datetime_string)
    if time_exists:
        full_time_start_position = time_exists.start()
        date_no_time = datetime_string[:full_time_start_position]
        return cleanstr(date_no_time)
    return datetime_string

def stripTimeIndicator(datetime_string):
    """ Removes time indicators (like 'AM' or 'PM') from a given datetime string. """
    match = strTime(datetime_string)
    
    if match:
        time_match = match['time_details']['time_found']
        time_end = match['time_details']["end"]
        fulltime_start = match['full_time_details']['start']
        fulltime_end = match['full_time_details']["end"]
        timezone_data = datetime_string[time_end:]
        if timezone_data == '':
            return datetime_string
        cleaned_string = re.sub(timemeridiem_regex, ' ', timezone_data)
        return datetime_string[:fulltime_start] + time_match + cleaned_string + datetime_string[fulltime_end:]
           
    return datetime_string

def stripTimeZone(datetime_string):
    """ Removes timezone info from a given datetime string. """
    match = strTime(datetime_string)
    
    if match:
        time_match = match['time_details']['time_found']
        time_start = match['time_details']['start']
        time_end = match['time_details']["end"]
        fulltime_start = match['full_time_details']['start']
        fulltime_end = match['full_time_details']["end"]

        timezone_data = datetime_string[time_end:]
        
        if timezone_data == '':
            return datetime_string

        indicator_match = timemeridiem_regex.search(timezone_data) 
        
        if indicator_match:
            indicator_end = indicator_match.end()
            new_end_position = time_end + indicator_end
            new_str = datetime_string[:new_end_position]
            return cleanstr(new_str)

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

def make_datetime_string(date_string):
    """
    Generate a standardized datetime string from a given date string.

    This function takes a date string and attempts to detect its format using the generate_date_formats function. If a valid format
    is detected, it compiles the appropriate regex patterns using __compile_maketime_patterns__. The function then checks if the date
    string matches the compiled pattern and, if the format is date-only, appends '00:00:00.000000 NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET' to
    standardize the datetime string. If the format is not detected or includes time information, the original date string is returned.

    Parameters:
        date_string (str): The date string to be standardized.

    Returns:
        str: A standardized datetime string. If the format is date-only, '00:00:00.000000 NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET' is appended to the date string. If the format
             includes time information or is not detected, the original date string is returned.
    """
    time_pattern = anytime_regex
    no_other_time_placeholder = "NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET"
    match = time_pattern.search(date_string)

    if match:
        time_component = match.group()
        tzinfo_pattern = gtf('tzinfo')
        if tzinfo_pattern.search(time_component):
            return date_string
        else:
            return f"{date_string.strip()} {get_time()} {no_other_time_placeholder}"
    else:
        return f"{date_string.strip()} {get_time()} {no_other_time_placeholder}"
       
def validate_timezone(datetime_string):
    match = strTime(datetime_string)
    
    if match:
        time_end = match['time_details']["end"]
        timezone_data = datetime_string[time_end:]
        timezone_data = timezone_data.lstrip()
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
    pattern = timemeridiem_regex
    match = pattern.search(time_fragment_str)
    if match:
        return True
    return None


def extract_time_fragment(date_time_string, locale=False):
    """
    Parse a date-time string to extract the time fragment and provide its position for possible modification.

    This function uses a compiled regex pattern to search for a time fragment within a given date-time string.
    If a match is found, it returns the matched time fragment along with its start and end positions within the 
    original string. If the 'locale' parameter is set to True, the positions are returned; otherwise, they are None.

    Parameters:
        date_time_string (str): The date-time string to be parsed for a time fragment.
        locale (bool): A flag indicating whether to return the start and end positions of the time fragment.

    Returns:
        tuple: A tuple containing the matched time fragment (str), and optionally its start (int) and end (int) 
               positions. If no match is found, (None, None, None) is returned.
    """
    pattern = anytime_regex
    match = pattern.search(date_time_string)
    if match:
        if locale:
            return match.group(0), match.start(), match.end()
        else:
            return match.group(0), None, None
    return None, None, None
 
def replace_time_by_position(datetime_string, component, new_value):
    """
    Modifies a specified component of a time within a datetime string based on provided patterns.

    This function updates the hour, minute, second, microsecond, or timezone information of a datetime string.
    Each component is adjusted based on regular expressions which identify these elements within the string.
    The function ensures that input values are within valid ranges and formats them accordingly before replacement.

    Args:
        datetime_string (str): The datetime string to modify.
        component (str): The component to modify, which can be 'hour', 'minute', 'second', 'microsecond', or 'tzinfo'.
        new_value (str): The new value to insert for the specified component. Should be a string that is valid
                         within the context of the component (e.g., numeric for hour, minute, and second).

    Returns:
        str: The modified datetime string with the specified component updated to the new value.
             Returns the original datetime string unchanged if the component does not match or if the new
             value is invalid for the specified component.

    Raises:
        ValueError: If the new value is out of the acceptable range for hours (0-23), minutes or seconds (0-59),
                    or if the microsecond value is not a digit.
    """
    # Validate and adjust the new value based on the component
##    if component == 'hour':
##        new_value = str(max(0, min(23, int(new_value))))
    if component == 'hour':
        # Check if the input is a string and starts with a '0' 
        if isinstance(new_value, str) and new_value.startswith("0") and len(new_value) == 2 and int(new_value) < 10:
            new_value = "0" + str(max(0, min(23, int(new_value))))
        else:
            new_value = str(max(0, min(23, int(new_value))))    
    elif component in ['minute', 'second']:
        new_value = str(max(0, min(59, int(new_value)))).zfill(2)
    elif component == 'microsecond':
        if not str(new_value).isdigit():
            return datetime_string

    time_component_pattern = gtf(component)
    gt_time_pattern_match = timeboundary_regex.search(datetime_string)
    if gt_time_pattern_match:
        time_start_position = gt_time_pattern_match.start()
        time_end_position = gt_time_pattern_match.end()
        time_matched_value = gt_time_pattern_match.group()
        if component == 'tzinfo':
            new_value = offset_convert(new_value)
            time_component_matches = list(time_component_pattern.finditer(time_matched_value))
            if time_component_matches:
                largest_match = max(time_component_matches, key=lambda m: m.end())
                part_before = datetime_string[:time_start_position + time_component_matches[0].start()]
                part_after = datetime_string[time_start_position + largest_match.end():]
                datetime_string = part_before + new_value + part_after
                return datetime_string.replace('NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET', new_value).strip()
            else:
                return datetime_string.replace('NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET', new_value).strip()
        time_component_match = time_component_pattern.search(time_matched_value)
        if time_component_match:
            part_before = datetime_string[:time_start_position + time_component_match.start(1)]
            part_after = datetime_string[time_start_position + time_component_match.end(1):]

            if component == 'microsecond':
                new_value = hundred_thousandths_place(new_value, decimal=False)
            datetime_string = part_before + new_value + part_after
            return datetime_string.replace('NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET', '').strip()
    datetime_string = datetime_string.replace('NO_MERIDIEM_NO_TIMEZONE_NO_OFFSET', '').strip()
    return datetime_string
