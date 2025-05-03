cdef extern from "iso8601z.h":
    void replace_zulu_suffix_with_utc(char *datetime_string)

cpdef str replaceZ(str datetime_string):
    cdef bytes datetime_bytes = datetime_string.encode('utf-8')
    cdef char *datetime_cstring = datetime_bytes

    # Call the C function
    replace_zulu_suffix_with_utc(datetime_cstring)
    
    # Convert the C string back to a Python string
    return datetime_cstring.decode('utf-8')