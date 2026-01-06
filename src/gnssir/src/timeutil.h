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




#ifndef GNSSIR_TIMEUTIL_H
#define GNSSIR_TIMEUTIL_H

double mjd(const int year, const int month,const int day, const int hour, const int minute, const double seccond);

void mjd_to_datetime(double mjd, int *year,int * month, int * day, int * hour,int * minute, double * second); 


#endif //GNSSIR_TIMEUTIL_H

