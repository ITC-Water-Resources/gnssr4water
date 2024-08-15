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
from gnssr4water.io.nmea import dispatchParse,nmeavalid
import lz4.frame

class NMEAFileStream:
    """
    Creates a continuous stream from a list of compressed nmea file logs. Note: the files must be chronological order!
    """
    def __init__(self,nmeaobjs,check=True):
        self.nmeaobjs=iter(nmeaobjs)
        self.fid=None 
        self.isFile=False
        self.openNext()
        self.check=check
        
    
    def readline(self):
        if self.fid is None:
            #no buffer available to read from
            return None

        try:
            nmealine=self.fid.readline()
        except EOFError:
            nmealine=None

        if not nmealine:
            #end of file: open the next stream and try again
            self.openNext()
            if self.fid is None:
                return None
            nmealine=self.fid.readline()
        return nmealine.rstrip() #will also work if EOF of last file is reached
     
    def readlines(self):
        """Iterate over all the lines of an NMEA stream

        Yields
        -------
        line: str
            The next line as a string
        """
        
        line="invalid"
        while line is not None:
            try:
                line=self.readline()
            except UnicodeDecodeError:
                line="invalid"
                log.warning("gibberish encountered in NMEA stream, trying next line")
                continue
            if line is not None:            
                yield line
        #stop iteration
        return
    
    def readnmeas(self):
        """Iterate over the lines of an NMEA stream, while checking their checksums

        Yields
        -------
        line: str
            The next VALID nmea message line as a string
        """

        line="invalid"
        while line is not None:
            try:
                line=self.readline()
            except UnicodeDecodeError:
                line="invalid"
                log.warning("gibberish encountered in NMEAstream, trying next line")
                continue
            if nmeavalid(line):
                yield line
            else:
                # import pdb;pdb.set_trace()
                log.warning("Invalid nmea line encountered, trying next line")

        #stop iteration
        return

    def satsInView(self):
        """Iterate over the NMEA cycles build from SV and RMC NMEA messages

        Yields
        -------
        nmeacycle: dict
            A dictionary containing, time, receiver position and satellite in view specific SNR data
        """
        nmeacycle={}
        if self.check:
            nmeagen=iter(self.readnmeas())
        else:
            nmeagen=iter(self.readlines())
        for ln in nmeagen:
            if ln.startswith("$"):
                try:
                    nmeacycle.update(dispatchParse[ln[0:6]](ln))

                    #When a fix is obtained (time key is present, from a RMC message) and multiple SNR values are found) we can yield a complete nmea cycle set
                    if "time" in nmeacycle and (sum(k.startswith("PRN") for k in nmeacycle.keys()) > 0):
                        yield nmeacycle
                        #reset nmeacycle dict before populating a new one
                        nmeacycle={}
                except KeyError:
                    continue
        log.info("NMEA stream is exhausted, stopping")
        return

    def openNext(self):
        if self.fid is not None and self.isFile:
            #close previous stream
            self.fid.close()
        try:
            #determine  whether we have a file object or need to open a new file
            nmeaobj=next(self.nmeaobjs)
            if hasattr(nmeaobj,'readline'):
                try:
                    name=nmeaobj.name
                except:
                    name=''
        
                log.info(f"Reading from next stream object {name}")
                #no need to open as a file just copy it as a file descriptor
                self.fid=nmeaobj
                self.isFile=False
            else:
                if nmeaobj.endswith('.gz'):
                    self.fid = gzip.open(nmeaobj,'rt')
                elif nmeaobj.endswith(".lz4"):
                    # lz4 compressed file (e.g. from Actinius devices)
                    self.fid=lz4.frame.open(nmeaobj, mode='rt')
                else:
                    self.fid = open(nmeaobj,'rt')
                
                log.info(f"Opening file {nmeaobj}")
                self.isFile=True
        except StopIteration:
            self.fid=None

