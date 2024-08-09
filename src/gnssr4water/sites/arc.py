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
from datetime import timedelta
from gnssr4water.core.logger import log
import numpy as np
import matplotlib.pyplot as mpl
from gnssr4water.io.nmea import smoothDegrees
from gnssr4water.io.nmea import resolveSubValues

class Arc:
    """ 
    Represents a certain Arc seen from a dedicated location
    """
    def __init__(self,prn,system,time,elev,az,cn0,refinenmea=True):
        self.prn=prn
        self.time=np.array(time)
        self.elev=np.array(elev)
        self.az=np.array(az)
        self.cn0=np.array(cn0)

        self.system=system
        if refinenmea:
            self.refinenmea()
        
        #determine direction of arc, (ascending, descending or both)
        ilast=len(self.time)-1
        imx=np.argmax(self.elev)

        imn=np.argmin(self.elev)
        
        if imx != 0 and imx != ilast:
            self.isplit=imx
            self.direction='asc-desc'
        elif imn !=0 and imn != ilast:
            self.isplit=imn
            self.direction='desc-asc'
        elif imn < imx :
            self.isplit=None
            self.direction='asc'
        else:
            self.isplit=None
            self.direction='desc'
    
    def refinenmea(self):

        self.elevint=self.elev.copy()
        self.elev=resolveSubValues(self.time,self.elev)
        # self.elev=smoothDegrees(self.elev,self.time)
        
        self.azint=self.az.copy()
        # self.az=smoothDegrees(self.az,self.time)
        self.az=resolveSubValues(self.time,self.az)
        
        # don't refine the actual Cn0 values
        # self.cn0int=self.cn0.copy()
        # self.cn0=resolveSubValues(self.time,self.cn0)
         
    def __len__(self):
        return len(self.time)

    @property
    def deltaT(self):
        return self.time[-1]-self.time[0]
    
    @property
    def centralT(self):
        t0=self.time[0]
        return timedelta(seconds=np.median([(dt-t0).total_seconds() for dt in self.time]))+t0

    def split(self):
        """
        Retrieve the ascending and descending parts of the arc (if any)
        """
        arc1=None
        arc2=None
        
        if self.isplit is None:
            # nothing to split
            return self,None
        slice1=slice(0,self.isplit)
        slice2=slice(self.isplit,len(self.time))
        refinenmea=hasattr(self,'elevint')

        arc1=Arc(self.prn,self.system,self.time[slice1],self.elev[slice1],self.az[slice1],self.cn0[slice1],refinenmea=refinenmea)
        arc2=Arc(self.prn,self.system,self.time[slice2],self.elev[slice2],self.az[slice2],self.cn0[slice2],refinenmea=refinenmea)
        
        return arc1,arc2 
        

        
    def plot(self,ax=None,**kwargs):
        """
        Plot C/N0 as a function of the elevation
        """
        if ax is None:
            fig,ax=mpl.subplots(1,1)
            ax.set_title('Carrier to noise density')
            ax.set_ylabel('C/N0 [Db-Hz]')
            ax.set_xlabel(f'elevation {chr(952)} [deg]')
        
        
        ax.scatter(self.elev,self.cn0int,label=self.prn,**kwargs)
        ax.scatter(self.elev,self.cn0,label=self.prn,**kwargs)

        return ax


    def skyplot(self,ax=None,**kwargs):

        if ax is None:
            fig,ax=mpl.subplots(1,1,subplot_kw={'projection': 'polar'})
            ax.set_title('Skyplot')

            ax.set_rlim([90,0])
            ax.set_theta_zero_location("N")
            ax.set_theta_direction(-1) 
            # ax.set_ylabel('SNR [v/v]')
            # ax.set_xlabel(f'sin {chr(952)}')
        
        ax.scatter(np.deg2rad(self.az),self.elev,label=self.prn,**kwargs)

        return ax


        
         


