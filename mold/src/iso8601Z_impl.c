#include <stdio.h>
#include <string.h>

void replace_zulu_suffix_with_utc(char *datetime_string) {
    int length = strlen(datetime_string);
    if (datetime_string[length - 1] == 'Z') {
        datetime_string[length - 1] = '\0'; // Remove 'Z'
        strcat(datetime_string, "+00:00");  // Append '+00:00'
    }
}
