cdef extern from "iso8601z.h":
    void replace_zulu_suffix_with_utc(char *datetime_string)

cpdef str replaceZ(str datetime_string):
    cdef bytes datetime_bytes = datetime_string.encode('utf-8')
    cdef char *datetime_cstring = datetime_bytes

    replace_zulu_suffix_with_utc(datetime_cstring)

    return datetime_cstring.decode('utf-8')
