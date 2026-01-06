# This file is part of gnssr4water
# gnssr4water is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.

# gnssr4water is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with gnssr4water if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2025

# distutils: language = c
# cython: profile=False

from cython.operator cimport dereference as deref
from libc.stdlib cimport malloc, free
from datetime import datetime,timedelta
import numpy as np
from cython.view cimport array as cvarray

cdef extern from "src/stream.h" nogil:
    cdef const int _GNSSR_SUCCESS "GNSSR_SUCCESS"
    cdef const int _GNSSR_IO_ERROR "GNSSR_IO_ERROR"
    cdef const int _GNSSR_EOF "GNSSR_EOF"
    struct gnssrstream:
        pass
    int open_stream(const char * filename, gnssrstream* gz)
    void close_stream(gnssrstream *gz)
    int readline(gnssrstream *gz, char * line,size_t slen)

cdef extern from "src/gnssir.h" nogil:
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

cdef extern from "src/position.h" nogil:
    cdef struct _enu_position "enu_position":
        float lat,
        float lon,
        float ortho_height,
        float geoid_height,
        double mjd
    cdef int init_enu_position(_enu_position *data)
    cdef int copy_enu_position(const _enu_position *indata, _enu_position * outdata)
    cdef int set_enu_position(_enu_position * data,float lat,float lon, float ortho_height, float geoid_height,double mjd)

cdef extern from "src/timeutil.h" nogil:
    cdef double mjd(const int year, const int month, const int day,const int hour, const int minute, const double second)
    cdef void mjd_to_datetime(double mjd, int *year,int * month, int * day, int * hour,int * minute, double * second) 


cpdef datetime_from_mjd(double mjd):
    cdef int yr,month,day,hr,minute
    cdef double sec;

    mjd_to_datetime(mjd,&yr,&month,&day,&hr,&minute,&sec)
    #return yr,month,day,hr,minute,sec
    return datetime(yr,month,day,hr,minute,int(sec),int((sec-int(sec))*1e3))

cpdef double mjd_from_datetime(dt:datetime):
        cdef int year=dt.year
        cdef int month=dt.month
        cdef int day=dt.day
        cdef int hour=dt.hour
        cdef int minute=dt.minute
        cdef double second=dt.second+dt.microsecond*1e-38
        return mjd(year,month,day,hour,minute,second) 


cdef extern from "src/nmea.h" nogil:
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

cdef extern from "src/arcs.h" nogil:
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
    
cdef class gnss_sys:
    cdef _gnss_system* system_ptr
    def __cinit__(self):
        self.system_ptr = <_gnss_system*>malloc(sizeof(_gnss_system))

    def __init__(self,sysstr='UNKNOWN'):
        if sysstr == 'GPSL1':
           copy_GNSS_as(self.system_ptr,&gnss_gpsl1)
        elif sysstr == 'GPSL2':
           copy_GNSS_as(self.system_ptr,&gnss_gpsl2)
        elif sysstr == 'GLONASSIIL1':
           copy_GNSS_as(self.system_ptr,&gnss_glonassiil1)
        else:
           copy_GNSS_as(self.system_ptr,&gnss_unknown)
    
    def __reduce__(self):
        return (gnss_sys,(self.system,))

    @staticmethod
    cdef from_(_gnss_system sys):
        cdef gnss_sys system=gnss_sys()
        copy_GNSS_as(system.system_ptr,&sys)
        return system
    
            
    def __dealloc__(self):
        free(self.system_ptr)

    @property
    def system(self):
        return deref(self.system_ptr).system.decode('utf-8')
    
    @property
    def frequency(self):
        return deref(self.system_ptr).frequency

    @property
    def bandwidth(self):
        return deref(self.system_ptr).bandwidth

    @property 
    def length(self):
        return deref(self.system_ptr).length
    
    def rinexcode(self,satno):
        satcode=f"{deref(self.system_ptr).rinexcode.decode('utf-8')}{satno:02d}"
        return satcode

GPSL1=gnss_sys.from_(gnss_gpsl1)
GPSL2=gnss_sys.from_(gnss_gpsl2)
GLONASSIIL1=gnss_sys.from_(gnss_glonassiil1)
GNSSUNKNOWN=gnss_sys.from_(gnss_unknown)


cdef class Arc:
    cdef _arc* arc_ptr
    def __cinit__(self):
        self.arc_ptr=<_arc*>malloc(sizeof(_arc))
        init_arc(self.arc_ptr)
    
    def __init__(self,prn:int=-1,lon:float=-9999.,lat:float=-9999.,ortho_height:float=-9999,geoid_height:float=-9999.,mjd:double=0,system:gnss_system=None):
        deref(self.arc_ptr).prn=prn

        set_enu_position(&deref(self.arc_ptr).site,lat,lon,ortho_height,geoid_height,mjd)
        # deref(self.arc_ptr).lat=lat
        # deref(self.arc_ptr).lon=lon
        # deref(self.arc_ptr).ortho_height=ortho_height
        # deref(self.arc_ptr).geoid_height=geoid_height
        cdef gnss_sys  sys;
        if system is None:
            copy_GNSS_as(&self.arc_ptr.system,&gnss_unknown)
        else:
            sys=<gnss_sys?>system
            copy_GNSS_as(&self.arc_ptr.system,sys.system_ptr)

    def __dealloc__(self):
        cdef int err
        if self.arc_ptr is not NULL:
            # free dynamically allocated members
            err= free_arc(self.arc_ptr)
            if err != 0:
                raise RuntimeError("error freeing arc members")
            free(self.arc_ptr)

    def append(self,time,elevation:float,azimuth:float,value:float):
        cdef double mjdv= mjd_from_datetime(time)
        cdef int err = append_to_arc(self.arc_ptr,mjdv,elevation,azimuth,value)
        if err != 0:
            raise RuntimeError("error appending data to arc")
    
    @property
    def lon(self):
        return deref(self.arc_ptr).site.lon
    
    @property
    def prn(self):
        return deref(self.arc_ptr).prn
    
    @property
    def lat(self):
        return deref(self.arc_ptr).site.lat

    @property
    def ortho_height(self):
        return deref(self.arc_ptr).site.ortho_height

    @property
    def geoid_height(self):
        return deref(self.arc_ptr).site.geoid_height

    @property
    def system(self):
        return gnss_sys.from_(deref(self.arc_ptr).system) 

    @property
    def elevation(self):
        cdef size_t dlen=deref(self.arc_ptr).len
        if dlen == 0:
            return None
        cdef cvarray elev = <float[:dlen] > &(deref(self.arc_ptr).elevation[0])
        return np.assay(elev);

    @property
    def time(self):
        cdef size_t dlen=deref(self.arc_ptr).len
        if dlen == 0:
            return None
        tm=np.asarray([ datetime_from_mjd(self.arc_ptr.mjd[i]) for i in range(dlen)])
        return tm
    
    @property
    def mjd(self):
        cdef size_t dlen=deref(self.arc_ptr).len
        if dlen == 0:
            return None
        cdef cvarray mjdar = <double[:dlen] > &(deref(self.arc_ptr).mjd[0])
        return np.asarray(mjdar)
    
    @property
    def azimuth(self):
        cdef size_t dlen=deref(self.arc_ptr).len
        if dlen == 0:
            return None
        cdef cvarray azim = <float[:dlen] > &(deref(self.arc_ptr).azimuth[0])
        return np.asarray(azim)
    
    @property
    def values(self):
        cdef size_t dlen=deref(self.arc_ptr).len
        if dlen == 0:
            return None
        cdef cvarray values = <float[:dlen] > &(deref(self.arc_ptr).values[0])
        return np.asarray(values)

    def __len__(self):
        return deref(self.arc_ptr).len

cdef class gnss_cycle:
    cdef _nmea_cycle* cycle_ptr
    def __cinit__(self):
        self.cycle_ptr=<_nmea_cycle*>malloc(sizeof(_nmea_cycle))
        init_nmea_cycle(self.cycle_ptr)

    def __dealloc__(self):
        if self.cycle_ptr is not NULL:
            free(self.cycle_ptr)

    @property
    def time(self):
        return datetime_from_mjd(self.cycle_ptr.mjd)
    
    @property
    def sats_in_view(self):
        return deref(self.cycle_ptr).sats_in_view
    
    @property
    def lon(self):
        return deref(self.cycle_ptr).site.lon
    
    @property
    def lat(self):
        return deref(self.cycle_ptr).site.lat
    
    @property
    def ortho_height(self):
        return deref(self.cycle_ptr).site.ortho_height

    @property
    def geoid_height(self):
        return deref(self.cycle_ptr).site.geoid_height

    @property
    def system(self):
        return np.asarray([gnss_sys.from_(deref(self.cycle_ptr).system[i]) for i in range(deref(self.cycle_ptr).sats_in_view)]) 

    @property
    def prn(self):
        cdef cvarray prn = <int[:NMEA_GSV_MAX_SATELLITES] > &(deref(self.cycle_ptr).prn[0])
        return np.asarray(prn[0:deref(self.cycle_ptr).sats_in_view])

    @property
    def azimuth(self):
        cdef cvarray azimuth = <float[:NMEA_GSV_MAX_SATELLITES] > &(deref(self.cycle_ptr).azimuth[0])
        # cdef float [:] az=deref(self.cycle_ptr).azimuth
        return np.asarray(azimuth[0:deref(self.cycle_ptr).sats_in_view])

    @property
    def elevation(self):
        cdef cvarray elev = <float[:NMEA_GSV_MAX_SATELLITES] > &(deref(self.cycle_ptr).elevation[0])
        # cdef float [:] elev=deref(self.cycle_ptr).elevation
        return np.asarray(elev[0:deref(self.cycle_ptr).sats_in_view])

    @property
    def cnr0(self):
        cdef cvarray cnr0 = <float[:NMEA_GSV_MAX_SATELLITES] > &(deref(self.cycle_ptr).cnr0[0])
        # cdef float [:] cnr0=deref(self.cycle_ptr).cnr0
        return np.asarray(cnr0[0:deref(self.cycle_ptr).sats_in_view])

cdef class gnss_trans_cycle:
    cdef _nmea_trans_cycle* tcycle_ptr
    def __cinit__(self):
        self.tcycle_ptr=<_nmea_trans_cycle*>malloc(sizeof(_nmea_trans_cycle))
        init_nmea_trans_cycle(self.tcycle_ptr)
    def __init__(self,c_clear:gnss_cycle,c_obstr:gnss_cycle,delta_sec=1):
        # self.tcycle_ptr=<_nmea_trans_cycle*>malloc(sizeof(_nmea_trans_cycle))
        # init_nmea_trans_cycle(self.tcycle_ptr)
        cdef int err=pair_nmea_trans_cycle(c_clear.cycle_ptr,c_obstr.cycle_ptr , delta_sec, self.tcycle_ptr)
        # if err != 0:
            # raise RuntimeError("No transmissivity pairs found")

    def __dealloc__(self):
        if self.tcycle_ptr is not NULL:
            free(self.tcycle_ptr)

    @property
    def time(self):
        tm=[datetime_from_mjd(self.tcycle_ptr.mjd[i]) for i in range(2)]
        return tm
    
    @property
    def sats_in_view(self):
        return deref(self.tcycle_ptr).sats_in_view
    
    # @property
    # def lon(self):
        # return deref(self.tcycle_ptr).lon
    
    # @property
    # def lat(self):
        # return deref(self.tcycle_ptr).lat
    
    # @property
    # def ortho_height(self):
        # return deref(self.tcycle_ptr).ortho_height

    # @property
    # def geoid_height(self):
        # return deref(self.tcycle_ptr).geoid_height

    @property
    def system(self):
        return np.asarray([gnss_sys.from_(deref(self.tcycle_ptr).system[i]) for i in range(deref(self.tcycle_ptr).sats_in_view)]) 

    @property
    def prn(self):
        cdef cvarray prn = <int[:NMEA_GSV_MAX_SATELLITES] > &(deref(self.tcycle_ptr).prn[0])
        return np.asarray(prn[0:deref(self.tcycle_ptr).sats_in_view])

    @property
    def azimuth(self):
        cdef cvarray azimuth = <float[:NMEA_GSV_MAX_SATELLITES] > &(deref(self.tcycle_ptr).azimuth[0])
        return np.asarray(azimuth[0:deref(self.tcycle_ptr).sats_in_view])

    @property
    def elevation(self):
        cdef cvarray elev = <float[:NMEA_GSV_MAX_SATELLITES] > &(deref(self.tcycle_ptr).elevation[0])
        return np.asarray(elev[0:deref(self.tcycle_ptr).sats_in_view])

    @property
    def cnr0(self):
        cdef cvarray cnr0 = <float[:2,:NMEA_GSV_MAX_SATELLITES] > &(deref(self.tcycle_ptr).cnr0[0][0])
        return np.asarray(cnr0[:,0:deref(self.tcycle_ptr).sats_in_view])
    
    @property
    def gamma(self):
        cdef cvarray gamma = <float[:NMEA_GSV_MAX_SATELLITES] > &(deref(self.tcycle_ptr).gamma[0])
        return np.asarray(gamma[0:deref(self.tcycle_ptr).sats_in_view])

cdef class NMEAFile:
    cdef public int _eof 
    cdef gnssrstream _sid
    cdef public str name
    def __init__(self, filename):
        self.name = filename
        err = open_stream(self.name.encode('utf-8'),&self._sid)
        if err is not 0:
            raise ValueError(f"Error opening {self.name}")
        self._eof = 0

    def eof(self):
        return self._eof == 1

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
   
    def close(self):
        self._eof = 1
        close_stream(&self._sid)
    
    cpdef readline(self):

        cdef int err=0
        cdef char nmealine[82]
        err=readline(&self._sid,&nmealine[0],82)
        if err == _GNSSR_EOF :
        #eof encountered
            nmealine[0]=0
            self._eof = 1
        
        return nmealine

    def readlines(self):
        line = self.readline()

        while len(line) != 0:
            yield line
            line = self.readline()
        self._eof = 1
        return StopIteration
    
    def readnmeas(self):
        cdef nmea_type nmea_t
        for nmea in self.readlines():
            nmea_t = check_nmea(nmea)
            yield nmea_t,nmea
        self._eof = 1
        return StopIteration

    def readcycles(self):
        cdef gnss_cycle cycle=gnss_cycle()
        cdef int err=_GNSSR_SUCCESS
        while err == _GNSSR_SUCCESS:
            err = read_nmea_cycle(&self._sid,cycle.cycle_ptr)
            if err == _GNSSR_SUCCESS:
                if cycle.sats_in_view > 0:
                    yield cycle
            elif err == _GNSSR_EOF:
                self._eof = 1
                break
        return StopIteration

