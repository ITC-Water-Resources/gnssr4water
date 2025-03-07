
/*# This file is part of gnssr4water*/
/*# gnssr4water is free software; you can redistribute it and/or*/
/*# modify it under the terms of the GNU Lesser General Public*/
/*# License as published by the Free Software Foundation; either*/
/*# version 3 of the License, or (at your option) any later version.*/

/*# gnssr4water is distributed in the hope that it will be useful,*/
/*# but WITHOUT ANY WARRANTY; without even the implied warranty of*/
/*# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU*/
/*# Lesser General Public License for more details.*/

/*# You should have received a copy of the GNU Lesser General Public*/
/*# License along with gnssr4water if not, write to the Free Software*/
/*# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA*/

/*# Author Roelof Rietbroek (r.rietbroek@utwente.nl), 2025*/

#include "gnssrlib.h"

#include <string.h>

const gnss_system gnss_unknown=GNSS_UNKNOWN;
const gnss_system gnss_gpsl1=GPSL1;
const gnss_system gnss_gpsl2=GPSL2;
const gnss_system gnss_glonassiil1=GLONASSIIL1

void copy_GNSS_as(gnss_system *sys, const gnss_system * sysfrom){
	memcpy(sys,sysfrom,sizeof(gnss_system));
}


