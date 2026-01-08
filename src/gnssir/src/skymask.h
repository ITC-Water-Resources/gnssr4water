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

#ifndef GNSSIR_SKYMASK_H
#define GNSSIR_SKYMASK_H


#ifndef SKYMASK_MAX_POINTS
#define SKYMASK_MAX_POINTS 40
#endif

#define SKYMASK_FULL  -555
#define SKYMASK_INVALID  -556


/**
 * @enum az_center
 * @brief Defines the azimuthal center point for a skymask polygon.
 * 
 * This enumeration specifies different coordinate system conventions for representing
 * azimuth angles, determining whether angles are centered around 0° or 180°.
 * 
 * @var az_center::D0
 * Center at 0°: Azimuth range is [-180°, 180°)
 * 
 * @var az_center::D180
 * Center at 180°: Azimuth range is [0°, 360°)
 * 
 * @var az_center::DUNK
 * Unknown or unspecified center (value: 1)
 */
enum az_center {D0=0,D180=180,DUNK=1};
typedef enum az_center az_center;




struct skymask{
	int npoints;
	float azimuth[SKYMASK_MAX_POINTS];
	float elevation[SKYMASK_MAX_POINTS];
	az_center center;
};

typedef struct skymask skymask;

int init_skymask(skymask * skymsk);

int within_mask(const skymask* skymsk,float azimuth,float elevation);

int add_polypoint(skymask *skymsk,float azimuth,float elevation);

int close_poly(skymask *skymsk);

int setup_simple_skymask(skymask *skymsk,float min_az,float max_az, float min_el, float max_el);

float wrap_azimuth(float azimuth, az_center center);

#endif //GNSSIR_SKYMASK_H
