#include <stdio.h>
#include <string.h>

/**
 * @brief Replaces the 'Z' suffix in a datetime string with '+00:00'.
 *
 * This function checks if the given datetime string ends with the 'Z' character,
 * which indicates Zulu time (UTC). If it does, the function replaces the 'Z' with '+00:00'.
 *
 * @param datetime_string A pointer to the datetime string to be modified. It is assumed that the string
 *                        is null-terminated and has enough space to accommodate the additional characters.
 */
void replace_zulu_suffix_with_utc(char *datetime_string) {
    int length = strlen(datetime_string);
    if (datetime_string[length - 1] == 'Z') {
        datetime_string[length - 1] = '\0'; // Remove 'Z'
        strcat(datetime_string, "+00:00");  // Append '+00:00'
    }
}