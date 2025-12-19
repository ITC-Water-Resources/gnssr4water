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

from gnssr4water.core.logger import log as gnssrlog
from gnssr4water.gnssir import gnss_trans_cycle
from datetime import timedelta,datetime
import numpy as np
import xarray




class GNSSVOD:
    #measurements should be within  certain time tolerance
    def __init__(self,stream_clearsky,stream_obstruct,t_tol=None,**kwargs):
        self._cycle_gen_clear=stream_clearsky.readcycles()
        self._cycle_gen_obstr=stream_obstruct.readcycles()
        if t_tol is None: 
            self.t_tol=timedelta(seconds=2)
        else:
            self.t_tol=t_tol

        #intialize initial cycle times
        self.t_clear=None 
        self.t_obstr=None
        

    def _get_cycle_pair(self):


        #always load the next cycles from the streams to ensure no duplicate usage 
        #this is to ensure that cycles are not used twice
        try:
            cycle_clear=next(self._cycle_gen_clear)            
            t_clear=cycle_clear.time
        except StopIteration:
                raise StopIteration("Clear sky stream depleted")
        

        try:
            cycle_obstr=next(self._cycle_gen_obstr)            
            t_obstr=cycle_obstr.time
        
        except StopIteration:
            raise StopIteration("Obstructed stream depleted")
        

        #catch up cycles so that they align in time 
        while self.t_tol < np.abs(t_clear-t_obstr):
            while t_clear < t_obstr:
                try:
                    cycle_clear=next(self._cycle_gen_clear)            
                    t_clear=cycle_clear.time
                except StopIteration:
                    raise StopIteration("No more matching cycles to process")
         
            while t_obstr < t_clear-self.t_tol:
                try:
                    cycle_obstr=next(self._cycle_gen_obstr)            
                    t_obstr=cycle_obstr.time
                except StopIteration:
                    raise StopIteration("No more matching cycles to process")
        cycle_t=gnss_trans_cycle(cycle_clear,cycle_obstr)
        breakpoint() 
        return cycle_clear,cycle_obstr

    def vods(self):
        """
            Generator to estimate VOD estimates for each cycle pair
        """
        
        while True: 
            try:
                cyc_clear,cyc_obstr=self._get_cycle_pair()
            except StopIteration:
                break
            prn_common,i1,i2=np.intersect1d(cyc_clear.prn,cyc_obstr.prn,assume_unique=False,return_indices=True)
            #take the average of the elevation and azimuth as the reference position in the sky
            elev=(cyc_clear.elevation[i1]+cyc_obstr.elevation[i2])/2.0
            azim=(cyc_clear.azimuth[i1]+cyc_obstr.azimuth[i2])/2.0
            dcnr=(cyc_obstr.cnr0[i2]-cyc_clear.cnr0[i1])

            vod=-np.log(np.power(10,dcnr/10))*np.cos(np.radians(elev))
            yield dict(time=cyc_obstr.time,prn=prn_common,sys=cyc_clear.system[i1],elevation=elev,azimuth=azim,vod=vod,cnr_obstr=cyc_obstr.cnr0[i2],cnr_clear=cyc_clear.cnr0[i1])

