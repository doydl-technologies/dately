cdef extern from "clean_str.h":
    void clean_string(const char* input, char* output)

def cleanstr(input_string):
    cdef bytes input_bytes = input_string.encode('utf-8')  # Keeps the backing buffer alive.
    cdef const char* input_c = input_bytes
    cdef char output_c[150]  # Sized for the maximum input accepted by the C helper.
    clean_string(input_c, output_c)
    return output_c.decode('utf-8')
