#ifndef ISO8601T_H
#define ISO8601T_H

int is_leap_year(int year);
int validate_date(int year, int month, int day);
int validate_time(int hour, int minute, int second);
int is_digit(char c);
int check_basic_format(const char* date_string);
int check_extended_format(const char* date_string);
int find_date_match(const char* date_string);

#endif // ISO8601T_H
