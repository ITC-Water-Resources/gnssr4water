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


# Imports
import gzip as gz
from datetime import datetime,timedelta
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d,UnivariateSpline
from scipy.optimize import curve_fit
import lz4.frame

from gnssr4water.core.logger import log
from gnssr4water.core.gnss import GPSL1,GLONASSIIL1


GNSSlookup={"GL":GLONASSIIL1,"GP":GPSL1}

###############################################################################

def nmeavalid(nmea):
    # if nmea is None or nmea == '':return False
    #checks the checksum of the nmea string (XOR of all bytes between $ and *)
    try:
        return f"{np.bitwise_xor.reduce([ord(a) for a in nmea[1:-3]]):02X}" == nmea[-2:]
    except:
        return False
cconv=(1-100/60)
swopfac={"E":+1,"W":-1,"N":1,"S":-1}
def parseDeg(deg,EWNS):
    decdeg=deg/60+cconv*int(deg/100)
    return swopfac[EWNS]*decdeg


def smoothDegrees(degarray,timev,irec=0):
        """ Smooths degree array which only have degree resolution to a version which varies more smoothly (i.e. no jumps)"""
        
        if len(degarray) == 1:
            #Corner case just return original value
            return degarray


        ddif=np.diff(degarray)

        if np.count_nonzero(ddif) == 0:
            #no need to interpolate in this case as all values are the same
            return degarray

        
        if irec > 1:
            assert("This function is not supposed to be called with a recursion depth more than 1)")
            #Possibly split into contigous sections (i.e. crossing  0-360 border or jumping in time)
        dsections=np.argwhere(np.logical_or((np.abs(ddif) > 180.0), (np.diff(timev) > np.timedelta64(30,'s'))))  
        if dsections.size != 0:
            degsmth=np.full([len(degarray)],np.nan)
            for ist,iend in zip(np.insert(dsections+1,0,0),np.append(dsections+1,len(degarray))):
                #call this function for the sections (it shouldn;t execute this if part)
                degsmth[ist:iend]=smoothDegrees(degarray[ist:iend],timev[ist:iend],irec=irec+1)
        else:
            
            #compute for the contiguous section
            #detect the jumps (and add the first and final index) value
            ijumps=np.insert(np.append(np.argwhere(ddif != 0).squeeze()+1,len(degarray)),0,0)

            #what are half the interval lengths between the jump locations (we need to shift the interpolant input by this)
            iintHalfDistance=np.diff(ijumps)/2
            #create the support points for the interpolant
            isup=ijumps[0:-1]+iintHalfDistance
            degsup=degarray[ijumps[0:-1]]
            inonnan=~np.isnan(degarray[ijumps[0:-1]])
            #create an interpolant based on the values where a jump was detected
            iinterp=interp1d(isup[inonnan],degsup[inonnan],kind='linear',fill_value="extrapolate")
            degsmth=iinterp([float(i) for i in range(len(degarray))])
            

            degsmth[np.isnan(degsmth)]=np.nan #refill original nan values with nans again
        
        return degsmth

def resolveSubValues(time, dataint):
    """Retrieve a smoothly varying degree vector from a integer-truncated vector of data, based on the assumption that it varies smoothly 

        Parameters
        ----------
        time : datetime array
            Time tags associated with the integer degree values
        dataint : float array
            Degrees as integer

        Returns
        -------
        float array
            Smoothly varying degree vector
    """
    nmin=4
    if len(time) < nmin:
        # log.warning(f"Arc segment is less than {nmin}, ignoring")
        return dataint

    icenter=int(len(time)/2)
    
    x0=time[icenter]
    dx=[td.total_seconds() for td in time-x0]
    
    #first guess
    s=len(time)*2
    # # s=10
    try:
        bSplApprox = UnivariateSpline(dx, dataint)
    except:
        # log.warning("Cannot fit spline to Arc segment is, ignoring")

        return dataint

    # def smooth_trunc(x,smooth):
        # bSplApprox.set_smoothing_factor(smooth)
        # print(f"Trying s {smooth}")
        # return np.floor(bSplApprox(x))

    # popt,pcov,info,mesg,ier=curve_fit(smooth_trunc, dx,dataint,p0=[s],bounds=[5,len(time)],full_output=True)


    datasub=bSplApprox(dx)
    
    return datasub
    # npoly=2
    
    # npara=npoly+1 #amount of unknown parameters
    # nobs=len(time)
    

    # A=np.ones([nobs,npara])
    # for n in range(1,npoly+1):
        # A[:,n]=np.power(dx,n)


    # def fwd(timev,*para):
        
    # fwd(time)

    



def parseGNRMC(ln):
    
    spl=ln.split(",")
    if spl[2] == "V":
        return {}
    hr=int(spl[1][0:2])
    mn=int(spl[1][2:4])
    sec=float(spl[1][4:])
    date=datetime.strptime(spl[9],"%d%m%y")
    dt={"time":date+timedelta(hours=hr,minutes=mn,seconds=sec)}
    #parse weird DDDMM.MMMMM format
    dt["lat"]=parseDeg(float(spl[3]),spl[4])
    dt["lon"]=parseDeg(float(spl[5]),spl[6])
    return dt

def parseGNGSV(ln):
    #split line without considerindexng the checksum at the end
    spl=ln[0:-4].split(",")
    dt={}
    # system=spl[0][1:3].replace('GL','GLONASS').replace('GP','GPS')
    system=GNSSlookup[spl[0][1:3]]
    #loop over available satellite prn's
    for i in range(4,len(spl),4):
        try:
            prn=f"PRN{spl[i]}"
            elev=float(spl[i+1])
            az=float(spl[i+2])
            snr=float(spl[i+3])
        
        except (ValueError,IndexError):
            #It may be possible that ,,, entries occur, so we'll just ignore those
            continue

        dt[prn]={"system":system,"elev":elev,"az":az,"snr":snr}
    
    return dt   


dispatchParse={"$GPRMC":parseGNRMC,"$GPGSV":parseGNGSV,"$GNRMC":parseGNRMC,"$GLGSV":parseGNGSV}
   # def to_geopkg(self,arName):
        # """
        # Save the mask as a layer to a geopackage file
        # Parameters
        # ----------
        # self : 
        
        # arName : 
        
        # """

        # pass

###############################################################################

def readnmea(fidorfile):
    """Parses a nmea file/stream and puts the output in a pandas dataframe"""
    if type(fidorfile) == str:
        if fidorfile.endswith('.gz'):
            fid=gz.open(fidorfile,'rt')
        elif fidorfile.endswith(".lz4"):
            # lz4 compressed file (e.g. from Actinius devices)
            fid=lz4.frame.open(fidorfile, mode='rt')
        else:
            fid=open(fidorfile,'rt')
    else:
        fid=fidorfile



    #loop over the buffer and parse messages as we go
    nmeacycle={}
    nmeadata=[]
    try:
        for ln in fid:
            if ln.startswith("$"):
                try:
                    nmeacycle.update(dispatchParse[ln[0:6]](ln))

                    #possibly append this cycle data to nmeadata when a time tag is present
                    if "time" in nmeacycle and (sum(k.startswith("PRN") for k in nmeacycle.keys()) > 0):

                        basedict={k:v for k,v in nmeacycle.items() if not k.startswith("PRN")}

                        #unwrap the different PRN's into separate rows
                        for ky,val in nmeacycle.items():
                            if ky.startswith("PRN"):
                                nmeadata.append({**basedict,"PRN":int(ky[3:]),**val})
                        #reset nmeacycle dict
                        nmeacycle={}
                except KeyError:
                    continue
    except UnicodeDecodeError:
        return None
    
    if len(nmeadata) == 0:
        return None
    #create a dataframe and set multiindex
    df=pd.DataFrame(nmeadata)
    
    #We wan to get rid of rows which don;t have a elevation of azimuth in them
    # df.dropna(subset=["elev","az"],inplace=True)
    

    #since the resolution of the elevatio, and azimuthn is only on discrete degrees, let's create smoothed versions (better for plotting etc)
    # Furthermore, we also want to identify the different ascending/descending segment, even/oddly numbered repspectively so we can select of those too
    df["elevsmth"]=np.nan 
    df["azsmth"]=np.nan 
    df["segment"]=-1
    for name,grp in df.groupby("PRN"):
        time=grp.time.to_numpy()
        for dvi,dvo in [("elev","elevsmth"),("az","azsmth")]:
            dsmooth=smoothDegrees(grp[dvi].to_numpy(),time)
            #put the stuff back in the dataframe
            df.loc[grp.index,dvo]=dsmooth


            if dvi == "elev" and len(dsmooth) > 2:
                #also figure out the valid iascending (will be even numbered, descending will be oddly numbered) segments per PRN
                pdif=(np.diff(dsmooth)>0).astype(float)
                segment=np.insert(np.cumsum(np.abs(np.diff(pdif))),0,[0,0]).astype(int)
                if pdif[0] == 0.0:
                    #starts with a descending node
                    #make sure it's oddly numbered
                    segment=segment+1

                df.loc[grp.index,"segment"]=segment

                df=df.loc[df.snr.notna()]
                
    return df.set_index(["time","PRN","segment"])
