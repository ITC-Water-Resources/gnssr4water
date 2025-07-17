from gnssr4water.sites.snrarc import SNRArc
import numpy as np
from scipy.signal import find_peaks
from astropy.timeseries import LombScargle
import matplotlib.pyplot as mpl
from gnssr4water.core.logger import log


def getLombScargle(sinelev,snr,antennaHeightBounds,gnss_wavelength,npoints=200,resolution=None):
    """ Compute the Lomb-Scargle periodogram, and express the spectrum in terms of antenna heights."""
    # LSP
    freqbounds=np.array(antennaHeightBounds)*2/gnss_wavelength
    #setup predetermined frequencies 
    if resolution is not None:

        frequency=np.arange(freqbounds[0],freqbounds[1],resolution)
    else:
        # use the provided number of points
        frequency=np.linspace(freqbounds[0],freqbounds[1],npoints)

    power = LombScargle(sinelev,snr).power(frequency,method="fastchi2",assume_regular_frequency=True)

    height=frequency*gnss_wavelength/2

    return height,power


def estimateAntennaHeight_multi_LombScargle(snrarc,antennaHeightBounds,maxpeaks=3,resolution=0.01,fullOutput=False):
    """Use a LombScargle periodogram to find the most dominant peaks and water level heights"""

    height,power=getLombScargle(snrarc.sinelev,snrarc.snrv_v,antennaHeightBounds,snrarc.system.length,resolution=resolution)
    promabs=np.max(power)-np.min(power)

    #find peaks
    relprom=0.6 # relative, w.r.t to the largest peak, prominence to keep the peaks for 
    pks,props=find_peaks(power,prominence=relprom*promabs)
    


    #use  heuristic approach to estimate the errors
    # we assume the bounds represent the left and right 3 sigma bounds
    sigma_h=(height[props['right_bases']]-height[props['left_bases']])/6
    h=height[pks]
    prom=props['prominences']
    if len(h) > 1: 
        #sort the result according to the prominencs (most prominent first)
        idx=np.argsort(prom)[::-1]
        if len(idx) > maxpeaks:
            idx=idx[:maxpeaks]
        sigma_h=sigma_h[idx]
        h=h[idx]
        prom=prom[idx]

    height_est={"time":snrarc.centralT,"height":h,"height_sigma":sigma_h,"prominence":prom}
    if fullOutput:
        #return the full periodogram
        height_est['periodogram']={'height':height,'power':power}
    return height_est


class WaterLevelLSEstimator:
    def __init__(self,arcs,ah_ref=None, ah_bounds=None,maxpeaks=3,resolution=0.01,**kwargs):
        
        self._arcgen=arcs
        self.ah0=ah_ref
        self.maxpeaks=maxpeaks
        self.resolution=resolution
        
        self.arcprocessargs=kwargs
         
        #loose bounds on initial antenna height
        if ah_bounds is None:
            ah_err=20 #set wide search bounds if not specified
            self.ahbounds=[max(0,self.ah0-ah_err),self.ah0+ah_err]
        else:
            self.ahbounds=ah_bounds

        self.currentArc=SNRArc(next(self._arcgen),**self.arcprocessargs)
        self.currentEst=None
    
    def plot_periodogram(self,ax=None,showpeaks=True,**kwargs):
        # """
        # Plot Spectral Lomb Scargle plot with estimated water height
        # """
        if ax is None:
            fig,ax=mpl.subplots(1,1)
            ax.set_title('Lomb Scargle Periodogram')
            ax.set_ylabel('Amplitude')
            ax.set_xlabel('Reflector height [m]')
        
        est=self.estimate(fullOutput=True)
        ax.plot(est['periodogram']['height'],est['periodogram']['power'],label=f"PRN:{self.currentArc.prn}",**kwargs)
        ax.set_xlim(self.ahbounds)
     
        if showpeaks is not None:
            peakcolors=['darkred','indianred','lightcoral']
            if showpeaks is True:
                #show all peaks
                showpeaks=np.arange(len(est['height']))
            
            for peak in showpeaks:
                ah=est['height'][peak]
                err_ah=est['height_sigma'][peak]
                color= peakcolors[peak]
                ax.axvline(x=ah, color=color, linestyle='-',label=f"Peak{peak} est.: {ah:0.2f}m,err: {err_ah:0.2f}m")
                ax.axvline(x=ah-err_ah, color=color, linestyle='--',alpha=0.7)
                ax.axvline(x=ah+err_ah, color=color, linestyle='--',alpha=0.7)
        ax.legend()
        return ax
    
    
    def estimate(self,fullOutput=False):
        """Default processing is to get a new Lomb-Scargle estimate for the current arc"""
        if self.currentArc is None:
            log.warning("No arc loaded, forcing the loading of a next arc")
            self._loadNextArc()
            
        est=estimateAntennaHeight_multi_LombScargle(self.currentArc,antennaHeightBounds=self.ahbounds,maxpeaks=self.maxpeaks,resolution=self.resolution,fullOutput=fullOutput)
        self.currentEst=est
        return est
    
    def _loadNextArc(self):
        """Load the next arc from the generator"""
        try:
            self.currentArc=SNRArc(next(self._arcgen),**self.arcprocessargs)
        except StopIteration:
            self.currentArc=None
            raise StopIteration
        return True

    def estimates(self,fullOutput=False):
        """Generator function to yield estimates for each arc"""
        while True:
            try:
                #load the next valid arc
                est=self.estimate(fullOutput=fullOutput)
                yield est
                self._loadNextArc()
            except StopIteration:
                #ok # no more arcs to process
                break
            except Exception as e:
                breakpoint()
                log.warning(f"Couldn't estimate height from the arc, skipping")
                continue
        return
