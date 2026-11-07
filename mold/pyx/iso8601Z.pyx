from cpython.mem cimport PyMem_Malloc, PyMem_Free
from libc.string cimport memcpy
from libc.stddef cimport size_t

cdef extern from "iso8601Z.h":
    int replace_zulu_suffix_with_utc(char *datetime_string, size_t capacity)

cpdef str replaceZ(str datetime_string):
    cdef bytes datetime_bytes = datetime_string.encode('utf-8')
    cdef size_t length = len(datetime_bytes)
    cdef size_t capacity = length + 6  # replacement adds five bytes, plus NUL
    cdef char* output = <char*>PyMem_Malloc(capacity)
    if output == NULL:
        raise MemoryError()
    try:
        memcpy(output, <const char*>datetime_bytes, length)
        output[length] = 0
        if replace_zulu_suffix_with_utc(output, capacity) != 0:
            raise ValueError("Insufficient capacity for UTC suffix")
        return output.decode('utf-8')
    finally:
        PyMem_Free(output)
