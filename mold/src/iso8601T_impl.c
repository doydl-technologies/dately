#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdlib.h>

int is_leap_year(int year) {
    return (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0));
}

// Validate the date
int validate_date(int year, int month, int day) {
    if (month < 1 || month > 12) return 0;  // Validates month range

    int days_in_month[] = {31, 28 + is_leap_year(year), 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    if (day < 1 || day > days_in_month[month - 1]) return 0;  // Validates day range considering leap years

    return 1;
}

// Validate the time
int validate_time(int hour, int minute, int second) {
    if (hour < 0 || hour > 23) return 0;  // Validates hour range
    if (minute < 0 || minute > 59) return 0;  // Validates minute range
    if (second < 0 || second > 59) return 0;  // Validates second range

    return 1;
}

int is_digit(char c) {
    return c >= '0' && c <= '9';
}

int check_basic_format(const char* date_string) {
    // Check basic date-time format: YYYYMMDDTHHMMSS
    if (strlen(date_string) < 15) return 0; // Minimum length check
    
    char year_str[5], month_str[3], day_str[3], hour_str[3], minute_str[3], second_str[3];
    
    // Extract date components
    strncpy(year_str, date_string, 4); year_str[4] = '\0';
    strncpy(month_str, date_string + 4, 2); month_str[2] = '\0';
    strncpy(day_str, date_string + 6, 2); day_str[2] = '\0';
    if (date_string[8] != 'T') return 0;
    strncpy(hour_str, date_string + 9, 2); hour_str[2] = '\0';
    strncpy(minute_str, date_string + 11, 2); minute_str[2] = '\0';
    strncpy(second_str, date_string + 13, 2); second_str[2] = '\0';

    // Convert to integers
    int year = atoi(year_str), month = atoi(month_str), day = atoi(day_str);
    int hour = atoi(hour_str), minute = atoi(minute_str), second = atoi(second_str);

    // Validate date and time
    if (!validate_date(year, month, day) || !validate_time(hour, minute, second)) return 0;

    // Handle optional parts like .SSS and Z or +HHMM
    int index = 15;
    if (date_string[index] == '.') {
        index += 4; // Skip milliseconds
    }
    if (date_string[index] == 'Z' || date_string[index] == '+' || date_string[index] == '-') {
        index += (date_string[index] == 'Z' ? 1 : 5); // Skip timezone
    }

    return index == strlen(date_string);
}

int check_extended_format(const char* date_string) {
    // Check extended date-time format: YYYY-MM-DDTHH:MM[:SS[.SSS]]
    // Optional: .SSS and Z or +HH:MM
    int len = strlen(date_string);
    if (len < 16) return 0; // Minimum length check for truncated format (YYYY-MM-DDTHH:MMZ)

    // Validate the date part
    for (int i = 0; i < 4; ++i) {
        if (!is_digit(date_string[i])) return 0;
    }
    if (date_string[4] != '-') return 0;
    for (int i = 5; i < 7; ++i) {
        if (!is_digit(date_string[i])) return 0;
    }
    if (date_string[7] != '-') return 0;
    for (int i = 8; i < 10; ++i) {
        if (!is_digit(date_string[i])) return 0;
    }
    if (date_string[10] != 'T') return 0;
    for (int i = 11; i < 13; ++i) {
        if (!is_digit(date_string[i])) return 0;
    }
    if (date_string[13] != ':') return 0;
    for (int i = 14; i < 16; ++i) {
        if (!is_digit(date_string[i])) return 0;
    }

    // Convert to integers for validation
    char year_str[5], month_str[3], day_str[3], hour_str[3], minute_str[3];
    strncpy(year_str, date_string, 4); year_str[4] = '\0';
    strncpy(month_str, date_string + 5, 2); month_str[2] = '\0';
    strncpy(day_str, date_string + 8, 2); day_str[2] = '\0';
    strncpy(hour_str, date_string + 11, 2); hour_str[2] = '\0';
    strncpy(minute_str, date_string + 14, 2); minute_str[2] = '\0';

    int year = atoi(year_str), month = atoi(month_str), day = atoi(day_str);
    int hour = atoi(hour_str), minute = atoi(minute_str);

    // Validate date
    if (!validate_date(year, month, day)) return 0;

    int index = 16;

    // Check for seconds part
    int second = 0;
    if (date_string[index] == ':') {
        if (len < 19) return 0;
        for (int i = 17; i < 19; ++i) {
            if (!is_digit(date_string[i])) return 0;
        }
        char second_str[3];
        strncpy(second_str, date_string + 17, 2); second_str[2] = '\0';
        second = atoi(second_str);
        if (!validate_time(hour, minute, second)) return 0;
        index = 19;

        // Check for fractional seconds
        if (date_string[index] == '.') {
            index++;
            while (is_digit(date_string[index])) {
                index++;
            }
        }
    } else if (!validate_time(hour, minute, second)) {
        return 0;
    }

    // Check for timezone designator
    if (date_string[index] == 'Z') {
        index += 1;
    } else if (date_string[index] == '+' || date_string[index] == '-') {
        if (is_digit(date_string[index + 1]) && is_digit(date_string[index + 2]) &&
            date_string[index + 3] == ':' && is_digit(date_string[index + 4]) &&
            is_digit(date_string[index + 5])) {
            index += 6;
        } else {
            return 0;
        }
    }

    return index == len;
}



int find_date_match(const char* date_string) {
    if (strchr(date_string, 'T')) {
        if (check_basic_format(date_string) || check_extended_format(date_string)) {
            return 1;
        }
    }
    return 0;
}

