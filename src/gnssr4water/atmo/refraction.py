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

import numpy as np
from gnssr4water.atmo.formula import pres_temp_isa_tropo

def Bennet82(pres_hpa,temp_c,elev_deg):
    """Compute the atmospheric bending angle using Bennet 1982 Formula

	    Parameters
	    ----------
	    pres_hpa : float
        Local surface pressure in hPa
        temp_c : float 
        local temperature in degrees Celsius 
	    elev_deg : array like
        True elevation in degrees

	    Returns
	    -------
	    array of float
        Apparent elevation angles in degrees.
        NOTE:formulas in Feng et al and Santamaria Gomez have inconsistent unit descriptions
	"""
    elev_rad=np.deg2rad(elev_deg)
    delta_elev_arcmin=(510/(9/5*temp_c+492))*(pres_hpa/1010.16)/(np.tan(np.deg2rad(elev_deg+7.31/(elev_deg+4.4))))
    
    return elev_deg+delta_elev_arcmin/60

def refractivity_ppm(pres_dry_hpa,pres_wet_hpa,temp_c):
    temp_k=temp_c+273.15
    # for GNSS
    K1=77.6890 #K/Hpa
    K2=71.2952 #K/Hpa
    K3=375463 #K^2/Hpa
    N=K1*(pres_dry_hpa/temp_k)+K2*(pres_wet_hpa/temp_k)+K3*(pres_wet_hpa/(temp_k**2))
    return N

def Ulich81_gnss(pres_dry_hpa,pres_wet_hpa,temp_c,elev_deg):
    """Compute the atmospheric bending angle using Ulich 1981 Formula modified for GNSS (see Feng et al 2023

	    Parameters
	    ----------
	    pres_dry_hpa : float
        Dry atmospheric vapor pressure in hPa
	    pres_wet_hpa : float
        Wet atmospheric vapor pressure in hPa
        temp_c : float 
        local temperature in degrees Celsius 
	    elev_deg : array like
        True elevation in degrees

	    Returns
	    -------
	    array of float
        Apparent elevation angles in degrees.
    """
    elev_rad=np.deg2rad(elev_deg)
    a_875=np.deg2rad(87.5)
    N=refractivity_ppm(pres_dry_hpa,pres_wet_hpa,temp_c)
    delta_elev=1e-6*N*(np.cos(elev_rad)/(np.sin(elev_rad)+0.00175*np.tan(a_875-elev_rad)))
    
    return elev_deg+np.rad2deg(delta_elev)




class BennetCorrection:
    def __init__(self,ellipsHeight=0):
        #use ISA standard atmosphere
        self.pres,self.temp=pres_temp_isa_tropo(ellipsHeight)

    def corr_elev(self,time,elevdeg):
        #apply the standard Bennet correction (time -invariable)
        return np.sin(np.deg2rad(Bennet82(self.pres,self.temp,elevdeg)))





