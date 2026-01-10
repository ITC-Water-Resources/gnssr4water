from position cimport _enu_position
from gnssir cimport _gnss_system
from stream cimport gnssrstream

cdef extern from "../src/nmea.h" nogil:
    #import the #define NMEA_GSV_MAX_SATELLITES in a constant for later use in cython.view.array's
    cdef const int NMEA_GSV_MAX_SATELLITES

    struct _nmea_cycle "nmea_cycle":
        double mjd,
        char status,
        _enu_position site,
        int sats_in_view,
        #note arrays are declared with size 1 but since they are extern,
        #they actually have size NMEA_GSV_MAX_SATELLITES (but cython won't eat the #define from nmea.h)
        _gnss_system system[1],
        int prn[1],
        float elevation[1],
        float azimuth[1],
        float cnr0[1]
    
    struct _nmea_trans_cycle "nmea_trans_cycle":
        double mjd[2],
        # int year[2],
        # int month[2],
        # int day[2],
        # int hr[2],
        # int min[2],
        # float sec[2],
        _enu_position sites[2],
        # float lat[2],
        # float lon[2],
        # float ortho_height[2],
        # float geoid_height[2],
        int sats_in_view,
        _gnss_system system[1],
        int prn[1],
        float elevation[1],
        float azimuth[1],
        float cnr0[2][1],
        float gamma[1]	

    cpdef enum nmea_type:
        NMEA_GGA,
        NMEA_GSV,
        NMEA_GLL,
        NMEA_GSA,
        NMEA_RMC,
        NMEA_VTG,
        NMEA_GNS,
        NMEA_UNSUPPORTED,
        NMEA_INVALID
    
    unsigned char calculate_checksum(const char * nmea)
    nmea_type check_nmea(char * nmea) 
    int read_nmea_cycle(gnssrstream *sid, _nmea_cycle * data);
    int init_nmea_cycle(_nmea_cycle * data)
    int init_nmea_trans_cycle(_nmea_trans_cycle * data)

    int pair_nmea_trans_cycle(const _nmea_cycle * c_clear,const _nmea_cycle * c_obstr , int delta_sec, _nmea_trans_cycle * tc_out)

