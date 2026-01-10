
cdef extern from "../src/position.h" nogil:
    cdef struct _enu_position "enu_position":
        float lat,
        float lon,
        float ortho_height,
        float geoid_height,
        double mjd
    cdef int init_enu_position(_enu_position *data)
    cdef int copy_enu_position(const _enu_position *indata, _enu_position * outdata)
    cdef int set_enu_position(_enu_position * data,float lat,float lon, float ortho_height, float geoid_height,double mjd)
