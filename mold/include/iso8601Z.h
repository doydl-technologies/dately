#ifndef ISO8601Z_H
#define ISO8601Z_H
#include <stddef.h>

int replace_zulu_suffix_with_utc(char *datetime_string, size_t capacity);

#endif // ISO8601Z_H
