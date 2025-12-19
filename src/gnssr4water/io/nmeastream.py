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

# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2024
import gzip
from gnssr4water.core.logger import log
from datetime import datetime,timedelta
from gnssr4water.gnssir import NMEAFile
import os



class NMEAFileStream:
    """
    Creates a continuous stream from a list of (compressed) nmea file logs. Note: the files must be chronological order!
    """
    def __init__(self,nmeaobjs,check=True):
        self.nmeaobjs=iter(nmeaobjs)
        self.fid=None 
        self.openNext()
        
    def readcycles(self):
        while self.fid is not None:
            for nmeacycle in self.fid.readcycles():
                yield nmeacycle
            self.openNext()

    def openNext(self):
        if self.fid is not None:
            #close previous nmeafile
            self.fid.close()
        try:
            #open new  (non-empty) NMEA file
            while True:
                #get the next file from the iterator
                nmeafile=next(self.nmeaobjs)
                if os.path.getsize(nmeafile) == 0:
                    #skip empty files
                    log.warning(f"Skipping empty NMEA file {nmeafile}")
                    continue
                
                break
            

            log.info(f"Reading from next stream object {nmeafile}")
            self.fid=NMEAFile(nmeafile)
        except StopIteration:
            self.fid=None

