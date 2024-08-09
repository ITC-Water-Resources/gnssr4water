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
import asyncio
from gnssr4water.refl.waterlevel import WaterLevelArc,atmo_corr_tag
from tqdm.asyncio import tqdm as tqdmasync
from gnssr4water.core.logger import log
from gnssr4water.io.cf import global_attrs
from gnssr4water.atmo.refraction import BennetCorrection

import math
import xarray as xr
from datetime import datetime
import os
import numpy as np
import shutil


class WaterLevelEstimator:
    
    encoding={'timev': {'units': 'milliseconds since 1970-01-01'}}
    def __init__(self,arcbuilder,ah0=None,ahalf_width=2,outlier=None,alpha=0.1,zarrlog=None,group="waterlevel_ema",mode="a",realign=True,**kwargs):
        self.group=group
        self.arcbuilder=arcbuilder
        self.processParam={ky:val for ky,val in kwargs.items() if ky in ["npoly","bandpass",atmo_corr_tag]}
        #possibly add a standard atmo angle correction
        if atmo_corr_tag in self.processParam and self.processParam[atmo_corr_tag] == "Bennet":
            self.processParam[atmo_corr_tag]=BennetCorrection(self.arcbuilder.mask.ellipseHeight).corr_elev


        #intial guess
        if ah0 is None:
            #take the reference height from the 
            self.aheight=self.arcbuilder.mask.antennaHeight
            self.ah0=self.aheight
        else:
            self.aheight=ah0
            self.ah0=ah0
        
        self.err_aheight=ahalf_width #assume an initial error which is 50% of the antennaheight window size

        self.ahalf_width=ahalf_width
        #first realignment of the search boundaries 
        self.realign=True
        self.realignBounds()
        
        self.iest=0
        self.warmupstop=20
        
        #possibly skip further dynamic realignments
        self.realign=realign

        #outlier test: reject new estimate when it is off by outlier from the previous estimate
        self.outlier=outlier
        
        #Exponential smoothing parameter
        self.wprev=(1.0-alpha)
        self.wnow=alpha


        self._processingtask=None

        #setup waterlevel xarray structure
        globattr=global_attrs()
        globattr["title"]="GNSS-R time series estimate"
        globattr.update(arcbuilder.attrs())
        globattr.update({"estimator":"Exponential Moving Average (EMA)",
                         "estimator_func":"s_i=alpha x_i + (1-alpha) s_i-1",
                         "alpha":self.wnow,
                         "outlier_threshold_from_prev":self.outlier,
                         "heigth_search_window_width":2*self.ahalf_width,
                         "dynamic_realign_bounds":self.realign,
                         "antennaheight_ref":self.ah0})
        globattr.update(self.processParam)
        if atmo_corr_tag in globattr:
            # convert to string to allow for storing in a file
            globattr[atmo_corr_tag]=str(globattr[atmo_corr_tag])
        self.tchunks=40
        self.ithval=0
        zeros=np.zeros(self.tchunks)
        self._dswl=xr.Dataset({"timev":(["time"],zeros.copy().astype('datetime64[ns]')),
                               "waterlevel": (["time"], zeros.copy()),
                               "err_waterlevel": (["time"], zeros.copy()),
                               "waterlevel_ls": (["time"], zeros.copy()),
                               "err_waterlevel_ls": (["time"], zeros.copy())},
                              attrs=globattr) #xarray structure to store timeseries data
        
        #check which mode to use for appending the data
        self.zarrlog=zarrlog
        if zarrlog is not None:
            if mode == 'w':
                #remove zarr group before starting

                shutil.rmtree(os.path.join(self.zarrlog,self.group),ignore_errors=True)
                self.appendmode=False # creates new zarr group on first save
            elif mode == "a":
                if os.path.isdir(os.path.join(self.zarrlog,self.group)):
                    self.appendmode=True
                    #open previous estimate
                    dstmp=xr.open_zarr(self.zarrlog,group=self.group)
                    
                    self.aheight=self.ah0-dstmp.waterlevel[-1].compute().item()
                else:
                    self.appendmode=False

    def save(self):
        if self.zarrlog is not None:
            if self.appendmode:
                #save/append to zarr
                self._dswl.sel(time=slice(0,self.ithval)).sortby('timev').to_zarr(self.zarrlog,mode='a',append_dim='time',group=self.group)
            else:
                self._dswl.sel(time=slice(0,self.ithval)).sortby('timev').to_zarr(self.zarrlog,mode='w',group=self.group,encoding=self.encoding)
                self.appendmode=True

    def realignBounds(self):
        if self.realign:
            self.ahbnds=[max(0.5,self.aheight-self.ahalf_width),self.aheight+self.ahalf_width]
            

    async def start(self):
    
        try:
            async for arc in tqdmasync(self.arcbuilder.arcs()):
                self.wlarc=WaterLevelArc(arc,noiseBandwidth=self.arcbuilder.mask.noiseBandwidth)
                time,aheight,erraheight=self.wlarc.estimateAntennaHeight(self.ahbnds,**self.processParam)
                if self.outlier is not None and self.iest > self.warmupstop:
                    if self.outlier < abs(self.aheight-aheight):
                        log.info(f"outlier detected {self.aheight}, {aheight}")
                        continue
                
                self.time=time

                if self.iest <= self.warmupstop:
                    if self.iest  == 0:
                        self.aheight=aheight
                        #Negative error denotes the warmup phase
                        self.err_aheight=-1
                    else:
                        delta=aheight-self.aheight
                        self.aheight+=delta/self.iest
                        self.err_aheight=-1
                else:
                    self.aheight=self.wprev*self.aheight+self.wnow*aheight
                    self.err_aheight=math.sqrt((self.wprev*self.err_aheight)**2+(self.wnow*erraheight)**2)
                self.iest+=1
                
                if self.zarrlog is not None:
                    self._dswl.timev[self.ithval]=np.datetime64(self.time,'ns')
                    self._dswl.waterlevel[self.ithval]=self.ah0-self.aheight
                    self._dswl.err_waterlevel[self.ithval]=self.err_aheight
                    self._dswl.waterlevel_ls[self.ithval]=self.ah0-aheight
                    self._dswl.err_waterlevel_ls[self.ithval]=erraheight
                    #save update data
                    
                    if self.ithval == self.tchunks-1:
                        log.info(f"saving new water level estimates")
                        self.save()
                        self.ithval=0
                    else:
                        self.ithval+=1

                # if self.fid:
                    # self.fid.write(f"{time};{self.aheight};{self.err_aheight};{aheight};{erraheight};{self.ahbnds[0]};{self.ahbnds[1]}\n")
                # print(f"current estimate {self.time}, {self.aheight}, {self.err_aheight} from estimate {aheight},{erraheight}")
                self.realignBounds()
                # print(f"new bounds {self.ahbnds[0],self.ahbnds[1]}")
        except KeyboardInterrupt:
            #ok just cancels the current loop
            pass
        except asyncio.CancelledError:
            log.info("Canceled arc processing")
    
    def done(self):
        if self._processingtask is None:
            return True

        return self._processingtask.done()
    
    def start_nowait(self):
        """ start the processing (non-blocking)"""
        
        log.info("Start processing Arcs")
        self._processingtask=asyncio.create_task(self.start())
        

    def stop(self):
        if not self.done():
            log.info("Cancelling the processing Arcs")
            self._processingtask.cancel()
        else:
            log.info("Nothing to cancel")
        
