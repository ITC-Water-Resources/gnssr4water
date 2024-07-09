# -*- coding: utf-8 -*-
"""
To compute and show the first Fresnel Zone.

@author: Lubin Roineau, ENSG-Geomatics (internship at UT-ITC Enschede), Aug 26, 2022
Modified/rewritten R.Rietbroek, March-June 2024
"""

# Usefull librairies
import numpy as np
import matplotlib.pyplot as plt
import math as m
from .geod import *
from shapely.geometry.polygon import Polygon
from shapely import GEOSException
import pyproj
from gnssr4water.core.gnss import *
import pymap3d as pm
import geopandas as gpd
from scipy.optimize import fsolve

# Calculation of the First Fresnel Zone

def firstFresnelZone(GNSSlambda, h, elev):
    """
    This function gets the size and center of the First Fresnel Zone ellipse.
    (based on a code by Kristine Larson and Carolyn Roesler).
    
    Parameters
    ----------
    GNSSlambda: float 
        wavelength of the GNSS signal
    h: float
        Hight of the receiver in meters.
    elev: float array_like
        Satellite elevation angle in degrees.
    
    Return
    ------
    a: float
        Semi-major axis, aligned with the satellite azimuth (meters).
    b: float
        Semi-minor axis (meters).
    R: float 
        Locates the center of the ellispe on the satellite azimuth direction 
        and R meters away from the base of the Antenna.
    area: float
        Area of the elliptical first Fresnel zone
    """
    if np.any(elev>90):
        raise Exception("Wrong value for elevation, can't excede 90° !")  

    # Directly put elevation in radians
    elevR = np.radians(elev)
    
    # delta = locus of points corresponding to a fixed delay;
    # typically the first Fresnel zone is is the
    # "zone for which the differential phase change across
    # the surface is constrained to lambda/2" (i.e. 1/2 the wavelength)
    d = GNSSlambda/2

    # from the appendix of Larson and Nievinski, 2013
    # semi-minor axis
    b = ((GNSSlambda*h)/np.sin(elevR)) + (GNSSlambda/(2*np.sin(elevR)))**2
    b = np.sqrt(b)
    # semi-major axis
    a = b/np.sin(elevR)

    # determine distance to ellipse center in meters
    R = (h + d/np.sin(elevR)) / np.tan(elevR)
    #for debugging
    #import pdb;pdb.set_trace()
    #R = (h) / np.tan(elevR)
    #R = 40* np.ones(elevR.shape)
    # a.name='semi-major'
    # b.name='semi-minor'
    # R.name='distance'
    area=np.pi*a*b
    # area.name='area'
    return a, b, R, area

def elev_from_radius(radius,antennaHeight,wavelength=GPSL1.length):
    """
    Retrieve the elevation angles associated with the radial distances of the centroids of the first Fresnel ellipses
    """
    
    #compute specular point as  a starting value
    elevspecular=np.arctan2(antennaHeight,radius)

    def rootfunc(elev):
        sinel=np.sin(elev)
        tanel=np.tan(elev)
        rootval=radius-(antennaHeight+wavelength/(2*sinel))/tanel
        return rootval

    #solve the non-linear problem using scipy's fsolve
    elevroots=fsolve(rootfunc,x0=elevspecular)
    return np.rad2deg(elevroots)
    
def generate_enu_ellipses(a,b,R,azim,npoints=100):
    
    # Change angle to match orientation of Python
    az_rad=np.deg2rad(azim)
    #az_rad = np.radians(azim)
    #az_rad = 2*np.pi - np.deg2rad(azim) + np.pi/2
    cos_az=np.cos(az_rad)
    sin_az=np.sin(az_rad)

    # Coordinates of the center in the local EN (U) frame
    ce = R*sin_az                    
    cn = R*cos_az
    # import pdb;pdb.set_trace()
    # c_u = all zero
    #broadcast
    nell=len(R)
    c_n=np.broadcast_to(cn,[npoints,nell]).T
    c_e=np.broadcast_to(ce,[npoints,nell]).T

    t = np.linspace(0, 2*np.pi, npoints)
    cos_t=np.cos(t)
    sin_t=np.sin(t)
    # Parametric equation of ellipse
    # el_e = c_e + np.outer(a*cos_az,cos_t) - np.outer(b*sin_az,sin_t)
    # el_n = c_n + np.outer(a*sin_az,cos_t) + np.outer(b*cos_az,sin_t)
    el_e = c_e + np.outer(a*sin_az,cos_t) - np.outer(b*cos_az,sin_t)
    el_n = c_n + np.outer(a*cos_az,cos_t) + np.outer(b*sin_az,sin_t)
    return el_e,el_n,ce,cn


###############################################################################

def plotEllipse(a, b, R, lon, lat, h, azim):
    """
    Create an ellipse of a Fresnel zone.
    
    Parameters
    ----------
    a: float
        Semi-major axis, aligned with the satellite azimuth (meters).
    b: float
        Semi-minor axis (meters).
    R: float 
        Locates the center of the ellispe on the satellite azimuth direction 
        and R meters away from the base of the Antenna.
    lon,lat: float
        Position of the receiver in geographical coordinates (degrees).
    h: float
        Hight of the receiver in meters.
    azim: float
        Given azimut of ellipse in degrees.
    
    Return
    ------
    p: Polygon
        Polygon of the ellipse.
    area: float
        Area of the Polygon in square meter.
    """
    # Check input for the azimuth in case
    if azim > 360 or azim < 0:
        raise Exception("Wrong value of azimuth, should be between 0 and 360!")  
        
    # Set coordinates of the receiver to cartesians
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy = True)
    X = transformer.transform(lon, lat)[0]
    Y = transformer.transform(lon, lat)[1]
    
    # Set to radians
    azim = m.radians(azim)
    
    # Change angle to match orientation of Python
    angle = 2*np.pi - azim + np.pi/2
    
    # Coordinate of the center
    xR = X + R*np.cos(angle)                    
    yR = Y + R*np.sin(angle)
    
    t = np.linspace(0, 2*np.pi, 100)

    # Parametric equation of ellipse
    x = xR + a*np.cos(angle)*np.cos(t) - b*np.sin(angle)*np.sin(t)
    y = yR + a*np.sin(angle)*np.cos(t) + b*np.cos(angle)*np.sin(t)

    # Polygon of ellipse in epsg:3857
    q = Polygon(list(zip(x,y)))
    area = q.area
    
    # Changing back the coordinates to geographic
    lon = []
    lat = []
    for i in range(len(x)):
        lo = transformer.transform(x[i], y[i],direction='INVERSE')[0]
        la = transformer.transform(x[i], y[i],direction='INVERSE')[1]
        lon.append(lo)
        lat.append(la)
        
    # Polygon of ellipse in epsg:4326
    p = Polygon(list(zip(lon,lat)))

    return p, area

###############################################################################

def specularPoint(a, b, R, azim, color=None):
    """
    This function just return the center of an ellipse, i.e the reflection point.

    Parameters
    ----------
    a: float
       Semi-major axis, aligned with the satellite azimuth (meters).
    b: float
       Semi-minor axis (meters).
    R: float 
       Locates the center of the ellispe on the satellite azimuth direction 
       and R meters away from the base of the Antenna.
    azim: list 
       List of azimuths
    color: String (optional)
       Color of center points.

    Returns
    -------
    Plot of center of ellipses.

    """
    for angle in azim:
        
        angle = 2*np.pi - angle + np.pi/2
        xR = R*np.cos(angle)  # x-position of the center
        yR = R*np.sin(angle)  # y-position of the center

        if color != None:
            plt.axis('equal')
            plt.scatter(xR,yR, color=color)
        else:
            plt.axis('equal')
            plt.scatter(xR,yR)

    return

###############################################################################

def fresnelZones(elev,azim,lon,lat,orthoHeight,antennaHeight,GNSSWavelength=GPSL1.length,npoints=100):
    """
    Compute Fresnel zones (center, and ellipses from satellite positions, geographical location, antenna height, and GNSS wavelength
    returns a geopandas dataframe Fresnel zones and properties
    """
    

    #First compute the first fresnel zones
    a,b,r,area=firstFresnelZone(GNSSWavelength,antennaHeight,elev)
    
    #generate ellipses and centroid locations in the ENU frame
    el_e,el_n,ce_e,ce_n=generate_enu_ellipses(a,b,r,azim,npoints=npoints)


    # convert the centroids to lon,lat
    ell=pm.Ellipsoid.from_name('wgs84')
    
    lat0,lon0,alt0=pm.enu.enu2geodetic(ce_e, ce_n, np.zeros(ce_e.shape), lat0=lat, lon0=lon, h0=orthoHeight, ell=ell,deg=True)
    #convert ellipses in enu coordinates to lon,lat crs 4326)
    el_lats,el_lons,el_alt=pm.enu.enu2geodetic(el_e, el_n, np.zeros(el_e.shape), lat0=lat, lon0=lon, h0=orthoHeight, ell=ell,deg=True)

    #create Shapely Polygons for the ellipses
    el_geoms=[]
    for i in range(el_lats.shape[0]):
        el_geoms.append(Polygon(zip(el_lons[i,:],el_lats[i,:])))

    #build a geopandas dataframe
    gdfout=gpd.GeoDataFrame(dict(elevation=elev,azimuth=azim,distance=r,lon=lon0,lat=lat0,alt=alt0),geometry=el_geoms,crs="EPSG:4326") 
    


    return gdfout


