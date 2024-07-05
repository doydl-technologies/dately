// clean_str.c
#include <stdio.h>
#include <ctype.h>
#include <string.h>

void clean_string(const char* input, char* output) {
    int i = 0, j = 0;
    int in_space = 0;

    // Skip leading whitespace
    while (isspace(input[i])) {
        i++;
    }

    // Copy characters to output
    for (; input[i] != '\0'; i++) {
        if (isspace(input[i])) {
            if (!in_space) {
                output[j++] = ' ';
                in_space = 1;
            }
        } else {
            output[j++] = input[i];
            in_space = 0;
        }
    }

    // Remove trailing space if exists
    if (j > 0 && output[j - 1] == ' ') {
        j--;
    }

    // Null-terminate the output string
    output[j] = '\0';
}
