from cython cimport cdivision
from cpython cimport bool
from cpython.datetime cimport datetime
import re

__all__ = [
    'zero_handling_date_formats',
    'non_padded_to_zero_padded_specifiers',
    'has_leading_zero',
    'date_format_leading_zero',
    'replace_non_padded_with_padded',
]


# Declare the dictionary types for better performance
cdef dict _zero_handling_date_formats
cdef dict _non_padded_to_zero_padded_specifiers

# Initialize the dictionaries
_zero_handling_date_formats = {
    'day': {
        'no_leading_zero': {
            'format': '%-d',
            'description': 'Day of the month as a decimal number without leading zero (1 to 31)'
        },
        'zero_padded': {
            'format': '%d',
            'description': 'Day of the month as a zero-padded decimal number (01 to 31)'
        }
    },
    'month': {
        'no_leading_zero': {
            'format': '%-m',
            'description': 'Month as a decimal number without leading zero (1 to 12)'
        },
        'zero_padded': {
            'format': '%m',
            'description': 'Month as a zero-padded decimal number (01 to 12)'
        }
    },
    'year': {
        'no_leading_zero': {
            'format': '%-y',
            'description': 'Year without century as a decimal number without leading zero (0 to 99)'
        },
        'zero_padded': {
            'format': '%y',
            'description': 'Year without century as a zero-padded decimal number (00 to 99)'
        }
    },
    'hour24': {
        'no_leading_zero': {
            'format': '%-H',
            'description': 'Hour (24-hour clock) as a decimal number without leading zero (0 to 23)'
        },
        'zero_padded': {
            'format': '%H',
            'description': 'Hour (24-hour clock) as a zero-padded decimal number (00 to 23)'
        }
    },
    'hour12': {
        'no_leading_zero': {
            'format': '%-I',
            'description': 'Hour (12-hour clock) as a decimal number without leading zero (1 to 12)'
        },
        'zero_padded': {
            'format': '%I',
            'description': 'Hour (12-hour clock) as a zero-padded decimal number (01 to 12)'
        }
    },
    'minute': {
        'no_leading_zero': {
            'format': '%-M',
            'description': 'Minute as a decimal number without leading zero (0 to 59)'
        },
        'zero_padded': {
            'format': '%M',
            'description': 'Minute as a zero-padded decimal number (00 to 59)'
        }
    },
    'second': {
        'no_leading_zero': {
            'format': '%-S',
            'description': 'Second as a decimal number without leading zero (0 to 59)'
        },
        'zero_padded': {
            'format': '%S',
            'description': 'Second as a zero-padded decimal number (00 to 59)'
        }
    }
}

_non_padded_to_zero_padded_specifiers = {
    '%-d': '%d',
    '%-m': '%m',
    '%-y': '%y',
    '%-H': '%H',
    '%-I': '%I',
    '%-M': '%M',
    '%-S': '%S'
}

# Use cdef to declare return types for functions
cdef dict get_zero_handling_date_formats():
    return _zero_handling_date_formats

cdef dict get_non_padded_to_zero_padded_specifiers():
    return _non_padded_to_zero_padded_specifiers

def zero_handling_date_formats():
    return get_zero_handling_date_formats()

def non_padded_to_zero_padded_specifiers(ret_format=None):
    if ret_format == 'no_leading_zero':
        return list(_non_padded_to_zero_padded_specifiers.keys())
    elif ret_format == 'leading_zero':
        return list(_non_padded_to_zero_padded_specifiers.values())
    else:
        return _non_padded_to_zero_padded_specifiers


@cdivision(True)
def has_leading_zero(object input_str):
    cdef str integer_part
    cdef int len_integer_part

    input_str = str(input_str)

    # Check if the converted input string is a valid number
    if not input_str.replace('-', '', 1).replace('.', '', 1).isdigit():
        return None  # Return None if it's not a valid number

    # Special case for "0"
    if input_str == "0" or input_str == "-0":
        return None  # Return None for "0" or "-0"

    # Check if the integer part has exactly two digits
    integer_part = input_str.split('.')[0].strip('-')
    len_integer_part = len(integer_part)
    
    if len_integer_part == 2 and integer_part != '00':
        return None  # Return None for whole numbers with exactly two digits, except '00'

    # Check if the integer part has more than two digits
    if len_integer_part > 2:
        return None  # Return None if the integer part has more than two digits

    # Check for leading zero in whole numbers or in the integer part of decimal numbers
    if input_str[0] == '-' and input_str[1] == '0':
        return True
    elif input_str[0] == '0' and input_str[1] != '.':
        return True
    elif input_str.startswith('0.') and input_str != '0.':
        return True
        
    return False


# Helper function to check format specifications
cdef bint has_non_padded_specifier(str format_string):
    non_padded_specifiers = non_padded_to_zero_padded_specifiers(ret_format='no_leading_zero')
    return any(spec in format_string for spec in non_padded_specifiers)

cpdef str date_format_leading_zero(datetime date, str format_string):
    cdef str platform_compatible_format, formatted_date, orig, repl
    if has_non_padded_specifier(format_string):
        platform_compatible_format = format_string
        for orig, repl in non_padded_to_zero_padded_specifiers().items():
            platform_compatible_format = platform_compatible_format.replace(orig, repl)
        
        formatted_date = date.strftime(platform_compatible_format)
        
        for orig in non_padded_to_zero_padded_specifiers(ret_format='no_leading_zero'):
            if orig in format_string:
                formatted_date = re.sub(r'\b0(?=\d)', '', formatted_date)
        return formatted_date
    else:
        return date.strftime(format_string)


cpdef str replace_non_padded_with_padded(str input_format):
    cdef str category, non_padded, zero_padded
    # Directly use the dictionary without additional function calls for better performance
    for category in _zero_handling_date_formats:
        non_padded = _zero_handling_date_formats[category]['no_leading_zero']['format']
        zero_padded = _zero_handling_date_formats[category]['zero_padded']['format']
        input_format = input_format.replace(non_padded, zero_padded)
    return input_format

