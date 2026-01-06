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

#include "gnssir.h"
#include "position.h"


int init_enu_position(enu_position *data){
  data->lat=F_FILL_VALUE;
  data->lon=F_FILL_VALUE;
  data->ortho_height=F_FILL_VALUE;
  data->geoid_height=F_FILL_VALUE;
  data->mjd=F_FILL_VALUE;
  return GNSSIR_SUCCESS;
  
}


int copy_enu_position(const enu_position *in, enu_position *out){
  out->lat=in->lat;
  out->lon=in->lon;
  out->ortho_height=in->ortho_height;
  out->geoid_height=in->geoid_height;
  out->mjd=in->mjd;
  return GNSSIR_SUCCESS;
}

int set_enu_position(enu_position * data,float lat,float lon, float ortho_height, float geoid_height,double mjd){
  data->lat=lat;
  data->lon=lon;
  data->ortho_height=ortho_height;
  data->geoid_height=geoid_height;
  data->mjd=mjd;

  return GNSSIR_SUCCESS;
}
