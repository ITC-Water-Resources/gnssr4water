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
from gnssr4water.refl.snr import cn0_2_vv, height_LSP,vv_2_cn0
from gnssr4water.sites.arc import Arc
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as mpl
    

class WaterLevelArc(Arc):
    def __init__(self,arc,antennaHeight=1,noiseBandwidth=1,npoly=1):
        super().__init__(arc.prn,arc.system,arc.time,arc.elev,arc.az,arc.cn0)
        self.sinelev=np.sin(np.deg2rad(self.elev))
        self.setNoisebandwidth(noiseBandwidth)
        self.setAntennaHeight(antennaHeight)
        self.npoly=npoly
        

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
        if ax is None:
            fig,ax=mpl.subplots(1,1)
            ax.set_title('Signal to noise ratio')
            ax.set_ylabel('SNR [Volts/Volts]')
            ax.set_xlabel(f'Sin {chr(952)}')
        
        ax.plot(self.sinelev,self.snrv_v,'C0.-',label=self.prn,**kwargs)
        # ax.scatter(self.sinelev,self.snrv_v,label=self.prn,**kwargs)
        if showfit:
            x,fwd,res=self.fitInterferometricCurve()
            ax.plot(self.sinelev,fwd,'C1-')
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
        popt,pcov,info,mesg,ier=curve_fit(self._obseqNoiseBandwidth,self.sinelev,self.cn0,bounds=noiseBWbounds,full_output=True)
        
        
        return popt[0],np.sqrt(np.diag(pcov))[0]

    def _obseqNoiseBandwidth(self,sinelev,noiseBandwidth):
        #step 1 convert to volt/volt with given noiseBandwidth
        self.setNoisebandwidth(noiseBandwidth)

        #step 2 fit the interferometricCurve
        x,fwd,_,res=self.fitInterferometricCurve()
        
        #step 3 return fitted curve as CNO
        yfit=vv_2_cn0(fwd,noiseBandwidth)
        return yfit

    def estimateAntennaHeight(self,antennaHeightBounds=[1,10],antennaheight0=None,weights=None):
        # non-linear fit to optimize antennaheight
        if antennaheight0 is None:
            antennaheight0=np.mean(antennaHeightBounds)
        popt,pcov,info,mesg,ier=curve_fit(self._obseqAntennaHeight,self.sinelev,self.snrv_v,p0=antennaheight0,sigma=weights,bounds=antennaHeightBounds,full_output=True)
        
        
        return self.centralT,popt[0],np.sqrt(np.diag(pcov))[0]

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

class WaterLevelEstimator:
    def __init__(self,arcbuilder,noiseBandwidth,timeInterval,npoly,abounds):
        pass

    async def start(self):
        pass

    async def stop(self):
        pass

    def save(self):
        pass


# class WaterLevelKalman():
    # def __init__(self,antennaHeight,absoluteAnntennaHeight=None):
        # if absoluteAnntennaHeight is None:
            # self.absoluteAnntennaHeight=anntennaHeight
        # else:
            # self.absoluteAnntennaHeight=absoluteAnntennaHeight

        # self.height=antennaHeight
        # self.errorHeight=3 #large initial error to allow for 
        # self.waterlevel=self.absoluteAntennaHeight-antennaHeight
    
    # def processArc(self,arc):
        # pass





