from cpython.mem cimport PyMem_Malloc, PyMem_Free
from libc.stddef cimport size_t

cdef extern from "clean_str.h":
    void clean_string(const char* input, char* output, size_t output_size)

def cleanstr(input_string):
    # Unicode whitespace is defined by Python, not the host C locale. Keep the
    # bounded native fast path for ASCII inputs.
    if not input_string.isascii():
        return ' '.join(input_string.split())
    cdef bytes input_bytes = input_string.encode('utf-8')
    cdef const char* input_c = input_bytes
    cdef size_t capacity = len(input_bytes) + 1
    cdef char* output_c = <char*>PyMem_Malloc(capacity)
    if output_c == NULL:
        raise MemoryError()
    try:
        clean_string(input_c, output_c, capacity)
        return output_c.decode('utf-8')
    finally:
        PyMem_Free(output_c)
