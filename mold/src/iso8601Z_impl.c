#include <stdio.h>
#include <string.h>
#include "iso8601Z.h"

/**
 * @brief Replaces the 'Z' suffix in a datetime string with '+00:00'.
 *
 * This function checks if the given datetime string ends with the 'Z' character,
 * which indicates Zulu time (UTC). If it does, the function replaces the 'Z' with '+00:00'.
 *
 * @param datetime_string A writable, null-terminated string.
 * @param capacity Size of its allocated buffer, including the terminator.
 * @return 0 on success/no replacement, -1 if the replacement will not fit.
 */
int replace_zulu_suffix_with_utc(char *datetime_string, size_t capacity) {
    size_t length = strlen(datetime_string);
    if (length > 0 && datetime_string[length - 1] == 'Z') {
        if (capacity < length + 6) return -1;
        datetime_string[length - 1] = '\0'; // Remove 'Z'
        strcat(datetime_string, "+00:00");  // Append '+00:00'
    }
    return 0;
}
