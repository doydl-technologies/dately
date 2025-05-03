# clean_str.pyx
cdef extern from "clean_str.h":
    void clean_string(const char* input, char* output)

def cleanstr(input_string):
    cdef bytes input_bytes = input_string.encode('utf-8')  # Ensure the bytes object persists
    cdef const char* input_c = input_bytes  # Safe cast to a C string
    cdef char output_c[150]  # Adjust the size based on expected input lengths
    clean_string(input_c, output_c)
    return output_c.decode('utf-8')
