// time_zones.h
#ifndef TIME_ZONES_H
#define TIME_ZONES_H

typedef struct {
    char full_name[50];
    char region[50];
    char offset[11];
    char type[10];
    char dst[7];
} TimeZoneInfo;

typedef struct {
    char code[7];
    TimeZoneInfo info;
} TimeZone;

extern TimeZone time_zones[];
extern int time_zones_count;

#endif // TIME_ZONES_H
