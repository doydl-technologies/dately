cdef extern from "iso8601T.h":
    int find_date_match(const char* date_string)

cpdef bint isISOT(str date_string):
    return find_date_match(date_string.encode('utf-8')) != 0
