# -*- coding: utf-8 -*-
"""
To compute and show the first Fresnel Zone.

@author: Lubin Roineau, ENSG-Geomatics (internship at UT-ITC Enschede), Aug 26, 2022
Modified R.Rietbroek, March 2024
"""

# Usefull librairies
import numpy as np
import matplotlib.pyplot as plt
import math as m
from .geod import *
from shapely.geometry.polygon import Polygon
import pyproj
from gnssr4water.core.gnss import *

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
    a.name='semi-major'
    b.name='semi-minor'
    R.name='distance'
    area=np.pi*a*b
    area.name='area'
    return a, b, R, area

def generate_enu_ellipses(a,b,R,azim,npoints=100):
    
    # Change angle to match orientation of Python
    #az_rad = np.radians(azim)
    az_rad = 2*np.pi - np.radians(azim) + np.pi/2

    cos_az=np.cos(az_rad)
    sin_az=np.sin(az_rad)

    # Coordinates of the center in the local EN (U) frame
    c_e = R*cos_az                    
    c_n = R*sin_az
    # c_u = all zero
    #broadcast
    nell=len(R)
    c_n=np.broadcast_to(c_n,[npoints,nell]).T
    c_e=np.broadcast_to(c_e,[npoints,nell]).T

    t = np.linspace(0, 2*np.pi, npoints)
    cos_t=np.cos(t)
    sin_t=np.sin(t)
    # Parametric equation of ellipse
    el_e = c_e + np.outer(a*cos_az,cos_t) - np.outer(b*sin_az,sin_t)
    el_n = c_n + np.outer(a*sin_az,cos_t) + np.outer(b*cos_az,sin_t)
    return el_e,el_n


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

def fresnelZones(elev,azim,lon,lat,orthoHeight,antennaHeight,GNSSsys=GPSL1):
    """
    Compute Fresnel zones from satellite positions, geographical location and antenna height
    returns a geopandas dataframe Fresnel zones and properties
    """
    
    fresnelIsotropic=firstFresnelZone(GNSSsys.length,antennaHeight,elev)
    return fresnelIsotropic
