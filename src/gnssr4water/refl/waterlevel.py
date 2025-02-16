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
from gnssr4water.refl.snr import cn0_2_vv, vv_2_cn0
from gnssr4water.sites.arc import Arc
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as mpl
from astropy.timeseries import LombScargle 
from scipy.constants import speed_of_light
from numpy.polynomial import Polynomial
from scipy.signal import butter, sosfilt
from gnssr4water.core.logger import log


atmo_corr_tag="atmo_corr"


class WaterLevelArc(Arc):
    def __init__(self,arc,noiseBandwidth=1):
        super().__init__(arc.prn,arc.system,arc.time,arc.elev,arc.az,arc.cn0)
        self.sinelev=np.sin(np.deg2rad(self.elev))
        self.setNoisebandwidth(noiseBandwidth)
        

    def setNoisebandwidth(self,noiseBandwidth):
        self.snrv_v=cn0_2_vv(self.cn0,noiseBandwidth)
        # self.snrv_vspline=cn0_2_vv(self.cn0spline,noiseBandwidth)
    
    def setAntennaHeight(self,antennaHeight):
        self.antennaHeight=antennaHeight
        if antennaHeight is not None:
            self.omega=4*np.pi*antennaHeight/(self.system.length)
        else:
            self.omega=None


    
    def mkDesignMat(self):
        assert(self.omega is not None)
        #make a design matrix mapping
        npara=self.npoly+1+2 #amount of unknown parameters
        nobs=len(self.sinelev)
        

        A=np.ones([nobs,npara])


        x0=0.0 #sin(0)
        dx=self.sinelev-x0
        for n in range(1,self.npoly+1):
            A[:,n]=np.power(dx,n)

        #add harmonics (as separate sin and cos to keep linearity

        A[:,self.npoly+1]=np.sin(self.omega*dx)
        A[:,self.npoly+2]=np.cos(self.omega*dx)
        return A

    def fitInterferometricCurve(self):
        """Fit the interferometric SNR curve for a fixed antennaHeight

            Parameters
            ----------
            param1 : int
                The first parameter.
            param2 : str
                The second parameter.

            Returns
            -------
            (x,Ax,y-Ax,res)
                x unknown parameters (polynomial coefficients and sine/cosine amplitude
                Ax: forward propagated fit
                y-Ax: data residuals
                res: data fit
        """
        A=self.mkDesignMat()
        # solve linear least squares problem
        x,res,rank,s=np.linalg.lstsq(A,self.snrv_v,rcond=None)
        fwd=A@x
        return x,fwd,self.snrv_v-fwd,res

    def plot(self,ax=None,showfit=False,**kwargs):
        """
        Plot SNR [Volts/Volts] as a function of the sine of the elevation
        """
        sinelev,snr=self.preprocess(**kwargs)
        if ax is None:
            fig,ax=mpl.subplots(1,1)
            ax.set_title('Signal to noise ratio')
            ax.set_ylabel('SNR [Volts/Volts]')
            ax.set_xlabel(f'Sin {chr(952)}')
        
        ax.plot(sinelev,snr,label=self.prn)
        # ax.scatter(self.sinelev,self.snrv_v,label=self.prn,**kwargs)
        if showfit:
            x,fwd,res,ltpl=self.fitInterferometricCurve()
            ax.plot(self.sinelev,fwd,'C1-')
        return ax
    
    
    def plotLombScargle(self,ax=None,antennaHeightBounds=[0,20],showfit=True,**kwargs):
        """
        Plot Spectral Lomb Scargle plot with estimated water height
        """
        if ax is None:
            fig,ax=mpl.subplots(1,1)
            ax.set_title('Lomb Scargle Periodogram')
            ax.set_ylabel('Amplitude')
            ax.set_xlabel('Reflector height [m]')

        sinelev,snr=self.preprocess(**kwargs)
        height,power=self.getLombScargle(antennaHeightBounds,sinelev,snr,npoints=200)
        ax.plot(height,power,label=self.prn)
        # ax.set_xlim(heightBounds)
        
        if showfit:
            # time,ah,err_ah=self.estimateAntennaHeight(antennaHeightBounds=antennaHeightBounds)
            time,ah,err_ah=self.estimateAntennaHeight(antennaHeightBounds=antennaHeightBounds,**kwargs)
            
            ax.axvline(x=ah, color='r', linestyle='-',label=f"height: {ah:0.2f}m,err: {err_ah:0.2f}m")
            ax.axvline(x=ah-err_ah, color='r', linestyle='--')
            ax.axvline(x=ah+err_ah, color='r', linestyle='--')
            ax.axvline(x=ah+err_ah, color='r', linestyle='--')
        ax.legend()
        return ax
    
    def estimateNoiseBandwidth(self,antennaHeight):
        #estimate receiver noise bandwidth while fixing the antenna height
        self.setAntennaHeight(antennaHeight)
        
        # bandwidthCandidates=np.arange(0.6,15,0.1)
        # resopt=np.finfo('float').max 
        # iopt=2
        # for i,bandw in enumerate(bandwidthCandidates):
            # self.setNoisebandwidth(bandw)
            # _,_,_,res=self.fitInterferometricCurve()
            # # print(res)
            # if res < resopt:
                # resopt=res
                # iopt=i

        # self.setNoisebandwidth(bandwidthCandidates[iopt])
        # return bandwidthCandidates[iopt],resopt        
        noiseBWbounds=[0.2,15] #bounds to search for the optimum
        popt,pcov,info,mesg,ier=curve_fit(self._obseqNoiseBandwidth,self.sinelev,self.cn0int,bounds=noiseBWbounds,full_output=True)
        
        
        return popt[0],np.sqrt(np.diag(pcov))[0]

    def _obseqNoiseBandwidth(self,sinelev,noiseBandwidth):
        #step 1 convert to volt/volt with given noiseBandwidth
        self.setNoisebandwidth(noiseBandwidth)

        #step 2 fit the interferometricCurve
        x,fwd,_,res=self.fitInterferometricCurve()
        
        #step 3 return fitted curve as CNO
        yfit=vv_2_cn0(fwd,noiseBandwidth)
        return yfit

    def removePolyfit(self,npoly=3,sinelev=None):
        #remove direct signal as a polynomial fit
        if sinelev is None:
            sinelev=self.sinelev
        x=sinelev-np.mean(sinelev)
        p=Polynomial.fit(x, self.snrv_v, npoly)
        res_snrv_v = self.snrv_v-p(x)
        return sinelev,res_snrv_v
    
    def preprocess(self,**kwargs):
        # import pdb;pdb.set_trace()
        if atmo_corr_tag in kwargs:
            #apply an atmospheric correction to the sinelev
            sinelev=kwargs[atmo_corr_tag](self.time,self.elev)
        else:
            sinelev=self.sinelev

        if "npoly" in kwargs:
            #preprocess SNR by removing a polynomial fit from the data
            sinelev,snrvv=self.removePolyfit(npoly=kwargs['npoly'],sinelev=sinelev)
        if "bandpass" in kwargs:
            sinelev,snrvv=self.butterBandPass(bandpass=kwargs["bandpass"],sinelev=sinelev)
        else:
            snrvv=self.snrv_v
        
        return sinelev,snrvv

    def estimateAntennaHeight(self,antennaHeightBounds=[1,10],**kwargs):
        sinelev,snr=self.preprocess(**kwargs) 

        time,ah,err_ah=self.estimateAntennaHeightLombScargle(antennaHeightBounds,sinelev,snr)

        # self.setAntennaHeight(ah)
        return time,ah,err_ah
    
    def estimateAntennaHeightFit(self,antennaHeightBounds=[1,10],antennaheight0=None,weights=None):
        # non-linear fit to optimize antennaheight
        if antennaheight0 is None:
            antennaheight0=np.mean(antennaHeightBounds)
        popt,pcov,info,mesg,ier=curve_fit(self._obseqAntennaHeight,self.sinelev,self.snrv_v,p0=antennaheight0,sigma=weights,bounds=antennaHeightBounds,full_output=True)
        
        
        return self.centralT,popt[0],np.sqrt(np.diag(pcov))[0]
    
    def butterBandPass(self,bandpass,butorder=3,sinelev=None):
        """Apply a butter worth bandpass filter"""
        if sinelev is None:
            sinelev=self.sinelev

        deltax=abs(np.median(np.diff(sinelev)))
        xstart=sinelev.min()
        xend=sinelev.max()
        try:
            sinelev_bp=np.arange(xstart,xend,deltax)
        except:
            import pdb;pdb.set_trace()
        lofreq=2*bandpass[0]/self.system.length
        hifreq=2*bandpass[1]/self.system.length
        sos = butter(butorder, [lofreq,hifreq], 'bandpass', fs=1/deltax, output='sos')
        if self.direction.startswith('desc'):
            filtered = sosfilt(sos, np.interp(sinelev_bp,sinelev[::-1],self.snrv_v[::-1]))
            sinelev_bp=sinelev_bp[::-1]
            snrv_v_bp=filtered[::1]
        else:
            filtered = sosfilt(sos, np.interp(sinelev_bp,sinelev,self.snrv_v))
            snrv_v_bp=filtered
        return sinelev_bp,snrv_v_bp 

    def getLombScargle(self,antennaHeightBounds,sinelev,snr,npoints=200):

        
        # LSP
        freqbounds=np.array(antennaHeightBounds)*2/self.system.length
        #setup predetermined frequencies 
        frequency=np.linspace(freqbounds[0],freqbounds[1],npoints)
        power = LombScargle(sinelev,snr).power(frequency,method="fastchi2",assume_regular_frequency=True)

        height=frequency*self.system.length/2

        return height,power

    def estimateAntennaHeightLombScargle(self,antennaHeightBounds,sinelev,snr,npoints=200):
        """Use a LombScargle periodogram to find the best"""

        height,power=self.getLombScargle(antennaHeightBounds,sinelev,snr,npoints=npoints)
        imax=np.argmax(power)
        
        #compute empirical estimate of the error by evaluating the peakiness of the peak
        
        #create a cosine window to mainly focus on the estimated peak itself
        dh=0.3333*(height[-1]-height[0])
        coswin=np.cos(np.pi/dh*(height-height[imax]))
        coswin=np.where(coswin>0,coswin,0)
        
        # get a window of maximum +/- 1 meter centered around the estimated antennaheight to compute a cumulative distribution from which to take the 16 and 86 percentile from 
        cumupower=np.cumsum(coswin*power)
        #normalize to 0-1
        cumupower/=cumupower.max()
        # center around estimate
        cumupower-=cumupower[imax]

        plo=-0.34
        phi=0.34
        ilo=np.argmax(cumupower > plo)
        ihi=np.argmax(cumupower > phi)
        if ihi == 0:
            # set to highest index if not found
            ihi=len(cumupower)-1

        #take the largest difference to height estimate as representative for the error
        d1=height[imax]-height[ilo]
        d2=height[ihi]-height[imax]

        return self.centralT,height[imax],max(d1,d2)


    def _obseqNoiseBandwidth(self,sinelev,noiseBandwidth):
        #step 1 convert to volt/volt with given noiseBandwidth
        self.setNoisebandwidth(noiseBandwidth)

        #step 2 fit the interferometricCurve
        _,fwd,_,_=self.fitInterferometricCurve()
        
        #step 3 return fitted curve as CNO
        yfit=vv_2_cn0(fwd,noiseBandwidth)
        return yfit
    
    def _obseqAntennaHeight(self,sinelev,antennaHeight):
        
        self.setAntennaHeight(antennaHeight)

        #step 2 fit the interferometricCurve (assumes fixed antennaHeight from above)
        _,fwd,_,_=self.fitInterferometricCurve()
        
        return fwd








