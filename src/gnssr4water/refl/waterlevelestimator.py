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
import pandas as pd
import math
import xarray as xr
from datetime import datetime,timedelta
import os
import numpy as np
import shutil


class WaterLevelEstimator:
    
    encoding={'timev': {'units': 'milliseconds since 1970-01-01'}}
    def __init__(self,arcbuilder,ah0=None,ahalf_width=2,outlier=None,tau_ema_sec=6*3600,zarrlog=None,freq=None,group="waterlevel_ema",mode="a",realign=True,**kwargs):
        self.group=group
        self.arcbuilder=arcbuilder
        self.processParam={ky:val for ky,val in kwargs.items() if ky in ["npoly","bandpass",atmo_corr_tag]}
        #possibly add a standard atmo angle correction
        if atmo_corr_tag in self.processParam and self.processParam[atmo_corr_tag] == "Bennet":
            self.processParam[atmo_corr_tag]=BennetCorrection(self.arcbuilder.mask.ellipseHeight).corr_elev

        self.zarrlog=zarrlog

        #intial guess for the antennaHeight
        if ah0 is None:
            #take the reference height from the 
            self.aheight=self.arcbuilder.mask.antennaHeight
            self.ah0=self.aheight
        else:
            self.aheight=ah0
            self.ah0=ah0
        
        self.err_aheight=ahalf_width #assume an initial error which is 50% of the antennaheight window size
        
        self.time=np.datetime64(0,'ns') #long ago

        self.ahalf_width=ahalf_width
        #first realignment of the search boundaries 
        self.realignBounds()
        
        #number of estimates since last save
        self.iest=0
        self.tchunks=20
        self.warmupstop=10
        self.nbuffer=4 # number of arcs to keep in the buffer without writing it to the file , this is needed so the EMA estimate stays consistent over time 
        #possibly skip further dynamic realignments
        self.realign=realign

        #outlier test: reject new estimate when it is off by outlier from the previous estimate
        self.outlier=outlier
        self.tau=np.timedelta64(tau_ema_sec,'s')
        self.alphafix=None
        if freq is not None:
            if type(freq) == str:
                freq=pd.to_timedelta(freq).to_timedelta64()
            self.alphafix,_=self.weights(freq,self.warmupstop+1)
            self.freq=freq #Set to None for dynamic frequency derivation (not recommended for data with large gaps)

        self.init_state()
        
        #check which mode to use for appending the data
        if zarrlog is not None:
            if mode == 'w':
                #remove zarr group before starting

                shutil.rmtree(os.path.join(self.zarrlog,self.group),ignore_errors=True)
                self.appendmode=False # creates new zarr group on first save
            elif mode == "a":
                try:
                    self.recover_state(zarrlog)
                    self.appendmode=True
                except:
                    self.appendmode=False
    
    def init_state(self):
        #setup waterlevel xarray structure
        globattr=global_attrs()
        globattr["title"]="GNSS-R time series estimate"
        globattr.update(self.arcbuilder.attrs())
        globattr.update({"estimator":"Exponential Moving Average (EMA)",
                         "estimator_func":"s_i=alpha x_i + (1-alpha) s_i-1",
                         "tau_ema_sec":self.tau.astype('int'),
                         "outlier_threshold_from_prev":self.outlier,
                         "heigth_search_window_width":2*self.ahalf_width,
                         "dynamic_realign_bounds":self.realign,
                         "antennaheight_ref":self.ah0})
        globattr.update(self.processParam)
        
        if atmo_corr_tag in globattr:
            # convert to string to allow for storing in a file
            globattr[atmo_corr_tag]=str(globattr[atmo_corr_tag])
        nsize=self.tchunks+self.nbuffer
        zeros=np.zeros(nsize)
        self._dswl=xr.Dataset({"timev":(["time"],zeros.astype('datetime64[ns]')),
                               "waterlevel": (["time"], zeros.copy()),
                               "err_waterlevel": (["time"], zeros.copy()),
                               "ah_ls": (["time"], zeros.copy()),
                               "err_ah_ls": (["time"], zeros.copy())},
                              attrs=globattr) #xarray structure to store timeseries data
        
    def recover_state(self,zarrlog):
        # load a previous state from a file
        if os.path.isdir(os.path.join(zarrlog,self.group)):
            self.appendmode=True
            #open previous estimate
            dstmp=xr.open_zarr(zarrlog,group=self.group)
            self.ah0=dstmp.attrs['antennaheight_ref']
            self.tau=dstmp.attrs['tau_ema_sec']
             
            self.aheight=self.ah0-dstmp.waterlevel[-1].compute().item()
            self.err_aheight=dstmp.err_waterlevel[-1].compute().item()
            self.time=dstmp.timev[-1].compute().item()
        else:
           raise RuntimeError(f"Expected recovery zarr archive but can't find it:{zarrlog}")
    


    def save(self):
        if self.zarrlog is not None:
            iend=(self.iest-self.nbuffer-1)%self.tchunks+1
            validslice=slice(0,iend) #note this does not store the last nbuffer epochs to the file
            if self.appendmode:
                log.info(f"appending to {self.zarrlog}/{self.group}")
                #save/append to zarr
                self._dswl.sel(time=validslice).to_zarr(self.zarrlog,mode='a',append_dim='time',group=self.group)
            else:
                log.info(f"Saving to file {self.zarrlog}/{self.group}")
                self._dswl.sel(time=validslice).to_zarr(self.zarrlog,mode='w',group=self.group,encoding=self.encoding)
                self.appendmode=True
            #move the buffer to the beginning of the dataset so it will be written on the next save
            self._dswl=self._dswl.roll(time=self.nbuffer)

    def realignBounds(self):
        self.ahbnds=[max(0.5,self.aheight-self.ahalf_width),self.aheight+self.ahalf_width]
    
    def weights(self,dt,ithpos):
        

        if ithpos < self.warmupstop:
            #use the average in the warmup phase
            alpha=1/(ithpos+1)
        elif self.alphafix is not None:
            #static weights
            return self.alphafix,1-self.alphafix
        else:
            #dynamic weights
            assert(dt >= 0)
            alpha=1-math.exp(-dt/self.tau)
        
        return alpha,1-alpha

    def update_state(self,time,aheight,err_aheight):
        """ Update the smoothed EMA estimates"""
        
        if self.iest < (self.nbuffer+self.tchunks):
            #window when the buffer is also filling up
            iest_delta=self.iest
        else:
            iest_delta=(self.iest-self.nbuffer)%self.tchunks+self.nbuffer # slot number in the filei, beyond the buffer since last save
        
        self._dswl.timev[iest_delta]=np.datetime64(time,'ns')
        self._dswl.ah_ls[iest_delta]=aheight
        self._dswl.err_ah_ls[iest_delta]=err_aheight
        
        
        deltaT=time-self.time
        if deltaT < 0:
            #previous smoothed estimates need a correction
            #make sure data is in the right order but only sort from the buffer until the current position
            sortslice=dict(time=slice(0,iest_delta+1))
            self._dswl[sortslice]=self._dswl[sortslice].sortby('timev')
        
        #where to start updating the ema esimates
        istart=(self._dswl.timev >= time).argmax().item()
        if istart> iest_delta or istart == 0:
            #buffer is not enough to guarantee chronological estimates
            # import pdb;pdb.set_trace()
            log.warning('EMA estimates need data beyond the buffer, output will be sligthly inconsistent')
            istart=1

        if self.iest == 0:
            # special edge case for the first value
            self._dswl.waterlevel[0]=self.ah0-self._dswl.ah_ls[0]
            self._dswl.err_waterlevel[0]=self._dswl.err_ah_ls[0]
            istart+=1

        for i in range(istart,iest_delta+1):
             
            deltaT=self._dswl.timev.values[i]-self._dswl.timev.values[i-1] 
            wnow,wprev=self.weights(deltaT,self.iest-iest_delta+i)

            ah_now=self._dswl.ah_ls.values[i]
            ah_ema_prev=self.ah0-self._dswl.waterlevel.values[i-1]
            #apply EMA (or running mean in warmup) smoother
            ah_ema_now=wnow*ah_now+wprev*ah_ema_prev
            self._dswl.waterlevel[i]=self.ah0-ah_ema_now
            #error propagation
            err_ah_now=self._dswl.err_ah_ls.values[i]
            err_ah_ema_prev=self._dswl.err_waterlevel.values[i-1]

            err_ah_ema_now=math.sqrt((wprev*err_ah_ema_prev)**2+(wnow*err_ah_now)**2)
            self._dswl.err_waterlevel[i]=err_ah_ema_now
       
        
        #possibly update state to the latest epoch
        self.time=self._dswl.timev.values[iest_delta]
        self.aheight=self.ah0-self._dswl.waterlevel.values[iest_delta]
        self.err_aheight=self._dswl.err_waterlevel[iest_delta]
        
        if  self.realign:
            self.realignBounds()

        self.iest+=1



    async def start(self):
    
        try:
            async for arc in tqdmasync(self.arcbuilder.arcs()):
                self.wlarc=WaterLevelArc(arc,noiseBandwidth=self.arcbuilder.mask.noiseBandwidth)
                time,aheight,erraheight=self.wlarc.estimateAntennaHeight(self.ahbnds,**self.processParam)
                if self.outlier is not None and self.iest > self.warmupstop:
                    if self.outlier < abs(self.aheight-aheight):
                        log.info(f"outlier rejected previous: {self.aheight}, new: {aheight}, diff: {aheight-self.aheight}")
                        continue
                
                #update state amnd smoothed estimate
                self.update_state(np.datetime64(time),aheight,erraheight)

                #possibly save updated data to disk
                save=(self.iest-self.nbuffer)%self.tchunks == 0 and self.tchunks < self.iest
                if save:
                    self.save()
                    
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
        
