# This file is part of gnssr4water
# gnssr4water is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.

# geoslurp is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with Frommle; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2024

from gnssr4water.core.logger import log
from pymap3d.enu import geodetic2enu,enu2aer
from pymap3d import Ellipsoid
import numpy as np
wgs84=Ellipsoid.from_name('wgs84')

def fromPolygon(geopoly,lon,lat,orthoHeight,antennaHeight):
    """Returns a discretized  azimuth elevation mas for (1st) Fresnel zones falling with a given lon,lat polygon as seen from a GNSS receiver

    Parameters
    ----------
    geopoly : shapely.geometry.polygon.Polygon
        The (lon,lat) polygon of the area where the 1st Fresnel Zones should fall in
    lon : float
        The longitude of the receiver
    lat : float
        The latitude of the receiver
    orthoheight: float
        Orthometric height of the receiver (antenna)
    antennaheight:
        Height of the Antenna above the reflecting surface

    Returns
    -------
    azimuth, elevation
        Azimuth and Elevation of the GNSS satellites positions which have there specular point of reflection on the polygon points
    """

    if not geopoly.is_simple:
        log.warning("Cannot (currently) handle polygons with interiors, taking exterior only")
        
    plon,plat=geopoly.exterior.coords.xy
    ph=orthoHeight*np.ones(len(plon))
    # We need to convert the lon,lat polygons in the local ENU frame
    e,n,u=geodetic2enu(lat=plat, lon=plon, h=ph, lat0=lat, lon0=lon, h0=orthoHeight, ell=wgs84, deg=True)
    az,e,r=enu2aer(e,n,u)
    #import pdb;pdb.set_trace()
    #compute the elevation if the point is actually the specular point of the center of the Fresnel zone
    elev=np.rad2deg(np.arctan2(antennaHeight,r))

    return az,elev,r

    

