from position cimport _enu_position
from gnssir cimport _gnss_system

cdef extern from "../src/arcs.h" nogil:
    struct _arc "arc":
        size_t len,
        _gnss_system system,
        int prn,
        # int year,
        # int month,
        # int day,
        # int hr,
        # int min,
        # float sec,
        _enu_position site,
        # float lat,
        # float lon,
        # float ortho_height,
        # float geoid_height,
        double * mjd,
        float * elevation,
        float * azimuth,
        float * values

    int init_arc(_arc * data)
    int free_arc(_arc* data)
    int append_to_arc(_arc *data,double mjd, float elevation,float azimuth,float value)
