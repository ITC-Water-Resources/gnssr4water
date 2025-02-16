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
    cpdef enum gnss_system:
        GPSL1=0,
        GLONASSIIL1,
        UNKNOWN

cdef extern from "src/nmea.h" nogil:
    cdef const int _NMEA_GSV_MAX_SATELLITES "NMEA_GSV_MAX_SATELLITES"
    struct nmea_cycle:
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
        gnss_system system[_NMEA_GSV_MAX_SATELLITES],
        int prn[_NMEA_GSV_MAX_SATELLITES],
        int elevation[_NMEA_GSV_MAX_SATELLITES],
        int azimuth[_NMEA_GSV_MAX_SATELLITES],
        int cnr0[_NMEA_GSV_MAX_SATELLITES]

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
    int read_nmea_cycle(gnssrstream *sid, nmea_cycle * data);

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
        cdef nmea_cycle cycle
        cdef int err=0
        while err == _GNSSR_SUCCESS:
            err = read_nmea_cycle(&self._sid,&cycle)
            if err == _GNSSR_SUCCESS:
                yield cycle
            elif err == _GNSSR_EOF:
                self._eof = 1
                break
        return StopIteration

