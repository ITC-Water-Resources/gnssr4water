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

cdef extern from "src/stream.h" nogil:
    cdef const int _GNSSR_SUCCESS "GNSSR_SUCCESS"
    cdef const int _GNSSR_IO_ERROR "GNSSR_IO_ERROR"
    cdef const int _GNSSR_EOF "GNSSR_EOF"
    struct gnssrstream:
        pass
    int open_stream(const char * filename, gnssrstream* gz)
    void close_stream(gnssrstream *gz)
    int readline(gnssrstream *gz, char * line,size_t slen)

cdef extern from "src/gnssrlib.h" nogil:
    cdef struct _gnss_system "gnss_system":
        char * system,
        double frequency,
        double length,
        double bandwidth
    # cdef void init_GNSS(_gnss_system * system, const char * sysname)
    cdef _gnss_system gnss_gpsl1
    cdef _gnss_system gnss_gpsl2
    cdef _gnss_system gnss_glonassiil1
    cdef void copy_GNSS_as(_gnss_system *sys, const _gnss_system * sysfrom);

cdef extern from "src/nmea.h" nogil:
    cdef const int _NMEA_GSV_MAX_SATELLITES "NMEA_GSV_MAX_SATELLITES"
    struct _nmea_cycle "nmea_cycle":
        int year,
        int month,
        int day,
        int hr,
        int min,
        float sec,
        char status,
        float lat,
        float lon,
        float ortho_height,
        float geoid_height,
        int sats_in_view,
        _gnss_system system[_NMEA_GSV_MAX_SATELLITES],
        int prn[_NMEA_GSV_MAX_SATELLITES],
        float elevation[_NMEA_GSV_MAX_SATELLITES],
        float azimuth[_NMEA_GSV_MAX_SATELLITES],
        float cnr0[_NMEA_GSV_MAX_SATELLITES]

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

cdef class gnss_sys:
    cdef _gnss_system* system_ptr
    def __cinit__(self):
        self.system_ptr = <_gnss_system*>malloc(sizeof(_gnss_system))
    
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
    
GPSL1=gnss_sys.from_(gnss_gpsl1)
GPSL2=gnss_sys.from_(gnss_gpsl2)
GLONASSIIL1=gnss_sys.from_(gnss_glonassiil1)


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
        tm=datetime(deref(self.cycle_ptr).year,deref(self.cycle_ptr).month,deref(self.cycle_ptr).day,deref(self.cycle_ptr).hr,deref(self.cycle_ptr).min)+timedelta(seconds=deref(self.cycle_ptr).sec)
        return tm
    
    @property
    def sats_in_view(self):
        return deref(self.cycle_ptr).sats_in_view
    
    @property
    def lon(self):
        return deref(self.cycle_ptr).lon
    
    @property
    def lat(self):
        return deref(self.cycle_ptr).lat
    
    @property
    def ortho_height(self):
        return deref(self.cycle_ptr).ortho_height

    @property
    def geoid_height(self):
        return deref(self.cycle_ptr).ortho_height

    @property
    def system(self):
        return np.asarray([gnss_sys.from_(deref(self.cycle_ptr).system[i]) for i in range(deref(self.cycle_ptr).sats_in_view)]) 

    @property
    def prn(self):
        cdef int [:] prn=deref(self.cycle_ptr).prn
        return np.asarray(prn[0:deref(self.cycle_ptr).sats_in_view])

    @property
    def azimuth(self):
        cdef float [:] az=deref(self.cycle_ptr).azimuth
        return np.asarray(az[0:deref(self.cycle_ptr).sats_in_view])

    @property
    def elevation(self):
        cdef float [:] elev=deref(self.cycle_ptr).elevation
        return np.asarray(elev[0:deref(self.cycle_ptr).sats_in_view])

    @property
    def cnr0(self):
        cdef float [:] cnr0=deref(self.cycle_ptr).cnr0
        return np.asarray(cnr0[0:deref(self.cycle_ptr).sats_in_view])

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

