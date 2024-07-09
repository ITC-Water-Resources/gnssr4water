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
from gnssr4water.io.cf import global_attrs
from pymap3d.enu import geodetic2enu,enu2aer,aer2enu,enu2geodetic
from pymap3d import Ellipsoid
import numpy as np
import matplotlib.pyplot as mpl
import matplotlib.patches as mplpatch
wgs84=Ellipsoid.from_name('wgs84')
from scipy.stats import  binned_statistic_2d
from shapely.geometry import Polygon,Point
from shapely import to_wkt,from_wkt
import xarray as xr
import os
from datetime import datetime
from gnssr4water.core.gnss import GPSL1
from gnssr4water.fresnel import firstFresnelZone,elev_from_radius

def geo2azelpoly(geopoly,lon,lat,orthoHeight,antennaHeight,wavelength=GPSL1.length):
    if not geopoly.is_simple:
        log.warning("Cannot (currently) handle polygons with interiors, taking exterior only")

    plon,plat=geopoly.exterior.coords.xy
    ph=orthoHeight*np.ones(len(plon))
    # We need to convert the lon,lat polygons,fixed to the plane  in the local ENU frame
    e,n,u=geodetic2enu(lat=plat, lon=plon, h=ph, lat0=lat, lon0=lon, h0=orthoHeight, ell=wgs84, deg=True)
    az,e,r=enu2aer(e,n,u)
    
    #compute the actual elevation assuming the reflection point is a specular point 
    # elev=np.rad2deg(np.arctan2(antennaHeight,r))
    

    #compute the elevation correpsonding to the centroids of the First Fresnel zone
    elev=elev_from_radius(r,antennaHeight,wavelength)
    
    #convert into a shapely polygon
    azelpoly=Polygon(zip(az,elev))
    return azelpoly

def azel2geopoly(azelpoly,lon,lat,orthoHeight,antennaHeight,wavelength=GPSL1.length):
    if not azelpoly.is_simple:
        log.warning("Cannot (currently) handle polygons with interiors, taking exterior only")
    
    az,el=azelpoly.exterior.coords.xy
    #compute the radius of the location of the specular point
    #radius=antennaHeight/np.tan(np.deg2rad(el))
    
    #compute radius of fresnel central point
    _,_,radius,_ = firstFresnelZone(wavelength, antennaHeight,np.array(el)) 
    # For the reflection points we actually assume the point has a 0 upward component (both up and elevation component are set to 0) 
    el0=np.zeros(len(el))
    u0=np.zeros(len(el))
    
    e,n,_=aer2enu(az,el0,radius,deg=True)
    # import pdb;pdb.set_trace()
    plat,plon,_=enu2geodetic(e,n,u0,lat0=lat,lon0=lon,h0=orthoHeight,ell=wgs84,deg=True)

    #convert into a shapely polygon
    geopoly=Polygon(zip(plon,plat))
    return geopoly

    
class SkyMask:
    def __init__(self,poly=None,geopoly=None,lon=None,lat=None,orthoHeight=None,antennaHeight=None,wavelength=GPSL1.length,noisebandwidth=1):
        
        self.res_elev=[]
        self.res_az=[]
        self.res_snr=[]
        self.poly=None
        self.geopoly=None
        

        globattr=global_attrs()
        globattr["title"]="GNSS-R selection skymask"
        # Note all arguments are optional so an empty mask can be created 
        if lon is not None: globattr["receiver_lon"]=lon
        if lat is not None: globattr["receiver_lat"]=lat
        if orthoHeight is not None: globattr["receiver_orthoheight"]=orthoHeight
        globattr['GNSSWavelength']=wavelength
        self._ds=xr.Dataset(attrs=globattr) #xarray structure to store things into
        
        self.antennaHeight=antennaHeight
        self.noiseBandwidth=noisebandwidth

        if poly is not None and geopoly is not None:
            raise RuntimeError("Input is ambigious if both geopoly and poly are provided")
            
        if poly is not None: 
            self.poly=poly
            self.geopoly=azel2geopoly(poly,lon=lon,lat=lat,orthoHeight=orthoHeight,antennaHeight=antennaHeight)
        
        if geopoly is not None:
            self.geopoly=geopoly
            self.poly=geo2azelpoly(geopoly,lon=lon,lat=lat,orthoHeight=orthoHeight,antennaHeight=antennaHeight)

    @property
    def antennaHeight(self):
        return self._ds.attrs['receiver_antennaheight']

    @antennaHeight.setter
    def antennaHeight(self,height):
        if height is not None:
            self._ds.attrs['receiver_antennaheight']=height

    @property
    def noiseBandwidth(self):
        return self._ds.attrs['receiver_noisebandwidth']

    @noiseBandwidth.setter
    def noiseBandwidth(self,bw):
        self._ds.attrs['receiver_noisebandwidth']=bw

    @staticmethod
    def load(filename):
        #start with an empty skymask
        skmsk=SkyMask()
        with xr.open_dataset(filename) as ds:
            skmsk._ds=ds.copy()

        skmsk.poly=from_wkt(skmsk._ds.attrs['azelpoly_wkt'])
        skmsk.geopoly=from_wkt(skmsk._ds.attrs['lonlatpoly_wkt'])

        return skmsk


    def masked (self,elevation,azimuth)-> bool:
        return not self.poly.contains(Point(azimuth,elevation))

    def isMasked(self,elevation,azimuth):
        """
        returns a boolean array
        """
        return np.array([self.masked(el,az) for el,az in zip(elevation,azimuth)])
        
    def weights(self,azimuth,elevation):

        return self._ds.snr_error.sel(azimuth=xr.DataArray(azimuth,dims='narc'),elevation=xr.DataArray(elevation,dims='narc'),method='nearest')

    def set_title(self,title):
        self._ds.attrs["title"]=title
    
    def add_history(self,action):
        self._ds.attrs["history"].append(datetime.now().isoformat()+f": {action}")

    def append_SNRresidual(self,elev,az,snrres):
        """Append SNR residuals points to the mask

            Parameters
            ----------
            elev : array_like [n]
            Elevation of the points in [degrees]
            az : array_like[n]
            Azimuth of the points in degrees
            snrres: array_like[n]
            SNR residuals
        """
        self.res_elev.extend(elev) 
        self.res_az.extend(az)
        self.res_snr.extend(snrres)
    
    def compute_WeightMask(self,fillmethod='median'):
        if len(self.res_elev) < 10:
            log.info("Enough SMR resildulas must have been added before being able to compute a weight mask")
            return
        
        minaz,minel,maxaz,maxel=self.poly.bounds
        #determine bins
        deltad=2
        elevbins=int((maxel-minel)/deltad)+1
        azbins=int((maxaz-minaz)/deltad)+1
        stat,x_edges,y_edges,bino=binned_statistic_2d(self.res_az,self.res_elev,np.abs(self.res_snr),statistic='median',bins=[azbins,elevbins])
        
        counts,_,_,_=binned_statistic_2d(self.res_az,self.res_elev,None,statistic='count',bins=[azbins,elevbins])
        
        weights=np.where(counts > 100,stat,np.nan)
        self._ds["grd_azimuth"]=(("grd_azimuth",),x_edges) 
        self._ds["grd_elevation"]=(("grd_elevation",),y_edges) 

        self._ds["snr_error"]=(("azimuth","elevation"),weights)

        if fillmethod == "median":
            self._ds['snr_error']=self._ds['snr_error'].fillna(np.median(self.res_snr))

        self._ds=self._ds.assign_coords(azimuth=(("azimuth",),x_edges[0:-1]+deltad/2),elevation=(("elevation",),y_edges[0:-1]+deltad/2))
                                    

    def skyplot(self,ax=None,**kwargs):
        maskcolor='#e15989'
        #maskcolor='blue'
        
        if ax is None:
            fig,ax=mpl.subplots(1,1,subplot_kw={'projection': 'polar'})
            ax.set_title('Skyplot mask')

            ax.set_rlim([90,0])
            ax.set_theta_zero_location("N")
            ax.set_theta_direction(-1)

        #create a matplotlib patch from the polygon data
        polyfine=self.poly.segmentize(2)
        x,y=polyfine.exterior.xy
        ppatch=mplpatch.Polygon(np.array(np.array([[x,y] for x,y in zip(np.deg2rad(x),y)])),edgecolor=maskcolor,fill=False,lw=2)

        #plot the weights within the mask
        if "snr_error" in self._ds:
            # self._ds.snr_error.plot.pcolormesh(x=np.deg2rad(self._ds.azimuth),y=self._ds.elevation,ax=ax)
            axob=ax.pcolormesh(np.deg2rad(self._ds.grd_azimuth),self._ds.grd_elevation,self._ds.snr_error.data.T,shading='flat',cmap='Reds',vmin=0,vmax=30)
            fig=ax.get_figure()
            fig.colorbar(axob,label="SNR error [v/v]")
        
        ax.add_patch(ppatch)

        return ax


    def save(self,netcdfname,mode='a'):
        """ Save the mask to a netcdf file, for later reuse

            Parameters
            ----------
            netcdfname: str
            netcdf file name to write to
        """
        #save the polygon  as a WKT attribute to the netcdf file
        self._ds.attrs["azelpoly_wkt"]=to_wkt(self.poly)
        self._ds.attrs["lonlatpoly_wkt"]=to_wkt(self.geopoly)

        self._ds.to_netcdf(netcdfname,mode=mode)
    
        
    def segmentize(self,max_segment_length=1):
        """
        Segmentize the azimuth-elevation polygon and create a new Skymask 
        """

        lon=self._ds.attrs["receiver_lon"]
        lat=self._ds.attrs["receiver_lat"]
        oh=self._ds.attrs['receiver_orthoheight']
        ah=self._ds.attrs['receiver_antennaheight']

        skmsk=SkyMask(poly=self.poly.segmentize(max_segment_length=max_segment_length),lon=lon,lat=lat,orthoHeight=oh,antennaHeight=ah)
        return skmsk

class SimpleMask(SkyMask):
    def __init__(self,lon,lat,orthoHeight,antennaHeight,elevations=[5,40],azimuths=[0,360],wavelength=GPSL1.length):
        pnts=[(azimuths[0],elevations[0]),(azimuths[1],elevations[0]),(azimuths[1],elevations[1]),(azimuths[0],elevations[1]),(azimuths[0],elevations[0])]
        super().__init__(poly=Polygon(pnts),lon=lon,lat=lat,orthoHeight=orthoHeight,antennaHeight=antennaHeight,wavelength=wavelength)
        self.elevBnds=elevations
        self.azBnds=azimuths

    def masked (self,elevation,azimuth)-> bool:

        if elevation < self.elevBnds[0] or elevation > self.elevBnds[1]:
            # import pdb;pdb.set_trace()
            return True
        if azimuth < 0:
            azimuth+=360
        if azimuth < self.azBnds[0] or azimuth > self.azBnds[1]:
            # import pdb;pdb.set_trace()
            return True
        #ok point is not masked
        return False

    

