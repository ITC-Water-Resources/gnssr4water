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

/*# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2025*/


#ifndef GNSSIR_POSITION_H
#define GNSSIR_POSITION_H



struct enu_position{
	//Observer position
	float lat;
	float lon;
	float ortho_height;
	float geoid_height;
	//Optionally has a time tag
	double mjd;
};

typedef struct enu_position enu_position; 

int init_enu_position(enu_position *data);

int copy_enu_position(const enu_position *in, enu_position *out);

int set_enu_position(enu_position * data,float lat,float lon, float ortho_height, float geoid_height,double mjd);

#endif //GNSSIR_POSITION_H
