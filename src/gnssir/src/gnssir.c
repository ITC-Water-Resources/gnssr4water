
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

#include "gnssir.h"

#include <string.h>

const gnss_system gnss_unknown=GNSS_UNKNOWN;
const gnss_system gnss_gpsl1=GPSL1;
const gnss_system gnss_gpsl2=GPSL2;
const gnss_system gnss_glonassiil1=GLONASSIIL1

void copy_GNSS_as(gnss_system *sys, const gnss_system * sysfrom){
	memcpy(sys,sysfrom,sizeof(gnss_system));
}


double mjd(const int yr, const int month,const int day, const int hr, const int min, const int sec){
  
int jd= day-32075+1461*(yr+4800+(month-14)/12)/4+367*(month-2-(month-14)/12*12)/12-3*((yr+4900+(month-14)/12)/100)/4;

  return (double)jd - 2400000.5 + ((double)hr+(double)min/60+(double)sec/3600)/24;



}
