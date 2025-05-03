# time_zones.pyx
cdef extern from "time_zones.h":
    ctypedef struct TimeZoneInfo:
        char full_name[50]
        char region[50]
        char offset[11]
        char type[10]
        char dst[7]

    ctypedef struct TimeZone:
        char code[7]
        TimeZoneInfo info

    extern TimeZone time_zones[]
    extern int time_zones_count

cdef dict get_time_zones_impl():
    cdef dict result = {}
    cdef int i
    cdef TimeZone tz
    for i in range(time_zones_count):
        tz = time_zones[i]
        result[tz.code.decode('utf-8')] = {
            "full_name": tz.info.full_name.decode('utf-8'),
            "region": tz.info.region.decode('utf-8'),
            "offset": tz.info.offset.decode('utf-8'),
            "type": tz.info.type.decode('utf-8'),
            "dst": tz.info.dst.decode('utf-8')
        }
    return result

cpdef dict get_time_zones():
    return get_time_zones_impl()
   
# Assign dict
time_zones_dict = get_time_zones()

# Define public interface
__all__ = [
    'time_zones_dict'
]