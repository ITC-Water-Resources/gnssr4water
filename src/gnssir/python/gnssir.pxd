
cdef extern from "../src/gnssir.h" nogil:
    cdef struct _gnss_system "gnss_system":
        char * system,
        char * rinexcode,
        double frequency,
        double length,
        double bandwidth
    # cdef void init_GNSS(_gnss_system * system, const char * sysname)
    cdef _gnss_system gnss_gpsl1
    cdef _gnss_system gnss_gpsl2
    cdef _gnss_system gnss_glonassiil1
    cdef _gnss_system gnss_unknown
    cdef void copy_GNSS_as(_gnss_system *sys, const _gnss_system * sysfrom)
