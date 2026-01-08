/*# This file is part of gnssir*/
/*# gnssir is free software; you can redistribute it and/or*/
/*# modify it under the terms of the GNU Lesser General Public*/
/*# License as published by the Free Software Foundation; either*/
/*# version 3 of the License, or (at your option) any later version.*/

/*# gnssir is distributed in the hope that it will be useful,*/
/*# but WITHOUT ANY WARRANTY; without even the implied warranty of*/
/*# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU*/
/*# Lesser General Public License for more details.*/

/*# You should have received a copy of the GNU Lesser General Public*/
/*# License along with gnssr4water if not, write to the Free Software*/
/*# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA*/

/*# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2026*/


#include "skymask.h"


/* Fast polygon test adapted from this discussion here:https://stackoverflow.com/questions/36399381/whats-the-fastest-way-of-checking-if-a-point-is-inside-a-polygon-in-python*/

int within_mask(const skymask * skymsk,float azimuth,float elevation){
    
    azimuth=wrap_azimuth(azimuth,skymsk->center); 
    
    int length = skymsk->npoints-1;
    float dy2 = elevation - skymsk->elevation[0];
    float dy;
    int intersections = 0;
    int ii = 0;
    int jj = 1;

    /*while ii<length:*/
    while (ii < length){
        dy  = dy2;
        dy2=elevation-skymsk->elevation[jj];

        /*# consider only lines which are not completely above/below/right from the point*/
        
        if (dy*dy2 < 0.0 && (azimuth >= skymsk->azimuth[ii] || azimuth >=skymsk->azimuth[jj])){


            /*# non-horizontal line*/
          if (dy < 0 || dy2 < 0){  
                float F = dy*(skymsk->azimuth[jj] - skymsk->azimuth[ii])/(dy-dy2) + skymsk->azimuth[ii];
                if (azimuth > F){
                  intersections++;
                }else{
                    if (azimuth == F){
                      ///point on line
                      return 2;
                    }
                }
          
          /*# point on upper peak (dy2=dx2=0) or horizontal line (dy=dy2=0 and dx*dx2<=0)*/
          }else{
            if (dy2 == 0.0 && ( azimuth == skymsk->azimuth[jj] || (dy == 0.0 && ((azimuth - skymsk->azimuth[ii])*(azimuth -skymsk->azimuth[jj]) <=0.0)))){
                return 2;
              }
          }
        }
        ii = jj;
        jj++;
        

    }
    return intersections & 1;


}


int init_skymask(skymask * skymsk){
    skymsk->npoints=0;
    skymsk->center=DUNK;
    return GNSSIR_SUCCESS;
}

// add a  new point to the polygon (need to go in a clock wise manner in the az,el grid)
int add_polypoint(skymask *skymsk,float azimuth,float elevation){
  if (SKYMASK_MAX_POINTS < skymsk->npoints+2){
    return SKYMASK_FULL; 
  }
  
  if (elevation > 90){
        return SKYMASK_INVALID;

  }


  if (azimuth < 0){
    switch(skymsk->center){

      case DUNK:
      //set central azimuth when unknown
        skymsk->center=D0;
        break;
      case D180:
        return SKYMASK_INVALID;
        break;
      default:
        break;
    }

  }
  
  if(azimuth > 180 ){
     switch(skymsk->center){

      case DUNK:
      //set central azimuth when unknown
        skymsk->center=D180;
        break;
      case D0:
        return SKYMASK_INVALID;
        break;
      default:
        break;
    }

  }


  skymsk->azimuth[skymsk->npoints]=azimuth;
  skymsk->elevation[skymsk->npoints]=elevation;
  skymsk->npoints++;


  return GNSSIR_SUCCESS;
}

int close_poly(skymask *skymsk){
    if (skymsk->npoints < 2){
    /*#nothing to close*/
      return SKYMASK_INVALID;
    }

    int err= add_polypoint(skymsk,skymsk->azimuth[0],skymsk->elevation[0]);
    if (skymsk-> center == DUNK){
      ///default
      skymsk->center=D180;

    }
    return err;
}
  

int setup_simple_skymask(skymask *skymsk,float min_az,float max_az, float min_el, float max_el){
    int err=init_skymask(skymsk);
    if (err != GNSSIR_SUCCESS){
      return err;
    }

    err=add_polypoint(skymsk,min_az,min_el);
    err=add_polypoint(skymsk,min_az,max_el);
    err=add_polypoint(skymsk,max_az,max_el);
    err=add_polypoint(skymsk,max_az,min_el);
    err=close_poly(skymsk);
    return err;

    
}


float wrap_azimuth(float azimuth, az_center center){
      if (azimuth < 0 && center == D180){
        return 360+azimuth;

      }

      if( azimuth > 180 && center == D0){
          return azimuth-360;
      }
      
      return azimuth;

}

