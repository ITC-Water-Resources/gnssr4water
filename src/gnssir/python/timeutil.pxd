
cdef extern from "../src/timeutil.h" nogil:
    cdef double mjd(const int year, const int month, const int day,const int hour, const int minute, const double second)
    cdef void mjd_to_datetime(double mjd, int *year,int * month, int * day, int * hour,int * minute, double * second) 
