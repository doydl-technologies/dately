# cython: language_level=3
import re
from cpython.datetime cimport datetime
from datetime import datetime as py_datetime
cimport cython
from libc.stdlib cimport malloc, free
from libc.string cimport strcpy, strlen
from cython cimport boundscheck, wraparound

@cython.boundscheck(False)
@cython.wraparound(False)
cdef class dFormats:
    """
    Manages a collection of date and time format strings supported by the system.
    """
    cdef char** dates
    cdef char** times
    cdef char** unique
    cdef size_t num_dates, num_times, num_unique

    def __cinit__(self):
        self.num_dates = 19
        self.num_times = 33
        self.num_unique = 55

        cdef char* date_formats[19]
        date_formats[0] = b'%m/%d/%y'
        date_formats[1] = b'%B/%d/%Y'
        date_formats[2] = b'%Y/%B/%d'
        date_formats[3] = b'%y%m%d'
        date_formats[4] = b'%m/%d/%Y'
        date_formats[5] = b'%d/%m/%Y'
        date_formats[6] = b'%y/%m/%d'
        date_formats[7] = b'%d/%B/%Y'
        date_formats[8] = b'%Y/%b/%d'
        date_formats[9] = b'%b/%d/%Y'
        date_formats[10] = b'%Y/%m/%d'
        date_formats[11] = b'%Y%m%d'
        date_formats[12] = b'%d/%m/%y'
        date_formats[13] = b'%d/%b/%Y'
        date_formats[14] = b'%a, %b %d, %Y'
        date_formats[15] = b'%A, %B %d, %Y'
        date_formats[16] = b'%d/%B/%y'
        date_formats[17] = b'%B %d, %y'
        date_formats[18] = b'%d %B %y'
        
        cdef char* time_formats[33]
        time_formats[0] = b'%H'
        time_formats[1] = b'%I'
        time_formats[2] = b'%H:%M'
        time_formats[3] = b'%H:%M:%S'
        time_formats[4] = b'%H:%M:%S:%f'
        time_formats[5] = b'%H:%M %p'
        time_formats[6] = b'%H:%M:%S %p'
        time_formats[7] = b'%H:%M:%S:%f %p'
        time_formats[8] = b'%I:%M'
        time_formats[9] = b'%I:%M %p'
        time_formats[10] = b'%I:%M:%S'
        time_formats[11] = b'%I:%M:%S %p'
        time_formats[12] = b'%I:%M:%S:%f'
        time_formats[13] = b'%I:%M:%S:%f %p'
        time_formats[14] = b'%H:%M:%S %z'
        time_formats[15] = b'%H:%M:%S %Z'
        time_formats[16] = b'%I:%M %p %z'
        time_formats[17] = b'%I:%M %p %Z'
        time_formats[18] = b'%H:%M:%S:%f %z'
        time_formats[19] = b'%H:%M:%S:%f %Z'
        time_formats[20] = b'%I:%M:%S %p %z'
        time_formats[21] = b'%I:%M:%S %p %Z'
        time_formats[22] = b'%H %p'
        time_formats[23] = b'%I %p'
        time_formats[24] = b'%H:%M:%S:%f %p %z'
        time_formats[25] = b'%H:%M:%S:%f %p %Z'
        time_formats[26] = b'%I:%M:%S:%f %p %z'
        time_formats[27] = b'%I:%M:%S:%f %p %Z'
        time_formats[28] = b'%H%M%S'
        time_formats[29] = b'%H:%M:%S%z'
        time_formats[30] = b'%H:%M:%SZ'
        time_formats[31] = b'%H:%M:%S.%f'
        time_formats[32] = b'%H:%M:%S.%f%z'

        cdef char* unique_formats[55]
        unique_formats[0] = b'%A the %dth of %B, %Y'
        unique_formats[1] = b'%A'
        unique_formats[2] = b'%a'
        unique_formats[3] = b'%A, %d %B %Y'
        unique_formats[4] = b'%Y, %b %d'
        unique_formats[5] = b'%B %d'
        unique_formats[6] = b'%B %d, %Y'
        unique_formats[7] = b'%b %d, %Y'
        unique_formats[8] = b'%b'
        unique_formats[9] = b'%B'
        unique_formats[10] = b'%B, %Y'
        unique_formats[11] = b'%b. %d, %Y'
        unique_formats[12] = b'%d %B'
        unique_formats[13] = b'%d %B, %Y'
        unique_formats[14] = b'%d of %B, %Y'
        unique_formats[15] = b'%d-%b-%y'
        unique_formats[16] = b'%d'
        unique_formats[17] = b'%dth %B %Y'
        unique_formats[18] = b'%dth of %B %Y'
        unique_formats[19] = b'%dth of %B, %Y'
        unique_formats[20] = b'%H'
        unique_formats[21] = b'%I'
        unique_formats[22] = b'%m-%Y-%d'
        unique_formats[23] = b'%m-%Y'
        unique_formats[24] = b'%m'
        unique_formats[25] = b'%M'
        unique_formats[26] = b'%m/%Y'
        unique_formats[27] = b'%m/%Y/%d'
        unique_formats[28] = b'%Y %B'
        unique_formats[29] = b'%Y Q%q'
        unique_formats[30] = b'%Y-%j'
        unique_formats[31] = b'%Y-%m'
        unique_formats[32] = b'%y'
        unique_formats[33] = b'%Y'
        unique_formats[34] = b'%Y, %B %d'
        unique_formats[35] = b'%Y.%m'
        unique_formats[36] = b'%Y/%m'
        unique_formats[37] = b'%Y-W%U-%w'
        unique_formats[38] = b'%Y-W%V-%u'
        unique_formats[39] = b'%a, %d %b %Y'
        unique_formats[40] = b'%b %d %y'
        unique_formats[41] = b'%b-%d-%y'
        unique_formats[42] = b'%b-%Y-%d'
        unique_formats[43] = b'%b.%Y-%d'
        unique_formats[44] = b'%d %b, %Y'
        unique_formats[45] = b'%d %B, %y'
        unique_formats[46] = b'%d-%Y.%m'
        unique_formats[47] = b'%d-%Y/%m'
        unique_formats[48] = b'%d.%Y-%m'
        unique_formats[49] = b'%d/%Y-%m'
        unique_formats[50] = b'%d/%Y.%m'
        unique_formats[51] = b'%m.%Y-%d'
        unique_formats[52] = b'%m.%Y/%d'
        unique_formats[53] = b'%m/%Y-%d'
        unique_formats[54] = b'on %B %d, %Y'

        self.dates = <char**>malloc(self.num_dates * sizeof(char*))
        self.times = <char**>malloc(self.num_times * sizeof(char*))
        self.unique = <char**>malloc(self.num_unique * sizeof(char*))

        for i in range(self.num_dates):
            self.dates[i] = <char*>malloc(strlen(date_formats[i]) + 1)
            strcpy(self.dates[i], date_formats[i])

        for i in range(self.num_times):
            self.times[i] = <char*>malloc(strlen(time_formats[i]) + 1)
            strcpy(self.times[i], time_formats[i])

        for i in range(self.num_unique):
            self.unique[i] = <char*>malloc(strlen(unique_formats[i]) + 1)
            strcpy(self.unique[i], unique_formats[i])

    def __dealloc__(self):
        if self.dates:
            for i in range(self.num_dates):
                if self.dates[i]:
                    free(self.dates[i])
            free(self.dates)
        if self.times:
            for i in range(self.num_times):
                if self.times[i]:
                    free(self.times[i])
            free(self.times)
        if self.unique:
            for i in range(self.num_unique):
                if self.unique[i]:
                    free(self.unique[i])
            free(self.unique)

    def Unique(self):
        cdef int i
        return [self.unique[i].decode('utf-8') for i in range(self.num_unique)]

    def Dates(self):
        cdef int i
        return [self.dates[i].decode('utf-8') for i in range(self.num_dates)]

    def Times(self):
        cdef int i
        return [self.times[i].decode('utf-8') for i in range(self.num_times)]



# Precompile the regex pattern
# @cython.boundscheck(False)
# @cython.wraparound(False)
# cpdef object anytime():
#     return re.compile(
#         r"(?<!\d)(\d{1,2}:\d{2}:\d{2}|\d{6})"
#         r"(?:\.\d{1,6})?"
#         r"(?:\s*[AP]M)?"
#         r"(?:\s*(?:[+-]\d{2}:?\d{2}|[+-]\d{4}|[A-Z]{3,4}|Z))?"
#         r"(?=\s|$)",
#         re.IGNORECASE
#     )
@cython.boundscheck(False)
@cython.wraparound(False)
cpdef object anytime():
    return re.compile(
        r"(?<!\d)(\d{1,2}:\d{2}(?::\d{2})?|\d{6})"
        r"(?:\.\d{1,6})?"
        r"(?:\s*[AP]M)?"
        r"(?:\s*(?:[+-]\d{2}:?\d{2}|[+-]\d{4}|[A-Z]{3,4}|Z))?"
        r"(?=\s|$)",
        re.IGNORECASE        
    )

# Define module-level variables for compiled regex patterns
anytime_regex = anytime()

@boundscheck(False)
@wraparound(False)
cpdef bint get_time_components(datetime_string: str):
    cdef object match
    match = anytime_regex.search(datetime_string)
    return match is not None

cdef class DateFormatFinder:
    cdef dFormats formats
    cdef list date_formats
    cdef list time_formats
    cdef list unique_formats
    cdef list separators
    cdef str old_sep
    cdef set seen_formats
    cdef list precomputed_formats

    successful_formats = {}  # Shared cache for successful formats
    historical_formats = set()  # Keep a record of all formats that were ever successful

    def __init__(self, old_sep='/'):
        self.formats = dFormats()
        self.date_formats = self.formats.Dates()
        self.time_formats = self.formats.Times()
        self.unique_formats = self.formats.Unique()
        self.separators = ['/', '.', '-', ' ', '']
        self.old_sep = old_sep
        self.seen_formats = set()

        # Precompute formats with different separators
        self.precomputed_formats = self._precompute_formats()

    cdef list _precompute_formats(self):
        cdef list precomputed = []
        cdef str new_format
        cdef int i, j
        cdef list all_formats = self.date_formats + self.unique_formats
        cdef int len_formats = len(all_formats)
        cdef int len_separators = len(self.separators)

        for i in range(len_formats):
            precomputed.append(all_formats[i])
            for j in range(len_separators):
                new_format = all_formats[i].replace(self.old_sep, self.separators[j])
                if new_format not in precomputed:
                    precomputed.append(new_format)
        return precomputed

    cdef str generate_formats(self, bytes date_string, list datetime_formats):
        cdef int i, len_formats = len(datetime_formats)
        cdef datetime dt
        for i in range(len_formats):
            try:
                dt = py_datetime.strptime(date_string.decode('utf-8'), datetime_formats[i])
                DateFormatFinder.historical_formats.add(datetime_formats[i])  # Log successful format
                return datetime_formats[i]
            except ValueError:
                continue
        return None

    cdef str try_formats(self, list formats, str date_string):
        cdef bytes date_bytes = date_string.encode('utf-8')
        cdef set seen_formats = self.seen_formats  # Local reference for speed
        cdef int i, len_formats = len(formats)

        # Try each format directly
        for i in range(len_formats):
            if formats[i] not in seen_formats:
                result = self.generate_formats(date_bytes, [formats[i]])
                if result:
                    return result
                seen_formats.add(formats[i])

        # Try precomputed formats with different separators
        for fmt in self.precomputed_formats:
            if fmt not in seen_formats:
                result = self.generate_formats(date_bytes, [fmt])
                if result:
                    return result
                seen_formats.add(fmt)
        return None

    cpdef str search(self, str date_string):
        cdef int i, j, len_date_formats, len_time_formats
        cdef str combined_format
        cdef str result

        if date_string in DateFormatFinder.successful_formats:
            cached_format = DateFormatFinder.successful_formats[date_string]
            # Verify that the cached format still works
            if self.generate_formats(date_string.encode('utf-8'), [cached_format]):
                return cached_format  # Return cached successful format
            # If not, remove the failed format from cache and continue
            del DateFormatFinder.successful_formats[date_string]
            DateFormatFinder.historical_formats.add(cached_format)  # Log failure to keep history

        if get_time_components(date_string):
            len_date_formats = len(self.date_formats)
            len_time_formats = len(self.time_formats)
            for i in range(len_date_formats):
                for j in range(len_time_formats):
                    for sep in self.separators:
                        combined_format = f"{self.date_formats[i].replace(self.old_sep, sep)} {self.time_formats[j]}"
                        result = self.generate_formats(date_string.encode('utf-8'), [combined_format])
                        if result:
                            DateFormatFinder.successful_formats[date_string] = combined_format
                            return combined_format
            raise ValueError("No matching format found for the given date string with time components.")

        result = self.try_formats(self.date_formats, date_string)
        if result:
            DateFormatFinder.successful_formats[date_string] = result
            return result

        result = self.try_formats(self.unique_formats, date_string)
        if result:
            DateFormatFinder.successful_formats[date_string] = result
            return result
        raise ValueError("No matching format found for the given date string.")

    @staticmethod
    def clear_cache():
        DateFormatFinder.successful_formats.clear()
        DateFormatFinder.historical_formats.clear()



__all__ = [
    "DateFormatFinder",
]










#────────── Python Code ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

# # Old
#------------------------------------------------
# import re
# from datetime import datetime
# 
# def anytime():
#     return re.compile(
#         r"(?<!\d)(\d{1,2}:\d{2}:\d{2}|\d{6})"
#         r"(?:\.\d{1,6})?"
#         r"(?:\s*[AP]M)?"
#         r"(?:\s*(?:[+-]\d{2}:?\d{2}|[+-]\d{4}|[A-Z]{3,4}|Z))?"
#         r"(?=\s|$)",
#         re.IGNORECASE
#     )
# 
# anytime_regex = anytime()
# 
# def get_time_components(datetime_string: str) -> bool:
#     """Return True if the date string appears to have time components."""
#     match = anytime_regex.search(datetime_string)
#     return match is not None
# 
# class dFormats:
#     """
#     Manages a collection of date and time format strings supported by the system.
#     """
#     def __init__(self):
#         self.num_dates = 19
#         self.num_times = 33
#         self.num_unique = 55
# 
#         # Define date formats
#         date_formats = [None] * self.num_dates
#         date_formats[0] = '%m/%d/%y'
#         date_formats[1] = '%B/%d/%Y'
#         date_formats[2] = '%Y/%B/%d'
#         date_formats[3] = '%y%m%d'
#         date_formats[4] = '%m/%d/%Y'
#         date_formats[5] = '%d/%m/%Y'
#         date_formats[6] = '%y/%m/%d'
#         date_formats[7] = '%d/%B/%Y'
#         date_formats[8] = '%Y/%b/%d'
#         date_formats[9] = '%b/%d/%Y'
#         date_formats[10] = '%Y/%m/%d'
#         date_formats[11] = '%Y%m%d'
#         date_formats[12] = '%d/%m/%y'
#         date_formats[13] = '%d/%b/%Y'
#         date_formats[14] = '%a, %b %d, %Y'
#         date_formats[15] = '%A, %B %d, %Y'
#         date_formats[16] = '%d/%B/%y'
#         date_formats[17] = '%B %d, %y'
#         date_formats[18] = '%d %B %y'
#         
#         # Define time formats
#         time_formats = [None] * self.num_times
#         time_formats[0] = '%H'
#         time_formats[1] = '%I'
#         time_formats[2] = '%H:%M'
#         time_formats[3] = '%H:%M:%S'
#         time_formats[4] = '%H:%M:%S:%f'
#         time_formats[5] = '%H:%M %p'
#         time_formats[6] = '%H:%M:%S %p'
#         time_formats[7] = '%H:%M:%S:%f %p'
#         time_formats[8] = '%I:%M'
#         time_formats[9] = '%I:%M %p'
#         time_formats[10] = '%I:%M:%S'
#         time_formats[11] = '%I:%M:%S %p'
#         time_formats[12] = '%I:%M:%S:%f'
#         time_formats[13] = '%I:%M:%S:%f %p'
#         time_formats[14] = '%H:%M:%S %z'
#         time_formats[15] = '%H:%M:%S %Z'
#         time_formats[16] = '%I:%M %p %z'
#         time_formats[17] = '%I:%M %p %Z'
#         time_formats[18] = '%H:%M:%S:%f %z'
#         time_formats[19] = '%H:%M:%S:%f %Z'
#         time_formats[20] = '%I:%M:%S %p %z'
#         time_formats[21] = '%I:%M:%S %p %Z'
#         time_formats[22] = '%H %p'
#         time_formats[23] = '%I %p'
#         time_formats[24] = '%H:%M:%S:%f %p %z'
#         time_formats[25] = '%H:%M:%S:%f %p %Z'
#         time_formats[26] = '%I:%M:%S:%f %p %z'
#         time_formats[27] = '%I:%M:%S:%f %p %Z'
#         time_formats[28] = '%H%M%S'
#         time_formats[29] = '%H:%M:%S%z'
#         time_formats[30] = '%H:%M:%SZ'
#         time_formats[31] = '%H:%M:%S.%f'
#         time_formats[32] = '%H:%M:%S.%f%z'
#         
#         # Define unique formats
#         unique_formats = [None] * self.num_unique
#         unique_formats[0] = '%A the %dth of %B, %Y'
#         unique_formats[1] = '%A'
#         unique_formats[2] = '%a'
#         unique_formats[3] = '%A, %d %B %Y'
#         unique_formats[4] = '%Y, %b %d'
#         unique_formats[5] = '%B %d'
#         unique_formats[6] = '%B %d, %Y'
#         unique_formats[7] = '%b %d, %Y'
#         unique_formats[8] = '%b'
#         unique_formats[9] = '%B'
#         unique_formats[10] = '%B, %Y'
#         unique_formats[11] = '%b. %d, %Y'
#         unique_formats[12] = '%d %B'
#         unique_formats[13] = '%d %B, %Y'
#         unique_formats[14] = '%d of %B, %Y'
#         unique_formats[15] = '%d-%b-%y'
#         unique_formats[16] = '%d'
#         unique_formats[17] = '%dth %B %Y'
#         unique_formats[18] = '%dth of %B %Y'
#         unique_formats[19] = '%dth of %B, %Y'
#         unique_formats[20] = '%H'
#         unique_formats[21] = '%I'
#         unique_formats[22] = '%m-%Y-%d'
#         unique_formats[23] = '%m-%Y'
#         unique_formats[24] = '%m'
#         unique_formats[25] = '%M'
#         unique_formats[26] = '%m/%Y'
#         unique_formats[27] = '%m/%Y/%d'
#         unique_formats[28] = '%Y %B'
#         unique_formats[29] = '%Y Q%q'
#         unique_formats[30] = '%Y-%j'
#         unique_formats[31] = '%Y-%m'
#         unique_formats[32] = '%y'
#         unique_formats[33] = '%Y'
#         unique_formats[34] = '%Y, %B %d'
#         unique_formats[35] = '%Y.%m'
#         unique_formats[36] = '%Y/%m'
#         unique_formats[37] = '%Y-W%U-%w'
#         unique_formats[38] = '%Y-W%V-%u'
#         unique_formats[39] = '%a, %d %b %Y'
#         unique_formats[40] = '%b %d %y'
#         unique_formats[41] = '%b-%d-%y'
#         unique_formats[42] = '%b-%Y-%d'
#         unique_formats[43] = '%b.%Y-%d'
#         unique_formats[44] = '%d %b, %Y'
#         unique_formats[45] = '%d %B, %y'
#         unique_formats[46] = '%d-%Y.%m'
#         unique_formats[47] = '%d-%Y/%m'
#         unique_formats[48] = '%d.%Y-%m'
#         unique_formats[49] = '%d/%Y-%m'
#         unique_formats[50] = '%d/%Y.%m'
#         unique_formats[51] = '%m.%Y-%d'
#         unique_formats[52] = '%m.%Y/%d'
#         unique_formats[53] = '%m/%Y-%d'
#         unique_formats[54] = 'on %B %d, %Y'
# 
#         self.dates = date_formats
#         self.times = time_formats
#         self.unique = unique_formats
# 
#     def Unique(self):
#         return self.unique
# 
#     def Dates(self):
#         return self.dates
# 
#     def Times(self):
#         return self.times
# 
# class DateFormatFinder:
#     successful_formats = {}  # Shared cache for successful formats
#     historical_formats = set()  # Keep a record of all formats that were ever successful
# 
#     def __init__(self, old_sep='/'):
#         self.formats = dFormats()
#         self.date_formats = self.formats.Dates()
#         self.time_formats = self.formats.Times()
#         self.unique_formats = self.formats.Unique()
#         self.separators = ['/', '.', '-', ' ', '']
#         self.old_sep = old_sep
#         self.seen_formats = set()
#         self.precomputed_formats = self._precompute_formats()
# 
#     def _precompute_formats(self):
#         precomputed = []
#         all_formats = self.date_formats + self.unique_formats
#         for fmt in all_formats:
#             precomputed.append(fmt)
#             for sep in self.separators:
#                 new_format = fmt.replace(self.old_sep, sep)
#                 if new_format not in precomputed:
#                     precomputed.append(new_format)
#         return precomputed
# 
#     def generate_formats(self, date_string: str, datetime_formats):
#         """Try to parse date_string using each format in datetime_formats.
#            Return the first matching format, or None if none match.
#         """
#         for fmt in datetime_formats:
#             try:
#                 datetime.strptime(date_string, fmt)
#                 DateFormatFinder.historical_formats.add(fmt)  # Log successful format
#                 return fmt
#             except ValueError:
#                 continue
#         return None
# 
#     def try_formats(self, formats, date_string: str):
#         # Try each format directly
#         for fmt in formats:
#             if fmt not in self.seen_formats:
#                 result = self.generate_formats(date_string, [fmt])
#                 if result:
#                     return result
#                 self.seen_formats.add(fmt)
# 
#         # Try precomputed formats with different separators
#         for fmt in self.precomputed_formats:
#             if fmt not in self.seen_formats:
#                 result = self.generate_formats(date_string, [fmt])
#                 if result:
#                     return result
#                 self.seen_formats.add(fmt)
#         return None
# 
#     def search(self, date_string: str) -> str:
#         # Check for a cached format
#         if date_string in DateFormatFinder.successful_formats:
#             cached_format = DateFormatFinder.successful_formats[date_string]
#             # Verify that the cached format still works
#             if self.generate_formats(date_string, [cached_format]):
#                 return cached_format
#             # If not, remove the failed format from cache and continue
#             del DateFormatFinder.successful_formats[date_string]
#             DateFormatFinder.historical_formats.add(cached_format)
# 
#         # If the string contains time components, try combined date and time formats
#         if get_time_components(date_string):
#             for d_fmt in self.date_formats:
#                 for t_fmt in self.time_formats:
#                     for sep in self.separators:
#                         combined_format = f"{d_fmt.replace(self.old_sep, sep)} {t_fmt}"
#                         result = self.generate_formats(date_string, [combined_format])
#                         if result:
#                             DateFormatFinder.successful_formats[date_string] = combined_format
#                             return combined_format
#             raise ValueError("No matching format found for the given date string with time components.")
# 
#         # Try date formats first
#         result = self.try_formats(self.date_formats, date_string)
#         if result:
#             DateFormatFinder.successful_formats[date_string] = result
#             return result
# 
#         # Then try unique formats
#         result = self.try_formats(self.unique_formats, date_string)
#         if result:
#             DateFormatFinder.successful_formats[date_string] = result
#             return result
# 
#         raise ValueError("No matching format found for the given date string.")
# 
#     @staticmethod
#     def clear_cache():
#         DateFormatFinder.successful_formats.clear()
#         DateFormatFinder.historical_formats.clear()
# 
# __all__ = [
#     "DateFormatFinder",
# ]
# 
# 
# 
# 
# # x = DateFormatFinder()
# # 
# # x.search("2024-01-01")







# # New
#------------------------------------------------
# import re
# from datetime import datetime
# 
# def remove_ordinal_suffixes(date_string):
#     """
#     Remove ordinal suffixes (st, nd, rd, th) from day numbers.
#     e.g. "May 14th, 2022" becomes "May 14, 2022"
#     """
#     return re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_string, flags=re.IGNORECASE)
#    
# def anytime():
#     return re.compile(
#         r"(?<!\d)((?:\d{1,2}:\d{2}(?::\d{2})?|\d{6})"
#         r"(?:\.\d{1,6})?"
#         r"(?:\s*[AP]M)?)"  
#         r"(?:\s*(?:[+-]\d{2}:?\d{2}|[+-]\d{4}|[A-Z]{3,4}|Z))?"
#         r"(?=\s|$)",
#         re.IGNORECASE
#     )
#     
# anytime_regex = anytime()
# 
# def get_time_components(datetime_string):
#     """Return True if the date string appears to have time components."""
#     match = anytime_regex.search(datetime_string)
#     return match is not None
# 
# class dFormats:
#     """
#     Manages a collection of date and time format strings supported by the system.
#     """
#     def __init__(self):
#         self.num_dates = 19
#         self.num_times = 33
#         self.num_unique = 56
# 
#         # Define date formats
#         date_formats = [None] * self.num_dates
#         date_formats[0] = '%m/%d/%y'
#         date_formats[1] = '%B/%d/%Y'
#         date_formats[2] = '%Y/%B/%d'
#         date_formats[3] = '%y%m%d'
#         date_formats[4] = '%m/%d/%Y'
#         date_formats[5] = '%d/%m/%Y'
#         date_formats[6] = '%y/%m/%d'
#         date_formats[7] = '%d/%B/%Y'
#         date_formats[8] = '%Y/%b/%d'
#         date_formats[9] = '%b/%d/%Y'
#         date_formats[10] = '%Y/%m/%d'
#         date_formats[11] = '%Y%m%d'
#         date_formats[12] = '%d/%m/%y'
#         date_formats[13] = '%d/%b/%Y'
#         date_formats[14] = '%a, %b %d, %Y'
#         date_formats[15] = '%A, %B %d, %Y'
#         date_formats[16] = '%d/%B/%y'
#         date_formats[17] = '%B %d, %y'
#         date_formats[18] = '%d %B %y'
# 
#         # Define time formats
#         time_formats = [None] * self.num_times
#         time_formats[0] = '%H'
#         time_formats[1] = '%I'
#         time_formats[2] = '%H:%M'
#         time_formats[3] = '%H:%M:%S'
#         time_formats[4] = '%H:%M:%S:%f'
#         time_formats[5] = '%H:%M %p'
#         time_formats[6] = '%H:%M:%S %p'
#         time_formats[7] = '%H:%M:%S:%f %p'
#         time_formats[8] = '%I:%M'
#         time_formats[9] = '%I:%M %p'
#         time_formats[10] = '%I:%M:%S'
#         time_formats[11] = '%I:%M:%S %p'
#         time_formats[12] = '%I:%M:%S:%f'
#         time_formats[13] = '%I:%M:%S:%f %p'
#         time_formats[14] = '%H:%M:%S %z'
#         time_formats[15] = '%H:%M:%S %Z'
#         time_formats[16] = '%I:%M %p %z'
#         time_formats[17] = '%I:%M %p %Z'
#         time_formats[18] = '%H:%M:%S:%f %z'
#         time_formats[19] = '%H:%M:%S:%f %Z'
#         time_formats[20] = '%I:%M:%S %p %z'
#         time_formats[21] = '%I:%M:%S %p %Z'
#         time_formats[22] = '%H %p'
#         time_formats[23] = '%I %p'
#         time_formats[24] = '%H:%M:%S:%f %p %z'
#         time_formats[25] = '%H:%M:%S:%f %p %Z'
#         time_formats[26] = '%I:%M:%S:%f %p %z'
#         time_formats[27] = '%I:%M:%S:%f %p %Z'
#         time_formats[28] = '%H%M%S'
#         time_formats[29] = '%H:%M:%S%z'
#         time_formats[30] = '%H:%M:%SZ'
#         time_formats[31] = '%H:%M:%S.%f'
#         time_formats[32] = '%H:%M:%S.%f%z'
# 
#         # Define unique formats
#         unique_formats = [None] * self.num_unique
#         unique_formats[0] = '%A the %dth of %B, %Y'
#         unique_formats[1] = '%A'
#         unique_formats[2] = '%a'
#         unique_formats[3] = '%A, %d %B %Y'
#         unique_formats[4] = '%Y, %b %d'
#         unique_formats[5] = '%B %d'
#         unique_formats[6] = '%B %d, %Y'
#         unique_formats[7] = '%b %d, %Y'
#         unique_formats[8] = '%b'
#         unique_formats[9] = '%B'
#         unique_formats[10] = '%B, %Y'
#         unique_formats[11] = '%b. %d, %Y'
#         unique_formats[12] = '%d %B'
#         unique_formats[13] = '%d %B, %Y'
#         unique_formats[14] = '%d of %B, %Y'
#         unique_formats[15] = '%d-%b-%y'
#         unique_formats[16] = '%d'
#         unique_formats[17] = '%dth %B %Y'
#         unique_formats[18] = '%dth of %B %Y'
#         unique_formats[19] = '%dth of %B, %Y'
#         unique_formats[20] = '%H'
#         unique_formats[21] = '%I'
#         unique_formats[22] = '%m-%Y-%d'
#         unique_formats[23] = '%m-%Y'
#         unique_formats[24] = '%m'
#         unique_formats[25] = '%M'
#         unique_formats[26] = '%m/%Y'
#         unique_formats[27] = '%m/%Y/%d'
#         unique_formats[28] = '%Y %B'
#         unique_formats[29] = '%Y Q%q'
#         unique_formats[30] = '%Y-%j'
#         unique_formats[31] = '%Y-%m'
#         unique_formats[32] = '%y'
#         unique_formats[33] = '%Y'
#         unique_formats[34] = '%Y, %B %d'
#         unique_formats[35] = '%Y.%m'
#         unique_formats[36] = '%Y/%m'
#         unique_formats[37] = '%Y-W%U-%w'
#         unique_formats[38] = '%Y-W%V-%u'
#         unique_formats[39] = '%a, %d %b %Y'
#         unique_formats[40] = '%b %d %y'
#         unique_formats[41] = '%b-%d-%y'
#         unique_formats[42] = '%b-%Y-%d'
#         unique_formats[43] = '%b.%Y-%d'
#         unique_formats[44] = '%d %b, %Y'
#         unique_formats[45] = '%d %B, %y'
#         unique_formats[46] = '%d-%Y.%m'
#         unique_formats[47] = '%d-%Y/%m'
#         unique_formats[48] = '%d.%Y-%m'
#         unique_formats[49] = '%d/%Y-%m'
#         unique_formats[50] = '%d/%Y.%m'
#         unique_formats[51] = '%m.%Y-%d'
#         unique_formats[52] = '%m.%Y/%d'
#         unique_formats[53] = '%m/%Y-%d'
#         unique_formats[54] = 'on %B %d, %Y'
#         unique_formats[55] = '%B %dth, %Y'        
# 
#         self.dates = date_formats
#         self.times = time_formats
#         self.unique = unique_formats
# 
#     def Unique(self):
#         return self.unique
# 
#     def Dates(self):
#         return self.dates
# 
#     def Times(self):
#         return self.times
# 
# 
# class DateFormatFinder:
#     successful_formats = {}  # Cache for successful formats across full strings
#     historical_formats = set()  # Record of all formats that were ever successful
# 
#     def __init__(self, old_sep='/'):
#         self.formats = dFormats()
#         self.date_formats = self.formats.Dates()
#         self.time_formats = self.formats.Times()
#         self.unique_formats = self.formats.Unique()
#         self.separators = ['/', '.', '-', ' ', '']
#         self.old_sep = old_sep
#         self.precomputed_formats = self._precompute_formats()
# 
#     def _precompute_formats(self):
#         precomputed = []
#         all_formats = self.date_formats + self.unique_formats
#         for fmt in all_formats:
#             precomputed.append(fmt)
#             for sep in self.separators:
#                 new_format = fmt.replace(self.old_sep, sep)
#                 if new_format not in precomputed:
#                     precomputed.append(new_format)
#         return precomputed
# 
#     def generate_formats(self, date_str, candidate_formats):
#         for fmt in candidate_formats:
#             try:
#                 datetime.strptime(date_str, fmt)
#                 return fmt
#             except ValueError:
#                 continue
#         return None
# 
#     def try_formats(self, formats, substring, local_seen):
#         for fmt in formats:
#             if (fmt, substring) in local_seen:
#                 continue
#             result = self.generate_formats(substring, [fmt])
#             local_seen.add((fmt, substring))
#             if result:
#                 return result
#         for fmt in self.precomputed_formats:
#             if (fmt, substring) in local_seen:
#                 continue
#             result = self.generate_formats(substring, [fmt])
#             local_seen.add((fmt, substring))
#             if result:
#                 return result
#         return None
# 
#     def search(self, date_string):
#         # Preprocess: remove ordinal suffixes
#         date_string = remove_ordinal_suffixes(date_string)
#     	
#         if date_string in DateFormatFinder.successful_formats:
#             cached_format, cached_date, cached_time = DateFormatFinder.successful_formats[date_string]
#             if self.generate_formats(date_string, [cached_format]):
#                 return cached_format
#             del DateFormatFinder.successful_formats[date_string]
#             DateFormatFinder.historical_formats.add(cached_format)
# 
#         if get_time_components(date_string):
#             date_only = anytime_regex.sub("", date_string).strip()
#             time_matches = [match.group(0) for match in anytime_regex.finditer(date_string)]
#             time_string = " ".join(time_matches).strip()
# 
#             local_seen_date = set()
#             local_seen_time = set()
# 
#             date_format = self.try_formats(self.date_formats, date_only, local_seen_date)
#             if not date_format:
#                 date_format = self.try_formats(self.unique_formats, date_only, local_seen_date)
#             if not date_format:
#                 raise ValueError("No matching date format found for the date part.")
# 
#             # If the time string has an AM/PM marker, restrict to formats with %I.
#             if re.search(r'(?i)\b(?:AM|PM)\b', time_string):
#                 candidate_time_formats = [fmt for fmt in self.time_formats if '%p' in fmt and '%I' in fmt]
#             else:
#                 candidate_time_formats = self.time_formats
# 
#             # Additional filtering: if a timezone abbreviation is present,
#             # restrict to formats that include a timezone specifier (%Z or %z).
#             if re.search(r'(?i)\b(?:[A-Z]{2,4}|Z)\b', time_string):
#                 candidate_time_formats = [fmt for fmt in candidate_time_formats if '%Z' in fmt or '%z' in fmt]
# 
#             time_format = self.try_formats(candidate_time_formats, time_string, local_seen_time)
#             if not time_format:
#                 raise ValueError("No matching time format found for the time part.")
# 
#             combined_format = f"{date_format} {time_format}"
#             if self.generate_formats(date_string, [combined_format]):
#                 DateFormatFinder.successful_formats[date_string] = (combined_format, date_only, time_string)
#                 return combined_format
#             else:
#                 raise ValueError("Combined format failed to parse the input string with time components.")
# 
#         local_seen = set()
#         result = self.try_formats(self.date_formats, date_string, local_seen)
#         if result:
#             DateFormatFinder.successful_formats[date_string] = (result, date_string, None)
#             return result
#         result = self.try_formats(self.unique_formats, date_string, local_seen)
#         if result:
#             DateFormatFinder.successful_formats[date_string] = (result, date_string, None)
#             return result
# 
#         raise ValueError("No matching format found for the given date string.")
# 
#     @staticmethod
#     def clear_cache():
#         DateFormatFinder.successful_formats.clear()
#         DateFormatFinder.historical_formats.clear()
