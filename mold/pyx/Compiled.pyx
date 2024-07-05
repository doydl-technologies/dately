# Compiled.pyx
import re
import os
import sys
from libc.string cimport strdup
from libc.stdlib cimport free  # Import free to release allocated memory
from cython cimport unicode, boundscheck, wraparound
from cpython cimport array

cdef extern from "root_dir_search.h":
    char* find_directory(const char *start_path, const char *dir_name)

def get_directory_path(directory_name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    directory_path_c = find_directory(script_dir.encode('utf-8'), directory_name.encode('utf-8'))
    if directory_path_c:
        directory_path = directory_path_c.decode('utf-8')
        free(directory_path_c)  # Free the allocated memory
        return directory_path
    else:
        raise EnvironmentError(f"{directory_name} directory not found.")

# Find the dately path
dately_path = get_directory_path("dately")
if dately_path:
    sys.path.append(dately_path)
else:
    raise EnvironmentError("dately directory not found.")

from mold.pyd.time_zones import time_zones_dict




cdef dict __datetime_named_group_patterns__ = {
    '%a': r'(?P<weekday>Mon|Tue|Wed|Thu|Fri|Sat|Sun)',
    '%A': r'(?P<weekday>Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',    
    '%w': r'(?P<weekday>\d)',
    '%u': r'\d',     
    '%b': r'(?P<month>[A-Za-z]{3})',
    '%B': r'(?P<month>[A-Za-z]+)',
    '%m': r'(?P<month>\d{1,2})',
    '%-m': r'(?P<month>\d{1,2})',
    '%d': r'(?P<day>\d{1,2})',
    '%-d': r'(?P<day>\d{1,2})',
    '%j': r'(?P<day>\d{1,3})',
    '%-H': r'(?P<hour24>(?:[0-9]|1[0-9]|2[0-3]|\d{1,2}))',
    '%H': r'(?P<hour24>(?:\d{1,2}|0?[0-9]|1[0-9]|2[0-3]))',
    '%I': r'(?P<hour12>(?:\d{1,2}|0?[1-9]|1[0-2]))',
    '%-I': r'(?P<hour12>(?:\d{1,2}|0?[1-9]|1[0-2]))',
    '%M': r'(?P<minute>\d{1,2})',
    '%-M': r'(?P<minute>\d{1,2})',
    '%S': r'(?P<second>\d{1,2})',
    '%-S': r'(?P<second>\d{1,2})',
    '%f': r'(?P<microsecond>\d{1,6})',
    '%p': r'(?P<am_pm>(?:AM|PM))',
    '%-y': r'(?P<year>\d{2})',
    '%y': r'(?P<year>\d{2})',
    '%Y': r'(?P<year>\d{4})',       
    '%z': r'(?P<timezone>[\+\-](?:\d{4}|\d{2}:?\d{2}))',
    '%Z': r'(?P<timezone>(?:[\+\-]\d{2}:[0-9]{2}|[A-Za-z\s]+|[A-Za-z]{2,4}|UTC|[\+\-]\d{2}:?\d{2}))',  
    '%q': r'\d',
    '%U': r'\d{1,2}',
    '%V': r'\d{1,2})',
}

cpdef object datetime(unicode fmt):
    cdef unicode regex = fmt
    cdef unicode key, value
    for key, value in __datetime_named_group_patterns__.items():
        regex = regex.replace(key, value)
    return re.compile(u'^' + regex + u'$')

# Create regex patterns for timezone abbreviations and full timezone names
timezone_abbrv = list(time_zones_dict.keys())
timezone_abbrv_pattern = r'\b(' + '|'.join(timezone_abbrv) + r')\b'
full_names = [info['full_name'] for info in time_zones_dict.values()]
full_names_pattern = r'\b(' + '|'.join(full_names) + r')\b'

# Define the regex patterns in a dictionary
regex_patterns = {
    "timemeridiem": r'\s*\b(AM|PM)\b\s*',
    # Purpose: Matches a time string in the format HH:MM:SS or HH:MM:SS.microseconds.
    "timeonly": r'(?P<hours>\d{1,2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})(?:\.(?P<microseconds>\d+))?',
    "timezone_offset": r'(?<!\d)[+-]?(?:\d{1,2}(?::\d{1,2})?|\d{3,4})(?!\d)',
    "iana_timezone_identifier": r'\b[A-Za-z_]+/[A-Za-z_]+\b',
    "anytime": (
        r"(?<!\d)(\d{1,2}:\d{2}:\d{2}|\d{6})"
        r"(?:\.\d{1,6})?"
        r"(?:\s*[AP]M)?"
        r"(?:\s*(?:[+-]\d{2}:?\d{2}|[+-]\d{4}|[A-Z]{3,4}|Z))?"
        r"(?=\s|$)"
    ),
    # Purpose: Matches various time string formats, including HH:MM:SS, HHMMSS, with optional microseconds, AM/PM indicators, and time zone information.
    "timeplus": (
        r"(\d{1,2}:\d{2}:\d{2}|\d{6})"
        r"(?:\.\d{1,6})?"
        r"(?:\s*[AP]M)?"
        r"(?:\s*(?:[+-]\d{2}:?\d{2}|[+-]\d{4}|[A-Z]{3,4}|Z))?"
    ),
    "establish_time_boundary": r'(?<!\d)(\d{1,2}:\S.*)',
    "datetime_second": r'\d{2}:\d{2}:(\d{2})(?:\.\d+)?',
    "datetime_minute": r'\d{2}:(\d{2})(:\d{2}(?:\.\d+)?)?',
    "datetime_hour": r'(\d{1,2}):(\d{2})(:\d{2}(?:\.\d+)?)?',
    "datetime_microsecond": r'\d{2}:\d{2}:\d{2}\.(\d+)',
    "datetime_timezone": (
        r'\b\d{1,2}(:\d{2})?Z\b|'          # Zulu time (UTC)
        r'[\+\-]\d{2}:?\d{2}|'             # UTC offset
        r'\b[A-Za-z]+/[A-Za-z_]+\b|'       # Continent/City format
        r'\bAM\b|\bPM\b'                   # AM/PM indicator
    ),
    "timezone_abbreviation": timezone_abbrv_pattern,
    "full_timezone_name": full_names_pattern
}

# Function to compile the regex patterns
cpdef dict compile_regex_patterns():
    cdef dict compiled_patterns = {}
    for key, pattern in regex_patterns.items():
        compiled_patterns[key] = re.compile(pattern, re.IGNORECASE)
    return compiled_patterns

# Compile the regex patterns at the module level
compiled_patterns = compile_regex_patterns()

# Function to get compiled pattern by name
cdef object get_pattern(str name):
    return compiled_patterns.get(name, None)

# Call the get_pattern function to retrieve the compiled regex
second_regex = get_pattern("datetime_second")
minute_regex = get_pattern("datetime_minute")
hour_regex = get_pattern("datetime_hour")
microsecond_regex = get_pattern("datetime_microsecond")
timezone_regex = get_pattern("datetime_timezone")
timezone_offset_regex = get_pattern("timezone_offset")
iana_timezone_identifier_regex = get_pattern("iana_timezone_identifier")
timemeridiem_regex = get_pattern("timemeridiem")
time_only_regex = get_pattern("timeonly")
anytime_regex = get_pattern("anytime")
timeboundary_regex = get_pattern("establish_time_boundary")
timezone_abbreviation_regex  = get_pattern("timezone_abbreviation")
full_timezone_name_regex = get_pattern("full_timezone_name")
timeplus_regex = get_pattern("timeplus")

cdef class cRegexps:
    cdef dict time_component_patterns

    def __cinit__(self):
        self.time_component_patterns = {
            "second": second_regex,
            "minute": minute_regex,
            "hour": hour_regex,
            "microsecond": microsecond_regex,
            "tzinfo": timezone_regex
        }
        
    cpdef object get_time_fragments(self, str component):
        return self.time_component_patterns.get(component)

# Create an instance of the cRegexps class
cdef cRegexps regexps = cRegexps()

# Define module-level variables for compiled regex patterns
datetime_regex = datetime
get_time_fragment = regexps.get_time_fragments

# Define public interface
__all__ = [
    'datetime_regex',
    'timemeridiem_regex',
    'anytime_regex',
    'timezone_regex',
    'timeboundary_regex',
    'second_regex',
    'minute_regex',
    'hour_regex',
    'microsecond_regex',
    'get_time_fragment',
    'time_only_regex',
    'timeplus_regex',
    'iana_timezone_identifier_regex',
    'timezone_offset_regex',
    'timezone_abbreviation_regex',
    'full_timezone_name_regex',
]