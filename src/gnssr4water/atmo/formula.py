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


TLapse_isa=-6.5e-3 # temperature lapse rate degC/m
T0=15+273.15 #standard temperature at MSL in K
P0=1013.25 # standard pressure at MSL in hPa
rho0=1225 # standard density

Rspec=287.0528 #specific gas constant J kg-1 K-1

Run=8.3144598 #universal gass constant J/(mol K)

M=0.0289644 # air molar mass kg/mol

g0=9.80665 # gravitation acceleration in m/s2
r0=6356766 #m

exp_isa=-g0*M/(Run*TLapse_isa)
def h_2_pot_alt(h):
    return r0*h/(h+r0)

def pot_alt_2_h(geopot_h):
    return r0*geopot_h/(r0-geopot_h)



def pres_temp_isa_tropo(h_above_msl):
    """Compute the pressure and temperature of the ISA standard atmopshere model at a level given a height above the mean sea level.

	:pep:`484` type annotations are supported. If attribute, parameter, and
	return types are annotated according to `PEP 484`_, they do not need to be
	included in the docstring:

	Parameters
	----------
	h_above_msl : float
	    height above the standard surface (mean sea level) in meter 
	Returns
	-------
	float, float
	    Pressure [hPa], and temperature [ideg C] at the given height
    """
    assert(h_above_msl < 15e3)
    pot_alt=h_2_pot_alt(h_above_msl)
    temp=T0+TLapse_isa*pot_alt
    pres=P0*np.power(temp/T0,exp_isa)
    return pres,temp-273.15



