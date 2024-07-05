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
@cython.boundscheck(False)
@cython.wraparound(False)
cpdef object anytime():
    return re.compile(
        r"(?<!\d)(\d{1,2}:\d{2}:\d{2}|\d{6})"
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
