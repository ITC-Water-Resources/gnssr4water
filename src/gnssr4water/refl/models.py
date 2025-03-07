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

import numpy as np
from functools import partial
from scipy.optimize import curve_fit
from collections import OrderedDict

class InterferometricCurve_damped:
    """
    This class models the interferometric propagation of a GNSS signal reflected from a planar surface as a damped sinusoid
    see e.g. Strandberg et al 2019
    """
    def __init__(self,gnss_wavelength):
        self.wlength=gnss_wavelength
        self.k=2*np.pi/self.wlength
        #possible initial values (note: order is important and needs to correspond to the argument order of the __call function
        self.p0=OrderedDict()
        self.p0['aheight']=10.0
        self.p0['phase']=0.0
        self.p0['amplitude']=10.0
        self.p0['damping']=5e-4

    def __call__(self,sinelev,aheight,phase,amplitude,damping):
        """Evaluate the interferometric curve for the provided values and parameters"""
        
        attenuation=np.exp(-4*damping*np.power(self.k*sinelev,2))
        return amplitude*attenuation*np.sin(2*self.k*aheight*np.sin(sinelev)+phase)

    def fit(self,sinelev,snr,**kwargs):
        
        """
            Fit the interferometric model to the sineelev and snr data, while possibly fixing some parameters to predefined values
        Parameters
        ----------
        sinelev : array
            Sine of the elevation angles
            
        snr : array
            Signal to noise ratio
            
        **kwargs : dict
            Possible fixed values for the parameters of the model, currently supported: aheight=..
            

        Returns
        -------
        popt : array
            optimal values for the parameters of the model from scipy.curve_fit
        pcov: array
            error-covariance matrix of popt
            

        """

        #Create a lambda function possibly fixing arguments to prescribed ones
        if "aheight" in kwargs.keys() and len(kwargs.keys())==1:
            ah=kwargs['aheight']
            fwdfunc=lambda sinelev,phase,amplitude,damping: self.__call__(sinelev,aheight=ah,phase=phase,amplitude=amplitude,damping=damping)
        elif len(kwargs) == 0:
            fwdfunc=self.__call__
        else:
            raise RuntimeError("Currently, only AntennaHeight (aheight) can be fixed in the interferometric fitting routine")
        #fit the model to the data
        #extract a priori values
        p0=[]
        p0keys=[]
        for ky,val in self.p0.items():
            if not ky in kwargs.keys():
                p0.append(val)
                p0keys.append(ky)
        popt,pcov=curve_fit(fwdfunc,sinelev,snr,p0=p0)
        
        #create a dictionary of the fitted values
        poptdict=OrderedDict()
        for i,pop in enumerate(popt):
            poptdict[p0keys[i]]=pop

        poptdict["ecov"]=pcov
        #forward propaggate with fitted values
        ydata_opt=fwdfunc(sinelev,*popt)
        
        #create dict of optimal values

        return poptdict,ydata_opt


