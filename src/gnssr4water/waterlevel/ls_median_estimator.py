from gnssr4water.waterlevel.lombscargle_estimator import WaterLevelLSEstimator
import numpy as np
from gnssr4water.core.logger import log
import re

class WaterLevelMedianLSEstimator(WaterLevelLSEstimator):
    """Estimate the water level from the median Lomb-Scargle estimates of the antenna height"""
    def __init__(self,arcsource,freq,maxarcbuffer=20,outlier_threshold=None,**kwargs):
        """
        Initialize the WaterLevelMedianLSEstimator
        :param arcsource: The source of arcs to process
        :param freq: The time frequency as a string ( e.g '6h', or '1d') or as a timedelta64 for which to estimate and output the median
        :param maxarcbuffer: The maximum number of arcs to hold in the buffer
        :param kwargs: Additional keyword arguments to pass to the WaterLevelLSEstimator parent class
        """
        super().__init__(arcsource,**kwargs)
        self._hbuffer=np.zeros(maxarcbuffer,dtype=float)  # buffer for the last maxarcbuffer estimates
        self._hsigmabuffer=np.zeros(maxarcbuffer,dtype=float)  # buffer for the last maxarcbuffer estimates
        self._timebuffer=np.zeros(maxarcbuffer,dtype='datetime64[ns]')
    
        
        self.outlier_threshold=outlier_threshold
        self.currentMedEst=None

        if isinstance(freq,str):
            match = re.match(r"([0-9]+)([a-z]+)", freq, re.I)
            if not match:
                raise ValueError(f"Invalid deltaT format: {deltaT}. Expected format is '<number><unit>', e.g. '6h' or '1d'.")
            items = match.groups()
            self.deltaT = np.timedelta64(int(items[0]), items[1])

        else:
            self.deltaT=freq
        
        self._maxbuf=maxarcbuffer
        self._bufsize=0
        self._minNeeded=8
        #add the first (valid) arc
        while True:
            self._loadNextArc()
            est=super().estimate()
            npks=len(est['height'])
            if npks == 0:
                # no estimates available, continue the loop
                continue
            for i in range(npks):
                self._hbuffer[i]=est['height'][i]
                self._hsigmabuffer[i]=est['height_sigma'][i]
                self._timebuffer[i]=est['time']
                self._bufsize+=1

            self._lastepoch=self._timebuffer[0]
            break
        

    def estimate(self,fullOutput=False):
        # Process arcs until enough arcs have been accumulated to provide a median estimate
        while True:
            est=super().estimate(fullOutput)
            npks=len(est['height'])
            if npks == 0:
                # no estimates available, continue the loop
                log.warning(f"No estimates available for {est['time']}, continuing to the next arc.")
                self._loadNextArc()
                continue
            
            #add found peaks
            
            for i in range(npks):
                if self._bufsize == self._maxbuf:
                    #find a spot discarding the oldest estimate
                    i_insert=np.argmin(self._timebuffer)
                else:
                    #append
                    i_insert=self._bufsize
                    self._bufsize+=1
                
                self._hbuffer[i_insert]=est['height'][i]
                self._hsigmabuffer[i_insert]=est['height_sigma'][i]
                etime=np.datetime64(est['time'])
                self._timebuffer[i_insert]=etime
        
            # log.warning(f"{self._lastepoch}, {etime}, {self.deltaT}, {self._bufsize} arcs in the buffer, processing next arc.")
            if self._lastepoch + self.deltaT < etime:

                # enough arcs have been processed to return a new median estimate
                #figure out valid time points to put in the median
                idx_valid = [ ix for ix,time in enumerate(self._timebuffer) if time >= self._lastepoch and time < self._lastepoch + self.deltaT ]
                if self.outlier_threshold is not None and self.currentMedEst is not None:
                    # remove outliers from the buffer
                    idx_valid = [ ix for ix in idx_valid if abs(self._hbuffer[ix] - self.currentMedEst['height']) < self.outlier_threshold ]  

                if len(idx_valid) == self._maxbuf:
                    # give warning that the buffer is fuller than expected
                    log.warning(f"Buffer is full ({self._maxbuf} arcs), some estimates in the window may have been discarded (consider increasing maxarcbuffer in the estimator).")
                elif len(idx_valid) < self._minNeeded:
                    self._lastepoch +=self.deltaT
                    log.info(f"Buffer contains too few valid estimates {len(idx_valid)} < {self._minNeeded}, for {self._lastepoch}, moving on  to the next timestep.")
                    continue
                
                #get the median estimate
                medest={"time":self._lastepoch+self.deltaT/2,"height":np.median(self._hbuffer[idx_valid])}
                
                if fullOutput:
                    # add the full input to the median window
                    medest['input']['heights']=self._hbuffer[idx_valid]

                self.currentMedEst=medest
                self._lastepoch += self.deltaT
                return medest

            #load the nextArc
            self._loadNextArc()


