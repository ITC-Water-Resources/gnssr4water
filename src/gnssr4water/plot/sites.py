# -*- coding: utf-8 -*-
"""
PLotting utilities for site plots

@author: Roelof Rietbroek, r.rietbroek@utwente.nl, 2025
"""

import numpy as np
import matplotlib.pyplot as plt
import cartopy.geodesic as cgeo
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import io
from urllib.request import urlopen, Request
from PIL import Image
from gnssr4water.plot.colors import gnssr_lightgreen,gnssr_darkblue,gnssr_yellow

def image_spoof(self, tile):
    """
    This function reformats web requests from OSM for cartopy.
    
    Heavily based on code by Joshua Hrisko at:
    https://makersportal.com/blog/2020/4/24/geographic-visualizations-in-python-with-cartopy
    """    
    url = self._image_url(tile)                # get the url of the street map API
    req = Request(url)                         # start request
    req.add_header('User-agent','Anaconda 3')  # add user agent to request
    fh = urlopen(req) 
    im_data = io.BytesIO(fh.read())            # get image
    fh.close()                                 # close url
    img = Image.open(im_data)                  # open image with PIL
    img = img.convert(self.desired_tile_form)  # set image format
    
    return img, self.tileextent(tile), 'lower' # reformat for cartopy

###############################################################################

def calc_extent(lon,lat,dist):
    """
    This function calculate extent of map
    
    Parameters
    ----------
    lat,lon: float
        Location of latitude and longitudee in degrees.   

    Return
    ------
    dist: float
        Distance to edge from centre in meters.
    """
    dist_cnr = np.sqrt(2*dist**2)
    top_left = cgeo.Geodesic().direct(points=(lon,lat),azimuths=-45,distances=dist_cnr)[:,0:2][0]
    bot_right = cgeo.Geodesic().direct(points=(lon,lat),azimuths=135,distances=dist_cnr)[:,0:2][0]

    extent = [top_left[0], bot_right[0], bot_right[1], top_left[1]]

    return extent


def siteBaseMap(lon,lat,distance=30,style=None):
    
    #generate a new map
    if style is None:
        img=None
        grdcolor=gnssr_darkblue
    elif style == 'OSM':
        cimgt.OSM.get_image = image_spoof # reformat web request for street map spoofing
        img = cimgt.OSM() # spoofed, downloaded street map
        grdcolor=gnssr_darkblue
    elif style == 'satellite':
        cimgt.QuadtreeTiles.get_image = image_spoof # reformat web request for street map spoofing
        grdcolor= gnssr_yellow
        img = cimgt.QuadtreeTiles()
    else:
        raise ValueError("Style must be 'OSM', 'satellite' or None for no background")
    data_crs = ccrs.PlateCarree()

    fig = plt.figure(figsize=(10,10)) # open matplotlib figure
    ax = plt.axes(projection=data_crs) # project using coordinate reference system (CRS) of street map




    scale = int(120/np.log(distance))
    scale = (scale<20) and scale or 19
    extent = calc_extent(lon,lat,distance*2.5)
    ax.set_extent(extent) # set extents
    if img:
        ax.add_image(img, int(scale)) # add background with zoom specification
    gl = ax.gridlines(draw_labels=True, crs=data_crs,color=grdcolor,lw=0.5,zorder=12)
    gl.xlabel_style = {'size': 12, 'color': grdcolor}
    gl.ylabel_style = {'size': 12, 'color': grdcolor}
    gl.top_labels = False
    gl.right_labels= False
    gl.xpadding = -8
    gl.ypadding = -8

    return ax


